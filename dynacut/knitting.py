"""
dynacut.knitting — Hybrid Tensor-Network Circuit Knitting Engine.

This module implements the core scientific novelty of Q-Forge: treating the
classical post-processing of circuit cutting as a tensor network contraction
problem rather than naive statistical sampling.

Mathematical Foundation
-----------------------
When a wire connecting sub-circuits S_A and S_B is cut, the identity channel
on that wire is decomposed via Quasi-Probability Decomposition (QPD):

    I = Σ_k  c_k · (M_k ⊗ P_k)

where M_k are measurement bases on S_A, P_k are preparation bases on S_B,
c_k are quasi-probability coefficients, and k ∈ {0, ..., D-1} with D typically
equal to 4 (the Pauli basis: I, X, Y, Z for single-qubit wire cuts).

The key insight is that each sub-circuit S becomes a tensor T_S whose indices
correspond to the cut wires attached to it. If S has two cut wires, T_S is a
matrix of shape (D, D). Element T_S[i, j] is the expectation value obtained
by running S on the QPU with the i-th basis on cut-wire-1 and the j-th basis
on cut-wire-2.

The global expectation value is then recovered by contracting the full tensor
network: a weighted sum over all basis combinations, with weights given by the
QPD coefficients c_k.

We use:
  - ``quimb`` for tensor network construction, index management, and
    approximate (SVD-truncated) contraction.
  - ``opt_einsum`` (via quimb/cotengra) for finding the optimal contraction
    path that minimizes intermediate memory.

Design Rationale
----------------
Why tensor-network contraction instead of naive reconstruction?
  - Naive reconstruction via ``reconstruct_expectation_values`` from
    qiskit-addon-cutting internally performs a weighted sum over all
    sub-experiment results. This works but treats the reconstruction as a
    black box.
  - By exposing the reconstruction as an explicit tensor network, we gain:
    (a) The ability to estimate contraction cost *before* running QPU jobs.
    (b) The ability to use approximate contraction (SVD truncation) to trade
        controlled precision for massive memory savings.
    (c) A direct pathway to integrate with cotengra/opt-einsum for optimal
        contraction ordering.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

import numpy as np
import quimb.tensor as qtn

if TYPE_CHECKING:
    from qiskit.quantum_info import PauliList, SparsePauliOp
    from qiskit.primitives import SamplerResult

from qiskit_addon_cutting.utils.observable_grouping import ObservableCollection
from qiskit_addon_cutting.utils.bitwise import bit_count
from qiskit_addon_cutting.cutting_experiments import _get_pauli_indices

logger = logging.getLogger(__name__)

# QPD basis size for single-qubit wire cuts (Pauli M&P decomposition)
QPD_BASIS_SIZE = 4


class HybridTensorNetworkKnitter:
    """Tensor-Network Assisted Circuit Knitting engine.

    This class takes the raw expectation values from QPU execution of the
    cutting sub-experiments and assembles them into a quimb TensorNetwork.
    Contraction of this network yields the reconstructed global expectation
    value.

    Parameters
    ----------
    max_classical_ram_gb : float
        Maximum classical RAM budget for tensor contraction. If the optimal
        exact contraction would exceed this, the engine falls back to
        approximate MPS-based contraction with SVD truncation.
    max_bond : int
        Maximum bond dimension for approximate contraction. Controls the
        precision-vs-memory tradeoff.
    """

    def __init__(
        self,
        max_classical_ram_gb: float = 23.0,
        max_bond: int = 256,
    ):
        self.max_classical_ram_gb = max_classical_ram_gb
        self.max_bond = max_bond

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def from_cutting_results(
        self,
        results: Dict[Any, SamplerResult],
        coefficients: List,
        subobservables: Dict[Any, PauliList],
        hamiltonian: SparsePauliOp,
    ) -> float:
        """Extract expectations, build the TN, and contract it.

        This method bridges qiskit-addon-cutting's raw sampler results
        to quimb's tensor network formulation.
        """
        num_groups = len(coefficients)
        partition_keys = sorted(results.keys())
        num_obs = len(hamiltonian)

        subsystem_observables = {
            label: ObservableCollection(subobs)
            for label, subobs in subobservables.items()
        }

        frag_expvals: Dict[Any, List[np.ndarray]] = {
            label: [] for label in partition_keys
        }

        for i in range(num_groups):
            for label in partition_keys:
                so = subsystem_observables[label]
                subobs_list = subobservables[label]

                subsystem_evs = [
                    np.zeros(len(cog.commuting_observables))
                    for cog in so.groups
                ]

                current_result = results[label]
                for k, cog in enumerate(so.groups):
                    idx = i * len(so.groups) + k
                    quasi_probs = current_result.quasi_dists[idx]
                    num_meas_bits = len(_get_pauli_indices(cog))
                    for outcome, quasi_prob in quasi_probs.items():
                        obs_outcomes = outcome & ((1 << num_meas_bits) - 1)
                        qpd_outcomes = outcome >> num_meas_bits
                        qpd_factor = 1 - 2 * (bit_count(qpd_outcomes) & 1)

                        for m, mask in enumerate(cog.pauli_bitmasks):
                            obs = 1 - 2 * (bit_count(obs_outcomes & mask) & 1)
                            subsystem_evs[k][m] += quasi_prob * qpd_factor * obs

                per_obs = np.ones(num_obs)
                for k_obs, subobservable in enumerate(subobs_list):
                    per_obs[k_obs] = np.mean(
                        [subsystem_evs[m][n_idx]
                         for m, n_idx in so.lookup[subobservable]]
                    )

                frag_expvals[label].append(per_obs)

        coeff_values = np.array([c[0] for c in coefficients])
        reconstructed = np.zeros(num_obs)

        for obs_idx in range(num_obs):
            tensors = []
            tensors.append(qtn.Tensor(
                data=coeff_values, inds=("qpd",), tags={"coefficients"}
            ))

            for label in partition_keys:
                frag_data = np.array(
                    [frag_expvals[label][g][obs_idx] for g in range(num_groups)]
                )
                tensors.append(qtn.Tensor(
                    data=frag_data, inds=("qpd",), tags={f"frag_{label}"}
                ))

            tn = qtn.TensorNetwork(tensors)
            
            # Using hyperedge contraction
            cost_info = self.estimate_contraction_cost(tn)
            
            # Ensure max_bond from the knitter instance is used for approximate contraction
            # But currently we only do exact for hyperedges unless specified
            try:
                res = tn.contract(optimize="auto", output_inds=())
            except Exception:
                # Fallback if something goes wrong
                res = tn.contract(optimize="auto")
                
            if hasattr(res, "data"):
                val = float(np.real(np.asarray(res.data).ravel()[0]))
            elif isinstance(res, np.ndarray):
                val = float(np.real(res.ravel()[0]))
            else:
                val = float(np.real(res))

            reconstructed[obs_idx] = val

        energy = float(np.real(
            sum(c * ev for c, ev in zip(hamiltonian.coeffs, reconstructed))
        ))

        return energy

    def build_tensor_network(
        self,
        fragment_results: Dict[int, np.ndarray],
        coefficients: np.ndarray,
        cut_map: Dict[int, List[int]],
    ) -> qtn.TensorNetwork:
        """Assemble a quimb TensorNetwork from QPU sub-experiment results.

        Parameters
        ----------
        fragment_results : dict[int, np.ndarray]
            Maps fragment_id → array of expectation values.  The array shape
            is (D, D, ..., D) with one axis per cut wire attached to that
            fragment, where D = QPD_BASIS_SIZE.  Element [i, j, ...] is the
            expectation value obtained by running the fragment with the i-th
            QPD basis on cut-wire-1, j-th on cut-wire-2, etc.
        coefficients : np.ndarray
            The QPD quasi-probability coefficients for each cut wire.
            Shape: (num_cuts, D).  These are folded into the tensor data
            as multiplicative weights.
        cut_map : dict[int, list[int]]
            Maps fragment_id → list of cut_wire_ids that are attached to
            that fragment.  Two fragments sharing the same cut_wire_id will
            have a shared index in the tensor network, triggering contraction.

        Returns
        -------
        qtn.TensorNetwork
            A tensor network whose contraction yields the reconstructed
            global expectation value.
        """
        tensors = []

        for frag_id, data in fragment_results.items():
            # Determine the indices for this fragment's tensor.
            # Each cut wire becomes a named index "cut_{wire_id}".
            wire_ids = cut_map.get(frag_id, [])
            inds = tuple(f"cut_{wid}" for wid in wire_ids)

            if len(inds) == 0:
                # Fragment has no cuts — it's a scalar tensor
                T = qtn.Tensor(
                    data=np.array(data).reshape(()),
                    inds=(),
                    tags={f"frag_{frag_id}"},
                )
            else:
                # Fold QPD coefficients into the tensor data.
                # For each axis (cut wire), multiply by the coefficient vector.
                weighted_data = np.copy(data).astype(np.float64)
                for axis_idx, wire_id in enumerate(wire_ids):
                    if wire_id < len(coefficients):
                        coeff_shape = [1] * weighted_data.ndim
                        coeff_shape[axis_idx] = QPD_BASIS_SIZE
                        coeff_vec = coefficients[wire_id].reshape(coeff_shape)
                        weighted_data = weighted_data * coeff_vec

                T = qtn.Tensor(
                    data=weighted_data,
                    inds=inds,
                    tags={f"frag_{frag_id}"},
                )

            tensors.append(T)

        tn = qtn.TensorNetwork(tensors)
        logger.info(
            "Built TensorNetwork: %d tensors, %d total indices",
            len(tensors), len(tn.ind_map),
        )
        return tn

    def estimate_contraction_cost(
        self, tn: qtn.TensorNetwork
    ) -> Dict[str, Any]:
        """Estimate the memory and FLOP cost of exact contraction.

        Returns
        -------
        dict
            Keys: 'estimated_ram_gb', 'estimated_flops', 'path',
                  'can_contract_exactly'.
        """
        try:
            # Use cotengra (bundled with quimb) to find optimal path
            path, info = tn.contraction_path_info(optimize="auto")
        except (AttributeError, TypeError):
            # Fallback: try the older API or just contract
            try:
                info = tn.contract(get="path-info", optimize="auto")
                path = info.path if hasattr(info, "path") else None
            except Exception:
                return {
                    "estimated_ram_gb": 0.0,
                    "estimated_flops": 0,
                    "path": None,
                    "can_contract_exactly": True,
                }

        # largest_intermediate is in number of elements
        largest = getattr(info, "largest_intermediate", 0)
        ram_gb = largest * 8 / (1024**3)  # float64

        return {
            "estimated_ram_gb": ram_gb,
            "estimated_flops": getattr(info, "opt_cost", 0),
            "path": path,
            "can_contract_exactly": ram_gb <= self.max_classical_ram_gb,
        }

    def contract(self, tn: qtn.TensorNetwork) -> float:
        """Contract the tensor network to obtain the global expectation value.

        Dynamically chooses between:
        1. **Exact contraction** via opt-einsum/cotengra if the estimated
           memory fits within the classical RAM budget.
        2. **Approximate contraction** via MPS-based compression with SVD
           truncation if exact contraction would exceed the budget.

        Returns
        -------
        float
            The reconstructed global expectation value ⟨H⟩.
        """
        cost_info = self.estimate_contraction_cost(tn)

        if cost_info["can_contract_exactly"]:
            logger.info(
                "Exact contraction: est. %.3f GB RAM",
                cost_info["estimated_ram_gb"],
            )
            result = tn.contract(optimize="auto")
        else:
            logger.warning(
                "Exact contraction requires %.2f GB > %.2f GB budget. "
                "Falling back to approximate MPS contraction (max_bond=%d).",
                cost_info["estimated_ram_gb"],
                self.max_classical_ram_gb,
                self.max_bond,
            )
            try:
                result = tn.contract_compressed(
                    max_bond=self.max_bond,
                    optimize="auto-hq",
                )
            except (AttributeError, TypeError):
                # Older quimb: fallback to regular contraction
                result = tn.contract(optimize="auto")

        # Extract scalar value
        if hasattr(result, "data"):
            val = float(np.real(result.data.ravel()[0]))
        elif isinstance(result, (np.ndarray,)):
            val = float(np.real(result.ravel()[0]))
        else:
            val = float(np.real(result))

        return val
