"""
Phase 9: Optimizer Comparison under QPD Noise (Massive Scale).

This script evaluates how different classical optimizers (SPSA, COBYLA, Nelder-Mead)
behave when subjected to the finite-shot statistical noise of QPD sampling.
To evaluate this rigorously at HPC scale (N=16) across multiple seeds without 
incurring intractable classical emulation overhead, we compute the exact statevector
energy and analytically inject the theoretically exact QPD Gaussian sampling noise 
bounded by Hoeffding's inequality: sigma = Gamma * ||H|| / sqrt(N_shots).
"""

import os
import sys
import json
import time
import numpy as np
import networkx as nx
from qiskit.quantum_info import Statevector

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dynacut.executor import maxcut_hamiltonian, DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
OUT_FILE = os.path.join(RESULTS_DIR, 'optimizer_comparison.json')

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def run_optimizer_comparison():
    # 1. Setup an HPC-scale problem
    N = 16
    G = nx.random_regular_graph(3, N, seed=42)
    edges = list(G.edges())
    hamiltonian = maxcut_hamiltonian(edges, N)
    norm_H = sum(abs(c) for c in hamiltonian.coeffs)
    
    # QAOA ansatz
    ansatz = DynaCutExecutor.build_ansatz(N, reps=1, ansatz_type="qaoa", hamiltonian=hamiltonian)
    
    # Find strategy
    hypervisor = ResourceHypervisor(max_qubits_per_fragment=8)
    strategy = hypervisor.find_optimal_strategy(ansatz)
    print(f"Strategy: {strategy.num_fragments} fragments, {strategy.num_cuts} cuts.")
    
    # Theoretical QPD overhead
    gamma = 3 ** strategy.num_cuts
    num_samples = 100_000 # tightly restricted shots
    variance = (gamma**2) * (norm_H**2) / num_samples
    sigma = np.sqrt(variance)
    print(f"Analytic Noise: Gamma={gamma}, ||H||={norm_H:.2f}, Sigma={sigma:.4f}")
    
    # Exact Ground State
    from qiskit_algorithms import NumPyMinimumEigensolver
    solver = NumPyMinimumEigensolver()
    exact_res = solver.compute_minimum_eigenvalue(hamiltonian)
    exact_energy = exact_res.eigenvalue.real
    print(f"Exact Minimum Energy: {exact_energy:.4f}")
    
    optimizers = ["COBYLA", "Nelder-Mead", "SPSA"]
    maxiter = 60
    num_seeds = 5
    
    results = {"exact_energy": float(exact_energy), "optimizers": {opt: [] for opt in optimizers}}
    
    for seed in range(num_seeds):
        print(f"\n=================== SEED {seed} ===================")
        np.random.seed(seed + 100)
        initial_params = np.random.uniform(-np.pi, np.pi, ansatz.num_parameters)
        
        for opt in optimizers:
            print(f"--- Running VQE with {opt} ---")
            t0 = time.time()
            
            history = []
            
            # Custom objective function injecting exact QPD Gaussian noise
            def noisy_objective(params):
                bound_circuit = ansatz.assign_parameters(params)
                sv = Statevector(bound_circuit)
                exact_val = float(np.real(sv.expectation_value(hamiltonian)))
                
                # SPSA requires stochastic noise to behave properly
                noisy_val = exact_val + np.random.normal(0, sigma)
                history.append(exact_val) # track the TRUE underlying energy for plotting
                return noisy_val
                
            from scipy.optimize import minimize
            if opt.upper() == "SPSA":
                from qiskit_algorithms.optimizers import SPSA
                optimizer = SPSA(maxiter=maxiter)
                res = optimizer.minimize(noisy_objective, initial_params)
                optimal_energy = res.fun
            else:
                res = minimize(
                    noisy_objective,
                    initial_params,
                    method=opt,
                    options={"maxiter": maxiter, "disp": False},
                )
                optimal_energy = res.fun
                
            elapsed = time.time() - t0
            true_final_energy = history[-1] if history else optimal_energy
            print(f"Finished {opt} in {elapsed:.2f}s. True Final Energy: {true_final_energy:.4f}")
            
            results["optimizers"][opt].append({
                "seed": seed,
                "convergence": history,
                "time_seconds": elapsed,
                "optimal_energy": float(optimal_energy)
            })
            
            with open(OUT_FILE, 'w') as f:
                json.dump(results, f, indent=4)
            
    print(f"\nOptimizer comparison complete! Saved to {OUT_FILE}")

if __name__ == "__main__":
    run_optimizer_comparison()
