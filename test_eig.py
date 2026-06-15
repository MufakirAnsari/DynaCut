from dynacut.executor import maxcut_hamiltonian
import numpy as np
from scipy.sparse.linalg import eigsh
N = 14
edges = [(i, (i + 1) % N) for i in range(N)]
edges += [(3, 10)]
ham = -1.0 * maxcut_hamiltonian(edges, N)
# Sparse matrix calculation
sparse_mat = ham.to_matrix(sparse=True)
val = eigsh(sparse_mat, k=1, which='SA', return_eigenvectors=False)
print("Sparse min eig:", val[0])
