"""
Phase 7: SVD Bond Dimension (chi) Ablation (MPS Baseline).

This script isolates the effect of the SVD truncation bond dimension (`max_bond`)
on the exactness and efficiency of the Tensor Network reconstruction.
To evaluate the true scaling on a large N=26 dense graph, we use Qiskit Aer's 
Matrix Product State (MPS) simulator. This allows us to cleanly measure the 
Truncation Error (epsilon_trunc) and extract the exact Pareto frontier 
(Error vs. Time/Memory) without exploding the QPD sampler.
"""

import os
import sys
import time
import json
import tracemalloc
import numpy as np
import networkx as nx
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit_aer import AerSimulator

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dynacut.executor import maxcut_hamiltonian, DynaCutExecutor

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
OUT_FILE = os.path.join(RESULTS_DIR, 'svd_ablation.json')

def generate_sbm_graph(N, p_in, p_out, seed=42):
    """Generate a dense 2-block Stochastic Block Model graph."""
    sizes = [N // 2, N - N // 2]
    probs = [[p_in, p_out], [p_out, p_in]]
    G = nx.stochastic_block_model(sizes, probs, seed=seed)
    return G

def run_svd_ablation():
    N = 26
    print(f"Generating N={N} dense SBM graph...")
    # Dense graph: high p_in and moderate p_out
    G = generate_sbm_graph(N, p_in=0.8, p_out=0.1, seed=123)
    edges = list(G.edges())
    print(f"Graph constructed: N={N}, Edges={len(edges)}")
    
    hamiltonian = maxcut_hamiltonian(edges, N)
    ansatz = DynaCutExecutor.build_ansatz(N, reps=1, ansatz_type="qaoa", hamiltonian=hamiltonian)
    
    np.random.seed(42)
    params = np.random.uniform(-np.pi, np.pi, ansatz.num_parameters)
    bound_circuit = ansatz.assign_parameters(params)
    
    # We need to save the expectation value in the circuit for Aer
    obs = SparsePauliOp(hamiltonian.paulis, hamiltonian.coeffs)
    bound_circuit.save_expectation_value(obs, bound_circuit.qubits)
    
    results = {}
    
    # 1. Exact Statevector (1GB RAM)
    print("\nEvaluating EXACT unpartitioned statevector energy...")
    t0 = time.time()
    tracemalloc.start()
    
    # Since we need to get peak memory accurately, we use the statevector simulator
    sim_exact = AerSimulator(method='statevector')
    res_exact = sim_exact.run(bound_circuit).result()
    exact_energy = res_exact.data()['expectation_value']
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed_exact = time.time() - t0
    peak_mb_exact = peak / (1024 * 1024)
    
    print(f"  Exact Energy: {exact_energy:.6f}")
    print(f"  Time:         {elapsed_exact:.2f}s")
    print(f"  Peak Memory:  {peak_mb_exact:.2f} MB")
    
    results["exact_sv"] = {
        "energy": float(np.real(exact_energy)),
        "time_seconds": elapsed_exact,
        "peak_memory_mb": peak_mb_exact
    }
    
    # 2. MPS Truncation Sweep
    bond_dims = [256, 128, 64, 32, 16, 8, 4, 2]
    
    for chi in bond_dims:
        print(f"\nEvaluating with MPS max_bond_dimension = {chi}...")
        t0 = time.time()
        tracemalloc.start()
        
        try:
            sim_mps = AerSimulator(method='matrix_product_state')
            sim_mps.set_options(matrix_product_state_max_bond_dimension=chi)
            res_mps = sim_mps.run(bound_circuit).result()
            
            if not res_mps.success:
                raise Exception(res_mps.status)
                
            energy = res_mps.data()['expectation_value']
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            elapsed = time.time() - t0
            peak_mb = peak / (1024 * 1024)
            err = abs(energy - exact_energy)
            
            print(f"  Energy:      {energy:.6f}")
            print(f"  Error:       {err:.2e}")
            print(f"  Time:        {elapsed:.2f}s")
            print(f"  Peak Memory: {peak_mb:.2f} MB")
            
            results[str(chi)] = {
                "max_bond": chi,
                "energy": float(np.real(energy)),
                "error": float(np.real(err)),
                "time_seconds": elapsed,
                "peak_memory_mb": peak_mb
            }
        except Exception as e:
            tracemalloc.stop()
            print(f"  Failed: {e}")
            
        with open(OUT_FILE, 'w') as f:
            json.dump(results, f, indent=4)

    print(f"\nSVD Ablation complete. Results saved to {OUT_FILE}")

if __name__ == "__main__":
    run_svd_ablation()
