import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit.circuit import Gate

# Uncut Circuit
qc_uncut = QuantumCircuit(4)
qc_uncut.h(range(4))
qc_uncut.cx(0, 1)
qc_uncut.cx(2, 3)
qc_uncut.barrier()
qc_uncut.cx(1, 2)
qc_uncut.barrier()
qc_uncut.rx(0.5, range(4))

fig_uncut = qc_uncut.draw(output='mpl', style='clifford')
fig_uncut.savefig('paper/figures/circuit_diagram_uncut.png', dpi=300, bbox_inches='tight')

# Cut Circuit
qc_cut = QuantumCircuit(4)
qc_cut.h(range(4))
qc_cut.cx(0, 1)
qc_cut.cx(2, 3)
qc_cut.barrier()

# QPD Gates
qpd_meas = Gate(name='QPD Meas', num_qubits=1, params=[])
qpd_prep = Gate(name='QPD Prep', num_qubits=1, params=[])

qc_cut.append(qpd_meas, [1])
qc_cut.append(qpd_prep, [2])

qc_cut.barrier()
qc_cut.rx(0.5, range(4))

fig_cut = qc_cut.draw(output='mpl', style='clifford')
fig_cut.savefig('paper/figures/circuit_diagram_cut.png', dpi=300, bbox_inches='tight')
