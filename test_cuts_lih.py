import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dynacut.executor import DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor
import qiskit_nature
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import ParityMapper

driver_lih = PySCFDriver(atom="Li 0 0 0; H 0 0 1.5474", basis="sto3g")
problem_lih = driver_lih.run()
mapper_lih = ParityMapper(num_particles=problem_lih.num_particles)
lih_ham = mapper_lih.map(problem_lih.hamiltonian.second_q_op())

hypervisor = ResourceHypervisor(max_vram_gb=1e-6, max_ram_gb=23.0)
ansatz = DynaCutExecutor.build_ansatz(10, reps=1, ansatz_type="hardware_efficient")
s = hypervisor.find_optimal_strategy(ansatz)
print(f"LiH K={s.num_cuts}")
