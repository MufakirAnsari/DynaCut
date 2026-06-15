import sys
from qiskit import transpile
from qiskit.circuit.library import TwoLocal
from qiskit_ibm_runtime.fake_provider import FakeBrisbane

backend = FakeBrisbane()
for N in [14, 18, 22, 26]:
    ansatz = TwoLocal(N, 'rx', 'cz', reps=2, entanglement='linear')
    ansatz.measure_all()
    monolithic = transpile(ansatz, backend, optimization_level=3)
    print(f"N={N}, Monolithic Depth={monolithic.depth()}")
