# Final Paper Tables (PRX Quantum Format)

## Table I: Baseline Comparison

| method                |   ('time', 10) |   ('time', 14) |   ('error', 10) |   ('error', 14) |   ('cuts', 10) |   ('cuts', 14) |
|:----------------------|---------------:|---------------:|----------------:|----------------:|---------------:|---------------:|
| Aer Noise Model       |     0.503086   |      6.56445   |     0.0285841   |     0.0120248   |              0 |              0 |
| CutQC (Simulated)     |     0.198847   |      8.43339   |     7.10543e-15 |     1.1724e-13  |              0 |              0 |
| DynaCut-V2 (TN Exact) |     5.0584     |     18.076     |     4.61853e-14 |     7.81597e-14 |              3 |              3 |
| METIS Partitioning    |     0          |      0         |   nan           |   nan           |              0 |              0 |
| MPS (bond=64)         |     0          |      0         |   nan           |   nan           |              0 |              0 |
| Random Partitioning   |     0          |      0         |   nan           |   nan           |              5 |              6 |
| Raw Cutting           |     4.93452    |     17.7852    |     4.26326e-14 |     8.17124e-14 |              3 |              3 |
| Statevector           |     0.00283384 |      0.0118196 |     0           |     0           |              0 |              0 |



## Table II: VRAM and Scalability

|   qubits |   mean_execution_time |   mean_cuts |   mean_vram_mb |   exact_vram_mb |
|---------:|----------------------:|------------:|---------------:|----------------:|
|       10 |            0.007201   |           0 |      0.0749836 |        0.015625 |
|       12 |            0.00907354 |           0 |      0.26002   |        0.0625   |
|       14 |            0.0157223  |           0 |      1.01008   |        0.25     |
|       16 |            1.51504    |           1 |      3.24298   |        1        |



## Table III: Partitioner Ablation

|   Qubits |   Random Cuts |   METIS Cuts |   DynaCut-V2 Cuts |
|---------:|--------------:|-------------:|------------------:|
|       10 |           6.6 |            0 |               3.8 |
|       14 |          14.2 |            0 |               7.2 |
|       18 |          21.3 |            0 |              14.8 |



## Table III-b: Fragment Size Sweep

|   max_fragment_size |   mean_cuts |   mean_fragments |   mean_time |
|--------------------:|------------:|-----------------:|------------:|
|                   4 |        18   |                6 | 0.00282183  |
|                   6 |        14.8 |                4 | 0.00175376  |
|                   8 |        15   |                4 | 0.00294833  |
|                  10 |         7.4 |                2 | 0.000623894 |
|                  12 |         7.4 |                2 | 0.000609112 |
|                  14 |         7   |                2 | 0.000588083 |
|                  16 |         7.4 |                2 | 0.000615358 |
|                  18 |         0   |                1 | 3.19958e-05 |



## Table III-c: Optimizer Comparison

| method      |   mean_energy |   mean_evals |   mean_time |
|:------------|--------------:|-------------:|------------:|
| COBYLA      |   0.0583575   |         42   |     3.99214 |
| Nelder-Mead |   0.0721893   |         71   |     6.6726  |
| SLSQP       |   1.23861e-05 |        265.8 |    26.0774  |
| L-BFGS-B    |   1.46069e-05 |        328   |    30.7892  |



## Table IV: Cross-Problem Generalization

| problem    |   num_qubits |     mean |      std |
|:-----------|-------------:|---------:|---------:|
| h2         |            4 |  1.07077 | 0.309799 |
| heisenberg |            8 | 13.0754  | 1.38458  |
| maxcut     |           10 | 10.8314  | 2.06641  |
| maxcut     |           14 | 17.8557  | 1.85278  |
| tfim       |           10 | 11.6063  | 1.48883  |
| tfim       |           14 | 17.3956  | 1.61394  |



## Table V: Adversarial Topologies

| topology   |     mean |      std |   cuts |
|:-----------|---------:|---------:|-------:|
| bipartite  | 17.3383  | 0.606535 |    1.4 |
| complete   | 32.3659  | 0.715995 |    2   |
| regular_3  |  7.90063 | 0.818832 |    1.6 |
| ring       |  5.04161 | 0.510784 |    1   |
| star       |  3.68603 | 2.5737   |    2.7 |


