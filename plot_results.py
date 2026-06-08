import json
import matplotlib.pyplot as plt
import os

def plot_scaling():
    if not os.path.exists('results/scaling_benchmark.json'):
        print("Data not found!")
        return

    with open('results/scaling_benchmark.json', 'r') as f:
        data = json.load(f)

    qubits = [d['qubits'] for d in data]
    exec_times = [d['execution_time'] for d in data]
    vram_bounds = [d['vram_bound_gb'] for d in data]
    cuts = [d['cuts'] for d in data]

    fig, ax1 = plt.subplots(figsize=(8, 5))

    color = 'tab:red'
    ax1.set_xlabel('Circuit Width (Qubits)', fontsize=12)
    ax1.set_ylabel('Execution Time (s)', color=color, fontsize=12)
    ax1.plot(qubits, exec_times, marker='o', color=color, linewidth=2, label='Execution Time')
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Peak VRAM Usage (GB)', color=color, fontsize=12)
    ax2.plot(qubits, vram_bounds, marker='s', linestyle='--', color=color, linewidth=2, label='VRAM Bound')
    ax2.axhline(y=4.0, color='gray', linestyle=':', label='Hardware Limit (4GB)')
    ax2.set_ylim(0, 5)
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title('DynaCut-V2: Hardware Scalability via Dynamic Fragmentation', fontsize=14)
    fig.tight_layout()

    os.makedirs('paper/figures', exist_ok=True)
    plt.savefig('paper/figures/scaling_plot.pdf')
    print("Plot saved to paper/figures/scaling_plot.pdf")

if __name__ == "__main__":
    plot_scaling()
