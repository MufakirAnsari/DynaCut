"""
Phase 6: HPC Regime Scaling — Classical Simulation Memory vs DynaCut.

Uses the CORRECT classical simulation cost:
  - Statevector: 2^N × 16 bytes (complex128). This is the fundamental
    minimum memory for exact classical simulation of an N-qubit circuit.
  - DynaCut: bounded by ResourceHypervisor partition strategy.

Sweeps N from 10 to 70 on dense SBM graphs (p_out=0.10).
"""

import os
import sys
import json
import math
import time
import numpy as np
import networkx as nx

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dynacut.executor import maxcut_hamiltonian, DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
OUT_FILE = os.path.join(RESULTS_DIR, 'hpc_scaling.json')


def statevector_memory_bytes(N):
    """Exact statevector memory: 2^N complex128 amplitudes = 2^N × 16 bytes."""
    return 2**N * 16


def statevector_memory_mb(N):
    return statevector_memory_bytes(N) / (1024**2)


def log2_statevector_memory_gb(N):
    """log2 of memory in GB, for safe computation at large N."""
    # 2^N * 16 bytes = 2^(N+4) bytes = 2^(N+4) / 2^30 GB = 2^(N-26) GB
    return N - 26


def estimate_dynacut_memory(graph_edges, N, max_ram_gb=32.0):
    """Estimate DynaCut's bounded memory via ResourceHypervisor.

    Uses max_vram_gb=4.0 GB (standard GPU) and the given RAM budget.
    Returns (memory_mb, num_cuts, contraction_mode, max_fragment_size).
    """
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_ram_gb=max_ram_gb)
    hamiltonian = maxcut_hamiltonian(graph_edges, N)
    ansatz = DynaCutExecutor.build_ansatz(
        N, reps=1, ansatz_type="qaoa", hamiltonian=hamiltonian
    )
    strategy = hypervisor.find_optimal_strategy(ansatz)

    # The largest fragment determines the per-fragment statevector cost
    frag_sv_mb = statevector_memory_mb(strategy.max_fragment_size)

    return (
        float(strategy.estimated_contraction_ram_gb * 1024),  # contraction RAM in MB
        frag_sv_mb,                                            # fragment statevector MB
        int(strategy.num_cuts),
        strategy.contraction_mode,
        int(strategy.max_fragment_size),
    )


def format_memory(mem_mb):
    """Human-readable memory string."""
    if mem_mb < 1:
        return f"{mem_mb * 1024:.1f} KB"
    elif mem_mb < 1024:
        return f"{mem_mb:.2f} MB"
    elif mem_mb < 1024**2:
        return f"{mem_mb / 1024:.2f} GB"
    elif mem_mb < 1024**3:
        return f"{mem_mb / 1024**2:.2f} TB"
    elif mem_mb < 1024**4:
        return f"{mem_mb / 1024**3:.2f} PB"
    else:
        return f"{mem_mb / 1024**4:.2f} EB"


def run_hpc_scaling():
    """Sweep N from 10 to 70 at fixed p_out = 0.10."""
    p_out = 0.10
    qubit_sizes = list(range(10, 72, 2))  # 10, 12, ..., 70
    results = {}

    print("=" * 78)
    print(f"  HPC Regime Scaling  |  p_out = {p_out}  |  N = {qubit_sizes[0]}..{qubit_sizes[-1]}")
    print(f"  Classical baseline: Exact statevector = 2^N × 16 bytes")
    print("=" * 78)

    for N in qubit_sizes:
        t0 = time.time()
        print(f"\nN = {N}")

        # Generate a 2-community SBM
        sizes = [N // 2, N - N // 2]
        G = nx.stochastic_block_model(
            sizes, [[0.8, p_out], [p_out, 0.8]], seed=42
        )
        edges = list(G.edges())
        num_edges = len(edges)
        density = 2 * num_edges / (N * (N - 1))

        # --- Classical Statevector Memory (exact, undeniable) ---
        log2_mem_gb = log2_statevector_memory_gb(N)
        if N <= 50:
            sv_mem_mb = statevector_memory_mb(N)
        else:
            sv_mem_mb = float('inf')  # can't even represent as float

        # --- DynaCut Memory ---
        (contraction_ram_mb, frag_sv_mb, num_cuts,
         mode, max_frag_size) = estimate_dynacut_memory(edges, N)

        elapsed = time.time() - t0

        # QPD overhead in log10
        log10_qpd = num_cuts * math.log10(9)

        results[str(N)] = {
            "N": N,
            "num_edges": num_edges,
            "density": round(density, 4),
            # Classical: exact statevector
            "classical_log2_memory_gb": round(log2_mem_gb, 2),
            "classical_memory_mb": sv_mem_mb if sv_mem_mb != float('inf') else None,
            # DynaCut: partitioned
            "dynacut_contraction_ram_mb": contraction_ram_mb,
            "dynacut_fragment_sv_mb": frag_sv_mb,
            "dynacut_max_fragment_qubits": max_frag_size,
            "dynacut_cuts": num_cuts,
            "dynacut_mode": mode,
            "log10_qpd_overhead": round(log10_qpd, 2),
            "elapsed_seconds": round(elapsed, 2),
        }

        # Pretty-print
        if sv_mem_mb != float('inf'):
            cls_str = format_memory(sv_mem_mb)
        else:
            cls_str = f"2^{log2_mem_gb + 30:.0f} bytes (= 2^{log2_mem_gb:.0f} GB)"

        print(f"  Graph: {num_edges} edges, density={density:.3f}")
        print(f"  Classical Statevector: {cls_str}  (2^{N} × 16 bytes)")
        print(f"  DynaCut: K={num_cuts}, max_frag={max_frag_size}q, "
              f"frag_sv={format_memory(frag_sv_mb)}, mode={mode}")
        print(f"  QPD overhead: 9^{num_cuts} = 10^{log10_qpd:.1f}")
        print(f"  [{elapsed:.1f}s]")

        # Save incrementally
        with open(OUT_FILE, 'w') as f:
            json.dump(results, f, indent=4)

    print(f"\nAll results saved to {OUT_FILE}")


if __name__ == "__main__":
    run_hpc_scaling()
