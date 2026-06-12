import json

with open("results/tn_scaling_combined_10_22.json", "r") as f:
    data = json.load(f)

with open("results/tn_scaling_real_24_raw.json", "r") as f:
    data["24"] = json.load(f)

with open("results/tn_scaling_combined.json", "w") as f:
    json.dump(data, f, indent=2)

print("Successfully combined 24-qubit data into tn_scaling_combined.json")
