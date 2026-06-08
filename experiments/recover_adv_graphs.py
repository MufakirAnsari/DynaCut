import os
import re
import json
from experiments.adversarial_graphs import generate_adversarial_graph
from dynacut.executor import maxcut_hamiltonian
from dynacut.ground_state import compute_exact_ground_state

log_path = "/home/ansari/.gemini/antigravity/brain/64780b99-605d-4b7f-b16f-b8c69dec5044/.system_generated/tasks/task-1022.log"

topologies = ["star", "complete", "ring", "bipartite", "regular_3"]
num_qubits = 14

with open(log_path, 'r') as f:
    lines = f.read().split('\n')

all_results = []
current_topo = None
current_seed = None
current_cuts = 0

for line in lines:
    if "Running Adversarial Graph:" in line:
        match = re.search(r"Running Adversarial Graph: (\w+) \(\d+ qubits\)", line)
        if match:
            current_topo = match.group(1)
            
    elif "[Seed " in line and "Running..." in line:
        match = re.search(r"\[Seed (\d+)\] Running", line)
        if match:
            current_seed = int(match.group(1))
            
    elif "Found strategy:" in line:
        match = re.search(r"(\d+) cuts", line)
        if match:
            current_cuts = int(match.group(1))
            
    elif "Reconstructed energy (IBM):" in line:
        match = re.search(r"Reconstructed energy \(IBM\): ([-.\d]+)", line)
        if match and current_topo and current_seed is not None:
            e_cut = float(match.group(1))
            
            # Recompute exact energy
            edges = generate_adversarial_graph(current_topo, num_qubits, current_seed)
            hamiltonian = maxcut_hamiltonian(edges, num_qubits)
            exact_energy = float(compute_exact_ground_state(hamiltonian))
            
            res = {
                "topology": current_topo,
                "num_qubits": num_qubits,
                "seed": current_seed,
                "exact_energy": exact_energy,
                "e_cut": e_cut,
                "error": abs(e_cut - exact_energy),
                "cuts": current_cuts,
                "cut_weight": float(current_cuts),
                "time_partition": 0.0,
                "time_eval": 0.0
            }
            all_results.append(res)

grouped = {}
for r in all_results:
    grouped.setdefault(r["topology"], []).append(r)

for topo, results in grouped.items():
    stats_path = f"results/adv_graph_{topo}_{num_qubits}q_stats.json"
    raw_path = f"results/adv_graph_{topo}_{num_qubits}q_raw.json"
    
    with open(raw_path, "w") as f:
        json.dump(results, f, indent=2)
        
    # We must also generate dummy stats.json so that experiment_runner skipping works.
    with open(stats_path, "w") as f:
        json.dump({"recovered": True}, f, indent=2)

with open("results/adversarial_graphs_combined_raw.json", "w") as f:
    json.dump(all_results, f, indent=2)

print(f"Successfully recovered {len(all_results)} results!")
