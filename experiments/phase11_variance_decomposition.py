"""
Phase 11: Variance Decomposition Bar Chart

This script isolates the three orthogonal sources of error:
1. Physical Error (eps_phys) -> Hardware Depolarizing Noise
2. Truncation Error (eps_trunc) -> Tensor Network SVD Bond Dimension
3. Statistical Error (eps_stat) -> QPD Sampling Variance

We compute these analytically for an N=10 QAOA MaxCut circuit,
comparing Monolithic execution against DynaCut.
"""

import os
import sys
import json
import time
import numpy as np
import networkx as nx
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit.quantum_info import Statevector
from scipy.optimize import minimize

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dynacut.executor import maxcut_hamiltonian, DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
OUT_FILE = os.path.join(RESULTS_DIR, 'variance_decomposition.json')

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_noisy_expectation(circuit, observable, noise_model):
    """Computes exact density matrix expectation value under noise."""
    sim = AerSimulator(method='density_matrix', noise_model=noise_model)
    qc = circuit.copy()
    qc.remove_final_measurements()
    qc.save_density_matrix()
    t_qc = transpile(qc, sim, optimization_level=0)
    result = sim.run(t_qc, shots=None).result()
    dm = result.data()['density_matrix']
    return float(np.real(dm.expectation_value(observable)))

def get_mps_expectation(circuit, observable, chi):
    """Computes exact MPS expectation value under finite bond dimension."""
    sim = AerSimulator(method='matrix_product_state')
    sim.set_options(matrix_product_state_max_bond_dimension=chi)
    qc = circuit.copy()
    qc.remove_final_measurements()
    qc.save_expectation_value(observable, qc.qubits)
    t_qc = transpile(qc, sim, optimization_level=0)
    result = sim.run(t_qc, shots=None).result()
    if not result.success:
        raise RuntimeError("MPS simulation failed.")
    return float(np.real(result.data()['expectation_value']))

def run_variance_decomposition():
    N = 10
    G = nx.random_regular_graph(3, N, seed=42)
    hamiltonian = maxcut_hamiltonian(G.edges(), N)
    norm_H = sum(abs(c) for c in hamiltonian.coeffs)
    
    ansatz = DynaCutExecutor.build_ansatz(N, reps=2, ansatz_type="qaoa", hamiltonian=hamiltonian)
    np.random.seed(42)
    init_params = np.random.uniform(-np.pi, np.pi, ansatz.num_parameters)
    
    # Optimize to a strong ground state
    def obj(params):
        sv = Statevector(ansatz.assign_parameters(params))
        return -float(np.real(sv.expectation_value(hamiltonian)))
        
    res = minimize(obj, init_params, method='COBYLA', options={'maxiter': 100})
    opt_params = res.x
    bound_circuit = ansatz.assign_parameters(opt_params)
    
    ideal_sv = Statevector(bound_circuit)
    E_ideal = float(np.real(ideal_sv.expectation_value(hamiltonian)))
    logger.info(f"Ideal Ground Energy: {E_ideal:.4f}")
    
    hypervisor = ResourceHypervisor(max_qubits_per_fragment=6)
    strategy = hypervisor.find_optimal_strategy(ansatz)
    gamma = 3 ** strategy.num_cuts
    
    # Custom circuit for analytical noise modeling
    from qiskit.circuit.library import CXGate
    custom_circuit = bound_circuit.copy()
    for i, instruction in enumerate(custom_circuit.data):
        if instruction.operation.name == 'cx':
            q0 = custom_circuit.find_bit(instruction.qubits[0]).index
            q1 = custom_circuit.find_bit(instruction.qubits[1]).index
            if strategy.partition_labels[q0] != strategy.partition_labels[q1]:
                new_op = CXGate(label="cx_cut")
                new_op.name = "cx_cut"
                custom_circuit.data[i] = instruction.replace(operation=new_op)
                
    S = 1000000 # 1,000,000 shots
    p_cx = 0.05 # High Hardware noise level
    chi = 8 # Finite bond dimension for TN
    
    # --- Monolithic Errors ---
    logger.info("Computing Monolithic Errors...")
    mono_noise = NoiseModel()
    mono_noise.add_all_qubit_quantum_error(depolarizing_error(p_cx, 2), ['cx', 'cx_cut'])
    E_mono_noisy = get_noisy_expectation(custom_circuit, hamiltonian, mono_noise)
    
    eps_phys_mono = abs(E_ideal - E_mono_noisy)
    eps_trunc_mono = 0.0
    eps_stat_mono = (1.0 * norm_H) / np.sqrt(S)
    
    # --- DynaCut Errors ---
    logger.info("Computing DynaCut Errors...")
    # 1. Truncation Error (via MPS)
    E_cut_mps = get_mps_expectation(bound_circuit, hamiltonian, chi)
    eps_trunc_cut = abs(E_ideal - E_cut_mps)
    
    # 2. Physical Error
    cut_noise = NoiseModel()
    cut_noise.add_all_qubit_quantum_error(depolarizing_error(p_cx, 2), ['cx']) # Noise ONLY on uncut CNOTs
    E_cut_noisy = get_noisy_expectation(custom_circuit, hamiltonian, cut_noise)
    eps_phys_cut = abs(E_ideal - E_cut_noisy)
    
    # 3. Statistical Error
    eps_stat_cut = (gamma * norm_H) / np.sqrt(S)
    
    results = {
        "N": N,
        "shots": S,
        "p_cx": p_cx,
        "chi": chi,
        "gamma": gamma,
        "norm_H": float(norm_H),
        "E_ideal": E_ideal,
        "monolithic": {
            "eps_phys": float(eps_phys_mono),
            "eps_trunc": float(eps_trunc_mono),
            "eps_stat": float(eps_stat_mono),
            "total_bound": float(eps_phys_mono + eps_trunc_mono + eps_stat_mono)
        },
        "dynacut": {
            "eps_phys": float(eps_phys_cut),
            "eps_trunc": float(eps_trunc_cut),
            "eps_stat": float(eps_stat_cut),
            "total_bound": float(eps_phys_cut + eps_trunc_cut + eps_stat_cut)
        }
    }
    
    with open(OUT_FILE, 'w') as f:
        json.dump(results, f, indent=4)
        
    logger.info(f"Finished Variance Decomposition. Saved to {OUT_FILE}")

if __name__ == "__main__":
    run_variance_decomposition()
