from experiments.adversarial_graphs import generate_adversarial_graph
from dynacut.executor import maxcut_hamiltonian
from qiskit.circuit.library import EfficientSU2
edges = generate_adversarial_graph("star", 14, 0)
print(edges)
qc = EfficientSU2(14, reps=1, entanglement=edges)
print("QC Depth:", qc.depth())
print("QC Ops:", qc.count_ops())
