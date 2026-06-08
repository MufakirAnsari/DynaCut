import os
import time
import json
import logging
import numpy as np
from typing import Dict, Any

from qiskit.circuit.library import QAOAAnsatz, TwoLocal
from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.hamiltonians import h2_molecule_hamiltonian
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

def build_qaoa_ansatz(hamiltonian, reps=2):
    return QAOAAnsatz(hamiltonian, reps=reps).decompose()

def build_ucc_inspired_ansatz(num_qubits, reps=2):
    # Pseudo-UCC chemistry ansatz using TwoLocal with particle-preserving-like gates
    # Since we can't use qiskit_nature UCCSD without the dependency, we use a heuristic
    ansatz = TwoLocal(
        num_qubits, 
        rotation_blocks=['ry', 'rz'], 
        entanglement_blocks='cx', 
        entanglement='linear', 
        reps=reps
    )
    return ansatz.decompose()

def cross_ansatz_experiment(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    problem = config["problem"]
    ansatz_type = config["ansatz_type"]
    num_qubits = config.get("num_qubits", 10)
    
    # 1. Setup Hamiltonian
    if problem == "maxcut":
        edges = generate_random_graph(num_qubits, p=0.5, seed=seed)
        hamiltonian = maxcut_hamiltonian(edges, num_qubits)
    elif problem == "h2":
        num_qubits = 4
        hamiltonian = h2_molecule_hamiltonian()
    else:
        raise ValueError(f"Unknown problem {problem}")
        
    exact_energy = compute_exact_ground_state(hamiltonian)
    
    # 2. Ansatz
    if ansatz_type == "he":
        ansatz = DynaCutExecutor.build_ansatz(num_qubits, reps=2, entanglement="linear")
    elif ansatz_type == "qaoa":
        ansatz = build_qaoa_ansatz(hamiltonian, reps=2)
    elif ansatz_type == "ucc_heuristic":
        ansatz = build_ucc_inspired_ansatz(num_qubits, reps=2)
    else:
        raise ValueError(f"Unknown ansatz {ansatz_type}")
        
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
        logger.error(f"Cut evaluation failed for {problem} / {ansatz_type}: {e}")
        e_cut = float('nan')
        t_cut = 0.0
        cuts = 0
        
    return {
        "problem": problem,
        "ansatz_type": ansatz_type,
        "num_qubits": num_qubits,
        "exact_energy": float(exact_energy),
        "e_cut": float(e_cut),
        "error": float(abs(e_cut - exact_energy)) if not np.isnan(e_cut) else float('nan'),
        "cuts": cuts,
        "time": float(t_cut)
    }

def main():
    logging.basicConfig(level=logging.INFO)
    
    configs = [
        {"problem": "maxcut", "ansatz": "he", "qubits": 10},
        {"problem": "maxcut", "ansatz": "qaoa", "qubits": 10},
        {"problem": "h2", "ansatz": "he", "qubits": 4},
        {"problem": "h2", "ansatz": "ucc_heuristic", "qubits": 4},
    ]
    
    all_raw_results = []
    
    for c in configs:
        p = c["problem"]
        a = c["ansatz"]
        q = c["qubits"]
        logger.info(f"Running Cross-Ansatz: {p} with {a}")
        runner = ExperimentRunner(experiment_name=f"cross_ansatz_{p}_{a}")
        res = runner.run(
            cross_ansatz_experiment, 
            config={"problem": p, "ansatz_type": a, "num_qubits": q}
        )
        all_raw_results.extend(res["raw"])
            
    os.makedirs("results", exist_ok=True)
    with open("results/cross_ansatz_combined_raw.json", "w") as f:
        json.dump(all_raw_results, f, indent=2)
    logger.info("Saved combined cross-ansatz results to results/cross_ansatz_combined_raw.json")

if __name__ == "__main__":
    main()
