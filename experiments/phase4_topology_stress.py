"""
Phase 4 — Topology Stress Test (Empirical).

Sweeps SBM inter-cluster density p_out on N=16 graphs.
Uses the REAL HypergraphPartitioner (KL bisection) from dynacut/topology.py
to partition an actual QAOA circuit, then counts the cut edges (K).

The key metric is the QPD sampling overhead Gamma = 3^K, which directly
controls the required number of shots: N_shots >= Gamma^2 * ||H||^2 / eps^2.
When K grows beyond ~3, the required shots become prohibitive (>10^6).
"""

import os
import sys
import json
import numpy as np
import networkx as nx
from qiskit import QuantumCircuit

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dynacut.topology import HypergraphPartitioner


def build_qaoa_circuit(G, gamma=0.5, beta=0.2):
    """Build a 1-layer QAOA circuit from graph G."""
    N = len(G.nodes)
    qc = QuantumCircuit(N)
    qc.h(range(N))
    for u, v in G.edges():
        qc.cx(u, v)
        qc.rz(2 * gamma, v)
        qc.cx(u, v)
    for i in range(N):
        qc.rx(2 * beta, i)
    return qc


def run_topology_stress_test():
    RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Sweep p_out from sparse to dense
    p_out_vals = np.linspace(0.05, 0.5, 20)
    N = 16
    max_fragment = N // 2  # KL bisection target: 8 qubits per fragment
    results = []

    partitioner = HypergraphPartitioner()

    # Fixed shot budget and error tolerance from the paper
    H_norm = 1.0  # Normalized observable
    epsilon = 0.01  # 1% error tolerance

    print("Starting Topology Stress Test (Real Partitioner)...")
    for p_out in p_out_vals:
        G = nx.random_partition_graph([N // 2, N // 2], 0.8, p_out, seed=42)
        qc = build_qaoa_circuit(G)

        # Use the REAL partitioner
        labels, cut_edges = partitioner.partition(qc, max_fragment)
        K = len(cut_edges)

        # QPD overhead: Gamma = 3^K (each cut wire contributes a factor of 3)
        gamma_qpd = 3.0 ** K

        # Required shots from Theorem 1: N >= Gamma^2 * ||H||^2 / epsilon^2
        required_shots = gamma_qpd ** 2 * H_norm ** 2 / epsilon ** 2

        print(f"  p_out={p_out:.3f}: K={K}, Γ={gamma_qpd:.1e}, shots={required_shots:.1e}")

        results.append({
            "p_out": float(p_out),
            "K": int(K),
            "gamma_qpd": float(gamma_qpd),
            "required_shots": float(required_shots),
        })

    with open(os.path.join(RESULTS_DIR, "topology_stress_test.json"), "w") as f:
        json.dump(results, f, indent=4)

    print("Done! Saved to topology_stress_test.json")


if __name__ == "__main__":
    run_topology_stress_test()
