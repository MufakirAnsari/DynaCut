"""
Phase 8: Chemistry Hamiltonian Test (Potential Energy Surface).

This script proves that DynaCut is Hamiltonian-agnostic and functions on
fermionic quantum chemistry problems. We compute the dissociation curve
(Potential Energy Surface) of the H2 molecule.

We use qiskit_nature and PySCFDriver to generate the true Fermionic Hamiltonian
at varying bond distances, map it to a SparsePauliOp via Jordan-Wigner, and
solve it using DynaCut VQE.
"""

import os
import sys
import json
import time
import numpy as np

# Require qiskit_nature and pyscf
try:
    from qiskit_nature.units import DistanceUnit
    from qiskit_nature.second_q.drivers import PySCFDriver
    from qiskit_nature.second_q.mappers import JordanWignerMapper
    from qiskit_algorithms import NumPyMinimumEigensolver
    from qiskit_nature.second_q.algorithms import GroundStateEigensolver
except ImportError:
    print("This script requires qiskit-nature and pyscf: pip install qiskit-nature pyscf")
    sys.exit(1)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dynacut.executor import DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
OUT_FILE = os.path.join(RESULTS_DIR, 'chemistry_pes.json')


def get_h2_qubit_op(distance):
    """Generate H2 qubit Hamiltonian at given bond distance."""
    driver = PySCFDriver(
        atom=f"H 0 0 0; H 0 0 {distance}",
        basis="sto3g",
        charge=0,
        spin=0,
        unit=DistanceUnit.ANGSTROM,
    )
    problem = driver.run()
    
    # Jordan-Wigner mapping
    mapper = JordanWignerMapper()
    fermionic_op = problem.hamiltonian.second_q_op()
    qubit_op = mapper.map(fermionic_op)
    
    return qubit_op, problem


def run_pes_scan():
    # Bond distances to scan
    distances = np.linspace(0.5, 2.5, 11)
    
    hypervisor = ResourceHypervisor(max_qubits_per_fragment=2) # Force cuts on 4-qubit H2
    executor = DynaCutExecutor(hypervisor)
    
    results = {"distances": list(distances), "exact_energies": [], "dynacut_energies": []}
    
    print("Starting H2 Potential Energy Surface Scan...")
    
    for r in distances:
        print(f"\n--- Bond Distance R = {r:.2f} Å ---")
        
        # 1. Generate Chemistry Hamiltonian
        qubit_op, problem = get_h2_qubit_op(r)
        num_qubits = qubit_op.num_qubits
        print(f"Generated {num_qubits}-qubit Hamiltonian with {len(qubit_op)} Pauli terms.")
        
        # 2. Exact Eigensolver Ground Truth
        exact_solver = NumPyMinimumEigensolver()
        calc = GroundStateEigensolver(JordanWignerMapper(), exact_solver)
        exact_result = calc.solve(problem)
        exact_energy = exact_result.total_energies[0]
        results["exact_energies"].append(exact_energy)
        print(f"Exact Energy: {exact_energy:.6f} Ha")
        
        # 3. DynaCut VQE with UCCSD
        from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
        initial_state = HartreeFock(
            problem.num_spatial_orbitals,
            problem.num_particles,
            JordanWignerMapper()
        )
        ansatz = UCCSD(
            problem.num_spatial_orbitals,
            problem.num_particles,
            JordanWignerMapper(),
            initial_state=initial_state
        )
        # UCCSD creates a QuantumCircuit natively, pass it to hypervisor
        strategy = hypervisor.find_optimal_strategy(ansatz)
        print(f"Cut Strategy: {strategy.num_fragments} fragments, {strategy.num_cuts} cuts.")
        
        t0 = time.time()
        # Run VQE for a few iterations (or just use exact sampling + COBYLA)
        vqe_res = executor.run_vqe(
            ansatz=ansatz,
            hamiltonian=qubit_op,
            strategy=strategy,
            method="COBYLA",
            maxiter=100,
            num_samples=np.inf, # exact QPD
            reconstruction_method="ibm"
        )
        elapsed = time.time() - t0
        
        # Need to add nuclear repulsion energy back to get total energy
        nuclear_repulsion = problem.hamiltonian.nuclear_repulsion_energy
        dynacut_total_energy = vqe_res["optimal_energy"] + nuclear_repulsion
        results["dynacut_energies"].append(dynacut_total_energy)
        
        print(f"DynaCut Energy: {dynacut_total_energy:.6f} Ha ({elapsed:.2f}s)")
        print(f"Error: {abs(dynacut_total_energy - exact_energy):.2e} Ha")
        
        # Save incrementally
        with open(OUT_FILE, 'w') as f:
            json.dump(results, f, indent=4)
            
    print(f"\nPES Scan complete. Results saved to {OUT_FILE}")

if __name__ == "__main__":
    run_pes_scan()
