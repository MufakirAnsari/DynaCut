import os
import sys
import json
import time
import numpy as np
import networkx as nx

# Add parent directory to path so we can import dynacut
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qiskit.quantum_info import Statevector
from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor

def generate_maxcut_graph(num_nodes: int, edge_prob: float = 0.5, seed: int = 42) -> list:
    G = nx.erdos_renyi_graph(num_nodes, edge_prob, seed=seed)
    return list(G.edges())

def main():
    np.random.seed(42)
    os.makedirs("results", exist_ok=True)
    
    qubit_sizes = [8, 10, 12, 14, 16]
    results = {}
    
    for n in qubit_sizes:
        print(f"\n--- Testing {n} qubits ---")
        edges = generate_maxcut_graph(n, edge_prob=0.3, seed=42)
        hamiltonian = maxcut_hamiltonian(edges, n)
        
        # Hypervisor with a small max_fragment to force cuts
        hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_qubits_per_fragment=n//2 + 1)
        executor = DynaCutExecutor(hypervisor)
        ansatz = executor.build_ansatz(n, reps=1, entanglement="linear")
        
        params = np.random.uniform(0, 2 * np.pi, size=ansatz.num_parameters)
        strategy = hypervisor.find_optimal_strategy(ansatz)
        
        print(f"Fragments: {strategy.num_fragments}, Cuts: {strategy.num_cuts}")
        
        # 1. Exact
        bound_circuit = ansatz.assign_parameters(params)
        exact_energy = float(np.real(Statevector(bound_circuit).expectation_value(hamiltonian)))
        
        # 2. IBM path
        t0 = time.time()
        energy_ibm = executor.evaluate_energy(
            params, ansatz, hamiltonian, strategy, 
            num_samples=np.inf, reconstruction_method="ibm"
        )
        t_ibm = time.time() - t0
        
        # 3. TN path
        t0 = time.time()
        energy_tn = executor.evaluate_energy(
            params, ansatz, hamiltonian, strategy, 
            num_samples=np.inf, reconstruction_method="tn", max_bond=None
        )
        t_tn = time.time() - t0
        
        diff_ibm_tn = abs(energy_ibm - energy_tn)
        diff_exact_tn = abs(exact_energy - energy_tn)
        
        print(f"  Exact: {exact_energy:.10f}")
        print(f"  IBM:   {energy_ibm:.10f} ({t_ibm:.3f}s)")
        print(f"  TN:    {energy_tn:.10f} ({t_tn:.3f}s)")
        print(f"  Diff (IBM-TN): {diff_ibm_tn:.2e}")
        
        assert diff_ibm_tn < 1e-10, f"Mismatch for {n} qubits: diff = {diff_ibm_tn}"
        
        results[n] = {
            "exact_energy": exact_energy,
            "energy_ibm": energy_ibm,
            "energy_tn": energy_tn,
            "diff_ibm_tn": diff_ibm_tn,
            "diff_exact_tn": diff_exact_tn,
            "time_ibm": t_ibm,
            "time_tn": t_tn,
            "num_cuts": strategy.num_cuts
        }
        
    with open("results/tn_vs_ibm.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print("\n✅ All tests passed successfully! Results saved to results/tn_vs_ibm.json.")

if __name__ == "__main__":
    main()
