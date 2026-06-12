"""
DynaCut Real-QPU Scaling Sweep — 8 to 50+ qubits on real IBM hardware.

Key insight: Circuit count depends on BOTH the number of cuts AND how many
Hamiltonian terms cross those cuts. Complete graphs have O(n²) cross-boundary
terms, each multiplying QPD circuits. Cycle graphs with 1 bridge edge have
exactly 1 cross-boundary term → minimal circuits at any qubit count.

Memory & time budget:
  cycle + 1 bridge → 1 cross-cut term → ~6 circuits/fragment  (seconds)
  cycle + 2 bridges → 2 cross-cut terms → ~36 circuits/fragment (minutes)
  complete + 2 bridges → O(n) cross-cut terms → TIMEOUT on free tier
"""
import os
import sys
import gc
import json
import time
import logging
import traceback
import resource
import networkx as nx
import numpy as np

from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dynacut.executor import DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger("scaling_sweep")

RESULTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qpu_scaling_results.json")


# ── Scaling configurations ──────────────────────────────────────────────
# (total_qubits, cluster_size, n_bridges, graph_type)
# Ordered from smallest to largest, 1-bridge configs first (safest)
CONFIGS = [
    # --- 1 bridge / 1 cut  (fastest, ~6 QPD circuits) ---
    (8,   4,  1, "complete"),    # barbell baseline
    (10,  5,  1, "cycle"),
    (12,  6,  1, "cycle"),
    (16,  8,  1, "cycle"),
    (20, 10,  1, "cycle"),
    (24, 12,  1, "cycle"),
    (30, 15,  1, "cycle"),
    (40, 20,  1, "cycle"),
    (50, 25,  1, "cycle"),
    # --- 2 bridges / 2 cuts  (moderate, ~36 QPD circuits) ---
    (10,  5,  2, "cycle"),
    (16,  8,  2, "cycle"),
    (20, 10,  2, "cycle"),
    (30, 15,  2, "cycle"),
]

MAX_SAFE_CUTS = 2  # Abort if partitioner chooses more than this (4 cuts uses 21GB+ RAM)


def build_cluster_graph(n_per_cluster: int, n_bridges: int, graph_type: str = "cycle"):
    """Build a dual-cluster graph with controlled bridge edges.

    Using cycle graphs keeps Hamiltonian terms to O(n) instead of O(n²),
    ensuring that very few ZZ terms cross the partition boundary.
    """
    n_qubits = 2 * n_per_cluster
    G = nx.Graph()
    G.add_nodes_from(range(n_qubits))

    if graph_type == "complete":
        for i in range(n_per_cluster):
            for j in range(i + 1, n_per_cluster):
                G.add_edge(i, j)
        for i in range(n_per_cluster, n_qubits):
            for j in range(i + 1, n_qubits):
                G.add_edge(i, j)
    else:  # cycle — sparse, O(n) edges
        for i in range(n_per_cluster):
            G.add_edge(i, (i + 1) % n_per_cluster)
        for i in range(n_per_cluster, n_qubits):
            next_node = n_per_cluster + ((i - n_per_cluster + 1) % n_per_cluster)
            G.add_edge(i, next_node)

    # Bridge edges
    bridges = []
    for b in range(n_bridges):
        src = n_per_cluster - 1 - b
        dst = n_per_cluster + b
        G.add_edge(src, dst)
        bridges.append((src, dst))

    # Count cross-boundary terms
    cross_terms = sum(1 for u, v in G.edges()
                      if (u < n_per_cluster) != (v < n_per_cluster))

    logger.info("Graph: %d qubits, %d edges, %d bridges %s, %d cross-boundary ZZ terms",
                n_qubits, G.number_of_edges(), n_bridges, bridges, cross_terms)

    # Build MaxCut Hamiltonian
    pauli_list = []
    for u, v in G.edges():
        zz = ["I"] * n_qubits
        zz[u] = "Z"
        zz[v] = "Z"
        pauli_list.append(("".join(zz)[::-1], 0.5))

    hamiltonian = SparsePauliOp.from_list(pauli_list)
    return G, hamiltonian, n_qubits, cross_terms


def load_existing_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return []


def save_results(results):
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)


def get_mem_mb():
    """Current process RSS in MB."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def run_scaling_sweep():
    token = os.environ.get("IBMQ_TOKEN")
    if not token:
        logger.error("Set IBMQ_TOKEN:  export IBMQ_TOKEN='your_token'")
        return

    logger.info("Authenticating with IBM Quantum...")
    QiskitRuntimeService.save_account(
        channel="ibm_quantum_platform", token=token, overwrite=True
    )
    service = QiskitRuntimeService(channel="ibm_quantum_platform")

    logger.info("Selecting least-busy QPU (≥50 qubits)...")
    backend = service.least_busy(simulator=False, min_num_qubits=50)
    logger.info("Selected QPU: %s (%d qubits)", backend.name, backend.num_qubits)

    pm = generate_preset_pass_manager(target=backend.target, optimization_level=1)

    all_results = load_existing_results()
    completed_keys = {(r["n_qubits"], r["n_bridges"], r["graph_type"]) for r in all_results
                      if r.get("status") == "SUCCESS"}

    logger.info("═" * 65)
    logger.info("  DynaCut Real-QPU Scaling Sweep — %d configs on %s", len(CONFIGS), backend.name)
    logger.info("  Already completed: %d", len(completed_keys))
    logger.info("═" * 65)

    for idx, (n_qubits, cluster_size, n_bridges, graph_type) in enumerate(CONFIGS):
        key = (n_qubits, n_bridges, graph_type)
        if key in completed_keys:
            logger.info("[%d/%d] SKIP %d qubits/%d bridges/%s — done",
                        idx + 1, len(CONFIGS), n_qubits, n_bridges, graph_type)
            continue

        logger.info("─" * 65)
        logger.info("[%d/%d] %d qubits | %s 2×%d | %d bridges | RSS=%.0f MB",
                    idx + 1, len(CONFIGS), n_qubits, graph_type,
                    cluster_size, n_bridges, get_mem_mb())
        logger.info("─" * 65)

        try:
            G, hamiltonian, n_q, cross_terms = build_cluster_graph(
                cluster_size, n_bridges, graph_type
            )

            hypervisor = ResourceHypervisor(
                max_qubits_per_fragment=cluster_size, max_ram_gb=8.0
            )

            ansatz = DynaCutExecutor.build_ansatz(
                num_qubits=n_q, reps=1,
                ansatz_type="qaoa", hamiltonian=hamiltonian,
            )
            logger.info("Ansatz: %d params, %d gates", ansatz.num_parameters, ansatz.size())

            strategy = hypervisor.find_optimal_strategy(ansatz)
            n_cuts = strategy.num_cuts
            logger.info("Strategy: %d fragments, %d cuts, γ=%d, cross-boundary=%d",
                        strategy.num_fragments, n_cuts, 3 ** n_cuts, cross_terms)

            if n_cuts > MAX_SAFE_CUTS:
                logger.error("ABORT: %d cuts too many. Skipping.", n_cuts)
                all_results.append({
                    "n_qubits": n_qubits, "n_bridges": n_bridges,
                    "graph_type": graph_type, "status": "SKIPPED_OOM_RISK",
                    "cuts": n_cuts,
                })
                save_results(all_results)
                continue

            gc.collect()
            qpu_sampler = Sampler(mode=backend)
            executor = DynaCutExecutor(hypervisor=hypervisor, sampler=qpu_sampler)
            params = np.random.uniform(0, np.pi, ansatz.num_parameters)

            logger.info("Submitting to %s (RSS=%.0f MB)...", backend.name, get_mem_mb())
            t0 = time.time()

            energy = executor.evaluate_energy(
                params=params,
                ansatz=ansatz,
                hamiltonian=hamiltonian,
                strategy=strategy,
                reconstruction_method="ibm",
                options={"isa_pass_manager": pm},
            )
            elapsed = time.time() - t0

            logger.info("✅ %d qubits | %d cuts | E=%.8f | %.1fs | RSS=%.0f MB",
                        n_qubits, n_cuts, energy, elapsed, get_mem_mb())

            all_results.append({
                "n_qubits": n_qubits,
                "cluster_size": cluster_size,
                "n_bridges": n_bridges,
                "graph_type": graph_type,
                "status": "SUCCESS",
                "energy": float(energy),
                "cuts": n_cuts,
                "fragments": strategy.num_fragments,
                "gamma": 3 ** n_cuts,
                "cross_boundary_terms": cross_terms,
                "elapsed_seconds": round(elapsed, 1),
                "backend": backend.name,
                "peak_rss_mb": round(get_mem_mb(), 0),
            })
            save_results(all_results)

            del executor, qpu_sampler, ansatz, hamiltonian, strategy, hypervisor
            gc.collect()

        except Exception as e:
            logger.error("FAILED %d qubits: %s", n_qubits, e)
            traceback.print_exc()
            all_results.append({
                "n_qubits": n_qubits, "n_bridges": n_bridges,
                "graph_type": graph_type, "status": "FAILED",
                "error": str(e),
            })
            save_results(all_results)

    # ── Summary table ───────────────────────────────────────────────────
    logger.info("")
    logger.info("═" * 75)
    logger.info("  FINAL RESULTS — DynaCut Real-QPU Scaling Sweep")
    logger.info("═" * 75)
    logger.info("  %-6s %-8s %-5s %-4s %-6s %-12s %-8s %-6s",
                "Qubits", "Topology", "Cuts", "γ", "X-ZZ", "Energy", "Time(s)", "Status")
    logger.info("  " + "-" * 71)
    for r in all_results:
        if r["status"] == "SUCCESS":
            logger.info("  %-6d %-8s %-5d %-4d %-6d %-12.6f %-8.1f %-6s",
                        r["n_qubits"], r["graph_type"], r["cuts"], r["gamma"],
                        r["cross_boundary_terms"], r["energy"],
                        r["elapsed_seconds"], "✅")
        else:
            logger.info("  %-6d %-8s %-5s %-4s %-6s %-12s %-8s %-6s",
                        r["n_qubits"], r.get("graph_type", "?"), "-", "-", "-",
                        "-", "-", r["status"])
    logger.info("═" * 75)


if __name__ == "__main__":
    run_scaling_sweep()
