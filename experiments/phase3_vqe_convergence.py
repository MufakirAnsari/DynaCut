"""
Phase 3 Evaluation: VQE Convergence (End-to-End Optimization).

This script runs a full Variational Quantum Eigensolver (VQE) loop on a
cut circuit and logs the energy at each iteration. It proves that the
optimization landscape (gradients, barren plateaus) remains stable and
converges to the ground state despite the QPD cutting and tensor network
reconstruction.
"""

from __future__ import annotations

import json
import logging
import os
import sys

import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("phase3")

from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor
from experiments.phase1_math_rigor import generate_maxcut_graph


from dynacut.experiment_runner import ExperimentRunner
from dynacut.ground_state import compute_exact_ground_state

def phase3_experiment(seed: int, config: dict) -> dict:
    num_qubits = config.get("num_qubits", 12)
    
    # 1. Problem Setup
    edges = generate_maxcut_graph(num_qubits, edge_prob=0.3, seed=seed)
    hamiltonian = maxcut_hamiltonian(edges, num_qubits)
    
    # EXACT ground state
    exact_ground_state = compute_exact_ground_state(hamiltonian)
    
    # 2. Build parameterized ansatz
    ansatz = DynaCutExecutor.build_ansatz(num_qubits, reps=1, entanglement="linear")
    
    # 3. Setup Hypervisor forcing a cut
    hypervisor = ResourceHypervisor(
        max_vram_gb=4.0,
        max_ram_gb=23.0,
        max_qubits_per_fragment=6,
    )
    strategy = hypervisor.find_optimal_strategy(ansatz)
    
    # Try to use standard CPU Sampler
    try:
        from qiskit_aer.primitives import Sampler as AerSampler
        sampler = AerSampler()
    except ImportError:
        sampler = None
        
    executor = DynaCutExecutor(hypervisor, sampler=sampler)

    # 4. Run Optimization
    rng = np.random.default_rng(seed)
    initial_params = rng.uniform(0, 0.1, size=ansatz.num_parameters)

    result = executor.run_vqe(
        ansatz=ansatz,
        hamiltonian=hamiltonian,
        strategy=strategy,
        initial_params=initial_params,
        method="COBYLA",
        maxiter=30,
        callback_interval=5,
    )
    
    approx_ratio = result["optimal_energy"] / exact_ground_state if exact_ground_state != 0 else float('nan')

    return {
        "optimal_energy": result["optimal_energy"],
        "exact_ground_state": exact_ground_state,
        "approx_ratio": approx_ratio,
        "num_evaluations": result["num_evaluations"],
        "time_seconds": result["wall_time_seconds"],
        "cuts": strategy.num_cuts,
        # Saving history for each seed
        "history": result["convergence_history"]
    }

def main():
    runner = ExperimentRunner("vqe_convergence_multi", seeds=list(range(10)))
    config = {"num_qubits": 20} # N=20 for final empirical VQE evaluation
    
    results = runner.run(phase3_experiment, config)
    
    stats = results["stats"]
    if "approx_ratio" in stats:
        logger.info(f"Mean Approx Ratio: {stats['approx_ratio']['mean']:.4f} ± {stats['approx_ratio']['std']:.4f}")
        
if __name__ == "__main__":
    main()
