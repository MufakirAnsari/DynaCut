"""
Phase 15: Cold-Start SPSA Ablation

This script runs a VQE optimization on a 10-qubit MaxCut graph 
starting from completely random parameters (Cold Start).
It compares the Monolithic (Noisy) execution against DynaCut execution.
"""

import os
import sys
import json
import numpy as np
import networkx as nx

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dynacut.executor import maxcut_hamiltonian, DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
OUT_FILE = os.path.join(RESULTS_DIR, 'phase15_cold_start.json')

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def run_cold_start_spsa():
    n = 6
    G = nx.path_graph(n)  # Simple chain graph
    edges = list(G.edges())
    hamiltonian = maxcut_hamiltonian(edges, n)
    
    hypervisor = ResourceHypervisor(max_qubits_per_fragment=3)
    executor = DynaCutExecutor(hypervisor)
    
    ansatz = DynaCutExecutor.build_ansatz(n, reps=1, ansatz_type="qaoa", hamiltonian=hamiltonian)
    strategy = hypervisor.find_optimal_strategy(ansatz)
    
    # 1. Cold Start Initialization
    np.random.seed(1337)
    initial_params = np.random.uniform(0, 2*np.pi, ansatz.num_parameters)
    
    logger.info("Running DynaCut VQE with Cold Start...")
    res_dynacut = executor.run_vqe(
        ansatz=ansatz,
        hamiltonian=hamiltonian,
        strategy=strategy,
        initial_params=initial_params,
        method="SPSA",
        maxiter=100,
        reconstruction_method="ibm" # exact arithmetic for profiling
    )
    
    logger.info("Running Monolithic Noisy VQE with Cold Start...")
    # Monolithic Noisy logic
    from qiskit_aer.primitives import Estimator
    from qiskit_ibm_runtime.fake_provider import FakeBrisbane
    from qiskit_aer.noise import NoiseModel
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from scipy.optimize import minimize
    
    backend = FakeBrisbane()
    noise_model = NoiseModel.from_backend(backend)
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    isa_circuit = pm.run(ansatz)
    isa_hamiltonian = hamiltonian.apply_layout(isa_circuit.layout)
    
    estimator = Estimator(
        backend_options={"method": "density_matrix", "noise_model": noise_model},
        run_options={"shots": None},
        transpile_options={"optimization_level": 0}
    )
    
    noisy_history = []
    
    def cost_func(params):
        e = estimator.run([isa_circuit], [isa_hamiltonian], [params]).result().values[0]
        noisy_history.append(float(e))
        return e
        
    from qiskit_algorithms.optimizers import SPSA
    optimizer = SPSA(maxiter=100)
    res_noisy = optimizer.minimize(cost_func, x0=initial_params)
    
    results = {
        "dynacut_history": res_dynacut["convergence_history"],
        "noisy_history": noisy_history,
        "dynacut_final_energy": float(res_dynacut["optimal_energy"]),
        "noisy_final_energy": float(res_noisy.fun),
        "exact_ground_state": float(np.min(np.linalg.eigvalsh(hamiltonian.to_matrix())))
    }
    
    with open(OUT_FILE, 'w') as f:
        json.dump(results, f, indent=4)
        
    logger.info("Done!")

if __name__ == "__main__":
    run_cold_start_spsa()
