import os
import time
import json
import logging
import numpy as np
from typing import Dict, Any

from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor
from dynacut.experiment_runner import ExperimentRunner
from dynacut.ground_state import compute_exact_ground_state

logger = logging.getLogger(__name__)

def generate_random_graph(num_nodes: int, p: float, seed: int):
    rng = np.random.default_rng(seed)
    edges = []
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if rng.random() < p:
                edges.append((i, j))
    return edges

def shot_noise_experiment(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    num_qubits = config["num_qubits"]
    num_samples = config["num_samples"]
    
    # Generate graph
    edges = generate_random_graph(num_qubits, p=0.5, seed=seed)
    hamiltonian = maxcut_hamiltonian(edges, num_qubits)
    
    # Exact Ground State
    exact_energy = compute_exact_ground_state(hamiltonian)
    
    # Ansatz
    ansatz = DynaCutExecutor.build_ansatz(num_qubits, reps=2, entanglement="linear")
    rng = np.random.default_rng(seed)
    params = rng.uniform(0, 2 * np.pi, size=ansatz.num_parameters)
    
    # Cut Evaluation
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_ram_gb=23.0, max_qubits_per_fragment=num_qubits//2 + 1)
    strategy = hypervisor.find_optimal_strategy(ansatz)
    
    executor = DynaCutExecutor(hypervisor)
    try:
        e_cut = executor.evaluate_energy(
            params, ansatz, hamiltonian, strategy, 
            num_samples=num_samples, reconstruction_method="ibm"
        )
        cuts = strategy.num_cuts
    except Exception as e:
        logger.error(f"Cut evaluation failed: {e}")
        e_cut = float('nan')
        cuts = 0
        
    return {
        "num_qubits": num_qubits,
        "num_samples": num_samples if num_samples != np.inf else -1,
        "exact_energy": exact_energy,
        "e_cut": e_cut,
        "error_cut": abs(e_cut - exact_energy) if not np.isnan(e_cut) else float('nan'),
        "cuts": cuts
    }

def main():
    logging.basicConfig(level=logging.INFO)
    sample_counts = [100, 500, 1000, 5000, 10000, np.inf]
    
    all_raw_results = []
    
    for num_qubits in [10, 14]:
        for s in sample_counts:
            logger.info(f"Running Shot Sweep: {num_qubits} qubits, shots={s}")
            s_label = "inf" if s == np.inf else str(s)
            runner = ExperimentRunner(experiment_name=f"shot_noise_{num_qubits}q_s{s_label}")
            res = runner.run(
                shot_noise_experiment, 
                config={"num_qubits": num_qubits, "num_samples": s}
            )
            all_raw_results.extend(res["raw"])
            
    os.makedirs("results", exist_ok=True)
    with open("results/shot_noise_combined_raw.json", "w") as f:
        json.dump(all_raw_results, f, indent=2)
    logger.info("Saved combined shot noise results to results/shot_noise_combined_raw.json")

if __name__ == "__main__":
    main()
