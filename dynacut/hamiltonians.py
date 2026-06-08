from qiskit.quantum_info import SparsePauliOp
from typing import List, Tuple
import numpy as np

def maxcut_hamiltonian(graph_edges: List[Tuple[int, int]], num_qubits: int) -> SparsePauliOp:
    """Build the MaxCut cost Hamiltonian as a SparsePauliOp."""
    pauli_list = []
    coeffs = []
    for i, j in graph_edges:
        identity = "I" * num_qubits
        pauli_list.append(identity)
        coeffs.append(0.5)
        zz = list("I" * num_qubits)
        zz[num_qubits - 1 - i] = "Z"
        zz[num_qubits - 1 - j] = "Z"
        pauli_list.append("".join(zz))
        coeffs.append(-0.5)
    return SparsePauliOp.from_list(list(zip(pauli_list, coeffs))).simplify()

def h2_molecule_hamiltonian() -> SparsePauliOp:
    """4-qubit Jordan-Wigner Hamiltonian for H2 at 0.735 Angstroms."""
    paulis = [
        "IIII", "IIIZ", "IIZI", "IZII", "ZIII", 
        "IIZZ", "IZIZ", "ZIIZ", "IZZI", "ZIZI", "ZZII", 
        "YYXX", "YXYY", "XYYX", "XXYY"
    ]
    coeffs = [
        -0.097066, 0.171413, 0.171413, -0.223432, -0.223432,
        0.168689, 0.120625, 0.165928, 0.165928, 0.120625, 0.174413,
        0.045303, -0.045303, -0.045303, 0.045303
    ]
    return SparsePauliOp.from_list(list(zip(paulis, coeffs)))

def tfim_hamiltonian(num_qubits: int, j_coupling: float = 1.0, h_field: float = 1.0) -> SparsePauliOp:
    """1D Transverse-Field Ising Model Hamiltonian.
    H = -J sum(Z_i Z_i+1) - h sum(X_i)
    """
    paulis = []
    coeffs = []
    
    # ZZ interaction (open boundary)
    for i in range(num_qubits - 1):
        zz = list("I" * num_qubits)
        zz[num_qubits - 1 - i] = "Z"
        zz[num_qubits - 1 - (i + 1)] = "Z"
        paulis.append("".join(zz))
        coeffs.append(-j_coupling)
        
    # X field
    for i in range(num_qubits):
        x = list("I" * num_qubits)
        x[num_qubits - 1 - i] = "X"
        paulis.append("".join(x))
        coeffs.append(-h_field)
        
    return SparsePauliOp.from_list(list(zip(paulis, coeffs))).simplify()

def heisenberg_hamiltonian(num_qubits: int, j_coupling: float = 1.0) -> SparsePauliOp:
    """1D Heisenberg XXX Model Hamiltonian.
    H = J sum(X_i X_i+1 + Y_i Y_i+1 + Z_i Z_i+1)
    """
    paulis = []
    coeffs = []
    
    for i in range(num_qubits - 1):
        for op in ["X", "Y", "Z"]:
            term = list("I" * num_qubits)
            term[num_qubits - 1 - i] = op
            term[num_qubits - 1 - (i + 1)] = op
            paulis.append("".join(term))
            coeffs.append(j_coupling)
            
    return SparsePauliOp.from_list(list(zip(paulis, coeffs))).simplify()
