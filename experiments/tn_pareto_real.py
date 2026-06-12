"""
Pareto Frontier Experiment: QPD Sampling Variance vs RAM Ceiling Reduction.

This experiment validates Figure 5 of the paper by sweeping over partition
granularity (max_qubits_per_fragment) for a fixed 20-qubit MaxCut circuit.
As the fragment size shrinks:
  - RAM usage drops (fewer qubits per statevector fragment)
  - But the number of cuts K increases, raising QPD overhead Gamma^2
    and therefore the sampling variance / reconstruction error.

The Pareto frontier shows this fundamental trade-off.
"""
import json
import logging
import time
import sys
import numpy as np
from typing import Dict, Any

from qiskit.quantum_info import Statevector

from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor
from dynacut.experiment_runner import ExperimentRunner
from dynacut.baselines import baseline_statevector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_maxcut_graph(num_nodes: int, edge_prob: float = 0.5, seed: int = 42) -> list:
    """Generate a random Erdos-Renyi graph and return its edge list."""
    import networkx as nx
    G = nx.erdos_renyi_graph(num_nodes, edge_prob, seed=seed)
    return list(G.edges())


def run_pareto_experiment(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    num_qubits = config.get('num_qubits', 20)

    # Use moderate density so we get meaningful cuts at different partition sizes
    edges = generate_maxcut_graph(num_qubits, edge_prob=0.25, seed=seed)
    hamiltonian = maxcut_hamiltonian(edges, num_qubits)
    ansatz = DynaCutExecutor.build_ansatz(num_qubits, reps=1, entanglement="linear")

    params = np.random.RandomState(seed).uniform(0, 2 * np.pi, ansatz.num_parameters)
    bound_circ = ansatz.assign_parameters(params)

    # Ground truth: exact statevector
    energy_exact, _, _ = baseline_statevector(bound_circ, hamiltonian)

    metrics: Dict[str, Any] = {}
    metrics["energy_exact"] = energy_exact

    # Sweep over fragment sizes: large fragments = few cuts = low error but high RAM
    # Small fragments = many cuts = high error but low RAM
    fragment_sizes = [20, 16, 14, 12, 10, 9, 8, 7, 6]

    for frag_size in fragment_sizes:
        label = f"frag{frag_size}"

        if frag_size >= num_qubits:
            # No cutting needed — this is the monolithic baseline
            metrics[f"energy_{label}"] = energy_exact
            metrics[f"error_{label}"] = 0.0
            metrics[f"ram_mb_{label}"] = (2**num_qubits) * 16 / (1024**2)
            metrics[f"num_cuts_{label}"] = 0
            metrics[f"num_fragments_{label}"] = 1
            metrics[f"qpd_overhead_{label}"] = 1.0
            continue

        hypervisor = ResourceHypervisor(
            max_vram_gb=100.0,  # Don't limit VRAM — let the fragment size control partitioning
            max_qubits_per_fragment=frag_size,
        )
        executor = DynaCutExecutor(hypervisor)
        strategy = hypervisor.find_optimal_strategy(ansatz)

        K = strategy.num_cuts
        num_frags = strategy.num_fragments

        # SAFETY ABORT: If KaHyPar found a cut requiring > 5 cuts, it will take over 8 hours to evaluate this single point.
        # Skip it to prevent the script from stalling for days.
        if K > 5:
            logger.warning(f"Fragment size {frag_size} requires K={K} cuts. This is too large to evaluate in reasonable time. Skipping.")
            metrics[f"energy_{label}"] = float('nan')
            metrics[f"error_{label}"] = float('nan')
            metrics[f"ram_mb_{label}"] = float('nan')
            metrics[f"num_cuts_{label}"] = K
            metrics[f"num_fragments_{label}"] = num_frags
            metrics[f"qpd_overhead_{label}"] = strategy.qpd_overhead
            metrics[f"time_{label}"] = float('nan')
            continue

        # RAM per fragment: 2^(frag_size) * 16 bytes, plus TN overhead
        ram_per_frag_mb = (2**frag_size) * 16 / (1024**2)
        # Total peak RAM is dominated by the largest fragment + TN storage
        # TN storage: O(6^K) floats
        tn_storage_mb = (6**K) * 8 / (1024**2)
        peak_ram_mb = ram_per_frag_mb + tn_storage_mb

        try:
            t0 = time.time()
            energy_cut = executor.evaluate_energy(
                params, ansatz, hamiltonian, strategy,
                reconstruction_method="tn", max_bond=None,  # Exact contraction
            )
            t_cut = time.time() - t0

            error = abs(energy_cut - energy_exact)
        except Exception as e:
            logger.warning(f"Fragment size {frag_size} failed: {e}")
            energy_cut = float('nan')
            error = float('nan')
            t_cut = float('nan')

        metrics[f"energy_{label}"] = energy_cut
        metrics[f"error_{label}"] = error
        metrics[f"ram_mb_{label}"] = peak_ram_mb
        metrics[f"num_cuts_{label}"] = K
        metrics[f"num_fragments_{label}"] = num_frags
        metrics[f"qpd_overhead_{label}"] = strategy.qpd_overhead
        metrics[f"time_{label}"] = t_cut

    return metrics


if __name__ == "__main__":
    runner = ExperimentRunner(experiment_name="tn_pareto_real", seeds=list(range(10)))
    logger.info("Running Pareto frontier experiment for 20 qubits...")
    res = runner.run(run_pareto_experiment, config={"num_qubits": 20})
