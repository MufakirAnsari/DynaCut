from qiskit_ibm_runtime.fake_provider import FakeGuadalupeV2
from qiskit_ibm_runtime import SamplerV2
from qiskit.circuit.random import random_circuit
backend = FakeGuadalupeV2()
qc = random_circuit(2, 2, measure=True)
sampler = SamplerV2(backend=backend)
sampler.options.resilience_level = 1 # TREX
job = sampler.run([qc])
print(job.result()[0].data)
