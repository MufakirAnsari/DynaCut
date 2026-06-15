import os
import sys
import json
import networkx as nx
from typing import Dict

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dynacut.executor import maxcut_hamiltonian, DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
OUT_FILE = os.path.join(RESULTS_DIR, 'phase17_dynamic_p.json')

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def evaluate_dynamic_p():
    """
    Evaluates how ResourceHypervisor dynamically shifts P (number of partitions)
    based on the total graph size and memory constraints.
    """
    results: Dict[str, dict] = {}
    
    # We will fix a strict RAM limit (e.g. 10 GB) and allow max VRAM
    # The hypervisor must dynamically choose P (frag_size) to fit!
    hypervisor = ResourceHypervisor(
        max_qubits_per_fragment=14, # Soft upper limit
        max_vram_gb=4.0, 
        max_ram_gb=10.0
    )
    
    executor = DynaCutExecutor(hypervisor)
    
    # Sweep graph sizes from N=10 to N=26
    for n in range(10, 28, 2):
        G = nx.barabasi_albert_graph(n, 2, seed=42)
        edges = list(G.edges())
        hamiltonian = maxcut_hamiltonian(edges, n)
        
        ansatz = DynaCutExecutor.build_ansatz(n, reps=1, ansatz_type="qaoa", hamiltonian=hamiltonian)
        
        # This triggers the dynamic search for P
        strategy = hypervisor.find_optimal_strategy(ansatz)
        
        results[str(n)] = {
            "num_qubits": n,
            "num_fragments": strategy.num_fragments,
            "num_cuts": strategy.num_cuts,
            "max_fragment_size": strategy.max_fragment_size,
            "qpd_overhead": float(strategy.qpd_overhead),
            "estimated_ram_gb": strategy.estimated_contraction_ram_gb
        }
        
        logger.info(
            f"N={n} -> Dynamically chose P={strategy.num_fragments} "
            f"(max_frag={strategy.max_fragment_size}, cuts={strategy.num_cuts})"
        )

    with open(OUT_FILE, 'w') as f:
        json.dump(results, f, indent=4)
        
    logger.info("Dynamic P Selection benchmark complete!")

if __name__ == "__main__":
    evaluate_dynamic_p()
