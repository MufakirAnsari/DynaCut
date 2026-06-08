# DynaCut

**DynaCut: A State-of-the-Art Hybrid Tensor-Network Quantum Circuit Knitting Framework**

DynaCut is an advanced software stack designed to dramatically extend the capabilities of near-term noisy quantum processing units (QPUs). By mathematically dividing large quantum circuits into smaller partitions (Circuit Knitting) and using an advanced **Tensor-Network Contraction Engine** for reconstruction, DynaCut makes it feasible to run complex algorithms (like large-scale VQE) on hardware with limited qubit counts and high noise levels.

## Core Scientific Innovation & Mathematical Foundation

The core scientific novelty of DynaCut lies in treating the classical post-processing of circuit cutting as a **tensor network contraction problem** rather than relying on naive statistical sampling.

### 1. Quasi-Probability Decomposition (QPD)
When a quantum wire connecting two sub-circuits $S_A$ and $S_B$ is severed, the quantum identity channel $\mathcal{I}$ on that wire is decomposed into a linear combination of physically realizable operations via QPD:
$$ \mathcal{I} = \sum_{k=0}^{D-1} c_k \cdot (\mathcal{M}_k \otimes \mathcal{P}_k) $$
Where:
- $\mathcal{M}_k$ are measurement bases on the source sub-circuit $S_A$.
- $\mathcal{P}_k$ are preparation bases on the target sub-circuit $S_B$.
- $c_k$ are the quasi-probability coefficients.
- $D$ is the basis size (typically $D=4$ or $D=6$ for single-qubit Pauli-based cuts).

### 2. Sub-Circuit Tensor Representation
Naive reconstruction performs a weighted sum over all sub-experiment results, leading to exponential sampling overhead. DynaCut instead maps each quantum sub-circuit $S$ to a classical tensor $\mathcal{T}^{(S)}$. 

If a sub-circuit has $N$ cut wires attached to it, $\mathcal{T}^{(S)}$ is constructed as a tensor of rank $N$ with shape $(D, D, \dots, D)$. An individual element $\mathcal{T}^{(S)}_{i_1, i_2, \dots, i_N}$ is the expectation value obtained directly from the QPU when executing the sub-circuit with the specific QPD basis indices $(i_1, \dots, i_N)$ injected at its boundaries.

### 3. Global Reconstruction via Tensor Contraction
The global expectation value $\langle \mathcal{O} \rangle$ of the original, uncut circuit is recovered by contracting the tensor network formed by all sub-circuit tensors and the QPD coefficients:
$$ \langle \mathcal{O} \rangle = \sum_{i, j, k \dots} \left( c_i c_j c_k \dots \right) \mathcal{T}^{(S_1)}_{i, \dots} \mathcal{T}^{(S_2)}_{i, j, \dots} \dots $$
This maps the quantum reconstruction directly to standard Einstein summation conventions.

### 4. SVD-Truncated Approximate Contraction
For highly entangled or densely cut graphs, exact tensor contraction requires exponential memory. DynaCut solves this using **Truncated Singular Value Decomposition (SVD)** on intermediate contraction results. 

When contracting two intermediate tensors $A$ and $B$, the exact contraction $M = A \cdot B$ is factorized:
$$ M = U \Sigma V^\dagger $$
By retaining only the top $\chi$ singular values (the maximum bond dimension), we project the intermediate tensor into a lower-dimensional subspace:
$$ M \approx U_\chi \Sigma_\chi V_\chi^\dagger $$
This trades a tightly bounded approximation error for **exponential memory savings**, a capability impossible in naive QPD reconstruction.

## Key Features

- **Tensor-Network Reconstruction Engine**: Leverages `quimb` for tensor network construction and SVD-truncated approximate contraction.
- **Optimal Pathfinding**: Integrates with `opt-einsum` and `cotengra` to calculate the optimal contraction ordering (path optimization), further minimizing intermediate tensor sizes and RAM footprint.
- **Adaptive Execution Scheduler**: Automatically scales sub-circuit chunk sizes to match hardware capabilities.
- **Dynamic Circuit Partitioning**: Cuts problem graphs using VF2 embedding and intelligent entanglement ablation strategies.
- **Hybrid VQE Execution**: Coordinates classical parameter optimization with distributed quantum sub-circuit evaluations.

## Architecture

1. **Topology & Partitioning (`topology.py`)**
   - Ingests problem graphs and identifies optimal cut points based on hardware connectivity.
2. **The Knitting Engine (`knitting.py`)**
   - Takes quasi-probability coefficients and sub-circuit expectations and builds the tensor network representation.
   - Computes contraction paths and executes precise or approximate (SVD) contractions.
3. **The Hybrid Executor (`executor.py`)**
   - Coordinates the entire workflow. Handles QPU dispatching and orchestrates the classical-quantum loop for the Variational Quantum Eigensolver.
4. **Adaptive Scheduler (`adaptive_scheduler.py`)**
   - Optimizes resource allocation by dynamically adjusting how QPD experiments are distributed across available quantum backends.

## Installation & Dependencies

DynaCut requires Python 3.9+ and relies heavily on the Qiskit ecosystem and advanced tensor libraries.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MufakirAnsari/DynaCut.git
   cd DynaCut
   ```

2. **Install the framework (recommend using a virtual environment):**
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

## Experimental Suite

The `experiments/` directory contains an extensive suite of benchmarks, validation scripts, and rigorous mathematical proofs for the framework:
- **`tn_pareto_real.py` & `tn_scaling_real.py`**: Demonstrate the real-world scalability and Pareto efficiency of the tensor-network reconstruction against naive baselines.
- **`phase1_math_rigor.py` - `phase5_ibm_hardware.py`**: A structured validation pipeline proving mathematical equivalence, VQE convergence, and execution on real IBM Q hardware models.
- **Ablation Studies**: Dedicated scripts (`ablation_depth.py`, `ablation_optimizer.py`, etc.) for isolating the performance impact of individual framework components.

## Development & Testing

Unit and integration tests are available in the `tests/` directory.

To run tests:
```bash
python -m unittest discover tests/
```

## Contributing

Contributions are welcome! If you have optimizations for the SVD truncation heuristics or support for new quantum hardware interfaces, please submit a pull request.
