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
logger = logging.getLogger("ablation_optimizer")

def optimizer_experiment(seed: int, config: dict) -> dict:
    n = 10
    method = config["method"]
    
    edges = generate_maxcut_graph(n, edge_prob=0.3, seed=seed)
    hamiltonian = maxcut_hamiltonian(edges, n)
    ansatz = DynaCutExecutor.build_ansatz(n, reps=1, entanglement="linear")
    
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_qubits_per_fragment=6)
    strategy = hypervisor.find_optimal_strategy(ansatz)
    executor = DynaCutExecutor(hypervisor)
    
    rng = np.random.default_rng(seed)
    initial_params = rng.uniform(0, 0.1, size=ansatz.num_parameters)
    
    res = executor.run_vqe(
        ansatz=ansatz,
        hamiltonian=hamiltonian,
        strategy=strategy,
        initial_params=initial_params,
        method=method,
        maxiter=30,
        callback_interval=5,
    )
    
    return {
        "method": method,
        "optimal_energy": res["optimal_energy"],
        "num_evaluations": res["num_evaluations"],
        "time": res["wall_time_seconds"]
    }

def main():
    methods = ["COBYLA", "Nelder-Mead", "SLSQP", "L-BFGS-B"]
    all_results = []
    
    for m in methods:
        logger.info(f"Running Optimizer Ablation for {m}")
        runner = ExperimentRunner(f"ablation_optimizer_{m}", seeds=list(range(5)))
        res = runner.run(optimizer_experiment, {"method": m})
        
        stats = res["stats"]
        all_results.append({
            "method": m,
            "mean_energy": stats["optimal_energy"]["mean"],
            "mean_evals": stats["num_evaluations"]["mean"],
            "mean_time": stats["time"]["mean"]
        })
        
    os.makedirs("results", exist_ok=True)
    with open("results/ablation_optimizer.json", "w") as f:
        json.dump(all_results, f, indent=4)

if __name__ == "__main__":
    main()
