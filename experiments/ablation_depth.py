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

def run_depth_experiment(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    num_qubits = config.get('num_qubits', 16)
    
    edges = generate_maxcut_graph(num_qubits, edge_prob=0.15, seed=seed)
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_qubits_per_fragment=14)
    executor = DynaCutExecutor(hypervisor)
    hamiltonian = maxcut_hamiltonian(edges, num_qubits)
    
    metrics = {}
    
    for reps in [1, 2, 3, 4, 5]:
        logger.info(f"Seed {seed}: Testing reps={reps}")
        ansatz = DynaCutExecutor.build_ansatz(num_qubits, reps=reps, entanglement="linear")
        
        params = np.random.RandomState(seed).uniform(0, 2*np.pi, ansatz.num_parameters)
        bound_circ = ansatz.assign_parameters(params)
        strategy = hypervisor.find_optimal_strategy(ansatz)
        
        # Safety guard: if cut weight is too high, it generates an astronomically huge number of experiments
        if strategy.num_cuts > 10 or getattr(strategy, "cut_weight", 0) > 10:
            logger.warning(f"Skipping reps={reps}: {strategy.num_cuts} cuts exceeds safety limits (would hang)")
            metrics[f"skipped_reps_{reps}"] = strategy.num_cuts
            continue

        energy_exact, _, _ = baseline_statevector(bound_circ, hamiltonian)
        
        start_time = time.time()
        energy_cut = executor.evaluate_energy(
            params, ansatz, hamiltonian, strategy, reconstruction_method="tn", max_bond=None
        )
        metrics[f"time_reps_{reps}"] = time.time() - start_time
        metrics[f"num_cuts_reps_{reps}"] = strategy.num_cuts
        
        metrics[f"energy_exact_reps_{reps}"] = energy_exact
        metrics[f"energy_cut_reps_{reps}"] = energy_cut
        metrics[f"error_reps_{reps}"] = abs(energy_cut - energy_exact)
        
    return metrics

if __name__ == "__main__":
    runner = ExperimentRunner(experiment_name="ablation_depth", seeds=list(range(5)))
    logger.info("Running Depth Ablation for 12 qubits...")
    res = runner.run(run_depth_experiment, config={"num_qubits": 12})
