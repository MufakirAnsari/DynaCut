import json
import numpy as np
import pandas as pd
import glob
import os

def load_json(path):
    if not os.path.exists(path): return []
    with open(path, 'r') as f:
        data = json.load(f)
    return data if isinstance(data, list) else []

def analyze():
    # 1. Noise Impact
    noise_data = load_json("results/noise_impact_combined_raw.json")
    if noise_data:
        df_noise = pd.DataFrame(noise_data)
        noise_table = df_noise.groupby(['num_qubits', 'noise_rate'])[['error_cut', 'error_uncut']].agg(['mean', 'std']).reset_index()
    else:
        noise_table = pd.DataFrame()
        
    # 2. Shot Noise
    shot_data = load_json("results/shot_noise_combined_raw.json")
    if shot_data:
        df_shot = pd.DataFrame(shot_data)
        shot_table = df_shot.groupby(['num_qubits', 'num_samples'])['error_cut'].agg(['mean', 'std', 'count']).reset_index()
    else:
        shot_table = pd.DataFrame()
        
    # 3. Cross Problem
    prob_data = load_json("results/cross_problem_combined_raw.json")
    if prob_data:
        df_prob = pd.DataFrame(prob_data)
        prob_table = df_prob.groupby(['problem', 'num_qubits'])['error'].agg(['mean', 'std']).reset_index()
    else:
        prob_table = pd.DataFrame()
        
    # 4. Cross Ansatz
    ansatz_data = load_json("results/cross_ansatz_combined_raw.json")
    if ansatz_data:
        df_ansatz = pd.DataFrame(ansatz_data)
        ansatz_table = df_ansatz.groupby(['problem', 'ansatz_type'])['error'].agg(['mean', 'std']).reset_index()
    else:
        ansatz_table = pd.DataFrame()
        
    # 5. Adversarial Graphs
    adv_data = load_json("results/adversarial_graphs_combined_raw.json")
    if adv_data:
        df_adv = pd.DataFrame(adv_data)
        adv_table = df_adv.groupby(['topology'])['error'].agg(['mean', 'std', 'count']).reset_index()
        adv_cuts = df_adv.groupby(['topology'])['cuts'].mean().reset_index()
        adv_table = pd.merge(adv_table, adv_cuts, on='topology')
    else:
        adv_table = pd.DataFrame()

    with open("results/sprint3_summary.md", "w") as f:
        f.write("# Sprint 3 Final Analysis\n\n")
        
        f.write("## 1. Noise Impact (Depolarizing)\n")
        if not noise_table.empty:
            f.write(noise_table.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## 2. Shot Noise (Sampling Variance)\n")
        if not shot_table.empty:
            f.write(shot_table.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## 3. Cross-Problem Generalization\n")
        if not prob_table.empty:
            f.write(prob_table.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## 4. Cross-Ansatz Generalization\n")
        if not ansatz_table.empty:
            f.write(ansatz_table.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## 5. Adversarial Graph Topologies\n")
        if not adv_table.empty:
            f.write(adv_table.to_markdown(index=False))
        f.write("\n\n")

if __name__ == "__main__":
    analyze()
