import os
import sys
import logging
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dynacut.adaptive_scheduler import ResourceHypervisor
from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_stress_test():
    sns.set_theme(style="whitegrid", palette="husl")
    num_qubits = 16
    densities = np.linspace(0.1, 0.9, 17)
    
    # We constrain max_qubits_per_fragment tightly to force cutting
    max_q_frag = 6
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_qubits_per_fragment=max_q_frag)
    executor = DynaCutExecutor(hypervisor)
    
    n_subs = []
    num_cuts = []
    
    logger.info("Running Topology Stress Test...")
    for p in densities:
        # Create Erdos-Renyi graph
        G = nx.erdos_renyi_graph(num_qubits, p, seed=42)
        # Ensure connected for meaningful cutting
        while not nx.is_connected(G):
            G = nx.erdos_renyi_graph(num_qubits, p)
            
        ansatz = executor.build_ansatz(num_qubits, reps=1, ansatz_type="qaoa", hamiltonian=maxcut_hamiltonian(list(G.edges()), num_qubits))
        
        # We catch exceptions if it's impossible to cut within the constraint
        try:
            strategy = hypervisor.find_optimal_strategy(ansatz)
            n_subs.append(strategy.num_fragments)
            num_cuts.append(strategy.num_cuts)
            logger.info(f"Density: {p:.2f} -> {strategy.num_cuts} cuts, {strategy.num_fragments} fragments")
        except ValueError:
            logger.warning(f"Density: {p:.2f} -> IMPOSSIBLE to partition into {max_q_frag}-qubit fragments")
            n_subs.append(0)
            num_cuts.append(0)

    # Plot
    fig, ax1 = plt.subplots(figsize=(8, 5))
    
    color = 'tab:blue'
    ax1.set_xlabel('Graph Density ($p$)')
    ax1.set_ylabel('Number of Subgraphs ($n_{sub}$)', color=color)
    ax1.plot(densities, n_subs, marker='o', linewidth=2, color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Number of Cuts Required', color=color)
    ax2.plot(densities, num_cuts, marker='s', linestyle='--', linewidth=2, color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title(f'Topology Stress Test (16 Qubits, Max Fragment Size = {max_q_frag})')
    fig.tight_layout()
    os.makedirs("paper/figures", exist_ok=True)
    plt.savefig("paper/figures/topology_stress_test.pdf", dpi=300, bbox_inches="tight")
    logger.info("Saved topology stress test plot to paper/figures/topology_stress_test.pdf")

if __name__ == "__main__":
    run_stress_test()
