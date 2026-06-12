import pytest
from qiskit import QuantumCircuit
from dynacut.adaptive_scheduler import ResourceHypervisor

def test_hypervisor_trivial_strategy():
    hypervisor = ResourceHypervisor(max_vram_gb=4.0)
    qc = QuantumCircuit(2)
    strategy = hypervisor.find_optimal_strategy(qc)
    assert strategy is not None
