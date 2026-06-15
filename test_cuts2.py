import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dynacut.executor import maxcut_hamiltonian, DynaCutExecutor
from dynacut.adaptive_scheduler import ResourceHypervisor

N = 14
edges = [(i, (i + 1) % N) for i in range(N)]
edges += [(3, 10)]
hamiltonian = maxcut_hamiltonian(edges, N)

ansatz = DynaCutExecutor.build_ansatz(
    N, reps=1, ansatz_type="qaoa", hamiltonian=hamiltonian
)

hypervisor = ResourceHypervisor(max_vram_gb=50e-6, max_ram_gb=23.0)
s = hypervisor.find_optimal_strategy(ansatz)
print(f"max_qubits={hypervisor.max_qubits}, K={s.num_cuts}")
