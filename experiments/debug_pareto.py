import json, os, numpy as np
filepath = "results/tn_pareto_real_raw.json"
with open(filepath, 'r') as f:
    raw_data = json.load(f)
fragment_sizes = [10, 7, 6, 5, 4]
ram_means = []
for frag_size in fragment_sizes:
    label = f"frag{frag_size}"
    rams = []
    for run in raw_data:
        ram_key = f"ram_mb_{label}"
        err_key = f"error_{label}"
        if ram_key in run and err_key in run:
            ram_val = run[ram_key]
            err_val = run[err_key]
            if not (np.isnan(ram_val) or np.isnan(err_val)):
                rams.append(ram_val)
    if rams:
        ram_means.append(np.mean(rams))
print(f"ram_means: {ram_means}")
