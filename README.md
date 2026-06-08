# DynaCut

**DynaCut: A State-of-the-Art Hybrid Tensor-Network Quantum Circuit Knitting Framework**

DynaCut is an advanced software stack designed to dramatically extend the capabilities of near-term noisy quantum processing units (QPUs). By mathematically dividing large quantum circuits into smaller partitions (Circuit Knitting) and using an advanced **Tensor-Network Contraction Engine** for reconstruction, DynaCut makes it feasible to run complex algorithms (like large-scale VQE) on hardware with limited qubit counts and high noise levels.

## Core Scientific Innovation

The core scientific novelty of DynaCut lies in treating the classical post-processing of circuit cutting as a **tensor network contraction problem** rather than relying on naive statistical sampling. 

When a wire connecting sub-circuits is cut, the identity channel is decomposed via Quasi-Probability Decomposition (QPD). Naive reconstruction performs a weighted sum over all sub-experiment results, which scales poorly. DynaCut instead exposes the reconstruction as an explicit tensor network, yielding three massive advantages:
1. **Predictive Costing:** We can estimate contraction cost *before* executing jobs on the QPU.
2. **Approximate Contraction (SVD Truncation):** We trade controlled precision for massive memory savings by using Truncated Singular Value Decomposition (SVD), avoiding exponential memory blowups.
3. **Optimal Pathfinding:** DynaCut integrates directly with `opt-einsum` and `cotengra` to calculate the optimal contraction ordering, minimizing intermediate tensor sizes and RAM footprint.

## Key Features

- **Tensor-Network Reconstruction Engine**: Leverages `quimb` for tensor network construction and SVD-truncated approximate contraction.
- **Adaptive Execution Scheduler**: Automatically scales sub-circuit chunk sizes to match hardware capabilities.
- **Dynamic Circuit Partitioning**: Cuts problem graphs using VF2 embedding and intelligent entanglement ablation strategies.
- **Hybrid VQE Execution**: Coordinates classical parameter optimization with distributed quantum sub-circuit evaluations.

## Architecture

1. **Topology & Partitioning (`topology.py`)**
   - Ingests problem graphs and identifies optimal cut points based on hardware connectivity.
2. **The Knitting Engine (`knitting.py`)**
   - Responsible for taking quasi-probability coefficients and sub-circuit expectations and building a tensor network.
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
