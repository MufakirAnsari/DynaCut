"""
Phase 4 Evaluation: Qubit Scaling & VRAM Flattening Benchmark.

This script sweeps across different qubit counts (e.g., 10 to 40) to record
execution time and peak memory bounds. It generates data proving that
DynaCut-V2 enables flat VRAM consumption at the cost of manageable classical
overhead.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("phase4")

from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor
from experiments.phase1_math_rigor import generate_maxcut_graph
from dynacut.profiler import measure_peak_memory, exact_statevector_vram_mb


from dynacut.experiment_runner import ExperimentRunner

def phase4_experiment(seed: int, config: dict) -> dict:
    n = config.get("num_qubits", 10)
    
    edges = generate_maxcut_graph(n, edge_prob=0.15, seed=seed)
    hamiltonian = maxcut_hamiltonian(edges, n)
    ansatz = DynaCutExecutor.build_ansatz(n, reps=1)
    
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_ram_gb=23.0, max_qubits_per_fragment=14)
    executor = DynaCutExecutor(hypervisor)
    
    t0_hyper = time.time()
    strategy = hypervisor.find_optimal_strategy(ansatz)
    t_hyper = time.time() - t0_hyper
    
    rng = np.random.default_rng(seed)
    params = rng.uniform(0, 0.1, size=ansatz.num_parameters)
    
    
    # We use measure_peak_memory to track peak memory
    energy, peak_mb, t_eval = measure_peak_memory(
        executor.evaluate_energy,
        params, ansatz, hamiltonian, strategy, 
        num_samples=np.inf, reconstruction_method="tn", max_bond=None
    )
    
    return {
        "qubits": n,
        "cuts": strategy.num_cuts,
        "fragments": strategy.num_fragments,
        "hypervisor_time": t_hyper,
        "execution_time": t_eval,
        "vram_bound_mb": peak_mb,
        "exact_vram_mb": exact_statevector_vram_mb(n),
        "energy": energy
    }

def main():
    # Phase 4 sweeps across qubits. We will configure the runner for each qubit size.
    # To use ExperimentRunner properly, we can wrap the runner in a loop over sizes.
    qubit_sizes = [10, 12, 14, 16]
    
    all_results = []
    
    for n in qubit_sizes:
        logger.info(f"Running sweep for {n} qubits")
        runner = ExperimentRunner(f"phase4_sweep_{n}q", seeds=[0, 1, 2, 3, 4])
        config = {"num_qubits": n}
        
        res = runner.run(phase4_experiment, config)
        
        
        # Aggregate mean over seeds for this n
        mean_time = res["stats"]["execution_time"]["mean"]
        mean_cuts = res["stats"]["cuts"]["mean"]
        mean_vram_mb = res["stats"]["vram_bound_mb"]["mean"]
        exact_vram_mb = res["stats"]["exact_vram_mb"]["mean"]
        
        all_results.append({
            "qubits": n,
            "mean_execution_time": mean_time,
            "mean_cuts": mean_cuts,
            "mean_vram_mb": mean_vram_mb,
            "exact_vram_mb": exact_vram_mb
        })
        
    os.makedirs("results", exist_ok=True)
    with open("results/scaling_benchmark.json", "w") as f:
        json.dump(all_results, f, indent=4)
        
if __name__ == "__main__":
    main()
