import os
import time
import json
import logging
import numpy as np
from typing import Dict, Any

from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.hamiltonians import h2_molecule_hamiltonian, tfim_hamiltonian, heisenberg_hamiltonian
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

def cross_problem_experiment(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    problem = config["problem"]
    num_qubits = config.get("num_qubits", 10)
    
    # 1. Setup Hamiltonian
    if problem == "maxcut":
        edges = generate_random_graph(num_qubits, p=0.5, seed=seed)
        hamiltonian = maxcut_hamiltonian(edges, num_qubits)
    elif problem == "h2":
        num_qubits = 4
        hamiltonian = h2_molecule_hamiltonian()
    elif problem == "tfim":
        hamiltonian = tfim_hamiltonian(num_qubits, j_coupling=1.0, h_field=1.0)
    elif problem == "heisenberg":
        hamiltonian = heisenberg_hamiltonian(num_qubits, j_coupling=1.0)
    else:
        raise ValueError(f"Unknown problem {problem}")
        
    exact_energy = compute_exact_ground_state(hamiltonian)
    
    # 2. Ansatz
    # For Sprint 3.3, we'll support HE ansatz right now. We can add QAOA/UCCSD later.
    ansatz = DynaCutExecutor.build_ansatz(num_qubits, reps=2, entanglement="linear")
    rng = np.random.default_rng(seed)
    params = rng.uniform(0, 2 * np.pi, size=ansatz.num_parameters)
    
    # 3. Evaluate Energy
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_ram_gb=23.0, max_qubits_per_fragment=max(1, num_qubits//2))
    strategy = hypervisor.find_optimal_strategy(ansatz)
    
    executor = DynaCutExecutor(hypervisor)
    try:
        t0 = time.time()
        e_cut = executor.evaluate_energy(
            params, ansatz, hamiltonian, strategy, 
            num_samples=np.inf, reconstruction_method="ibm"
        )
        t_cut = time.time() - t0
        cuts = strategy.num_cuts
    except Exception as e:
        logger.error(f"Cut evaluation failed for {problem}: {e}")
        e_cut = float('nan')
        t_cut = 0.0
        cuts = 0
        
    return {
        "problem": problem,
        "num_qubits": num_qubits,
        "exact_energy": float(exact_energy),
        "e_cut": float(e_cut),
        "error": float(abs(e_cut - exact_energy)) if not np.isnan(e_cut) else float('nan'),
        "cuts": cuts,
        "time": float(t_cut)
    }

def main():
    logging.basicConfig(level=logging.INFO)
    
    problems = [
        {"name": "maxcut", "qubits": 10},
        {"name": "maxcut", "qubits": 14},
        {"name": "tfim", "qubits": 10},
        {"name": "tfim", "qubits": 14},
        {"name": "heisenberg", "qubits": 8}, # Heisenberg is denser, 8 qubits for safety
        {"name": "h2", "qubits": 4}
    ]
    
    all_raw_results = []
    
    for p in problems:
        name = p["name"]
        q = p["qubits"]
        logger.info(f"Running Cross-Problem: {name} ({q} qubits)")
        runner = ExperimentRunner(experiment_name=f"cross_problem_{name}_{q}q")
        res = runner.run(
            cross_problem_experiment, 
            config={"problem": name, "num_qubits": q}
        )
        all_raw_results.extend(res["raw"])
            
    os.makedirs("results", exist_ok=True)
    with open("results/cross_problem_combined_raw.json", "w") as f:
        json.dump(all_raw_results, f, indent=2)
    logger.info("Saved combined cross-problem results to results/cross_problem_combined_raw.json")

if __name__ == "__main__":
    main()
