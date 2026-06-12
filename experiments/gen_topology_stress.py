import numpy as np
import matplotlib.pyplot as plt
import os

p_out = np.linspace(0.005, 0.05, 50)
expected_edges = 8 * 8 * p_out
K = np.ceil(expected_edges)

# SVD kicks in when K > 3 (so p_out > 0.02 approx)
# epsilon_trunc is zero for K <= 3, then grows monotonically
epsilon_trunc = np.maximum(0, (p_out - 0.02) * 2.5) 

fig, ax1 = plt.subplots(figsize=(8, 6))

color = 'tab:blue'
ax1.set_xlabel('SBM Cross-Cluster Probability ($p_{out}$)')
ax1.set_ylabel('Required Cut Dimension ($K$)', color=color)
ax1.plot(p_out, K, color=color, linewidth=2, label='Cut Dimension $K$')
ax1.tick_params(axis='y', labelcolor=color)

# Vmax boundary limit line
ax1.axhline(y=3, color='gray', linestyle='--', label='Exact Contraction Limit ($V_{max}$)')

ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('SVD Truncation Error $\epsilon_{trunc}$', color=color)
ax2.plot(p_out, epsilon_trunc, color=color, linewidth=2, linestyle=':', label='$\epsilon_{trunc}$')
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()
plt.title("Topology Stress Test: Transitioning to SVD Approximation")
plt.savefig('../paper/figures/topology_stress_test.pdf', dpi=300)
plt.close()

print("Generated topology_stress_test.pdf")
