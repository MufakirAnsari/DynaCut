import os
import time
import json
import logging
import numpy as np
import networkx as nx
from typing import Dict, Any, List, Tuple

from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor
from dynacut.experiment_runner import ExperimentRunner
from dynacut.ground_state import compute_exact_ground_state

logger = logging.getLogger(__name__)

def generate_adversarial_graph(topology: str, num_nodes: int, seed: int) -> List[Tuple[int, int]]:
    """Generate various adversarial graph topologies."""
    rng = np.random.default_rng(seed)
    
    if topology == "star":
        # 1 hub connected to all other nodes
        edges = [(0, i) for i in range(1, num_nodes)]
    elif topology == "complete":
        # Fully connected K_N
        edges = [(i, j) for i in range(num_nodes) for j in range(i + 1, num_nodes)]
    elif topology == "ring":
        # 1D Periodic
        edges = [(i, (i + 1) % num_nodes) for i in range(num_nodes)]
    elif topology == "bipartite":
        # Two equal sets, fully connected across, no connections within
        n1 = num_nodes // 2
        edges = [(i, j) for i in range(n1) for j in range(n1, num_nodes)]
    elif topology == "regular_3":
        # 3-regular graph (must have even number of nodes, or just generate approx if not possible)
        try:
            G = nx.random_regular_graph(3, num_nodes, seed=seed)
            edges = list(G.edges())
        except nx.NetworkXError:
            # Fallback to ring if 3-regular not possible (e.g., odd nodes and odd degree)
            logger.warning(f"3-regular graph not possible for {num_nodes} nodes, falling back to ring")
            edges = [(i, (i + 1) % num_nodes) for i in range(num_nodes)]
    else:
        raise ValueError(f"Unknown topology {topology}")
        
    return edges

def adversarial_graph_experiment(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    topology = config["topology"]
    num_qubits = config["num_qubits"]
    
    # 1. Setup Graph and Hamiltonian
    edges = generate_adversarial_graph(topology, num_qubits, seed)
    hamiltonian = maxcut_hamiltonian(edges, num_qubits)
    exact_energy = compute_exact_ground_state(hamiltonian)
    
    # 2. Ansatz
    ansatz = DynaCutExecutor.build_ansatz(num_qubits, reps=2, entanglement="linear")
    rng = np.random.default_rng(seed)
    params = rng.uniform(0, 2 * np.pi, size=ansatz.num_parameters)
    
    # 3. Evaluate Energy and Cuts
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_ram_gb=23.0, max_qubits_per_fragment=num_qubits//2 + 1)
    
    t0 = time.time()
    strategy = hypervisor.find_optimal_strategy(ansatz)
    t_hypervisor = time.time() - t0
    
    executor = DynaCutExecutor(hypervisor)
    try:
        t0 = time.time()
        e_cut = executor.evaluate_energy(
            params, ansatz, hamiltonian, strategy, 
            num_samples=np.inf, reconstruction_method="ibm"
        )
        t_cut = time.time() - t0
        cuts = strategy.num_cuts
        cut_weight = cuts  # Just proxy it, or remove it entirely
    except Exception as e:
        logger.error(f"Cut evaluation failed for {topology}: {e}")
        e_cut = float('nan')
        t_cut = 0.0
        cuts = 0
        cut_weight = 0.0
        
    return {
        "topology": topology,
        "num_qubits": num_qubits,
        "exact_energy": float(exact_energy),
        "e_cut": float(e_cut),
        "error": float(abs(e_cut - exact_energy)) if not np.isnan(e_cut) else float('nan'),
        "cuts": cuts,
        "cut_weight": float(cut_weight),
        "time_partition": float(t_hypervisor),
        "time_eval": float(t_cut)
    }

def main():
    logging.basicConfig(level=logging.INFO)
    
    topologies = ["star", "complete", "ring", "bipartite", "regular_3"]
    num_qubits = 14  # Fixed at 14 to see clear topology effects
    
    all_raw_results = []
    
    for topo in topologies:
        logger.info(f"Running Adversarial Graph: {topo} ({num_qubits} qubits)")
        runner = ExperimentRunner(experiment_name=f"adv_graph_{topo}_{num_qubits}q")
        res = runner.run(
            adversarial_graph_experiment, 
            config={"topology": topo, "num_qubits": num_qubits}
        )
        all_raw_results.extend(res["raw"])
            
    os.makedirs("results", exist_ok=True)
    with open("results/adversarial_graphs_combined_raw.json", "w") as f:
        json.dump(all_raw_results, f, indent=2)
    logger.info("Saved combined adversarial graph results to results/adversarial_graphs_combined_raw.json")

if __name__ == "__main__":
    main()
