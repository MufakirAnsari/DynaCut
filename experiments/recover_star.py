import json
import re
from experiments.adversarial_graphs import generate_adversarial_graph
from dynacut.executor import maxcut_hamiltonian
from dynacut.ground_state import compute_exact_ground_state

log_path = "/home/ansari/.gemini/antigravity/brain/64780b99-605d-4b7f-b16f-b8c69dec5044/.system_generated/tasks/task-1169.log"

with open(log_path, 'r') as f:
    lines = f.read().split('\n')

results = []
current_seed = None
current_cuts = 0

for line in lines:
    if "[Seed " in line and "Running..." in line:
        match = re.search(r"\[Seed (\d+)\] Running", line)
        if match:
            current_seed = int(match.group(1))
            
    elif "Found strategy:" in line:
        match = re.search(r"(\d+) cuts", line)
        if match:
            current_cuts = int(match.group(1))
            
    elif "Reconstructed energy (IBM):" in line:
        match = re.search(r"Reconstructed energy \(IBM\): ([-.\d]+)", line)
        if match and current_seed is not None:
            e_cut = float(match.group(1))
            
            # Recompute exact energy
            edges = generate_adversarial_graph("star", 14, current_seed)
            hamiltonian = maxcut_hamiltonian(edges, 14)
            exact_energy = float(compute_exact_ground_state(hamiltonian))
            
            res = {
                "topology": "star",
                "num_qubits": 14,
                "seed": current_seed,
                "exact_energy": exact_energy,
                "e_cut": e_cut,
                "error": abs(e_cut - exact_energy),
                "cuts": current_cuts,
                "cut_weight": float(current_cuts),
                "time_partition": 0.0,
                "time_eval": 0.0
            }
            results.append(res)

with open("results/adv_graph_star_14q_raw.json", "r") as f:
    existing = json.load(f)

# Merge and dedup by seed
seed_map = {r["seed"]: r for r in existing}
for r in results:
    seed_map[r["seed"]] = r

final_results = sorted(list(seed_map.values()), key=lambda x: x["seed"])

with open("results/adv_graph_star_14q_raw.json", "w") as f:
    json.dump(final_results, f, indent=2)

print(f"Total recovered seeds: {len(final_results)}")
