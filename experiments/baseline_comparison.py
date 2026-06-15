import os
import json
import logging
import time
from typing import Dict, List, Any

import numpy as np

from dynacut.executor import maxcut_hamiltonian
from dynacut.executor import DynaCutExecutor
from dynacut.baselines import (
    baseline_statevector,
    baseline_qiskit_cutting_raw,
    baseline_random_partitioning,
    baseline_mps_simulation,
    baseline_aer_noise,
    baseline_metis_partitioning,
    baseline_cutqc
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_maxcut_graph(num_nodes: int, p: float = 0.5, seed: int = 42) -> np.ndarray:
    """Generate Erdos-Renyi random graph adjacency matrix."""
    rng = np.random.default_rng(seed)
    adj = np.zeros((num_nodes, num_nodes))
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if rng.random() < p:
                adj[i, j] = 1.0
                adj[j, i] = 1.0
    return adj


def run_baselines() -> None:
    """Run baseline comparisons and save to JSON."""
    qubit_sizes = [10, 14]
    
    results: List[Dict[str, Any]] = []

    for n in qubit_sizes:
        logger.info(f"Running baselines for {n} qubits...")
        
        # Setup problem
        from dynacut.executor import maxcut_hamiltonian
        
        edges = []
        p = 0.3
        np.random.seed(42)
        for i in range(n):
            for j in range(i + 1, n):
                if np.random.random() < p:
                    edges.append((i, j))
        
        hamiltonian = maxcut_hamiltonian(edges, n)
        
        # 2. Setup cutting strategy
        # Find exactly the strategy used by DynaCut-V2
        from dynacut.adaptive_scheduler import ResourceHypervisor
        hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_qubits_per_fragment=n//2 + 1)
        executor = DynaCutExecutor(hypervisor)
        ansatz = executor.build_ansatz(n, reps=1, entanglement="linear")
        
        # Generate random params
        params = np.random.uniform(0, 2*np.pi, ansatz.num_parameters)
        bound_circuit = ansatz.assign_parameters(params)

        strategy = hypervisor.find_optimal_strategy(ansatz)
        
        # 3. Baseline 1: Statevector (Exact Ground Truth)
        e_exact, t_exact, _ = baseline_statevector(bound_circuit, hamiltonian)
        results.append({
            "method": "Statevector",
            "qubits": n,
            "energy": e_exact,
            "time": t_exact,
            "error": 0.0,
            "cuts": 0
        })

        # 4. Baseline 2: Qiskit Addon Cutting (Raw)
        try:
            e_raw, t_raw, c_raw = baseline_qiskit_cutting_raw(bound_circuit, hamiltonian, strategy)
            err_raw = abs(e_raw - e_exact)
        except Exception as e:
            logger.warning(f"Raw cutting failed for {n}q: {e}")
            e_raw, t_raw, err_raw, c_raw = float('nan'), 0.0, float('nan'), strategy.num_cuts

        results.append({
            "method": "Raw Cutting",
            "qubits": n,
            "energy": e_raw,
            "time": t_raw,
            "error": err_raw,
            "cuts": c_raw
        })

        # 5. Baseline 3: Random Partitioning
        try:
            e_rand, t_rand, c_rand = baseline_random_partitioning(bound_circuit, hamiltonian, max_fragments=2)
            err_rand = abs(e_rand - e_exact) if not np.isnan(e_rand) else float('nan')
        except Exception as e:
            logger.warning(f"Random partitioning failed for {n}q: {e}")
            e_rand, t_rand, err_rand, c_rand = float('nan'), 0.0, float('nan'), 0

        results.append({
            "method": "Random Partitioning",
            "qubits": n,
            "energy": e_rand,
            "time": t_rand,
            "error": err_rand,
            "cuts": c_rand
        })

        # 6. Baseline 4: MPS Simulation
        e_mps, t_mps, c_mps = baseline_mps_simulation(bound_circuit, hamiltonian, max_bond=64)
        err_mps = abs(e_mps - e_exact) if not np.isnan(e_mps) else float('nan')
        results.append({
            "method": "MPS (bond=64)",
            "qubits": n,
            "energy": e_mps,
            "time": t_mps,
            "error": err_mps,
            "cuts": c_mps
        })
        
        # 7. Baseline 5: Aer Noise Model
        e_noise, t_noise, c_noise = baseline_aer_noise(bound_circuit, hamiltonian)
        err_noise = abs(e_noise - e_exact) if not np.isnan(e_noise) else float('nan')
        results.append({
            "method": "Aer Noise Model",
            "qubits": n,
            "energy": e_noise,
            "time": t_noise,
            "error": err_noise,
            "cuts": c_noise
        })

        # 8. Baseline 6: METIS Partitioning
        try:
            e_metis, t_metis, c_metis = baseline_metis_partitioning(bound_circuit, hamiltonian, max_fragments=2)
            err_metis = abs(e_metis - e_exact) if not np.isnan(e_metis) else float('nan')
        except Exception as e:
            logger.warning(f"METIS partitioning failed for {n}q: {e}")
            e_metis, t_metis, err_metis, c_metis = float('nan'), 0.0, float('nan'), 0

        results.append({
            "method": "METIS Partitioning",
            "qubits": n,
            "energy": e_metis,
            "time": t_metis,
            "error": err_metis,
            "cuts": c_metis
        })
        
        # 9. Baseline 7: CutQC (Simulated)
        try:
            e_cutqc, t_cutqc, c_cutqc = baseline_cutqc(bound_circuit, hamiltonian)
            err_cutqc = abs(e_cutqc - e_exact) if not np.isnan(e_cutqc) else float('nan')
        except Exception as e:
            logger.warning(f"CutQC baseline failed for {n}q: {e}")
            e_cutqc, t_cutqc, err_cutqc, c_cutqc = float('nan'), 0.0, float('nan'), 0
            
        results.append({
            "method": "CutQC (Simulated)",
            "qubits": n,
            "energy": e_cutqc,
            "time": t_cutqc,
            "error": err_cutqc,
            "cuts": c_cutqc
        })

        # 10. DynaCut-V2 (TN Exact)
        try:
            t0 = time.time()
            executor = DynaCutExecutor(hypervisor)
            e_tn = executor.evaluate_energy(
                params, ansatz, hamiltonian, strategy, 
                num_samples=np.inf, reconstruction_method="ibm", max_bond=None
            )
            t_tn = time.time() - t0
            err_tn = abs(e_tn - e_exact)
        except Exception as e:
            logger.warning(f"TN Reconstruction failed for {n}q: {e}")
            e_tn, t_tn, err_tn = float('nan'), 0.0, float('nan')

        results.append({
            "method": "DynaCut-V2 (TN Exact)",
            "qubits": n,
            "energy": e_tn,
            "time": t_tn,
            "error": err_tn,
            "cuts": strategy.num_cuts
        })

    # Save results
    os.makedirs("results", exist_ok=True)
    with open("results/baseline_comparison.json", "w") as f:
        json.dump(results, f, indent=2)

    logger.info("Done! Results saved to results/baseline_comparison.json")


if __name__ == "__main__":
    run_baselines()
