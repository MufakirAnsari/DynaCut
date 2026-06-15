import networkx as nx
import numpy as np
import cvxpy as cp
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gw_baseline")

def solve_maxcut_sdp(edges, num_nodes):
    """
    Solve the Goemans-Williamson SDP relaxation for MaxCut.
    
    Returns the SDP upper bound for the maxcut.
    """
    if not edges:
        return 0.0

    X = cp.Variable((num_nodes, num_nodes), PSD=True)
    
    # Objective: Maximize 1/4 \sum_{(i,j)\in E} (1 - X_{ij})
    # Since X_{ii}=1, (1-X_{ij})/2 is the SDP relaxed cut value.
    # Wait, the maxcut problem obj is usually 0.5 * sum_{i,j} (1 - X_{ij}) ?
    # Standard MaxCut: sum_{i,j \in E} (1 - z_i z_j)/2
    objective_expr = 0
    for u, v in edges:
        objective_expr += 0.5 * (1 - X[u, v])
        
    objective = cp.Maximize(objective_expr)
    constraints = [cp.diag(X) == 1]
    
    prob = cp.Problem(objective, constraints)
    prob.solve(solver=cp.SCS)
    
    if prob.status not in ["optimal", "optimal_inaccurate"]:
        logger.warning(f"SDP solver did not converge optimally: {prob.status}")
        return 0.0, 0
        
    X_val = X.value
    sdp_bound = prob.value
    
    # GW Rounding
    # Cholesky decomposition X = V^T V
    # Add small epsilon to diagonal to ensure PSD
    eps = 1e-6
    X_val = X_val + np.eye(num_nodes) * eps
    try:
        V = np.linalg.cholesky(X_val).T
    except np.linalg.LinAlgError:
        # Fallback to eigen decomposition if Cholesky fails
        eigvals, eigvecs = np.linalg.eigh(X_val)
        eigvals[eigvals < 0] = 0
        V = (eigvecs @ np.diag(np.sqrt(eigvals))).T

    # Generate random hyperplanes and round
    best_cut = 0
    num_random_hyperplanes = 1000
    for _ in range(num_random_hyperplanes):
        r = np.random.randn(num_nodes)
        r = r / np.linalg.norm(r)
        
        # Rounding
        spins = np.sign(V.T @ r)
        # Calculate cut value
        cut_val = 0
        for u, v in edges:
            if spins[u] != spins[v]:
                cut_val += 1
                
        if cut_val > best_cut:
            best_cut = cut_val

    return sdp_bound, best_cut

def solve_maxcut_sa(edges, num_nodes, num_reads=1000, num_steps=1000):
    """
    Solve MaxCut using Simulated Annealing.
    """
    if not edges:
        return 0
        
    best_cut = 0
    
    for _ in range(num_reads):
        # Random initial state
        spins = np.random.choice([-1, 1], size=num_nodes)
        
        # Current cut value
        current_cut = sum(1 for u, v in edges if spins[u] != spins[v])
        
        # Annealing schedule
        T_start = 10.0
        T_end = 0.01
        
        for step in range(num_steps):
            T = T_start * (T_end / T_start) ** (step / max(1, num_steps - 1))
            
            # Pick a random node to flip
            node = np.random.randint(0, num_nodes)
            
            # Calculate change in cut value
            delta_cut = 0
            for u, v in edges:
                if u == node:
                    neighbor = v
                elif v == node:
                    neighbor = u
                else:
                    continue
                    
                # If they were different, they will become same (lose cut edge)
                # If they were same, they will become different (gain cut edge)
                if spins[node] != spins[neighbor]:
                    delta_cut -= 1
                else:
                    delta_cut += 1
                    
            if delta_cut > 0 or np.random.rand() < np.exp(delta_cut / T):
                spins[node] *= -1
                current_cut += delta_cut
                
        if current_cut > best_cut:
            best_cut = current_cut
            
    return best_cut

def maxcut_exact(edges, num_nodes):
    """
    Solve MaxCut exactly by enumerating all 2^N states.
    For validation purposes on small graphs.
    """
    best_cut = 0
    import itertools
    for state in itertools.product([-1, 1], repeat=num_nodes):
        cut = sum(1 for u, v in edges if state[u] != state[v])
        if cut > best_cut:
            best_cut = cut
    return best_cut


if __name__ == "__main__":
    import time
    import json
    import os
    
    results_gw = []
    results_sa = []
    
    graph_sizes = [10, 14, 18, 22, 26]
    seeds = list(range(10))
    topologies = ["1D_chain", "3_regular", "SBM"]
    
    logger.info("Starting Baseline Runs...")
    
    for N in graph_sizes:
        for topo in topologies:
            for seed in seeds:
                # Generate Graph
                if topo == "1D_chain":
                    G = nx.path_graph(N)
                elif topo == "3_regular":
                    # Must be even N for 3-regular, 10, 14, 18, 22, 26 are all even
                    G = nx.random_regular_graph(3, N, seed=seed)
                elif topo == "SBM":
                    # Stochastic Block Model with p_in = 0.8, p_out = 0.1
                    sizes = [N//2, N - N//2]
                    probs = [[0.8, 0.1], [0.1, 0.8]]
                    G = nx.stochastic_block_model(sizes, probs, seed=seed)
                
                edges = list(G.edges())
                
                # Run GW
                t0 = time.time()
                sdp_bound, gw_cut = solve_maxcut_sdp(edges, N)
                t_gw = time.time() - t0
                
                results_gw.append({
                    "N": N,
                    "topology": topo,
                    "seed": seed,
                    "sdp_bound": float(sdp_bound),
                    "cut_value": int(gw_cut),
                    "time": float(t_gw)
                })
                
                # Run SA
                t0 = time.time()
                sa_cut = solve_maxcut_sa(edges, N)
                t_sa = time.time() - t0
                
                results_sa.append({
                    "N": N,
                    "topology": topo,
                    "seed": seed,
                    "cut_value": int(sa_cut),
                    "time": float(t_sa)
                })
                
                logger.info(f"N={N}, topo={topo}, seed={seed} | GW:{gw_cut} SA:{sa_cut} SDP:{sdp_bound:.2f}")

    # Save Results
    os.makedirs("results", exist_ok=True)
    with open("results/gw_baseline.json", "w") as f:
        json.dump(results_gw, f, indent=4)
        
    with open("results/sa_baseline.json", "w") as f:
        json.dump(results_sa, f, indent=4)
        
    logger.info("Saved gw_baseline.json and sa_baseline.json to results/")
