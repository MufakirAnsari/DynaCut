import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dynacut.executor import maxcut_hamiltonian, DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor

N = 14
edges = [(i, (i + 1) % N) for i in range(N)]
edges += [(0, 7), (3, 10), (5, 12)]
hamiltonian = maxcut_hamiltonian(edges, N)

ansatz = DynaCutExecutor.build_ansatz(
    N, reps=1, ansatz_type="qaoa", hamiltonian=hamiltonian
)

hypervisor1 = ResourceHypervisor(max_vram_gb=1e-6, max_ram_gb=23.0)
s1 = hypervisor1.find_optimal_strategy(ansatz)
print(f"max_vram_gb=1e-6 -> max_qubits={hypervisor1.max_qubits}, K={s1.num_cuts}")

hypervisor2 = ResourceHypervisor(max_vram_gb=5e-6, max_ram_gb=23.0)
s2 = hypervisor2.find_optimal_strategy(ansatz)
print(f"max_vram_gb=5e-6 -> max_qubits={hypervisor2.max_qubits}, K={s2.num_cuts}")

hypervisor3 = ResourceHypervisor(max_vram_gb=50e-6, max_ram_gb=23.0)
s3 = hypervisor3.find_optimal_strategy(ansatz)
print(f"max_vram_gb=50e-6 -> max_qubits={hypervisor3.max_qubits}, K={s3.num_cuts}")

