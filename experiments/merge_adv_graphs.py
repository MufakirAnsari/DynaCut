import json
import glob
import os

all_results = []
for f in glob.glob("results/adv_graph_*_raw.json"):
    with open(f, "r") as file:
        data = json.load(file)
        if isinstance(data, list):
            all_results.extend(data)

dedup_map = {}
for r in all_results:
    key = f'{r["topology"]}_{r["seed"]}'
    dedup_map[key] = r

final_results = list(dedup_map.values())

with open("results/adversarial_graphs_combined_raw.json", "w") as out:
    json.dump(final_results, out, indent=2)

print(f"Merged {len(final_results)} results into adversarial_graphs_combined_raw.json!")
