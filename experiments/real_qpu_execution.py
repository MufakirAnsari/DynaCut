import os
import sys
import logging
import numpy as np
import networkx as nx

# Qiskit Runtime imports
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from qiskit_ibm_runtime.fake_provider import FakeGuadalupeV2

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_backend(use_real_hardware: bool = False, backend_name: str = "ibm_brisbane"):
    if use_real_hardware:
        try:
            logger.info("Attempting to connect to real IBM Quantum device...")
            service = QiskitRuntimeService()
            backend = service.backend(backend_name)
            logger.info(f"Connected to real hardware: {backend.name}")
            return backend
        except Exception as e:
            logger.warning(f"Could not connect to real hardware: {e}. Falling back to FakeProvider.")
            
    logger.info("Using hardware-realistic FakeGuadalupeV2...")
    return FakeGuadalupeV2()

def run_hardware_benchmark(use_real_hardware=False):
    # 1. Get backend
    backend = get_backend(use_real_hardware=use_real_hardware)
    
    # 2. Setup SamplerV2
    sampler = SamplerV2(mode=backend)
    # Enable Readout Twirling
    sampler.options.twirling.enable_measure = True 
    
    # We set default_shots on sampler directly
    sampler.options.default_shots = 10000
    
    # Generate ISA Pass Manager for the backend
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)

    # 3. Initialize DynaCut Executor
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_qubits_per_fragment=backend.num_qubits)
    executor = DynaCutExecutor(hypervisor, sampler=sampler)
    
    # 4. Create problem (10-qubit MaxCut)
    num_qubits = 10
    G = nx.random_regular_graph(3, num_qubits, seed=42)
    graph_edges = list(G.edges())
    hamiltonian = maxcut_hamiltonian(graph_edges, num_qubits)
    ansatz = executor.build_ansatz(num_qubits, reps=1, entanglement="linear")
    
    # Use fixed non-zero parameters
    params = np.array([0.1, 0.2, -0.1, 0.4, 0.5, -0.2, 0.3, 0.1, -0.4, 0.2, 0.1, 0.2, -0.1, 0.4, 0.5, -0.2, 0.3, 0.1, -0.4, 0.2][:ansatz.num_parameters])
    if len(params) < ansatz.num_parameters:
        params = np.pad(params, (0, ansatz.num_parameters - len(params)), 'constant')
    
    exact_energy = executor._direct_expectation(
        ansatz.assign_parameters(params), hamiltonian
    )
    
    # 5. Get Strategy
    strategy = hypervisor.find_optimal_strategy(ansatz)
    # Force hardware execution even if trivial (so it doesn't use exact statevector)
    logger.info(f"Using strategy: {strategy.contraction_mode} with {strategy.num_cuts} cuts")
    
    bound_ansatz = ansatz.assign_parameters(params)

    # 6. Run Unmitigated / Basic (Readout Twirling enabled, no ZNE)
    logger.info("--- Running With Readout Mitigation Only ---")
    energy_rm = executor._cut_and_reconstruct(
        circuit=bound_ansatz,
        hamiltonian=hamiltonian,
        strategy=strategy,
        options={"use_zne": False, "num_samples": 10000, "isa_pass_manager": pm}
    )
    
    # 7. Run with ZNE (Zero-Noise Extrapolation + Readout Mitigation)
    logger.info("--- Running With Readout Mitigation + ZNE ---")
    energy_zne = executor._cut_and_reconstruct(
        circuit=bound_ansatz,
        hamiltonian=hamiltonian,
        strategy=strategy,
        options={
            "use_zne": True, 
            "zne_scales": [1, 3, 5],
            "num_samples": 10000,
            "isa_pass_manager": pm
        }
    )
    
    logger.info("================ RESULTS ================")
    logger.info(f"Exact Ideal Energy:      {exact_energy:.4f}")
    logger.info(f"Readout Mitigated Only:  {energy_rm:.4f} (Abs Error: {abs(exact_energy - energy_rm):.4f})")
    logger.info(f"Readout + ZNE Mitigated: {energy_zne:.4f} (Abs Error: {abs(exact_energy - energy_zne):.4f})")
    logger.info("=========================================")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="Attempt to run on real IBM hardware")
    args = parser.parse_args()
    run_hardware_benchmark(use_real_hardware=args.real)
