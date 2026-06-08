from qiskit.circuit.library import EfficientSU2
from dynacut.topology import HypergraphPartitioner
edges = [(0, i) for i in range(1, 14)]
qc = EfficientSU2(14, reps=1, entanglement=edges)
partitioner = HypergraphPartitioner(None)
G = partitioner.circuit_to_interaction_graph(qc)
print("Nodes:", G.number_of_nodes())
print("Edges:", len(G.edges()))
print("Degrees:", [G.degree(n) for n in G.nodes])
import networkx as nx
part_a, part_b = nx.community.kernighan_lin_bisection(G, weight="weight")
print("Bisection sizes:", len(part_a), len(part_b))
cut_edges = [(u, v) for u, v in G.edges() if (u in part_a and v in part_b) or (u in part_b and v in part_a)]
print("Cut edges in bisection:", len(cut_edges))
