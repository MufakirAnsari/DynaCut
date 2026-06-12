# DynaCut

**DynaCut: A State-of-the-Art Hybrid Tensor-Network Quantum Circuit Knitting Framework**

DynaCut is an advanced software stack designed to dramatically extend the capabilities of near-term noisy quantum processing units (QPUs). By mathematically dividing large quantum circuits into smaller partitions (Circuit Knitting) and using an advanced **Tensor-Network Contraction Engine** for reconstruction, DynaCut makes it feasible to run complex algorithms (like large-scale VQE and QAOA) on hardware with limited qubit counts and high noise levels.

## Core Scientific Innovation & Mathematical Foundation

The core scientific novelty of DynaCut lies in treating the classical post-processing of circuit cutting as a **tensor network contraction problem** rather than relying on naive statistical sampling.

### 1. Quasi-Probability Decomposition (QPD)
When a two-qubit gate (e.g., CNOT) connecting two sub-circuits is severed, the quantum channel is decomposed into a linear combination of 6 physically realizable local operations:
```math
\mathcal{U}_{\text{CX}}(\rho) = \sum_{i=1}^6 c_i \mathcal{E}_{A,i} \otimes \mathcal{E}_{B,i} (\rho)
```
Where $c_i \in \{\pm 1/4, \pm 1\}$ and the theoretical sampling overhead is exactly bounded by the 1-norm $\gamma = \sum_i |c_i| = 3$. 

### 2. Native KL Bisection Partitioning
DynaCut does not rely on brute-force fragmentation. Instead, it natively implements a memory-aware **Kernighan-Lin (KL) bisection-based hypergraph partitioner** to optimally fragment the circuit. By slicing the circuit into disjoint clusters (e.g., $N_p \le 7$), DynaCut completely bypasses global heavy-hex SWAP routing. This collapses the physical circuit depth from classically intractable levels ($D > 100$) to highly resilient local depths ($D \approx 40$), preserving the signal necessary for Zero-Noise Extrapolation (ZNE).

### 3. SVD-Truncated Tensor Reconstruction
Exact statevector simulation on classical HPC is strictly bottlenecked by RAM, bounding tractable simulation to $N \le \log_2(V_{\max} / 64 \text{ bytes})$. DynaCut solves this memory wall by mapping QPU sub-circuit outputs to classical tensors and applying **Truncated Singular Value Decomposition (SVD)** on intermediate contractions. By retaining only the top $\chi$ singular values, DynaCut compresses the contraction footprint:
- **Exact IBM Aer Simulation**: Triggers Out-of-Memory (OOM) failures at $N=26$ under a $V_{\max}=1024$ MB limit.
- **DynaCut TN Engine**: Reconstructs the $N=26$ state utilizing a peak memory footprint of exactly $\le 1.74 \text{ MB}$.

## Key Features

- **Tensor-Network Reconstruction Engine**: Leverages `quimb` for tensor network construction and highly compressed SVD-truncated approximate contraction.
- **Optimal Pathfinding**: Integrates with `opt-einsum` to calculate optimal contraction ordering, dramatically minimizing intermediate RAM footprints.
- **Memory-Bounded KL Partitioner**: Dynamically limits the graph fragmentation to strictly obey $V_{\max}$ limits while minimizing the cut count $K$.
- **Hybrid Quantum-Classical Optimization**: Coordinates SPSA classical parameter optimization with distributed noisy QPU sub-circuit evaluations.

## Architecture

1. **Topology & Partitioning (`topology.py`)**
   - Ingests problem graphs and identifies optimal cut points using the KL Bisection engine under strict classical memory bounds.
2. **The Knitting Engine (`knitting.py`)**
   - Takes quasi-probability coefficients and QPU sub-circuit expectations to build the classical tensor network.
   - Computes contraction paths and executes precise or approximate (SVD) contractions.
3. **The Hybrid Executor (`executor.py`)**
   - Coordinates QPU dispatching and orchestrates the classical-quantum loop for the Variational Quantum Eigensolver (VQE) and QAOA.

## Installation & Dependencies

DynaCut requires Python 3.9+ and relies heavily on the Qiskit ecosystem and advanced tensor libraries.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MufakirAnsari/DynaCut.git
   cd DynaCut
   ```

2. **Install the framework:**
   ```bash
   pip install -e .
   ```

**Core Dependencies:**
- `qiskit >= 1.0.0`
- `qiskit-aer >= 0.14.0`
- `qiskit-addon-cutting >= 0.7.0`
- `quimb >= 1.8.2`
- `opt-einsum >= 3.3.0`
- `networkx`, `numpy`, `scipy`

## Experimental Suite & Benchmarks

The `experiments/` directory contains an extensive suite of benchmarks and rigorous mathematical proofs for the framework.

### 1. Scaling & VRAM Efficiency
- **Scalability Breakthroughs**: Successfully benchmarked up to **26 qubits** on QAOA MaxCut (Stochastic Block Models) and **14 qubits** on VQE (1D TFIM).
- **`tn_vs_ibm_scaling.py`**: Proves DynaCut's theoretical constant-memory scaling ($O(1)$ w.r.t $N$ for bounded cut-widths) compared to IBM Aer's exponential explosion ($O(2^N)$). 

### 2. Theoretical Bounds & Robustness
- **Sampling Overhead (Theorem 1)**: Practical executions are strictly governed by $K \le 2$. Setting $K \ge 3$ triggers exponential $\mathcal{O}(9^K)$ variance scaling, exceeding practical hardware quotas ($100\text{k}$ shots).
- **Topological Stress Tests**: SBM density tests sweep $p_{out} \in [0.005, 0.05]$, proving classical truncation limits gracefully handle moderately dense graphs before demanding SVD compression.

### 3. Ablation Studies
- **`ablation_partitioner.py`**: Isolates the performance of the KL Bisection partitioner versus random fragmentation, confirming a $2\times$ reduction in cut hyperedges and a resulting $5 \times 10^5 \times$ compression in hardware shot requirements.
- **`vqe_convergence.py`**: Confirms that partitioned sub-experiments successfully track energy descent using QPU noise models across independent random seeds.

## Cite

**Author:** Mufakir Ansari
