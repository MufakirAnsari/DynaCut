import time
import numpy as np
import random
from typing import Tuple, Dict, Any, Optional

from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.primitives import StatevectorSampler

from qiskit_addon_cutting import (
    partition_problem,
    generate_cutting_experiments,
    reconstruct_expectation_values,
)

import quimb.tensor as qtn

from .executor import DynaCutExecutor
from .adaptive_scheduler import CutStrategy

def baseline_statevector(circuit: QuantumCircuit, hamiltonian: SparsePauliOp) -> Tuple[float, float, int]:
    """Exact statevector simulation. No cuts.
    Returns (energy, time, cuts).
    """
    t0 = time.time()
    energy = Statevector(circuit).expectation_value(hamiltonian).real
    dt = time.time() - t0
    return energy, dt, 0


def baseline_qiskit_cutting_raw(
    circuit: QuantumCircuit, 
    hamiltonian: SparsePauliOp, 
    strategy: CutStrategy
) -> Tuple[float, float, int]:
    """Raw qiskit-addon-cutting pipeline without TN reconstruction.
    Uses the partition strategy provided but reconstructs using IBM's method.
    """
    t0 = time.time()
    
    n = circuit.num_qubits
    partition_labels = [strategy.partition_labels[q] for q in range(n)]
    
    partitioned = partition_problem(
        circuit=circuit,
        partition_labels=partition_labels,
        observables=hamiltonian.paulis,
    )
    
    subexperiments, coefficients = generate_cutting_experiments(
        circuits=partitioned.subcircuits,
        observables=partitioned.subobservables,
        num_samples=np.inf,
    )
    
    from qiskit_addon_cutting.utils.simulation import ExactSampler
    
    sampler = ExactSampler()
    results = {
        label: sampler.run(experiments).result()
        for label, experiments in subexperiments.items()
    }
    
    reconstructed_expvals = reconstruct_expectation_values(
        results,
        coefficients,
        partitioned.subobservables,
    )
    
    energy = sum(c * ev for c, ev in zip(hamiltonian.coeffs, reconstructed_expvals)).real
    
    dt = time.time() - t0
    return float(energy), dt, strategy.num_cuts


def baseline_random_partitioning(
    circuit: QuantumCircuit, 
    hamiltonian: SparsePauliOp,
    max_fragments: int = 2
) -> Tuple[float, float, int]:
    """Randomly partitions the qubits and uses raw cutting.
    Demonstrates what happens without KL-bisection.
    """
    n = circuit.num_qubits
    
    # Assign qubits to random fragments
    partition_labels = [random.randint(0, max_fragments-1) for _ in range(n)]
    
    # Count cuts (edges between different partitions)
    # We must infer cuts from the circuit's gates.
    cuts = set()
    for inst in circuit.data:
        if len(inst.qubits) == 2:
            q0 = circuit.find_bit(inst.qubits[0]).index
            q1 = circuit.find_bit(inst.qubits[1]).index
            if partition_labels[q0] != partition_labels[q1]:
                cuts.add((min(q0, q1), max(q0, q1)))
                
    num_cuts = len(cuts)
    
    # If random partitioning creates too many cuts, QPD will be extremely slow
    if num_cuts > 3:
        # Cap it for tractability in baseline testing
        return float('nan'), 0.0, num_cuts
        
    t0 = time.time()
    try:
        partitioned = partition_problem(
            circuit=circuit,
            partition_labels=partition_labels,
            observables=hamiltonian.paulis,
        )
        subexperiments, coefficients = generate_cutting_experiments(
            circuits=partitioned.subcircuits,
            observables=partitioned.subobservables,
            num_samples=np.inf,
        )
        from qiskit_addon_cutting.utils.simulation import ExactSampler
        sampler = ExactSampler()
        results = {
            label: sampler.run(experiments).result()
            for label, experiments in subexperiments.items()
        }
        reconstructed_expvals = reconstruct_expectation_values(
            results,
            coefficients,
            partitioned.subobservables,
        )
        energy = sum(c * ev for c, ev in zip(hamiltonian.coeffs, reconstructed_expvals)).real
    except Exception:
        return float('nan'), 0.0, num_cuts
        
    dt = time.time() - t0
    return float(energy), dt, num_cuts


def baseline_mps_simulation(
    circuit: QuantumCircuit, 
    hamiltonian: SparsePauliOp, 
    max_bond: int = 64
) -> Tuple[float, float, int]:
    """Pure classical MPS simulation using Qiskit Aer.
    """
    t0 = time.time()
    try:
        from qiskit_aer import AerSimulator
        from qiskit.primitives import Estimator
        from qiskit_aer.primitives import Estimator as AerEstimator
        
        # Aer Estimator with MPS method
        estimator = AerEstimator(
            run_options={"method": "matrix_product_state", "matrix_product_state_max_bond_dimension": max_bond},
            approximation=True # exact expectation value from MPS
        )
        
        job = estimator.run([circuit], [hamiltonian])
        energy = job.result().values[0]
        
        dt = time.time() - t0
        return float(energy), dt, 0
    except ImportError:
        return float('nan'), 0.0, 0

def baseline_aer_noise(
    circuit: QuantumCircuit, 
    hamiltonian: SparsePauliOp, 
) -> Tuple[float, float, int]:
    """Baseline: Qiskit Aer with a basic depolarizing noise model."""
    t0 = time.time()
    try:
        from qiskit_aer import AerSimulator
        from qiskit_aer.noise import NoiseModel, depolarizing_error
        from qiskit_aer.primitives import Estimator as AerEstimator
        
        # Simple noise model
        noise_model = NoiseModel()
        error_1q = depolarizing_error(0.001, 1)
        error_2q = depolarizing_error(0.01, 2)
        noise_model.add_all_qubit_quantum_error(error_1q, ['rx', 'ry', 'rz', 'h'])
        noise_model.add_all_qubit_quantum_error(error_2q, ['cx', 'cz'])
        
        estimator = AerEstimator(
            run_options={"noise_model": noise_model, "shots": 10000}
        )
        
        job = estimator.run([circuit], [hamiltonian])
        energy = job.result().values[0]
        
        dt = time.time() - t0
        return float(energy), dt, 0
    except ImportError:
        return float('nan'), 0.0, 0


def baseline_metis_partitioning(
    circuit: QuantumCircuit, 
    hamiltonian: SparsePauliOp,
    max_fragments: int = 2
) -> Tuple[float, float, int]:
    """Baseline: METIS graph partitioning for cuts."""
    t0 = time.time()
    try:
        import pymetis
        from dynacut.topology import circuit_to_interaction_graph
        from qiskit_addon_cutting import partition_problem, generate_cutting_experiments, reconstruct_expectation_values
        from qiskit_addon_cutting.utils.simulation import ExactSampler
        
        # Build interaction graph
        graph = circuit_to_interaction_graph(circuit)
        
        # Run pymetis
        n_cuts, membership = pymetis.part_graph(max_fragments, adjacency=graph)
        
        partition_labels = list(membership)
        
        partitioned = partition_problem(
            circuit=circuit,
            partition_labels=partition_labels,
            observables=hamiltonian.paulis,
        )
        subexperiments, coefficients = generate_cutting_experiments(
            circuits=partitioned.subcircuits,
            observables=partitioned.subobservables,
            num_samples=np.inf,
        )
        sampler = ExactSampler()
        results = {
            label: sampler.run(experiments).result()
            for label, experiments in subexperiments.items()
        }
        reconstructed_expvals = reconstruct_expectation_values(
            results,
            coefficients,
            partitioned.subobservables,
        )
        energy = sum(c * ev for c, ev in zip(hamiltonian.coeffs, reconstructed_expvals)).real
        
        dt = time.time() - t0
        return float(energy), dt, n_cuts
    except ImportError:
        return float('nan'), 0.0, 0


def baseline_cutqc(
    circuit: QuantumCircuit, 
    hamiltonian: SparsePauliOp,
) -> Tuple[float, float, int]:
    """Baseline: CutQC (Tang et al., 2021).
    Since CutQC is a specific toolkit that may not be compatible with Qiskit 1.0,
    we simulate its MIP-based partitioning and standard QPD reconstruction overhead.
    """
    t0 = time.time()
    try:
        # We simulate CutQC's performance by using standard qiskit-addon-cutting 
        # but with a MIP-like minimal bisection (approximated here by KL for compatibility).
        # In a full paper, one would interface directly with the CutQC repo.
        from dynacut.adaptive_scheduler import ResourceHypervisor
        from dynacut.executor import DynaCutExecutor
        
        hypervisor = ResourceHypervisor(max_vram_gb=4.0)
        executor = DynaCutExecutor(hypervisor)
        strategy = hypervisor.find_optimal_strategy(circuit)
        
        # CutQC does not use TN reconstruction, so we use IBM raw path
        energy, _, cuts = baseline_qiskit_cutting_raw(circuit, hamiltonian, strategy)
        
        dt = time.time() - t0
        return float(energy), dt, cuts
    except Exception:
        return float('nan'), 0.0, 0
