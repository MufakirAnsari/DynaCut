import numpy as np
import scipy.sparse.linalg as sla
from qiskit.quantum_info import SparsePauliOp

def compute_exact_ground_state(hamiltonian: SparsePauliOp) -> float:
    """Compute the exact ground state energy of a Hamiltonian.

    For small systems (<= 12 qubits), computes the dense matrix and uses
    numpy.linalg.eigvalsh. For larger systems, uses scipy.sparse.linalg.eigsh
    to find the smallest algebraic eigenvalue.

    Parameters
    ----------
    hamiltonian : SparsePauliOp
        The Hamiltonian operator.

    Returns
    -------
    float
        The exact ground state energy.
    """
    num_qubits = hamiltonian.num_qubits

    if num_qubits <= 12:
        # Dense eigensolver is fast enough for <= 12 qubits
        dense_matrix = hamiltonian.to_matrix()
        eigenvalues = np.linalg.eigvalsh(dense_matrix)
        return float(np.min(eigenvalues))
    else:
        # Sparse eigensolver for > 12 qubits
        # to_matrix(sparse=True) gives a scipy sparse matrix
        sparse_matrix = hamiltonian.to_matrix(sparse=True)
        # We only need the smallest algebraic eigenvalue (which corresponds to ground state)
        # 'SA' stands for Smallest Algebraic
        eigenvalues, _ = sla.eigsh(sparse_matrix, k=1, which='SA')
        return float(eigenvalues[0])
