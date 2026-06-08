"""
Phase 1 Evaluation: Mathematical Rigor (12 Qubits).

This script proves that Q-Forge's circuit cutting produces EXACTLY the same
energy as an un-cut direct statevector simulation.  Any discrepancy beyond
floating-point noise would indicate a bug in the QPD ↔ TN mapping.

Methodology
-----------
1. Create a random 12-qubit MaxCut graph.
2. Build the MaxCut Hamiltonian as a SparsePauliOp.
3. Build a hardware-efficient ansatz with fixed random parameters.
4. Compute the EXACT energy via direct statevector simulation (ground truth).
5. Compute the CUT energy by:
   a. Partitioning the circuit into 2 fragments of ≤6 qubits.
   b. Running all QPD sub-experiments via qiskit-addon-cutting.
   c. Reconstructing the expectation value.
6. Compare: |E_exact - E_cut| must be < 1e-10.
"""

from __future__ import annotations

import logging
import sys
import time

import numpy as np
import networkx as nx

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("phase1")

# Q-Forge imports
from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor


def generate_maxcut_graph(num_nodes: int, edge_prob: float = 0.5, seed: int = 42) -> list:
    """Generate a random Erdos-Renyi graph and return its edge list."""
    G = nx.erdos_renyi_graph(num_nodes, edge_prob, seed=seed)
    return list(G.edges())


from dynacut.experiment_runner import ExperimentRunner

def phase1_experiment(seed: int, config: dict) -> dict:
    num_qubits = config.get("num_qubits", 12)
    max_fragment = config.get("max_fragment", 6)
    
    # 1. Problem Setup
    edges = generate_maxcut_graph(num_qubits, edge_prob=0.15, seed=seed)
    hamiltonian = maxcut_hamiltonian(edges, num_qubits)

    # 2. Build ansatz
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_qubits_per_fragment=max_fragment)
    executor = DynaCutExecutor(hypervisor)
    ansatz = executor.build_ansatz(num_qubits, reps=2, entanglement="linear")

    rng = np.random.default_rng(seed)
    params = rng.uniform(0, 2 * np.pi, size=ansatz.num_parameters)

    # 3. Ground Truth
    hypervisor_nocut = ResourceHypervisor(max_vram_gb=100.0)
    executor_nocut = DynaCutExecutor(hypervisor_nocut)
    strategy_nocut = hypervisor_nocut.find_optimal_strategy(ansatz)

    t0 = time.time()
    energy_exact = executor_nocut.evaluate_energy(params, ansatz, hamiltonian, strategy_nocut)
    t_exact = time.time() - t0

    # 4. Cut Simulation
    strategy_cut = hypervisor.find_optimal_strategy(ansatz)
    t0 = time.time()
    energy_cut = executor.evaluate_energy(
        params, ansatz, hamiltonian, strategy_cut, 
        reconstruction_method="tn", max_bond=None
    )
    t_cut = time.time() - t0

    diff = abs(energy_exact - energy_cut)
    
    return {
        "energy_exact": energy_exact,
        "energy_cut": energy_cut,
        "diff": diff,
        "time_exact": t_exact,
        "time_cut": t_cut,
        "num_cuts": strategy_cut.num_cuts,
        "qpd_overhead": strategy_cut.qpd_overhead
    }


def main():
    runner = ExperimentRunner("phase1_math_rigor", seeds=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    config = {"num_qubits": 12, "max_fragment": 6}
    
    results = runner.run(phase1_experiment, config)
    
    stats = results["stats"]
    if "diff" in stats:
        diff_mean = stats["diff"]["mean"]
        diff_max = stats["diff"]["max"]
        logger.info(f"Mean Difference: {diff_mean:.2e}, Max Difference: {diff_max:.2e}")
        if diff_max > 1e-10:
            logger.error("TEST FAILED! Discrepancy > 1e-10 detected.")
            sys.exit(1)
        else:
            logger.info("TEST PASSED! All seeds match up to machine precision.")


if __name__ == "__main__":
    main()
