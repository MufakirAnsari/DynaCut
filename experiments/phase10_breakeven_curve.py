"""
Phase 10: Empirical Breakeven Curve

This script rigorously evaluates the core hypothesis of DynaCut: trading
QPD sampling variance for a massive reduction in physical hardware noise.
We simulate an N=10 QAOA circuit using exact DensityMatrix simulation 
across a sweep of 2-qubit depolarizing error rates.
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
from qiskit.quantum_info import Statevector, DensityMatrix

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dynacut.executor import maxcut_hamiltonian, DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor
from qiskit_addon_cutting import partition_problem, generate_cutting_experiments

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
OUT_FILE = os.path.join(RESULTS_DIR, 'breakeven_curve.json')

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

def run_breakeven_sweep():
    N = 10
    G = nx.random_regular_graph(3, N, seed=42)
    hamiltonian = maxcut_hamiltonian(G.edges(), N)
    norm_H = sum(abs(c) for c in hamiltonian.coeffs)
    
    ansatz = DynaCutExecutor.build_ansatz(N, reps=2, ansatz_type="qaoa", hamiltonian=hamiltonian)
    np.random.seed(42)
    init_params = np.random.uniform(-np.pi, np.pi, ansatz.num_parameters)
    
    # We want to MAXIMIZE the MaxCut objective (which is positive). So we minimize negative expectation.
    from scipy.optimize import minimize
    def obj(params):
        sv = Statevector(ansatz.assign_parameters(params))
        return -float(np.real(sv.expectation_value(hamiltonian)))
        
    res = minimize(obj, init_params, method='COBYLA', options={'maxiter': 100})
    opt_params = res.x
    bound_circuit = ansatz.assign_parameters(opt_params)
    
    ideal_sv = Statevector(bound_circuit)
    ideal_energy = float(np.real(ideal_sv.expectation_value(hamiltonian)))
    logger.info(f"Ideal Ground Energy: {ideal_energy:.4f}")
    
    hypervisor = ResourceHypervisor(max_qubits_per_fragment=6)
    strategy = hypervisor.find_optimal_strategy(ansatz)
    logger.info(f"Strategy: {strategy.num_fragments} fragments, {strategy.num_cuts} cuts.")
    gamma = 3 ** strategy.num_cuts
    
    # We will rename the CUT cx gates so we can apply noise selectively.
    from qiskit.circuit.library import CXGate
    
    custom_circuit = bound_circuit.copy()
    cut_count = 0
    
    for i, instruction in enumerate(custom_circuit.data):
        if instruction.operation.name == 'cx':
            q0 = custom_circuit.find_bit(instruction.qubits[0]).index
            q1 = custom_circuit.find_bit(instruction.qubits[1]).index
            frag0 = strategy.partition_labels[q0]
            frag1 = strategy.partition_labels[q1]
            
            if frag0 != frag1:
                # This is a cut gate! Rename it.
                new_op = CXGate(label="cx_cut")
                new_op.name = "cx_cut"
                custom_circuit.data[i] = instruction.replace(operation=new_op)
                cut_count += 1
                
    logger.info(f"Identified {cut_count} CX gates crossing partitions.")
    
    error_rates = [0.0, 0.005, 0.01, 0.02, 0.03, 0.04, 0.06, 0.08, 0.10]
    results = {
        "N": N,
        "ideal_energy": ideal_energy,
        "gamma": gamma,
        "norm_H": float(norm_H),
        "data": []
    }
    
    for p in error_rates:
        logger.info(f"--- Evaluating p_cx = {p} ---")
        
        # Monolithic Noise Model: Noise on ALL CX gates
        mono_noise = NoiseModel()
        # DynaCut Noise Model: Noise ONLY on uncut CX gates (cut gates are reconstructed ideally via QPD SPAM)
        cut_noise = NoiseModel()
        
        if p > 0:
            error_2q = depolarizing_error(p, 2)
            mono_noise.add_all_qubit_quantum_error(error_2q, ['cx', 'cx_cut'])
            cut_noise.add_all_qubit_quantum_error(error_2q, ['cx']) # No noise on cx_cut!
            
        t0 = time.time()
        mono_energy = get_noisy_expectation(custom_circuit, hamiltonian, mono_noise)
        t_mono = time.time() - t0
        
        t0 = time.time()
        cut_energy = get_noisy_expectation(custom_circuit, hamiltonian, cut_noise)
        t_cut = time.time() - t0
        
        logger.info(f"  Monolithic Energy: {mono_energy:.4f} ({t_mono:.2f}s)")
        logger.info(f"  DynaCut Energy: {cut_energy:.4f} ({t_cut:.2f}s)")
        
        results["data"].append({
            "p_cx": p,
            "monolithic_energy": float(mono_energy),
            "dynacut_energy": float(cut_energy)
        })
        
        with open(OUT_FILE, 'w') as f:
            json.dump(results, f, indent=4)
            
    logger.info(f"Finished sweep. Saved to {OUT_FILE}")

if __name__ == "__main__":
    run_breakeven_sweep()
