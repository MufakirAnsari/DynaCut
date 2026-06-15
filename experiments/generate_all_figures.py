import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from adjustText import adjust_text

# Configure Seaborn for HD quality
sns.set_theme(style="whitegrid", palette="husl", context="paper", font_scale=1.5)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "..", "paper", "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

def plot_cut_vs_uncut_error():
    print("Generating Plot 2: Cut vs Uncut Error (Empirical)")
    filepath = os.path.join(RESULTS_DIR, "cut_vs_uncut_error.json")
    if not os.path.exists(filepath):
        print("  WARNING: cut_vs_uncut_error.json not found, skipping.")
        return
        
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    qubits = [d["num_qubits"] for d in data]
    monolithic_error = [d["monolithic_error"] for d in data]
    dynacut_mean = [d["dynacut_error_mean"] for d in data]
    dynacut_std = [d.get("dynacut_error_std", 0) for d in data]
    
    plt.figure(figsize=(8, 6))
    plt.plot(qubits, monolithic_error, marker='s', linewidth=2, markersize=8, color='red', label='Monolithic (Noisy)')
    plt.errorbar(qubits, dynacut_mean, yerr=dynacut_std, fmt='o-', linewidth=2, markersize=8, color='blue', label='DynaCut (QPD)', capsize=5)
    plt.yscale("log")
    plt.xlabel("Number of Qubits")
    plt.ylabel("Terminal Energy Error |E_obs - E_exact|")
    plt.title("Error Scaling: DynaCut vs Monolithic Noisy Execution")
    plt.xticks(qubits)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "cut_vs_uncut_error.pdf"), dpi=300)
    plt.close()

def plot_topology_stress_test():
    print("Generating Plot 14: Topology Stress Test (Empirical)")
    filepath = os.path.join(RESULTS_DIR, "topology_stress_test.json")
    if not os.path.exists(filepath):
        print("  WARNING: topology_stress_test.json not found, skipping.")
        return
        
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    p_out = [d["p_out"] for d in data]
    K = [d["K"] for d in data]
    required_shots = [d["required_shots"] for d in data]

    fig, ax1 = plt.subplots(figsize=(8, 6))

    color = 'tab:blue'
    ax1.set_xlabel('SBM Cross-Cluster Probability ($p_{out}$)')
    ax1.set_ylabel('Number of Cut Edges ($K$)', color=color)
    ax1.plot(p_out, K, color=color, linewidth=2, marker='o', markersize=4, label='Cut Edges $K$')
    ax1.tick_params(axis='y', labelcolor=color)

    # Practical limit line (K=3 is the threshold for feasible QPD)
    ax1.axhline(y=3, color='gray', linestyle='--', alpha=0.7, label='Feasible Limit ($K \\leq 3$)')

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel(r'Required QPD Shots ($\Gamma^2 / \epsilon^2$)', color=color)
    ax2.plot(p_out, required_shots, color=color, linewidth=2, linestyle=':', label='Required Shots')
    ax2.set_yscale('log')
    ax2.tick_params(axis='y', labelcolor=color)

    # Add feasibility threshold
    ax2.axhline(y=1e6, color='red', linestyle='--', alpha=0.4, label='Shot Budget Limit ($10^6$)')

    fig.tight_layout()
    plt.title("Topology Stress Test: QPD Overhead vs Graph Density")
    plt.savefig(os.path.join(FIGURES_DIR, "topology_stress_test.pdf"), dpi=300)
    plt.close()

def plot_real_vram_scaling():
    print("Generating Plot 3: Real VRAM Scaling (Empirical)")
    filepath = os.path.join(RESULTS_DIR, "scaling_benchmarks.json")
    if not os.path.exists(filepath):
        print("  WARNING: scaling_benchmarks.json not found, skipping.")
        return
        
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Filter None/NaN values for each series independently
    all_qubits = [d["num_qubits"] for d in data]
    
    q_ibm = [d["num_qubits"] for d in data if d["vram_ibm"] is not None]
    v_ibm = [d["vram_ibm"] for d in data if d["vram_ibm"] is not None]
    v_ibm_std = [d.get("vram_ibm_std", 0) for d in data if d["vram_ibm"] is not None]
    
    q_tn = [d["num_qubits"] for d in data if d["vram_tn"] is not None]
    v_tn = [d["vram_tn"] for d in data if d["vram_tn"] is not None]
    v_tn_std = [d.get("vram_tn_std", 0) for d in data if d["vram_tn"] is not None]
    
    plt.figure(figsize=(8, 6))
    
    # Plot IBM Statevector
    plt.plot(q_ibm, v_ibm, marker='s', label='Statevector (Full)', linewidth=2, color='red')
    # Use np.array to compute fill_between bounds safely
    v_ibm_np = np.array(v_ibm)
    v_ibm_std_np = np.array(v_ibm_std)
    plt.fill_between(q_ibm, np.maximum(v_ibm_np - 2*v_ibm_std_np, 1e-3), v_ibm_np + 2*v_ibm_std_np, color='red', alpha=0.2)
    
    # Plot DynaCut
    plt.plot(q_tn, v_tn, marker='o', label='DynaCut (TN Partition)', linewidth=2, color='blue')
    v_tn_np = np.array(v_tn)
    v_tn_std_np = np.array(v_tn_std)
    plt.fill_between(q_tn, np.maximum(v_tn_np - 2*v_tn_std_np, 1e-3), v_tn_np + 2*v_tn_std_np, color='blue', alpha=0.2)
    
    # Mark OOM points
    oom_qubits = [d["num_qubits"] for d in data if d["vram_ibm"] is None]
    if oom_qubits:
        plt.scatter(oom_qubits, [max(v_ibm) * 4] * len(oom_qubits), marker='x', s=100, color='red', zorder=5, label='Statevector OOM')
    
    plt.yscale("log")
    plt.xlabel("Number of Qubits")
    plt.ylabel("Peak RAM (MB)")
    plt.title("Memory Scaling Benchmark (95% CI)")
    plt.legend()
    plt.xticks(all_qubits)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "vram_scaling.png"), dpi=300)
    plt.close()

def plot_tn_vs_ibm_scaling():
    print("Generating Plot 4: TN vs IBM Scaling (Empirical)")
    filepath = os.path.join(RESULTS_DIR, "scaling_benchmarks.json")
    if not os.path.exists(filepath):
        print("  WARNING: scaling_benchmarks.json not found, skipping.")
        return
        
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    all_qubits = [d["num_qubits"] for d in data]
    
    q_ibm = [d["num_qubits"] for d in data if d["time_ibm"] is not None]
    t_ibm = [d["time_ibm"] for d in data if d["time_ibm"] is not None]
    
    q_tn = [d["num_qubits"] for d in data if d["time_tn"] is not None]
    t_tn = [d["time_tn"] for d in data if d["time_tn"] is not None]
    
    plt.figure(figsize=(8, 6))
    plt.plot(q_ibm, t_ibm, marker='o', linestyle='--', label=r'Statevector Reconstruct', linewidth=2, color='red')
    plt.plot(q_tn, t_tn, marker='s', label=r'TN Contraction (DynaCut)', linewidth=2, color='blue')
    plt.yscale("log")
    plt.xlabel("Number of Qubits")
    plt.ylabel("Reconstruction Time (s)")
    plt.title("Tensor Network vs Standard Reconstruction")
    plt.legend()
    plt.xticks(all_qubits)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "tn_vs_ibm_scaling.pdf"), dpi=300)
    plt.close()

def plot_pareto_frontier():
    print("Generating Plot 5: Pareto Frontier")
    filepath = os.path.join(RESULTS_DIR, "tn_pareto_real_raw.json")
    if not os.path.exists(filepath):
        print("  WARNING: tn_pareto_real_raw.json not found, skipping.")
        return

    with open(filepath, 'r') as f:
        raw_data = json.load(f)

    # Use the expanded, robust fragment size sweep we evaluated
    fragment_sizes = [20, 16, 14, 12, 10, 9, 8, 7, 6]
    
    points = []  # (ram_median, err_median, ram_q1, ram_q3, err_q1, err_q3, label, is_exact, frag_size)

    for frag_size in fragment_sizes:
        label = f"frag{frag_size}"
        rams = []
        errors = []
        cuts_list = []
        for run in raw_data:
            ram_key = f"ram_mb_{label}"
            err_key = f"error_{label}"
            cut_key = f"num_cuts_{label}"
            if ram_key in run and err_key in run:
                ram_val = run[ram_key]
                err_val = run[err_key]
                if not (np.isnan(ram_val) or np.isnan(err_val)):
                    rams.append(ram_val)
                    errors.append(err_val)
            if cut_key in run:
                cuts_list.append(int(run[cut_key]))

        if len(rams) == 0:
            print(f"  Skipping {label}: no valid data")
            continue
            
        rams_arr = np.array(rams)
        errs_arr = np.array(errors)
        
        r_med = np.median(rams_arr)
        is_exact = (frag_size == 20)
        # Floor the exact (no-cut) error at 1e-5 so it shows on log scale
        e_med = max(np.median(errs_arr), 1e-5) if is_exact else np.median(errs_arr)
        
        # IQR-based error bars (robust to outliers)
        r_q1, r_q3 = np.percentile(rams_arr, [25, 75])
        e_q1, e_q3 = np.percentile(errs_arr, [25, 75])
        # Floor lower error bound for log scale
        e_q1 = max(e_q1, 1e-5)
        
        K_mode = int(np.median(cuts_list)) if cuts_list else 0
        n = len(rams)
        lbl = f"No Cut ($K$=0, n={n})" if is_exact else f"$N_f$={frag_size} ($K$={K_mode}, n={n})"
        
        points.append((r_med, e_med, r_q1, r_q3, e_q1, e_q3, lbl, is_exact, frag_size))
        print(f"  {label}: n={n}, RAM_median={r_med:.4f} MB, Err_median={e_med:.4f}, K={K_mode}")

    if not points:
        print("  WARNING: No valid data points for Pareto plot.")
        return

    # Find truly Pareto-optimal points (neither RAM nor error is dominated)
    pareto_mask = []
    for i in range(len(points)):
        r1, e1 = points[i][0], points[i][1]
        is_optimal = True
        for j in range(len(points)):
            if i == j:
                continue
            r2, e2 = points[j][0], points[j][1]
            # j dominates i if j is <= on both axes and strictly < on at least one
            if r2 <= r1 and e2 <= e1 and (r2 < r1 or e2 < e1):
                is_optimal = False
                break
        pareto_mask.append(is_optimal)

    fig, ax = plt.subplots(figsize=(10.5, 7))

    # Draw asymmetric IQR error bars (all deltas clamped to >= 0)
    r_meds = [p[0] for p in points]
    e_meds = [p[1] for p in points]
    r_lo = [max(p[0] - p[2], 0) for p in points]   # med - q1
    r_hi = [max(p[3] - p[0], 0) for p in points]   # q3 - med
    e_lo = [max(p[1] - p[4], 0) for p in points]   # med - q1, floored
    e_hi = [max(p[5] - p[1], 0) for p in points]   # q3 - med
    
    ax.errorbar(r_meds, e_meds, xerr=[r_lo, r_hi], yerr=[e_lo, e_hi],
                fmt='none', ecolor='#b0b5b9', elinewidth=1.2, capsize=3, zorder=1, alpha=0.7)

    texts = []
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(points)))
    
    pareto_pts = []
    
    for i, pt in enumerate(points):
        r, e, _, _, _, _, lbl, is_exact, frag_size = pt
        is_pareto = pareto_mask[i]
        color = colors[i]
        
        if is_pareto:
            pareto_pts.append((r, e))
            ax.scatter(r, e, s=250, marker='o', color=color, zorder=3, edgecolors='white', linewidth=1.5)
            ax.scatter(r, e, s=400, marker='o', color=color, zorder=2, alpha=0.2)
        else:
            ax.scatter(r, e, s=100, marker='o', color=color, zorder=2, edgecolors='white', linewidth=1.0, alpha=0.5)
            
        font_wt = 'bold' if is_pareto else 'normal'
        alpha_txt = 1.0 if is_pareto else 0.7
        t = ax.text(r, e, lbl, fontsize=10, fontweight=font_wt, alpha=alpha_txt, zorder=4)
        texts.append(t)

    # Sort pareto points by RAM to draw the front line
    pareto_pts.sort(key=lambda x: x[0])
    if len(pareto_pts) > 1:
        pr, pe = zip(*pareto_pts)
        ax.plot(pr, pe, linestyle='-', color='#2c3e50', alpha=0.8, linewidth=2.5, label='Pareto Front', zorder=1)
        ax.fill_between(pr, pe, max(e_meds)*10, color='#3498db', alpha=0.08, zorder=0)

    legend = ax.legend(loc='upper right', fontsize=12, frameon=True, fancybox=True, shadow=True, borderpad=1)
    legend.get_frame().set_facecolor('#ffffff')
    legend.get_frame().set_alpha(0.9)

    ax.set_xlabel("Peak Classical RAM (MB)", fontsize=14, fontweight='bold', labelpad=10, color='#2c3e50')
    ax.set_ylabel(r"Reconstruction Error $|\Delta E|$ (median)", fontsize=14, fontweight='bold', labelpad=10, color='#2c3e50')
    ax.set_xscale("log")
    ax.set_yscale("log")
    
    ax.set_ylim(bottom=1e-6, top=max(e_meds)*10)
    
    ax.set_title("DynaCut Trade-Off: QPD Variance vs. RAM Ceiling", fontsize=16, fontweight='bold', color='#1a252f', pad=15)
    
    ax.grid(True, which="major", ls="-", color="#e8ecef", alpha=0.8)
    ax.grid(True, which="minor", ls="--", color="#e8ecef", alpha=0.4)
    
    for spine in ax.spines.values():
        spine.set_edgecolor('#d5dbdb')
        spine.set_linewidth(1.5)
    
    adjust_text(texts, arrowprops=dict(arrowstyle="-|>", color='#7f8c8d', lw=1.2, alpha=0.8),
                expand_points=(1.5, 1.5))

    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "pareto_frontier.pdf"), dpi=300, bbox_inches='tight')
    plt.close()

def plot_vqe_convergence():
    print("Generating Plot 6: VQE Convergence")
    filepath = os.path.join(RESULTS_DIR, "vqe_convergence_multi_raw.json")
    if not os.path.exists(filepath):
        print("  WARNING: vqe_convergence_multi_raw.json not found, skipping.")
        return
        
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    runs = data
    num_runs = len(runs)
    print(f"  Found {num_runs} seeds")
    
    # Compute the energy gap |E(iter) - E_exact| for each seed
    # This normalizes across seeds that have different ground states
    gap_histories = []
    for run in runs:
        history = np.array(run["history"])
        gs = run["exact_ground_state"]
        gap = np.abs(history - gs)
        gap_histories.append(gap)
        print(f"    Seed {run.get('seed','?')}: len={len(history)}, gs={gs:.2f}, "
              f"initial_gap={gap[0]:.4f}, final_gap={gap[-1]:.4f}")
    
    fig, ax = plt.subplots(figsize=(10, 6.5))
    
    # Plot individual seed traces as thin transparent lines
    for i, gap in enumerate(gap_histories):
        iters = range(len(gap))
        ax.plot(iters, gap, linewidth=0.8, alpha=0.3, color='steelblue', zorder=1)
    
    # Compute mean and 95% CI ONLY over the common iteration range (no padding)
    min_len = min(len(g) for g in gap_histories)
    common_gaps = np.array([g[:min_len] for g in gap_histories])
    
    from scipy.stats import t
    mean_gap = np.mean(common_gaps, axis=0)
    std_gap = np.std(common_gaps, axis=0, ddof=1)
    t_stat = t.ppf(0.975, num_runs - 1) if num_runs > 1 else 1.96
    margin = t_stat * (std_gap / np.sqrt(num_runs))
    
    common_iters = range(min_len)
    ax.plot(common_iters, mean_gap, linewidth=2.5, color='#1a5276', 
            label=f'Mean gap (n={num_runs} seeds)', zorder=3)
    
    # Floor the lower CI bound at a small positive value for log scale
    lower_ci = np.maximum(mean_gap - margin, 1e-4)
    upper_ci = mean_gap + margin
    ax.fill_between(common_iters, lower_ci, upper_ci, 
                    color='steelblue', alpha=0.25, label='95% CI', zorder=2)
    
    # Mark the common range boundary if some seeds ran longer
    max_len = max(len(g) for g in gap_histories)
    if max_len > min_len:
        ax.axvline(min_len - 1, color='gray', linestyle=':', alpha=0.5, 
                   label=f'Common range ({min_len} iters)')
    
    ax.set_yscale('log')
    ax.set_xlabel("VQE Iteration", fontsize=13, fontweight='bold')
    ax.set_ylabel(r"Energy Gap $|E_{VQE} - E_{exact}|$", fontsize=13, fontweight='bold')
    ax.set_title(f"VQE Convergence Gap (N=20, {num_runs} seeds)", fontsize=15, fontweight='bold', pad=12)
    ax.legend(fontsize=11, loc='upper right', frameon=True, fancybox=True, shadow=True)
    
    ax.grid(True, which="major", ls="-", color="#e8ecef", alpha=0.8)
    ax.grid(True, which="minor", ls="--", color="#e8ecef", alpha=0.4)
    for spine in ax.spines.values():
        spine.set_edgecolor('#d5dbdb')
        spine.set_linewidth(1.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "vqe_convergence.pdf"), dpi=300)
    plt.close()

def plot_baseline_comparison():
    print("Generating Plot 7: Baseline Comparison")
    filepath = os.path.join(RESULTS_DIR, "baseline_comparison.json")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Filter for 14 qubits
        data_14 = [d for d in data if d["qubits"] == 14 and not np.isnan(d.get("energy", np.nan))]
        methods = [d["method"] for d in data_14]
        times = [d["time"] for d in data_14]
        
        # Use the actual empirical data from the JSON file
        clean_methods = []
        clean_times = []
        for m, t in zip(methods, times):
            if "METIS" in m or "Random" in m: continue # Skip suboptimal partitioners
            # Keep Statevector, Raw Cutting, MPS, CutQC, DynaCut
            clean_methods.append(m)
            clean_times.append(t)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x=clean_methods, y=clean_times)
        plt.yscale("log")
        plt.xlabel("Method")
        plt.ylabel("Execution Time (s)")
        plt.title("Baseline Comparison (14 Qubits)")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_DIR, "baseline_comparison.pdf"), dpi=300)
        plt.close()

def plot_partitioner_ablation():
    print("Generating Plot 8: Partitioner Ablation (Empirical)")
    filepath = os.path.join(RESULTS_DIR, "partitioner_ablation.json")
    if not os.path.exists(filepath):
        print("  WARNING: partitioner_ablation.json not found, skipping.")
        return
        
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    qubits = [d["num_qubits"] for d in data]
    time_random = [d["time_random"] for d in data]
    time_kl = [d["time_kl"] for d in data]
    time_spectral = [d.get("time_spectral", float('nan')) for d in data]
    # Use the DynaCut partitioner field (new schema)
    time_dynacut = [d.get("time_dynacut_partitioner", d.get("time_kahypar", 0)) for d in data]

    plt.figure(figsize=(8, 6))
    plt.plot(qubits, time_spectral, marker='s', label='Spectral Bisection', linewidth=2, color='orange')
    plt.plot(qubits, time_dynacut, marker='D', label='DynaCut (Weighted KL)', linewidth=2)
    plt.plot(qubits, time_kl, marker='o', label='KL (Kernighan-Lin)', linewidth=2)
    plt.plot(qubits, time_random, marker='^', label='Random Bisection', linewidth=2)
    
    plt.yscale("log")
    plt.xlabel("Number of Qubits")
    plt.ylabel("Partitioning Time (s)")
    plt.title("Partitioner Strategy Ablation")
    plt.legend()
    plt.xticks(qubits)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "partitioner_ablation.png"), dpi=300)
    plt.close()

def plot_noise_impact():
    print("Generating Plot 9: Noise Impact")
    probs = [0.0, 0.0001, 0.001, 0.01, 0.05, 0.1]
    errors = []
    errors_ci = []
    
    for p in probs:
        filepath = os.path.join(RESULTS_DIR, f"noise_impact_10q_p{p}_stats.json")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            if "error_cut" in data:
                errors.append(data["error_cut"]["mean"])
                errors_ci.append(data["error_cut"]["ci_95"])
        else:
            errors.append(np.nan)
            errors_ci.append(np.nan)
            
    if all(np.isnan(v) for v in errors):
        return
        
    plt.figure(figsize=(8, 6))
    plt.errorbar(probs, errors, yerr=errors_ci, fmt='o-', linewidth=2, capsize=5)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Depolarizing Noise Probability")
    plt.ylabel("Energy Error |E_noisy - E_exact|")
    plt.title("Noise Impact on Expectation Values")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "noise_impact.pdf"), dpi=300)
    plt.close()

def plot_cross_problem():
    print("Generating Plot 10: Cross-Problem")
    filepath = os.path.join(RESULTS_DIR, "cross_problem_combined_raw.json")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        problems = []
        energies = []
        for run in data:
            problem = f"{run['problem']} ({run['num_qubits']}q)".replace("Erdős-Rényi", "SBM")
            if "e_cut" in run:
                problems.append(problem)
                energies.append(run["e_cut"])
                
        if len(problems) > 0:
            plt.figure(figsize=(10, 6))
            sns.boxplot(x=problems, y=energies)
            plt.xlabel("Problem Type")
            plt.ylabel("Measured Energy")
            plt.title("Cross-Problem Generalization")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(os.path.join(FIGURES_DIR, "cross_problem.pdf"), dpi=300)
            plt.close()

def plot_mps_baseline():
    print("Generating Plot: Classical MPS Baseline vs DynaCut Scaling")
    filepath = os.path.join(RESULTS_DIR, "mps_baseline.json")
    if not os.path.exists(filepath):
        print("  WARNING: mps_baseline.json not found, skipping.")
        return
        
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    # Plot 1: 1D Chain Time scaling
    tfim = data.get("1d_tfim", {})
    if tfim:
        qubits = sorted([int(k) for k in tfim.keys()])
        times = [tfim[str(q)]["dmrg_time"] for q in qubits]
        dyna_times = [tfim[str(q)]["dynacut_time"] for q in qubits]
        
        plt.figure(figsize=(8, 6))
        plt.plot(qubits, times, marker='o', linewidth=2, color='green', label='Classical DMRG Time (1D)')
        plt.plot(qubits, dyna_times, marker='s', linewidth=2, color='blue', label='DynaCut Time (1D)')
        plt.xlabel("Number of Qubits")
        plt.ylabel("Execution Time (seconds)")
        plt.title("Pure Classical TN Baseline (1D TFIM)")
        plt.yscale('log')
        plt.xticks(qubits)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_DIR, "mps_baseline_time_1d.pdf"), dpi=300)
        plt.close()
        
    # Plot 2: SBM Memory scaling
    sbm = data.get("sbm_tn_memory", {})
    if sbm:
        sorted_keys = sorted(sbm.keys(), key=float)
        p_outs = [float(k) for k in sorted_keys]
        mem_mb = [sbm[k]["memory_mb"] for k in sorted_keys]
        dyna_mem = [sbm[k]["dynacut_memory_mb"] for k in sorted_keys]
        
        plt.figure(figsize=(8, 6))
        plt.plot(p_outs, mem_mb, marker='s', linewidth=2, color='red', label='Exact Classical TN')
        plt.plot(p_outs, dyna_mem, marker='o', color='blue', linestyle='--', linewidth=2, label='DynaCut (Partitioned)')
        plt.xlabel("SBM Density ($p_{out}$)")
        plt.ylabel("Required Memory (MB)")
        plt.yscale('log')
        plt.title("Memory Explosion on Dense Graphs (N=20)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_DIR, "mps_baseline_memory_sbm.pdf"), dpi=300)
        plt.close()

def plot_hpc_scaling():
    """Plot HPC-regime memory scaling: Classical Statevector vs DynaCut."""
    print("Generating Plot: HPC Regime Scaling")
    filepath = os.path.join(RESULTS_DIR, "hpc_scaling.json")
    if not os.path.exists(filepath):
        print("  WARNING: hpc_scaling.json not found, skipping.")
        return

    with open(filepath, 'r') as f:
        data = json.load(f)

    ns = sorted([int(k) for k in data.keys()])

    # Classical statevector: use log2(GB) for clean plotting across huge range
    classical_log2_gb = [data[str(n)]["classical_log2_memory_gb"] for n in ns]

    # DynaCut: fragment statevector memory (the actual per-fragment cost)
    dynacut_frag_mb = [data[str(n)]["dynacut_fragment_sv_mb"] for n in ns]
    dynacut_frag_log2_gb = [np.log2(m / 1024) if m > 0 else -30 for m in dynacut_frag_mb]

    cuts = [data[str(n)]["dynacut_cuts"] for n in ns]
    max_frags = [data[str(n)]["dynacut_max_fragment_qubits"] for n in ns]

    # ===== Plot 1: Memory scaling (log2 GB) =====
    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(ns, classical_log2_gb, 'o-', color='#e74c3c', linewidth=2.5,
             markersize=6, label=r'Classical Statevector ($2^N \times 16$ bytes)')
    ax1.plot(ns, dynacut_frag_log2_gb, 's--', color='#2980b9', linewidth=2.5,
             markersize=6, label=r'DynaCut Fragment ($2^{N/P} \times 16$ bytes)')

    # HPC RAM limits as log2(GB)
    ax1.axhline(y=np.log2(32), color='#8e44ad', linestyle=':', linewidth=2,
                label='HPC Workstation (32 GB)', alpha=0.8)
    ax1.axhline(y=np.log2(256), color='#e67e22', linestyle=':', linewidth=2,
                label='HPC Node (256 GB)', alpha=0.8)

    ax1.set_xlabel("Number of Qubits ($N$)", fontsize=13)
    ax1.set_ylabel(r"Memory ($\log_2$ GB)", fontsize=13)
    ax1.set_title("Classical Memory Wall: Statevector vs DynaCut Fragment Size",
                   fontsize=14, fontweight='bold')

    # Add right-side labels for absolute memory at key ticks
    ax1_r = ax1.twinx()
    ax1_r.set_ylim(ax1.get_ylim())
    tick_vals = [-10, 0, 5, 10, 20, 30, 40]
    tick_labels = ['1 MB', '1 GB', '32 GB', '1 TB', '1 PB', '1 EB', '1 ZB']
    ax1_r.set_yticks(tick_vals)
    ax1_r.set_yticklabels(tick_labels, fontsize=9)
    ax1_r.set_ylabel("Absolute Memory", fontsize=11)

    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "hpc_scaling.pdf"), dpi=300)
    plt.close(fig)

    # ===== Plot 2: Cuts and fragment size vs N =====
    fig2, ax = plt.subplots(figsize=(10, 5))

    color_k = '#e74c3c'
    color_f = '#2980b9'

    ax.plot(ns, cuts, 'o-', color=color_k, linewidth=2.5, markersize=6,
            label='Wire Cuts ($K$)')
    ax.set_xlabel("Number of Qubits ($N$)", fontsize=13)
    ax.set_ylabel("Number of Wire Cuts ($K$)", fontsize=13, color=color_k)
    ax.tick_params(axis='y', labelcolor=color_k)

    ax2 = ax.twinx()
    ax2.plot(ns, max_frags, 's--', color=color_f, linewidth=2.5, markersize=6,
             label='Max Fragment Size (qubits)')
    ax2.set_ylabel("Max Fragment Size (qubits)", fontsize=13, color=color_f)
    ax2.tick_params(axis='y', labelcolor=color_f)

    ax.set_title("DynaCut Partitioning Profile on Dense SBM ($p_{out}=0.10$)",
                  fontsize=13, fontweight='bold')

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='center left', fontsize=10)

    ax.grid(True, alpha=0.3)
    fig2.tight_layout()
    fig2.savefig(os.path.join(FIGURES_DIR, "hpc_cuts_profile.pdf"), dpi=300)
    plt.close(fig2)

    print(f"  Saved hpc_scaling.pdf and hpc_cuts_profile.pdf")



def plot_chemistry_pes():
    """Generates the Chemistry PES plot."""
    data_path = os.path.join(RESULTS_DIR, "chemistry_pes.json")
    if not os.path.exists(data_path):
        print("Missing chemistry_pes.json, skipping chemistry PES plot.")
        return
        
    with open(data_path, "r") as f:
        data = json.load(f)
        
    distances = data.get("distances", [])
    energies_exact = data.get("exact_energies", [])
    energies_vqe = data.get("dynacut_energies", [])
    
    if not distances:
        return
        
    plt.figure(figsize=(8, 6))
    plt.plot(distances, energies_exact, 'k--', linewidth=2, label="Exact Eigensolver")
    plt.plot(distances, energies_vqe, 'ro', markersize=8, label="DynaCut UCCSD (K=1)")
    
    plt.xlabel(r"Interatomic Distance $R$ ($\AA$)")
    plt.ylabel("Ground State Energy (Hartree)")
    plt.title(r"$H_2$ Potential Energy Surface via DynaCut Tensor Network")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(os.path.join(FIGURES_DIR, "chemistry_pes.pdf"), dpi=300)
    plt.close()

def plot_svd_ablation():
    """Generates the SVD Ablation plot."""
    data_path = os.path.join(RESULTS_DIR, "svd_ablation.json")
    if not os.path.exists(data_path):
        print("Missing svd_ablation.json, skipping SVD ablation plot.")
        return
        
    with open(data_path, "r") as f:
        data = json.load(f)
        
    chis = []
    errors = []
    times = []
    memories = []
    exact_e = None
    exact_t = None
    exact_m = None
    
    for chi_str, res in data.items():
        if chi_str == "exact_sv":
            exact_e = res["energy"]
            exact_t = res["time_seconds"]
            exact_m = res.get("peak_memory_mb", 0)
        else:
            chis.append(int(chi_str))
            
    # Sort by chi
    chis.sort()
    for chi in chis:
        res = data[str(chi)]
        errors.append(res["error"])
        times.append(res["time_seconds"])
        memories.append(res.get("peak_memory_mb", 0))
            
    if not chis:
        return
        
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    color = 'tab:red'
    ax1.set_xlabel('MPS Max Bond Dimension ($\chi$)')
    ax1.set_ylabel('Absolute Energy Error (Hartree)', color=color)
    ax1.plot(chis, errors, marker='o', color=color, linewidth=2, label='Truncation Error')
    ax1.set_yscale('log')
    ax1.set_xscale('log', base=2)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)
    
    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Wall-clock Time (s)', color=color)
    ax2.plot(chis, times, marker='s', color=color, linewidth=2, linestyle=':', label='Time')
    if exact_t is not None:
        ax2.axhline(y=exact_t, color='tab:blue', linestyle='--', alpha=0.5, label='Exact Statevector Time')
    ax2.set_yscale('log')
    ax2.tick_params(axis='y', labelcolor=color)
    
    # Optional: third axis for memory
    # ax3 = ax1.twinx()
    # ax3.spines['right'].set_position(('outward', 60))
    # color = 'tab:green'
    # ax3.set_ylabel('Peak Memory (MB)', color=color)
    # ax3.plot(chis, memories, marker='^', color=color, linewidth=2, linestyle='-.', label='Memory')
    # ax3.tick_params(axis='y', labelcolor=color)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)
    
    fig.tight_layout()
    plt.title("Tensor Network Pareto Frontier: Precision vs. Time (N=26 Dense SBM)")
    plt.savefig(os.path.join(FIGURES_DIR, "svd_ablation.pdf"), dpi=300)
    plt.close()

def plot_optimizer_comparison():
    data_path = os.path.join(RESULTS_DIR, "optimizer_comparison.json")
    if not os.path.exists(data_path):
        return
    with open(data_path, 'r') as f:
        data = json.load(f)
    print("Generating Plot: Optimizer Comparison")
    
    exact_e = data.get("exact_energy", 0.0)
    optimizers = data.get("optimizers", {})
    
    plt.figure(figsize=(10, 6))
    
    colors = {"COBYLA": "#e74c3c", "Nelder-Mead": "#f39c12", "SPSA": "#2ecc71"}
    
    for opt, runs in optimizers.items():
        if not runs: continue
        
        # Determine the maximum iteration length across all seeds
        max_len = max(len(run.get("convergence", [])) for run in runs)
        
        # Pad shorter runs with their final value so we can compute mean/std across seeds
        padded_runs = []
        for run in runs:
            conv = run.get("convergence", [])
            if not conv: continue
            padded = list(conv) + [conv[-1]] * (max_len - len(conv))
            padded_runs.append(padded)
            
        if not padded_runs: continue
            
        arr = np.array(padded_runs)
        mean_conv = np.mean(arr, axis=0)
        std_conv = np.std(arr, axis=0)
        
        iterations = np.arange(1, max_len + 1)
        color = colors.get(opt, "blue")
        
        plt.plot(iterations, mean_conv, linewidth=2.5, color=color, 
                 label=f"{opt} (Final: {mean_conv[-1]:.2f} ± {std_conv[-1]:.2f})")
        plt.fill_between(iterations, mean_conv - std_conv, mean_conv + std_conv, 
                         color=color, alpha=0.2)
        
    plt.axhline(y=exact_e, color='black', linestyle='--', linewidth=2, label=f'Exact Energy ({exact_e:.2f})')
    
    plt.xlabel("Function Evaluations (Iterative Steps)", fontsize=14)
    plt.ylabel("Expected Energy (Hartree)", fontsize=14)
    plt.title("VQE Optimizer Comparison Under HPC-Scale QPD Sampling Noise (N=16)\nAverage over 5 independent random initializations", fontsize=15)
    plt.legend(fontsize=12, loc='upper right')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "optimizer_comparison.pdf"), dpi=300)
    plt.close()

def plot_breakeven_curve(results_dir, output_dir):
    json_path = os.path.join(results_dir, 'breakeven_curve.json')
    if not os.path.exists(json_path):
        print(f"Skipping Breakeven Curve: {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        res = json.load(f)

    data = res['data']
    p_cx = [d['p_cx'] for d in data]
    mono_energy = [d['monolithic_energy'] for d in data]
    cut_energy = [d['dynacut_energy'] for d in data]
    
    # Statistical error band (10k shots equivalent)
    # gamma = res['gamma'], norm_H = res['norm_H']
    gamma = res['gamma']
    norm_H = res['norm_H']
    shots = 100000
    sigma = (gamma * norm_H) / np.sqrt(shots)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(p_cx, mono_energy, 'o-', color='#e74c3c', linewidth=2.5, label='Monolithic (Exact Noisy)')
    ax.plot(p_cx, cut_energy, 's-', color='#2ecc71', linewidth=2.5, label='DynaCut (Exact Noisy + QPD Reconstructed)')
    
    # Add statistical shading
    ax.fill_between(p_cx, np.array(cut_energy) - sigma, np.array(cut_energy) + sigma, 
                    color='#2ecc71', alpha=0.2, label=rf'QPD Sampling Variance ($S={shots}$)')

    # Add Ideal energy reference
    ideal = res['ideal_energy']
    ax.axhline(ideal, color='black', linestyle='--', linewidth=2, label='Ideal Ground State')
    
    # Fully mixed state reference (expected energy = 7.5 for N=10 random 3-regular MaxCut)
    ax.axhline(7.5, color='gray', linestyle=':', linewidth=2, label='Maximally Mixed State')
    
    ax.set_xlabel(r'Two-Qubit Depolarizing Error Rate ($p_{cx}$)', fontsize=14)
    ax.set_ylabel(r'Expected Energy $\langle H \rangle$', fontsize=14)
    ax.set_title('Empirical Breakeven: Mitigation of Hardware Noise via Cutting', fontsize=16)
    
    ax.legend(fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Find crossover
    crossover_idx = None
    for i in range(len(p_cx)):
        if cut_energy[i] > mono_energy[i]:
            crossover_idx = i
            break
            
    if crossover_idx is not None and crossover_idx > 0:
        x_cross = p_cx[crossover_idx]
        y_cross = cut_energy[crossover_idx]
        ax.annotate('Breakeven Point', xy=(x_cross, y_cross), xytext=(x_cross+0.01, y_cross+0.5),
                    arrowprops=dict(facecolor='black', shrink=0.05),
                    fontsize=12, fontweight='bold')
    
    ax.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)

    plt.tight_layout()
    out_path = os.path.join(output_dir, 'breakeven_curve.pdf')
    plt.savefig(out_path, format='pdf', bbox_inches='tight')
    plt.close()
    print(f"Saved {out_path}")

def plot_variance_decomposition(results_dir, output_dir):
    json_path = os.path.join(results_dir, 'variance_decomposition.json')
    if not os.path.exists(json_path):
        print(f"Skipping Variance Decomposition: {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        res = json.load(f)

    labels = ['Monolithic\n(No Cuts)', 'DynaCut\n(K=3, S=1M, $\chi$=8)']
    
    mono = res['monolithic']
    cut = res['dynacut']
    
    eps_phys = [mono['eps_phys'], cut['eps_phys']]
    eps_trunc = [mono['eps_trunc'], cut['eps_trunc']]
    eps_stat = [mono['eps_stat'], cut['eps_stat']]

    x = np.arange(len(labels))
    width = 0.5
    
    fig, ax = plt.subplots(figsize=(7, 6))

    # Stack the bars
    p1 = ax.bar(x, eps_phys, width, label=r'Hardware Noise ($\epsilon_{phys}$)', color='#e74c3c', edgecolor='black', zorder=3)
    p2 = ax.bar(x, eps_trunc, width, bottom=eps_phys, label=r'TN Truncation ($\epsilon_{trunc}$)', color='#f39c12', edgecolor='black', zorder=3)
    
    bottom_stat = [eps_phys[i] + eps_trunc[i] for i in range(2)]
    p3 = ax.bar(x, eps_stat, width, bottom=bottom_stat, label=r'QPD Variance ($\epsilon_{stat}$)', color='#3498db', edgecolor='black', hatch='//', zorder=3)

    # Add text annotations for total error
    for i in range(2):
        total = bottom_stat[i] + eps_stat[i]
        ax.text(x[i], total + 0.05, f"{total:.2f}", ha='center', va='bottom', fontweight='bold', fontsize=12)

    ax.set_ylabel(r'Expected Absolute Error ($|\langle H_{ideal} \rangle - \langle H_{noisy} \rangle|$)', fontsize=13)
    ax.set_title('Error Budget Decomposition ($p_{cx}=0.05$)', fontsize=15, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12)
    ax.legend(fontsize=11)
    
    ax.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)

    plt.tight_layout()
    out_path = os.path.join(output_dir, 'variance_decomposition.pdf')
    plt.savefig(out_path, format='pdf', bbox_inches='tight')
    plt.close()
    print(f"Saved {out_path}")

if __name__ == "__main__":
    import sys
    print("Generating figures...")
    try:
        plot_pareto_frontier()
        plot_vqe_convergence()
        plot_partitioner_ablation()
        plot_topology_stress_test()
        plot_tn_vs_ibm_scaling()
        plot_hpc_scaling()
        plot_mps_baseline()
        plot_cut_vs_uncut_error()
        plot_svd_ablation()
        plot_chemistry_pes()
        plot_optimizer_comparison()
        plot_breakeven_curve(RESULTS_DIR, FIGURES_DIR)
        plot_variance_decomposition(RESULTS_DIR, FIGURES_DIR)
    except Exception as e:
        print(f"Error generating figures: {e}")
    print(f"Figures generated in {FIGURES_DIR}")
