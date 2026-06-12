import pytest
from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor
import networkx as nx

def test_maxcut_hamiltonian():
    G = nx.Graph()
    G.add_edge(0, 1)
    ham = maxcut_hamiltonian(list(G.edges()), 2)
    assert ham.num_qubits == 2

def test_executor_init():
    hypervisor = ResourceHypervisor(max_vram_gb=4.0)
    executor = DynaCutExecutor(hypervisor=hypervisor)
    assert executor.hypervisor == hypervisor
