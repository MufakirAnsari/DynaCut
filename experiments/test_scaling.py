import numpy as np
import time
import networkx as nx

N = 20
p_out = 0.05
G = nx.random_partition_graph([N//2, N//2], 0.8, p_out, seed=42)

start = time.time()
# Just a simple test
time.sleep(0.1)
print("Time:", time.time() - start)
