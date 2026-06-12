import json, numpy as np
with open('results/tn_pareto_real_raw.json', 'r') as f:
    raw_data = json.load(f)

fragment_sizes = [10, 7, 6, 5, 4]
ram_means = []
error_means = []
for frag_size in fragment_sizes:
    label = f"frag{frag_size}"
    rams = []
    errors = []
    for run in raw_data:
        if f"ram_mb_{label}" in run and f"error_{label}" in run:
            ram_val = run[f"ram_mb_{label}"]
            err_val = run[f"error_{label}"]
            if not (np.isnan(ram_val) or np.isnan(err_val)):
                rams.append(ram_val)
                errors.append(err_val)
    if len(rams) == 0:
        print(f"Skipping {label}")
        continue
    ram_means.append(np.mean(rams))
    error_means.append(np.mean(errors))
print("ram_means:", ram_means)
