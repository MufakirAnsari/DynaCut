import os
import json
import matplotlib.pyplot as plt

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
DATA_FILE = os.path.join(RESULTS_DIR, 'phase15_cold_start.json')
PLOT_FILE = os.path.join(RESULTS_DIR, '..', 'vqe_cold_start.png')

def plot_cold_start():
    if not os.path.exists(DATA_FILE):
        print("Data file not found.")
        return
        
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        
    plt.figure(figsize=(8, 5))
    
    # Plot histories
    plt.plot(data['dynacut_history'], label='DynaCut (Noiseless TN Recon)', color='blue', linewidth=2)
    plt.plot(data['noisy_history'], label='Monolithic Noisy (FakeBrisbane)', color='red', alpha=0.7)
    
    plt.axhline(data['exact_ground_state'], color='black', linestyle='--', label='Exact Ground State')
    
    plt.title('Cold-Start SPSA Convergence Comparison (Random Init)')
    plt.xlabel('Evaluation Number')
    plt.ylabel('Energy')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(PLOT_FILE, dpi=300)
    print(f"Plot saved to {PLOT_FILE}")

if __name__ == "__main__":
    plot_cold_start()
