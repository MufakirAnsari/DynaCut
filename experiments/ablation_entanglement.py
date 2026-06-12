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

def run_entanglement_experiment(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    num_qubits = config.get('num_qubits', 16)
    reps = config.get('reps', 2)
    
    edges = generate_maxcut_graph(num_qubits, edge_prob=0.15, seed=seed)
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_qubits_per_fragment=14)
    executor = DynaCutExecutor(hypervisor)
    hamiltonian = maxcut_hamiltonian(edges, num_qubits)
    
    metrics = {}
    
    for ent_type in ["linear", "circular", "sca", "pairwise"]:
        logger.info(f"Seed {seed}: Testing entanglement={ent_type}")
        try:
            ansatz = DynaCutExecutor.build_ansatz(num_qubits, reps=reps, entanglement=ent_type)
        except Exception as e:
            logger.error(f"Failed to build {ent_type}: {e}")
            continue
            
        params = np.random.RandomState(seed).uniform(0, 2*np.pi, ansatz.num_parameters)
        bound_circ = ansatz.assign_parameters(params)
        strategy = hypervisor.find_optimal_strategy(ansatz)
        
        # Safety guard: skip patterns that produce too many cuts (would hang)
        if strategy.num_cuts > 10 or getattr(strategy, "qpd_overhead", 0) > 50:
            logger.warning(f"Skipping {ent_type}: exceeds safety limits (overhead={getattr(strategy, 'qpd_overhead', 'N/A')})")
            metrics[f"skipped_{ent_type}"] = strategy.num_cuts
            continue
        
        energy_exact, _, _ = baseline_statevector(bound_circ, hamiltonian)
        
        start_time = time.time()
        energy_cut = executor.evaluate_energy(
            params, ansatz, hamiltonian, strategy, reconstruction_method="tn", max_bond=None
        )
        metrics[f"time_{ent_type}"] = time.time() - start_time
        metrics[f"num_cuts_{ent_type}"] = strategy.num_cuts
        
        metrics[f"energy_exact_{ent_type}"] = energy_exact
        metrics[f"energy_cut_{ent_type}"] = energy_cut
        metrics[f"error_{ent_type}"] = abs(energy_cut - energy_exact)
        
    return metrics

if __name__ == "__main__":
    runner = ExperimentRunner(experiment_name="ablation_entanglement", seeds=list(range(5)))
    logger.info("Running Entanglement Ablation for 16 qubits...")
    res = runner.run(run_entanglement_experiment, config={"num_qubits": 16, "reps": 2})
