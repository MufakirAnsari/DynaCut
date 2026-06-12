import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams.update({'font.size': 14})

def plot_qpu_scaling():
    # Load data
    try:
        with open('experiments/qpu_scaling_results.json', 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # Filter for successes
    success_data = [d for d in data if d.get('status') == 'SUCCESS']
    
    if not success_data:
        print("No successful runs to plot.")
        return

    df = pd.DataFrame(success_data)
    
    # Sort by n_qubits
    df = df.sort_values(by='n_qubits')

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot Execution Time
    ax.plot(df['n_qubits'], df['elapsed_seconds'], marker='o', linewidth=2, markersize=8, 
            label='Physical Execution Time', color='blue')
    
    # Fill between to show the variance or flat trend
    mean_time = df['elapsed_seconds'].mean()
    ax.axhline(mean_time, color='blue', linestyle='--', alpha=0.5, label=f'Mean Time ({mean_time:.1f}s)')

    ax.set_xlabel('Number of Qubits', fontweight='bold')
    ax.set_ylabel('Execution Time (seconds)', fontweight='bold')
    ax.set_title('Flat Temporal Scaling on Real Hardware (ibm_marrakesh)', fontweight='bold', pad=20)
    
    ax.set_xticks(df['n_qubits'])
    ax.set_ylim(0, max(df['elapsed_seconds']) * 1.5)
    
    # Add text annotation for O(1) cuts
    ax.text(df['n_qubits'].max() * 0.6, mean_time * 1.2, 
            "O(1) Cross-Boundary Entanglement\nyields flat hardware execution time", 
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='blue'),
            fontsize=12)
            
    ax.legend(loc='upper left')
    plt.tight_layout()
    
    # Save
    out_path = 'paper/figures/qpu_scaling.pdf'
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {out_path}")

if __name__ == "__main__":
    plot_qpu_scaling()
