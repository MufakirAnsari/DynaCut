import os
import sys
import time
import json
import networkx as nx
import numpy as np

# Qiskit imports
from qiskit import QuantumCircuit
from qiskit.circuit.library import QAOAAnsatz
from qiskit.quantum_info import SparsePauliOp
# (Estimator removed)

# Quimb imports
import quimb.tensor as qtn
import cotengra as ctg

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dynacut.executor import maxcut_hamiltonian, DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor, CutStrategy

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
OUT_FILE = os.path.join(RESULTS_DIR, 'mps_baseline.json')

def run_1d_dmrg(N):
    """Run exact classical DMRG for 1D MaxCut (Ising without transverse field)."""
    # MaxCut H = sum 0.5(I - Z_i Z_j). 
    # The interaction is -0.5 Z_i Z_j.
    # MPO_ham_ising(j) gives H = -j Z_i Z_j. So j=0.5.
    mpo = qtn.MPO_ham_ising(N, j=0.5, bx=0.0)
    dmrg = qtn.DMRG2(mpo, bond_dims=[10, 20, 50, 100], cutoffs=1e-10)
    t0 = time.time()
    dmrg.solve(tol=1e-6, verbosity=0)
    t1 = time.time()
    
    # Add the constant offset sum(0.5 * I) = 0.5 * (N-1)
    offset = 0.5 * (N - 1)
    return {
        "energy": float(dmrg.energy) + offset,
        "time_seconds": t1 - t0,
        "max_bond_dimension": int(dmrg.state.max_bond())
    }

def run_1d_dynacut(N):
    """Run DynaCut VQE for 1D MaxCut."""
    edges = [(i, i+1) for i in range(N-1)]
    hamiltonian = maxcut_hamiltonian(edges, N)
    
    # Very aggressive max_vram to force cutting (but enough to keep K=1 for N=20)
    hypervisor = ResourceHypervisor(max_vram_gb=2.0 / 1024)
    executor = DynaCutExecutor(hypervisor)
    ansatz = DynaCutExecutor.build_ansatz(N, reps=1, ansatz_type="qaoa", hamiltonian=hamiltonian)
    strategy = hypervisor.find_optimal_strategy(ansatz)
    
    t0 = time.time()
    res = executor.run_vqe(ansatz, hamiltonian, strategy, maxiter=10)
    t1 = time.time()
    
    return {
        "energy": float(res["optimal_energy"]),
        "time_seconds": t1 - t0,
        "num_cuts": int(strategy.num_cuts)
    }

def get_real_circuit_memory_mb(graph_edges, N):
    import opt_einsum as oe
    terms = []
    for i in range(N):
        node_edges = [f"e_{min(i, j)}_{max(i, j)}" for j in range(N) if (i, j) in graph_edges or (j, i) in graph_edges]
        terms.append([f"n_{i}"] + node_edges)
    
    tn = qtn.TensorNetwork([])
    for i in range(N):
        inds = tuple([f"e_{min(i, j)}_{max(i, j)}" for j in range(N) if (i, j) in graph_edges or (j, i) in graph_edges])
        tn.add_tensor(qtn.Tensor(np.random.rand(*( [2]*len(inds) )), inds=inds, tags={f'I{i}'}))
    
    opt = ctg.ReusableHyperOptimizer(
        methods=['greedy', 'kahypar'],
        max_repeats=16,
        progbar=False
    )
    info = tn.contraction_info(optimize=opt)
    largest_val = float(info.largest_intermediate)
    treewidth = np.log2(largest_val)
    peak_memory_mb = (largest_val * 16) / (1024**2)
    return float(peak_memory_mb), float(treewidth)

def get_dynacut_memory_mb(graph_edges, N):
    hypervisor = ResourceHypervisor(max_vram_gb=2.0 / 1024)
    ansatz = DynaCutExecutor.build_ansatz(N, reps=1, ansatz_type="qaoa", hamiltonian=maxcut_hamiltonian(graph_edges, N))
    strategy = hypervisor.find_optimal_strategy(ansatz)
    return float(strategy.estimated_contraction_ram_gb * 1024)

def run_sbm_scaling():
    N = 20 
    p_outs = [0.01, 0.05, 0.1, 0.2, 0.4]
    results = {}
    
    print(f"--- Running 1-to-1 Memory Benchmark for SBM (N={N}) ---")
    for p in p_outs:
        G = nx.stochastic_block_model([N//2, N - N//2], [[0.8, p], [p, 0.8]], seed=42)
        mem_classical, treewidth = get_real_circuit_memory_mb(list(G.edges()), N)
        mem_dynacut = get_dynacut_memory_mb(list(G.edges()), N)
        
        results[str(p)] = {
            "p_out": p, 
            "memory_mb": mem_classical, 
            "treewidth": treewidth,
            "dynacut_memory_mb": mem_dynacut
        }
        print(f"p_out: {p:.2f} -> Classical TN Memory: {mem_classical:.2f} MB | DynaCut Memory: {mem_dynacut:.2f} MB")
        
    return results

def run_all_benchmarks():
    results = {"1d_tfim": {}, "sbm_tn_memory": {}}
    
    print("--- Running 1-to-1 Time/Accuracy Baseline (1D MaxCut) ---")
    # For speed of the classical TN optimizer in VQE loop, keep N <= 20
    # for N in [10, 12, 14, 16, 18, 20]:
    #     print(f"Running N={N}...")
    #     res_dmrg = run_1d_dmrg(N)
    #     res_dyna = run_1d_dynacut(N)
    #     
    #     results["1d_tfim"][str(N)] = {
    #         "dmrg_time": res_dmrg["time_seconds"],
    #         "dmrg_energy": res_dmrg["energy"],
    #         "dynacut_time": res_dyna["time_seconds"],
    #         "dynacut_energy": res_dyna["energy"],
    #         "dynacut_cuts": res_dyna["num_cuts"]
    #     }
    #     print(f"  DMRG: Time={res_dmrg['time_seconds']:.2f}s, Energy={res_dmrg['energy']:.4f}")
    #     print(f"  DynaCut: Time={res_dyna['time_seconds']:.2f}s, Energy={res_dyna['energy']:.4f}, Cuts={res_dyna['num_cuts']}")

    print("\n--- Running SBM Density Scaling ---")
    results["sbm_tn_memory"] = run_sbm_scaling()

    with open(OUT_FILE, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"\nResults saved to {OUT_FILE}")

if __name__ == "__main__":
    run_all_benchmarks()
