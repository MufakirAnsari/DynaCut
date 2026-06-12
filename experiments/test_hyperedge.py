import quimb.tensor as qtn
import numpy as np
import time

coeff = np.random.rand(216)
frag0 = np.random.rand(216)
frag1 = np.random.rand(216)

t1 = qtn.Tensor(coeff, inds=("qpd",))
t2 = qtn.Tensor(frag0, inds=("qpd",))
t3 = qtn.Tensor(frag1, inds=("qpd",))

tn = qtn.TensorNetwork([t1, t2, t3])

print("Trying greedy with output_inds=()...")
t0 = time.time()
res = tn.contract(optimize="greedy", output_inds=())
print("Time:", time.time() - t0, "Result:", res)

print("Trying auto with output_inds=()...")
t0 = time.time()
res = tn.contract(optimize="auto", output_inds=())
print("Time:", time.time() - t0, "Result:", res)
