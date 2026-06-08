import json
import numpy as np
import pandas as pd
import os

def load_json(path):
    if not os.path.exists(path): return []
    with open(path, 'r') as f: return json.load(f)

def generate_tables():
    output = []
    output.append("# Final Paper Tables (PRX Quantum Format)\n")
    
    # 1. Baseline Comparison (Sprint 2)
    b_data = load_json("results/baseline_comparison.json")
    if b_data:
        df_b = pd.DataFrame(b_data)
        # We want to format numbers nicely
        # Group by method and qubits
        table_b = df_b.pivot(index='method', columns='qubits', values=['time', 'error', 'cuts'])
        output.append("## Table I: Baseline Comparison\n")
        output.append(table_b.to_markdown())
        output.append("\n\n")

    # 2. VRAM Measurement (Sprint 4.1)
    s_data = load_json("results/scaling_benchmark.json")
    if s_data:
        df_s = pd.DataFrame(s_data)
        output.append("## Table II: VRAM and Scalability\n")
        output.append(df_s.to_markdown(index=False))
        output.append("\n\n")
        
    # 3. Partitioner Ablation (Sprint 4.2)
    p_data = load_json("results/ablation_partitioner.json")
    if p_data:
        # p_data is list of dicts with nested dicts
        flat_p = []
        for d in p_data:
            flat_p.append({
                "Qubits": d["qubits"],
                "Random Cuts": d["random"]["mean_cuts"],
                "METIS Cuts": d["metis"]["mean_cuts"],
                "DynaCut-V2 Cuts": d["kl_bisection"]["mean_cuts"]
            })
        df_p = pd.DataFrame(flat_p)
        output.append("## Table III: Partitioner Ablation\n")
        output.append(df_p.to_markdown(index=False))
        output.append("\n\n")

    # 3.1 Fragment Size Ablation
    f_data = load_json("results/ablation_fragment_size.json")
    if f_data:
        df_f = pd.DataFrame(f_data)
        output.append("## Table III-b: Fragment Size Sweep\n")
        output.append(df_f.to_markdown(index=False))
        output.append("\n\n")

    # 3.2 Optimizer Ablation
    opt_data = load_json("results/ablation_optimizer.json")
    if opt_data:
        df_opt = pd.DataFrame(opt_data)
        output.append("## Table III-c: Optimizer Comparison\n")
        output.append(df_opt.to_markdown(index=False))
        output.append("\n\n")

    # 4. Cross Problem & Cross Ansatz & Topologies (Sprint 3)
    # Re-use what we did in analyze_sprint3
    prob_data = load_json("results/cross_problem_combined_raw.json")
    if prob_data:
        df_prob = pd.DataFrame(prob_data)
        prob_table = df_prob.groupby(['problem', 'num_qubits'])['error'].agg(['mean', 'std']).reset_index()
        output.append("## Table IV: Cross-Problem Generalization\n")
        output.append(prob_table.to_markdown(index=False))
        output.append("\n\n")

    adv_data = load_json("results/adversarial_graphs_combined_raw.json")
    if adv_data:
        df_adv = pd.DataFrame(adv_data)
        adv_table = df_adv.groupby(['topology'])['error'].agg(['mean', 'std']).reset_index()
        adv_cuts = df_adv.groupby(['topology'])['cuts'].mean().reset_index()
        adv_table = pd.merge(adv_table, adv_cuts, on='topology')
        output.append("## Table V: Adversarial Topologies\n")
        output.append(adv_table.to_markdown(index=False))
        output.append("\n\n")

    with open("results/paper_tables.md", "w") as f:
        f.write("\n".join(output))
        
    print("Paper tables generated at results/paper_tables.md")

if __name__ == "__main__":
    generate_tables()
