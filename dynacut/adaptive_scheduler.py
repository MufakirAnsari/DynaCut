"""
dynacut.adaptive_scheduler — Resource-Aware Cut Strategy Optimizer.

This module balances two competing constraints:
  1. **Quantum constraint (VRAM):** Each sub-fragment must have ≤ N qubits
     so its statevector fits in GPU memory.  For a GTX 1650 with 4 GB VRAM,
     the maximum is ~27 qubits (2^27 × 16 bytes = 2 GB for complex128),
     but we use 20 as a safe limit to allow for batching overhead.
  2. **Classical constraint (RAM):** The tensor network contraction of the
     cut-reconstruction must fit in system RAM.  More cuts → larger tensors
     → more RAM for contraction.

The scheduler iteratively searches for the partition that maximizes fragment
size (to minimize the number of cuts) while respecting both budgets.

Design Rationale
----------------
We search from large fragments downward because:
  - Fewer cuts = exponentially less sampling overhead.
  - The QPD overhead scales as O(4^K) where K = number of cuts.
  - Finding the LARGEST partition that fits is equivalent to minimizing K.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import VF2Layout
from qiskit.transpiler.coupling import CouplingMap

from .topology import HypergraphPartitioner
from .knitting import HybridTensorNetworkKnitter, QPD_BASIS_SIZE

logger = logging.getLogger(__name__)


@dataclass
class CutStrategy:
    """Encapsulates a complete cutting strategy with cost estimates."""

    partition_labels: Dict[int, int]
    """Maps qubit_index → fragment_id."""

    cut_edges: List[Tuple[int, int]]
    """Edges in the interaction graph that are cut."""

    num_fragments: int
    """Number of distinct fragments."""

    max_fragment_size: int
    """Maximum number of qubits in any single fragment."""

    num_cuts: int
    """Number of wire cuts."""

    qpd_overhead: float
    """Sampling overhead factor: 4^num_cuts."""

    estimated_contraction_ram_gb: float
    """Estimated RAM for exact tensor contraction."""

    contraction_mode: str
    """'exact', 'approximate', or 'trivial' (no cuts)."""

    @property
    def is_trivial(self) -> bool:
        return self.num_cuts == 0


class ResourceHypervisor:
    """Resource-aware cut strategy optimizer.

    Searches for the partition that minimizes the number of wire cuts
    while guaranteeing:
      (a) Every fragment fits in GPU VRAM.
      (b) The classical tensor contraction fits in system RAM.

    Parameters
    ----------
    max_vram_gb : float
        GPU VRAM budget (default: 4.0 for GTX 1650).
    max_ram_gb : float
        System RAM budget for classical contraction (default: 23.0).
    max_qubits_per_fragment : int, optional
        Override the automatic VRAM-derived qubit limit.
    coupling_map : optional
        Hardware coupling map for topology-aware partitioning.
    """

    def __init__(
        self,
        max_vram_gb: float = 4.0,
        max_ram_gb: float = 23.0,
        max_qubits_per_fragment: Optional[int] = None,
        coupling_map=None,
    ):
        self.max_vram_gb = max_vram_gb
        self.max_ram_gb = max_ram_gb

        if max_qubits_per_fragment is not None:
            self.max_qubits = max_qubits_per_fragment
        else:
            # Derive from VRAM: statevector of n qubits requires 2^n × 16 bytes
            # Solve: 2^n × 16 / 1e9 ≤ max_vram_gb × 0.8  (80% safety margin)
            usable_bytes = max_vram_gb * 0.8 * 1e9
            self.max_qubits = int(math.log2(usable_bytes / 16))
            # Cap at 25 qubits: 2^25 × 16 = 512 MB statevector, safe for
            # most GPUs while keeping fragment circuits simulable.
            self.max_qubits = min(self.max_qubits, 25)

        self.partitioner = HypergraphPartitioner(coupling_map=coupling_map)
        self.knitter = HybridTensorNetworkKnitter(max_classical_ram_gb=max_ram_gb)
        self.coupling_map = coupling_map

        logger.info(
            "ResourceHypervisor initialized: max_qubits=%d, VRAM=%.1fGB, RAM=%.1fGB",
            self.max_qubits, max_vram_gb, max_ram_gb,
        )

    def find_optimal_strategy(self, circuit: QuantumCircuit) -> CutStrategy:
        """Find the optimal cutting strategy for the given circuit.

        Parameters
        ----------
        circuit : QuantumCircuit
            The full parameterized ansatz circuit.

        Returns
        -------
        CutStrategy
            The optimal strategy balancing quantum and classical costs.
        """
        n = circuit.num_qubits

        # Trivial case: circuit fits without cutting
        if n <= self.max_qubits:
            is_embeddable = self.check_hardware_embeddability(circuit)
            logger.info("Circuit (%d qubits) fits in VRAM. VF2 Embeddable: %s", n, is_embeddable)
            return CutStrategy(
                partition_labels={q: 0 for q in range(n)},
                cut_edges=[],
                num_fragments=1,
                max_fragment_size=n,
                num_cuts=0,
                qpd_overhead=1.0,
                estimated_contraction_ram_gb=0.0,
                contraction_mode="trivial",
            )

        logger.info(
            "Circuit (%d qubits) exceeds VRAM limit (%d max). "
            "Searching for optimal partition...",
            n, self.max_qubits,
        )

        # Search from largest possible fragment size downward
        best_strategy: Optional[CutStrategy] = None

        for frag_size in range(self.max_qubits, max(1, self.max_qubits // 2 - 1), -1):
            labels, cut_edges = self.partitioner.partition(circuit, frag_size)
            num_cuts = len(cut_edges)
            num_fragments = len(set(labels.values()))

            # Estimate classical contraction RAM
            # Each cut introduces a QPD_BASIS_SIZE-dimensional index.
            # The largest intermediate in contraction is bounded by:
            #   prod(bond_dims along the widest slice)
            # Conservative upper bound: D^(num_cuts) × 8 bytes
            # Use log-space to avoid OverflowError for large K
            log2_elements = num_cuts * math.log2(QPD_BASIS_SIZE)
            log2_ram_gb = log2_elements + math.log2(8) - 30  # 30 = log2(1024^3)
            if log2_ram_gb < 64:  # fits in a float
                estimated_ram_gb = 2 ** log2_ram_gb
            else:
                estimated_ram_gb = float('inf')

            if log2_elements < 1023:  # fits in a float
                qpd_overhead = float(QPD_BASIS_SIZE ** num_cuts)
            else:
                qpd_overhead = float('inf')

            if estimated_ram_gb <= self.max_ram_gb:
                best_strategy = CutStrategy(
                    partition_labels=labels,
                    cut_edges=cut_edges,
                    num_fragments=num_fragments,
                    max_fragment_size=frag_size,
                    num_cuts=num_cuts,
                    qpd_overhead=qpd_overhead,
                    estimated_contraction_ram_gb=estimated_ram_gb,
                    contraction_mode="exact",
                )
                logger.info(
                    "Found strategy: %d fragments, %d cuts, "
                    "QPD overhead=%.0f, est. RAM=%.3f GB",
                    num_fragments, num_cuts, qpd_overhead, estimated_ram_gb,
                )
                break

        # Fallback: if no exact contraction fits, use approximate mode
        if best_strategy is None:
            labels, cut_edges = self.partitioner.partition(circuit, self.max_qubits)
            num_cuts = len(cut_edges)
            num_fragments = len(set(labels.values()))

            logger.warning(
                "No exact contraction fits in %.1f GB RAM. "
                "Using approximate SVD contraction (%d cuts).",
                self.max_ram_gb, num_cuts,
            )

            # Use log-space to avoid OverflowError for large K
            log2_el = num_cuts * math.log2(QPD_BASIS_SIZE)
            qpd_overhead_val = float(QPD_BASIS_SIZE ** num_cuts) if log2_el < 1023 else float('inf')

            best_strategy = CutStrategy(
                partition_labels=labels,
                cut_edges=cut_edges,
                num_fragments=num_fragments,
                max_fragment_size=self.max_qubits,
                num_cuts=num_cuts,
                qpd_overhead=qpd_overhead_val,
                estimated_contraction_ram_gb=self.max_ram_gb,
                contraction_mode="approximate",
            )

        return best_strategy

    def check_hardware_embeddability(self, circuit: QuantumCircuit) -> bool:
        """Verify if the circuit can be embedded on the target hardware using VF2 graph isomorphism."""
        if self.coupling_map is None:
            return True
            
        try:
            if isinstance(self.coupling_map, CouplingMap):
                cmap = self.coupling_map
            else:
                cmap = CouplingMap(self.coupling_map)
                
            pm = PassManager(VF2Layout(cmap, strict_direction=False))
            pm.run(circuit)
            if pm.property_set['layout']:
                return True
            return False
        except Exception as e:
            logger.warning(f"VF2 embeddability check failed: {e}")
            return False
