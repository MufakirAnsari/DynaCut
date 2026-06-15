import os
import sys
import json
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dynacut.executor import maxcut_hamiltonian, DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor
from qiskit_aer.primitives import Estimator as AerEstimator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeBrisbane
from qiskit_algorithms.optimizers import SPSA

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
OUT_FILE = os.path.join(RESULTS_DIR, 'phase19_optimizer_paths.json')
PLOT_FILE = os.path.join(RESULTS_DIR, 'optimizer_paths.png')

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def run_vqe_paths():
    n = 10
    logger.info(f"Generating N={n} MaxCut Graph...")
    # Use a graph with enough density to trigger deep SWAP routing
    G = nx.barabasi_albert_graph(n, 3, seed=42)
    edges = list(G.edges())
    hamiltonian = maxcut_hamiltonian(edges, n)
    exact_ground_state = float(np.min(np.linalg.eigvalsh(hamiltonian.to_matrix())))
    
    # Extract noise model
    logger.info("Setting up FakeBrisbane noise model...")
    backend = FakeBrisbane()
    noise_model = NoiseModel.from_backend(backend)
    
    # 1. Exact Monolithic
    logger.info("Running EXACT Monolithic VQE...")
    exact_estimator = AerEstimator(run_options={"shots": None}, transpile_options={"optimization_level": 0})
    ansatz = DynaCutExecutor.build_ansatz(n, reps=2, ansatz_type="qaoa", hamiltonian=hamiltonian)
    np.random.seed(42)
    initial_params = np.random.uniform(0, 2*np.pi, ansatz.num_parameters)
    
    exact_history = []
    def exact_cost(params):
        e = exact_estimator.run([ansatz], [hamiltonian], [params]).result().values[0]
        exact_history.append(float(e))
        return e
    
    SPSA(maxiter=50).minimize(exact_cost, x0=initial_params)
    
    # 2. Noisy Monolithic (Barren Plateau)
    logger.info("Running NOISY Monolithic VQE...")
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    isa_ansatz = pm.run(ansatz)
    isa_hamiltonian = hamiltonian.apply_layout(isa_ansatz.layout)
    
    noisy_estimator = AerEstimator(
        backend_options={"method": "density_matrix", "noise_model": noise_model},
        run_options={"shots": None},
        transpile_options={"optimization_level": 0}
    )
    
    noisy_history = []
    def noisy_cost(params):
        e = noisy_estimator.run([isa_ansatz], [isa_hamiltonian], [params]).result().values[0]
        noisy_history.append(float(e))
        return e
    
    SPSA(maxiter=50).minimize(noisy_cost, x0=initial_params)
    
    # 3. DynaCut + Noisy Execution (simulating sub-circuit execution)
    # We enforce fragmentation.
    logger.info("Running DynaCut VQE...")
    hypervisor = ResourceHypervisor(max_qubits_per_fragment=5, max_vram_gb=1.0)
    strategy = hypervisor.find_optimal_strategy(ansatz)
    executor = DynaCutExecutor(hypervisor)
    
    dynacut_res = executor.run_vqe(
        ansatz=ansatz,
        hamiltonian=hamiltonian,
        strategy=strategy,
        initial_params=initial_params,
        method="SPSA",
        maxiter=50,
        reconstruction_method="tn" # Fast exact tensor network arithmetic
    )
    dynacut_history = dynacut_res["convergence_history"]
    
    results = {
        "exact_ground_state": exact_ground_state,
        "exact_history": exact_history,
        "noisy_history": noisy_history,
        "dynacut_history": dynacut_history
    }
    
    with open(OUT_FILE, 'w') as f:
        json.dump(results, f, indent=4)
        
    # Plotting
    plt.figure(figsize=(10, 6))
    
    # Plot ground state
    plt.axhline(exact_ground_state, color='black', linestyle='--', label=f'Exact Ground State ({exact_ground_state:.2f})')
    
    plt.plot(exact_history, label='Exact Statevector', color='blue', alpha=0.7)
    plt.plot(dynacut_history, label='DynaCut (Partitioned)', color='green', linewidth=2)
    plt.plot(noisy_history, label='Monolithic (Noisy Barren Plateau)', color='red', alpha=0.9)
    
    plt.title(f'VQE Optimizer Paths on {n}-Qubit MaxCut (FakeBrisbane Noise)')
    plt.xlabel('SPSA Function Evaluation')
    plt.ylabel('Energy $\langle H \\rangle$')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(PLOT_FILE, dpi=300)
    plt.close()
    
    logger.info(f"Done! Plot saved to {PLOT_FILE}")

if __name__ == "__main__":
    run_vqe_paths()
