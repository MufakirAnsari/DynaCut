import numpy as np
from qiskit import QuantumCircuit

def fold_circuit_global(circuit: QuantumCircuit, scale_factor: int) -> QuantumCircuit:
    """
    Globally fold a quantum circuit to increase its noise for Zero-Noise Extrapolation (ZNE).
    Maps U -> U (U^dagger U)^n where scale_factor = 2n + 1.
    
    Args:
        circuit: The input QuantumCircuit to be folded.
        scale_factor: An odd integer (1, 3, 5, etc.) representing the noise scaling.
        
    Returns:
        A new QuantumCircuit that is the folded version of the input.
    """
    if scale_factor % 2 == 0 or scale_factor < 1:
        raise ValueError("Scale factor for ZNE global folding must be an odd integer >= 1.")
        
    if scale_factor == 1:
        return circuit.copy()
        
    # We only want to fold the unitary part, NOT the measurements!
    # If the circuit has mid-circuit measurements, global folding is extremely tricky.
    # Qiskit Addon Cutting produces circuits with mid-circuit measurements and resets.
    # U^dagger of a measurement is not defined.
    # To properly do ZNE on QPD circuits, we must fold ONLY the unitary gates.
    
    # Simple workaround for QPD circuits:
    # Instead of global unitary folding, we can just do identity insertion or local folding.
    # For now, let's build a gate-by-gate folding (local folding):
    # For each gate G, if G is a unitary, we map G -> G (G^dagger G)^n
    
    n = (scale_factor - 1) // 2
    folded_circ = QuantumCircuit(*circuit.qregs, *circuit.cregs)
    
    for instruction in circuit.data:
        op = instruction.operation
        qargs = instruction.qubits
        cargs = instruction.clbits
        
        # Add the original operation
        folded_circ.append(op, qargs, cargs)
        
        # If it's a standard gate (unitary, not measure/reset/barrier/QPD)
        # QPD measure/resets are just standard measure/resets in the Qiskit circuit
        if op.name not in ['measure', 'reset', 'barrier', 'delay']:
            try:
                op_inv = op.inverse()
                for _ in range(n):
                    folded_circ.append(op_inv, qargs, cargs)
                    folded_circ.append(op, qargs, cargs)
            except Exception:
                # If it cannot be inverted (e.g. non-unitary), skip folding it
                pass
                
    return folded_circ

def linear_extrapolate(scale_factors, expectation_values):
    """
    Linearly extrapolate the expectation value to the zero-noise limit (scale_factor = 0).
    
    Args:
        scale_factors: List of integers, e.g. [1, 3, 5]
        expectation_values: Corresponding list of noisy expectation values.
        
    Returns:
        The extrapolated expectation value at scale_factor = 0.
    """
    if len(scale_factors) != len(expectation_values):
        raise ValueError("Length of scale factors and expectation values must match.")
        
    # Fit a line: E(lambda) = E(0) + m * lambda
    # We want the intercept E(0)
    coeffs = np.polyfit(scale_factors, expectation_values, 1)
    intercept = coeffs[1]
    return intercept

def richardson_extrapolate(scale_factors, expectation_values):
    """
    Perform Richardson extrapolation to the zero-noise limit.
    This fits a polynomial of degree N-1 where N is the number of points.
    
    Args:
        scale_factors: List of scale factors.
        expectation_values: Corresponding list of expectation values.
        
    Returns:
        The zero-noise extrapolated value.
    """
    # Fit a polynomial of degree N-1
    degree = len(scale_factors) - 1
    coeffs = np.polyfit(scale_factors, expectation_values, degree)
    # The intercept is the last coefficient in numpy's polyfit (highest to lowest degree)
    return coeffs[-1]
