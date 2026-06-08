import os
import time
import logging
import numpy as np
from typing import Dict, Any

from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit_aer.primitives import Sampler, Estimator

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

def noise_impact_experiment(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    num_qubits = config["num_qubits"]
    noise_rate = config["noise_rate"]
    
    # Generate graph
    edges = generate_random_graph(num_qubits, p=0.5, seed=seed)
    hamiltonian = maxcut_hamiltonian(edges, num_qubits)
    
    # Exact Ground State
    exact_energy = compute_exact_ground_state(hamiltonian)
    
    # Ansatz
    ansatz = DynaCutExecutor.build_ansatz(num_qubits, reps=2, entanglement="linear")
    rng = np.random.default_rng(seed)
    params = rng.uniform(0, 2 * np.pi, size=ansatz.num_parameters)
    bound_circuit = ansatz.assign_parameters(params)
    
    # Create Noise Model
    noise_model = NoiseModel()
    if noise_rate > 0:
        error_1q = depolarizing_error(noise_rate / 10.0, 1) # typical 1q error is 1/10 of 2q error
        error_2q = depolarizing_error(noise_rate, 2)
        noise_model.add_all_qubit_quantum_error(error_1q, ['rx', 'ry', 'rz', 'h', 'sx', 'x'])
        noise_model.add_all_qubit_quantum_error(error_2q, ['cx', 'cz'])
        
        # Sampler and Estimator with noise
        noisy_sampler = Sampler(run_options={"noise_model": noise_model, "shots": 10000})
        noisy_estimator = Estimator(run_options={"noise_model": noise_model, "shots": 10000})
    else:
        # Noiseless
        noisy_sampler = Sampler(run_options={"shots": 10000})
        noisy_estimator = Estimator(run_options={"shots": 10000})
        
    # Uncut Baseline (Noisy)
    job = noisy_estimator.run([bound_circuit], [hamiltonian])
    e_noisy_uncut = job.result().values[0]
    
    # Cut Evaluation (Noisy)
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_ram_gb=23.0, max_qubits_per_fragment=num_qubits//2 + 1)
    strategy = hypervisor.find_optimal_strategy(ansatz)
    
    executor = DynaCutExecutor(hypervisor, sampler=noisy_sampler)
    try:
        e_noisy_cut = executor.evaluate_energy(
            params, ansatz, hamiltonian, strategy, 
            num_samples=np.inf, reconstruction_method="ibm"
        )
        cuts = strategy.num_cuts
    except Exception as e:
        logger.error(f"Cut evaluation failed: {e}")
        e_noisy_cut = float('nan')
        cuts = 0
        
    return {
        "num_qubits": num_qubits,
        "noise_rate": noise_rate,
        "exact_energy": exact_energy,
        "e_noisy_uncut": e_noisy_uncut,
        "e_noisy_cut": e_noisy_cut,
        "error_uncut": abs(e_noisy_uncut - exact_energy),
        "error_cut": abs(e_noisy_cut - exact_energy) if not np.isnan(e_noisy_cut) else float('nan'),
        "cuts": cuts
    }

def main():
    logging.basicConfig(level=logging.INFO)
    noise_rates = [0.0, 1e-4, 1e-3, 1e-2, 5e-2, 1e-1]
    
    all_raw_results = []
    
    for num_qubits in [10]:
        for p in noise_rates:
            logger.info(f"Running Noise Sweep: {num_qubits} qubits, p={p}")
            runner = ExperimentRunner(experiment_name=f"noise_impact_{num_qubits}q_p{p}")
            res = runner.run(
                noise_impact_experiment, 
                config={"num_qubits": num_qubits, "noise_rate": p}
            )
            all_raw_results.extend(res["raw"])
            
    # Save combined results
    import json
    os.makedirs("results", exist_ok=True)
    with open("results/noise_impact_combined_raw.json", "w") as f:
        json.dump(all_raw_results, f, indent=2)
    logger.info("Saved combined noise impact results to results/noise_impact_combined_raw.json")

if __name__ == "__main__":
    main()
