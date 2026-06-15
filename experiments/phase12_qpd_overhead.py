"""
Phase 12: QPD Overhead Profiling

This script profiles the theoretical and empirical QPD overhead across
different qubit sizes (N) and topological densities (Ring, 3-Regular, Dense SBM).
"""

import os
import sys
import json
import time
import numpy as np
import networkx as nx

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dynacut.executor import maxcut_hamiltonian, DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
OUT_FILE = os.path.join(RESULTS_DIR, 'qpd_overhead_profiling.json')

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_graph(topology: str, n: int) -> nx.Graph:
    if topology == "ring":
        return nx.cycle_graph(n)
    elif topology == "3-regular":
        # Random regular graph requires n * d to be even.
        if (n * 3) % 2 != 0:
            n += 1
        return nx.random_regular_graph(3, n, seed=42)
    elif topology == "dense":
        return nx.erdos_renyi_graph(n, p=0.4, seed=42)
    else:
        raise ValueError(f"Unknown topology: {topology}")

def profile_qpd_overhead():
    qubits = [14, 18, 22]
    topologies = ["ring", "3-regular", "dense"]
    
    hypervisor = ResourceHypervisor(max_qubits_per_fragment=6)
    results = []
    
    for n in qubits:
        for topo in topologies:
            logger.info(f"Profiling N={n}, Topology={topo}")
            G = generate_graph(topo, n)
            actual_n = G.number_of_nodes()
            edges = list(G.edges())
            
            hamiltonian = maxcut_hamiltonian(edges, actual_n)
            norm_H = sum(abs(c) for c in hamiltonian.coeffs)
            
            ansatz = DynaCutExecutor.build_ansatz(actual_n, reps=1, ansatz_type="qaoa", hamiltonian=hamiltonian)
            
            # Find cutting strategy
            strategy = hypervisor.find_optimal_strategy(ansatz)
            k_cuts = strategy.num_cuts
            gamma = 3 ** k_cuts
            
            # Hoeffding's bound for S (shots)
            # S = (Gamma^2 ||H||^2) / (2 * epsilon^2) * ln(2/delta)
            epsilon = 0.01
            delta = 0.05
            S_required = (gamma**2 * norm_H**2) / (2 * epsilon**2) * np.log(2 / delta)
            
            # We skip the actual TN evaluation to prevent the script from taking hours on dense graphs.
            # We just track the theoretical bounds.
            t_tn = float('nan')
            
            results.append({
                "N": actual_n,
                "topology": topo,
                "density": len(edges) / (actual_n * (actual_n - 1) / 2),
                "cuts": k_cuts,
                "gamma": float(gamma),
                "shots_required": float(S_required),
                "tn_time": t_tn
            })
            
            logger.info(f"  Cuts={k_cuts}, Gamma={gamma:.2e}, Shots={S_required:.2e}, TN Time={t_tn:.2f}s")
            
    with open(OUT_FILE, 'w') as f:
        json.dump(results, f, indent=4)
        
    logger.info(f"Finished profiling. Results saved to {OUT_FILE}")

if __name__ == "__main__":
    profile_qpd_overhead()
