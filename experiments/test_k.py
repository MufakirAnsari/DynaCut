import networkx as nx
from dynacut.kahypar_partitioner import kahypar_partition

N = 16
p_out = 0.05
G = nx.random_partition_graph([N//2, N//2], 0.8, p_out, seed=42)
assignment = kahypar_partition(G, k=2, epsilon=0.03)
print("Assignment:", assignment)
cuts = 0
for u, v in G.edges():
    if assignment[u] != assignment[v]:
        cuts += 1
print("Cuts:", cuts)
