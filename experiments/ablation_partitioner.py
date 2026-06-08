import json
import logging
import os
import time

import numpy as np

from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor
from experiments.phase1_math_rigor import generate_maxcut_graph
from dynacut.baselines import (
    baseline_random_partitioning,
    baseline_metis_partitioning,
)
from dynacut.experiment_runner import ExperimentRunner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ablation_partitioner")

def partitioner_experiment(seed: int, config: dict) -> dict:
    n = config.get("num_qubits", 14)
    
    edges = generate_maxcut_graph(n, edge_prob=0.3, seed=seed)
    hamiltonian = maxcut_hamiltonian(edges, n)
    
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_qubits_per_fragment=n//2 + 1)
    executor = DynaCutExecutor(hypervisor)
    ansatz = DynaCutExecutor.build_ansatz(n, reps=1, entanglement=edges)
    
    # 1. Random Partitioning
    e_rand, t_rand, c_rand = baseline_random_partitioning(ansatz, hamiltonian, max_fragments=2)
    
    # 2. METIS Partitioning
    e_metis, t_metis, c_metis = baseline_metis_partitioning(ansatz, hamiltonian, max_fragments=2)
    
    # 3. DynaCut-V2 (KL-Bisection)
    t0 = time.time()
    strategy = hypervisor.find_optimal_strategy(ansatz)
    t_kl = time.time() - t0
    c_kl = strategy.num_cuts
    
    # For speed, we just report the cuts and time, energy error is secondary here
    # since we want to evaluate partitioners on cut weight!
    return {
        "random_cuts": c_rand,
        "metis_cuts": c_metis,
        "kl_cuts": c_kl,
        "random_time": t_rand,
        "metis_time": t_metis,
        "kl_time": t_kl,
    }

def main():
    qubit_sizes = [10, 14, 18]
    all_results = []
    
    for n in qubit_sizes:
        logger.info(f"Running Partitioner Ablation for {n} qubits")
        runner = ExperimentRunner(f"ablation_partitioner_{n}q", seeds=list(range(10)))
        res = runner.run(partitioner_experiment, {"num_qubits": n})
        
        # Pull stats
        stats = res["stats"]
        all_results.append({
            "qubits": n,
            "random": {"mean_cuts": stats["random_cuts"]["mean"]},
            "metis": {"mean_cuts": stats["metis_cuts"]["mean"]},
            "kl_bisection": {"mean_cuts": stats["kl_cuts"]["mean"]}
        })
        
    os.makedirs("results", exist_ok=True)
    with open("results/ablation_partitioner.json", "w") as f:
        json.dump(all_results, f, indent=4)

if __name__ == "__main__":
    main()
