import quimb.tensor as qtn
import numpy as np
T1 = qtn.Tensor(np.random.rand(6, 6), inds=('a', 'b'))
T2 = qtn.Tensor(np.random.rand(6, 6), inds=('b', 'c'))
T3 = qtn.Tensor(np.random.rand(6, 6), inds=('c', 'd'))
T4 = qtn.Tensor(np.random.rand(6, 6), inds=('d', 'a'))
tn = qtn.TensorNetwork([T1, T2, T3, T4])
res_exact = tn.contract()
res_comp2 = tn.contract_compressed(optimize='greedy', max_bond=2)
res_comp3 = tn.contract_compressed(optimize='greedy', max_bond=3)
print("Exact:", res_exact)
print("Comp 2:", res_comp2)
print("Comp 3:", res_comp3)
