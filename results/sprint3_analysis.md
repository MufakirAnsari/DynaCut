# Sprint 3 Data Analysis

This report validates the robustness, generalizability, and noise-resilience of DynaCut-V2.

### Depolarizing Noise Impact

- **Noise p=0.0**: Cut Error = 10.87486 ± 1.98427 | Uncut Error = 10.82710 ± 1.96416
- **Noise p=0.0001**: Cut Error = 10.83233 ± 1.95940 | Uncut Error = 10.83286 ± 1.97672
- **Noise p=0.001**: Cut Error = 10.81529 ± 1.95741 | Uncut Error = 10.83792 ± 1.96108
- **Noise p=0.01**: Cut Error = 10.84791 ± 1.94162 | Uncut Error = 10.84390 ± 1.92511
- **Noise p=0.05**: Cut Error = 10.88824 ± 1.80374 | Uncut Error = 10.87642 ± 1.81466
- **Noise p=0.1**: Cut Error = 10.90972 ± 1.77501 | Uncut Error = 10.89115 ± 1.70873

### Shot Noise Overhead

- **10 qubits, -1 samples**: Avg Error = 10.83138 ± 1.96037
- **10 qubits, 100 samples**: Avg Error = 15.43782 ± 9.10598
- **10 qubits, 500 samples**: Avg Error = 10.83138 ± 1.96037
- **10 qubits, 1000 samples**: Avg Error = 10.83138 ± 1.96037
- **10 qubits, 5000 samples**: Avg Error = 11.17310 ± 2.16968
- **10 qubits, 10000 samples**: Avg Error = 10.75887 ± 1.99180
- **14 qubits, -1 samples**: Avg Error = 17.85567 ± 1.75770
- **14 qubits, 100 samples**: Avg Error = 53.68825 ± 94.60211
- **14 qubits, 500 samples**: Avg Error = 17.85567 ± 1.75770
- **14 qubits, 1000 samples**: Avg Error = 58.48129 ± 96.48374
- **14 qubits, 5000 samples**: Avg Error = 28.96317 ± 25.88274
- **14 qubits, 10000 samples**: Avg Error = 16.24671 ± 4.71711

### Cross-Problem Generalization

- **maxcut (10 qubits)**: Avg Error = 10.83138 ± 1.96037 | Avg Cuts = 1.00000 ± 0.00000
- **maxcut (14 qubits)**: Avg Error = 17.85567 ± 1.75770 | Avg Cuts = 1.80000 ± 0.97980
- **tfim (10 qubits)**: Avg Error = 11.60625 ± 1.41243 | Avg Cuts = 1.00000 ± 0.00000
- **tfim (14 qubits)**: Avg Error = 17.39563 ± 1.53112 | Avg Cuts = 1.00000 ± 0.00000
- **heisenberg (8 qubits)**: Avg Error = 13.07537 ± 1.31353 | Avg Cuts = 1.00000 ± 0.00000
- **h2 (4 qubits)**: Avg Error = 1.07077 ± 0.29390 | Avg Cuts = 1.00000 ± 0.00000

### Cross-Ansatz Comparison

- **maxcut with he**: Avg Error = 10.83138 ± 1.96037 | Avg Iters = 0.00000 ± 0.00000
- **maxcut with qaoa**: Avg Error = 10.28189 ± 2.32639 | Avg Iters = 0.00000 ± 0.00000
- **h2 with he**: Avg Error = 1.07077 ± 0.29390 | Avg Iters = 0.00000 ± 0.00000
- **h2 with ucc_heuristic**: Avg Error = 1.08938 ± 0.14932 | Avg Iters = 0.00000 ± 0.00000

### Adversarial Graph Topologies

- **Topology bipartite**: Avg Error = 17.33827 ± 0.57541 | Avg Cuts = 1.40000 ± 0.80000
- **Topology complete**: Avg Error = 32.36593 ± 0.67925 | Avg Cuts = 2.00000 ± 1.00000
- **Topology regular_3**: Avg Error = 7.90063 ± 0.77681 | Avg Cuts = 1.60000 ± 0.91652
- **Topology ring**: Avg Error = 5.04161 ± 0.48457 | Avg Cuts = 1.00000 ± 0.00000
- **Topology star**: Avg Error = 5.22589 ± 0.48241 | Avg Cuts = 1.00000 ± 0.00000

