"""
Phase 16: Vary QPU Noise Profiles

Evaluates the exactness of DynaCut across different IBM heavy-hex noise topologies.
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
OUT_FILE = os.path.join(RESULTS_DIR, 'phase16_noise_profiles.json')

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def run_noise_ablation():
    n = 6
    G = nx.path_graph(n)
    edges = list(G.edges())
    hamiltonian = maxcut_hamiltonian(edges, n)
    
    hypervisor = ResourceHypervisor(max_qubits_per_fragment=3)
    executor = DynaCutExecutor(hypervisor)
    
    ansatz = DynaCutExecutor.build_ansatz(n, reps=1, ansatz_type="qaoa", hamiltonian=hamiltonian)
    strategy = hypervisor.find_optimal_strategy(ansatz)
    
    np.random.seed(42)
    params = np.random.uniform(0, 2*np.pi, ansatz.num_parameters)
    
    # Get exact ground truth
    exact_energy = executor.evaluate_energy(
        params, ansatz, hamiltonian, strategy, 
        reconstruction_method="ibm" # uses ExactSampler by default
    )
    
    backends_to_test = ["FakeBrisbane", "FakeKyiv", "FakeTorino"]
    
    results = {
        "exact_energy": float(exact_energy),
        "profiles": {}
    }
    
    from qiskit_aer.noise import NoiseModel
    from qiskit_aer.primitives import Estimator as AerEstimator
    from qiskit_ibm_runtime.fake_provider import FakeBrisbane, FakeKyiv, FakeTorino
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    
    backend_map = {
        "FakeBrisbane": FakeBrisbane(),
        "FakeKyiv": FakeKyiv(),
        "FakeTorino": FakeTorino()
    }
    
    for name, backend in backend_map.items():
        logger.info(f"Evaluating Monolithic on {name}...")
        
        noise_model = NoiseModel.from_backend(backend)
        pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
        isa_circuit = pm.run(ansatz)
        isa_hamiltonian = hamiltonian.apply_layout(isa_circuit.layout)
        
        estimator = AerEstimator(
            backend_options={"method": "density_matrix", "noise_model": noise_model},
            run_options={"shots": None},
            transpile_options={"optimization_level": 0}
        )
        
        noisy_energy = float(estimator.run([isa_circuit], [isa_hamiltonian], [params]).result().values[0])
        
        error = abs(noisy_energy - exact_energy)
        
        results["profiles"][name] = {
            "noisy_energy": noisy_energy,
            "absolute_error": error
        }
        
        logger.info(f"[{name}] Exact: {exact_energy:.4f} | Noisy: {noisy_energy:.4f} | Error: {error:.4f}")
    
    with open(OUT_FILE, 'w') as f:
        json.dump(results, f, indent=4)
        
    logger.info("Done!")

if __name__ == "__main__":
    run_noise_ablation()
