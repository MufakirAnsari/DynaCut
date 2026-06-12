import os
import sys
import logging
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_breakeven_analysis():
    sns.set_theme(style="whitegrid", palette="deep")
    
    # Parameters
    E_ideal = 1.0  # Normalized ideal expectation value
    D_uncut = 60   # Depth of uncut circuit
    D_cut = 30     # Depth of partitioned subcircuits
    
    # We will plot across different error rates per layer
    epsilons = np.logspace(-4, -1, 100)
    
    # Noise model: depolarization channel per layer
    # Expectation value decays as (1 - 2*epsilon)^Depth
    def exp_val(D, eps):
        return E_ideal * (1 - 2*eps)**D
        
    E_uncut_vals = exp_val(D_uncut, epsilons)
    E_cut_vals = exp_val(D_cut, epsilons)
    
    # The gain from shallower depth
    depth_gain = E_cut_vals - E_uncut_vals
    
    # The penalty from QPD cutting (sampling error)
    # Variance scales as gamma^2. For N samples, statistical error is gamma / sqrt(N)
    # Let's consider a few different cut counts (k=1, 2, 3) where gamma = 3^k
    N_shots = 1_000_000
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.plot(epsilons, depth_gain, 'k-', linewidth=3, label=r'Depth Gain (Signal Improvement)')
    
    colors = ['tab:blue', 'tab:orange', 'tab:green']
    for idx, k in enumerate([1, 2, 3]):
        gamma = 3**k
        sampling_penalty = gamma / np.sqrt(N_shots)
        ax.axhline(y=sampling_penalty, color=colors[idx], linestyle='--', linewidth=2, 
                   label=f'Sampling Penalty ($k={k}$ cuts)')
                   
        # Find crossover
        valid_indices = np.where(depth_gain > sampling_penalty)[0]
        if len(valid_indices) > 0:
            crossover_eps = epsilons[valid_indices[0]]
            ax.plot(crossover_eps, sampling_penalty, 'ro', markersize=8)
            ax.annotate(f'Breakeven\n{crossover_eps:.1e}', 
                        (crossover_eps, sampling_penalty),
                        textcoords="offset points", xytext=(10,-15), ha='left')
    
    ax.set_xscale('log')
    ax.set_xlabel('Hardware Error Rate Per Layer ($\epsilon$)')
    ax.set_ylabel('Expectation Value Difference ($\Delta E$)')
    ax.set_title('Entanglement Severing Penalty vs. Depth Reduction Gain')
    ax.legend()
    
    os.makedirs("paper/figures", exist_ok=True)
    plt.savefig("paper/figures/entanglement_vs_noise.pdf", dpi=300, bbox_inches="tight")
    logger.info("Saved entanglement vs noise plot to paper/figures/entanglement_vs_noise.pdf")

if __name__ == "__main__":
    run_breakeven_analysis()
