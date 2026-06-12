import pytest
import networkx as nx
from qiskit import QuantumCircuit
from dynacut.topology import HypergraphPartitioner

def test_circuit_to_interaction_graph():
    qc = QuantumCircuit(3)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.cx(0, 2)
    
    partitioner = HypergraphPartitioner()
    G = partitioner.circuit_to_interaction_graph(qc)
    
    assert G.number_of_nodes() == 3
    assert G.number_of_edges() == 3
    assert G[0][1]["weight"] == 1.0

def test_partition():
    qc = QuantumCircuit(4)
    # create two disconnected components
    qc.cx(0, 1)
    qc.cx(2, 3)
    
    partitioner = HypergraphPartitioner()
    labels, cut_edges = partitioner.partition(qc, max_fragment_qubits=2)
    
    assert len(labels) == 4
    assert len(cut_edges) == 0
    assert labels[0] == labels[1]
    assert labels[2] == labels[3]
    assert labels[0] != labels[2]

def test_check_hardware_embeddability():
    partitioner = HypergraphPartitioner() # No coupling map
    assert partitioner.check_hardware_embeddability({0, 1}) == True
