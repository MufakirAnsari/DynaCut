import numpy as np
import itertools
from qiskit.circuit.library import CXGate
from qiskit_addon_cutting.qpd import QPDGate
from qiskit_addon_cutting.qpd.instructions import qpd_basis_from_instruction
from qiskit_addon_cutting.cutting_experiments import generate_cutting_experiments
from qiskit.circuit import QuantumCircuit

circuit = QuantumCircuit(4)
circuit.append(QPDGate(qpd_basis_from_instruction(CXGate()), qubit_indices=[0, 1]), [0, 1])
circuit.append(QPDGate(qpd_basis_from_instruction(CXGate()), qubit_indices=[2, 3]), [2, 3])

subs, coeffs = generate_cutting_experiments(
    {0: circuit},
    observables={0: []},
    num_samples=np.inf
)

joint_weights = np.array([c[0] for c in coeffs])
joint_nd = joint_weights.reshape(6, 6)

w0 = joint_nd[:, 0] / joint_nd[0, 0]
w1 = joint_nd[0, :] / joint_nd[0, 0]

print("w0:", w0)
print("w1:", w1)
print("Reconstructed exact?", np.allclose(joint_nd, joint_nd[0, 0] * np.outer(w0, w1)))
