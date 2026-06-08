import json
import logging
import os
import time
import numpy as np

from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor
from experiments.phase1_math_rigor import generate_maxcut_graph
from dynacut.experiment_runner import ExperimentRunner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ablation_fragment_size")

def fragment_experiment(seed: int, config: dict) -> dict:
    n = 18 # fixed circuit size
    max_frag = config["max_fragment_size"]
    
    edges = generate_maxcut_graph(n, edge_prob=0.2, seed=seed)
    hamiltonian = maxcut_hamiltonian(edges, n)
    ansatz = DynaCutExecutor.build_ansatz(n, reps=1, entanglement=edges)
    
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_qubits_per_fragment=max_frag)
    t0 = time.time()
    strategy = hypervisor.find_optimal_strategy(ansatz)
    t_partition = time.time() - t0
    
    return {
        "max_fragment_size": max_frag,
        "cuts": strategy.num_cuts,
        "time": t_partition,
        "fragments": strategy.num_fragments,
        "ram_gb": strategy.estimated_contraction_ram_gb
    }

def main():
    sizes = [4, 6, 8, 10, 12, 14, 16, 18]
    all_results = []
    
    for s in sizes:
        logger.info(f"Running Fragment Ablation for size {s}")
        runner = ExperimentRunner(f"ablation_fragment_size_{s}", seeds=list(range(5)))
        res = runner.run(fragment_experiment, {"max_fragment_size": s})
        
        stats = res["stats"]
        all_results.append({
            "max_fragment_size": s,
            "mean_cuts": stats["cuts"]["mean"],
            "mean_fragments": stats["fragments"]["mean"],
            "mean_time": stats["time"]["mean"]
        })
        
    os.makedirs("results", exist_ok=True)
    with open("results/ablation_fragment_size.json", "w") as f:
        json.dump(all_results, f, indent=4)

if __name__ == "__main__":
    main()
