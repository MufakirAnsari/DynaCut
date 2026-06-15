import qiskit_nature
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import ParityMapper

driver = PySCFDriver(atom="H 0 0 0; H 0 0 0.735", basis="sto3g")
problem = driver.run()
mapper = ParityMapper(num_particles=problem.num_particles)
hamiltonian = mapper.map(problem.hamiltonian.second_q_op())
print(f"Num qubits: {hamiltonian.num_qubits}")
print(hamiltonian)
