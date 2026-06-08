import json
import logging
import time
import numpy as np
from typing import Dict, Any

from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor
from dynacut.experiment_runner import ExperimentRunner
from dynacut.baselines import baseline_statevector
from experiments.phase1_math_rigor import generate_maxcut_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_pareto_experiment(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    num_qubits = config.get('num_qubits', 20)
    
    edges = generate_maxcut_graph(num_qubits, edge_prob=0.15, seed=seed)
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_qubits_per_fragment=14)
    executor = DynaCutExecutor(hypervisor)
    hamiltonian = maxcut_hamiltonian(edges, num_qubits)
    ansatz = DynaCutExecutor.build_ansatz(num_qubits, reps=1, entanglement="linear")
    
    params = np.random.RandomState(seed).uniform(0, 2*np.pi, ansatz.num_parameters)
    bound_circ = ansatz.assign_parameters(params)
    strategy = hypervisor.find_optimal_strategy(ansatz)
    
    metrics = {}
    metrics["num_cuts"] = strategy.num_cuts
    metrics["num_fragments"] = strategy.num_fragments
    
    start_time = time.time()
    energy_exact, _, _ = baseline_statevector(bound_circ, hamiltonian)
    metrics["energy_exact"] = energy_exact
    metrics["time_exact"] = time.time() - start_time
    
    chis = [2, 3, 4, 6, 8, 16, 32, None] # None = exact contraction
    for chi in chis:
        chi_label = "exact" if chi is None else str(chi)
        start_time = time.time()
        energy = executor.evaluate_energy(
            params, ansatz, hamiltonian, strategy, 
            reconstruction_method="tn", max_bond=chi
        )
        t = time.time() - start_time
        metrics[f"energy_{chi_label}"] = energy
        metrics[f"error_{chi_label}"] = abs(energy - energy_exact)
        metrics[f"time_{chi_label}"] = t
        
    return metrics

if __name__ == "__main__":
    runner = ExperimentRunner(experiment_name="tn_pareto_real", seeds=list(range(10)))
    logger.info("Running Pareto frontier experiment for 20 qubits...")
    res = runner.run(run_pareto_experiment, config={"num_qubits": 20})
