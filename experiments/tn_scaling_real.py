import json
import logging
import time
import numpy as np
from typing import Dict, Any

from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor
from dynacut.experiment_runner import ExperimentRunner
from experiments.phase1_math_rigor import generate_maxcut_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_scaling_experiment(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    num_qubits = config.get('num_qubits', 10)
    
    edges = generate_maxcut_graph(num_qubits, edge_prob=0.15, seed=seed)
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_qubits_per_fragment=14)
    executor = DynaCutExecutor(hypervisor)
    hamiltonian = maxcut_hamiltonian(edges, num_qubits)
    ansatz = DynaCutExecutor.build_ansatz(num_qubits, reps=1, entanglement="linear")
    
    params = np.random.RandomState(seed).uniform(0, 2*np.pi, ansatz.num_parameters)
    strategy = hypervisor.find_optimal_strategy(ansatz)
    
    metrics = {}
    metrics["num_cuts"] = strategy.num_cuts
    metrics["num_fragments"] = strategy.num_fragments
    
    # --- Method 1 & 2: Exact ---
    if num_qubits <= 16:
        start_time = time.time()
        energy_ibm = executor.evaluate_energy(
            params, ansatz, hamiltonian, strategy, reconstruction_method="ibm"
        )
        metrics["time_ibm"] = time.time() - start_time
        metrics["energy_ibm"] = energy_ibm
        
        start_time = time.time()
        energy_tn_exact = executor.evaluate_energy(
            params, ansatz, hamiltonian, strategy, reconstruction_method="tn", max_bond=None
        )
        metrics["time_tn_exact"] = time.time() - start_time
        metrics["energy_tn_exact"] = energy_tn_exact
    
    # --- Method 3: TN Approximate ---
    chis = [2, 4, 8, 16, 32]
    for chi in chis:
        start_time = time.time()
        energy_approx = executor.evaluate_energy(
            params, ansatz, hamiltonian, strategy, reconstruction_method="tn", max_bond=chi
        )
        metrics[f"time_tn_chi_{chi}"] = time.time() - start_time
        metrics[f"energy_tn_chi_{chi}"] = energy_approx
        
    return metrics

if __name__ == "__main__":
    sweep_results = {}
    for q in [24, 26]:
        logger.info(f"Running scaling for {q} qubits...")
        runner = ExperimentRunner(experiment_name=f"tn_scaling_real_{q}", seeds=list(range(5)))
        res = runner.run(run_scaling_experiment, config={"num_qubits": q})
        sweep_results[q] = res
        
    with open("results/tn_scaling_combined.json", "w") as f:
        json.dump(sweep_results, f, indent=2)
    logger.info("Saved tn_scaling_combined.json")
