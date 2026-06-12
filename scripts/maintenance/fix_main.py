with open("paper/main.tex", "r") as f:
    lines = f.readlines()

# The new architecture section is currently at lines 167-227 (0-indexed 166 to 226)
new_arch = lines[166:227]

# The missing experimental setup section
exp_setup = [
    "\\section{Experimental Setup}\n",
    "To validate the framework, we perform evaluations spanning small-scale (10-16 qubits) to classically intensive (26-qubits) regimes.\n",
    "\\begin{itemize}\n",
    "    \\item \\textbf{Datasets}: Erdős-Rényi and 3-Regular graphs for MaxCut, 1D Transverse-Field Ising Models (TFIM), and Heisenberg models.\n",
    "    \\item \\textbf{Hardware Profile}: All noisy simulations are executed using the \\texttt{FakeGuadalupeV2} physical topology, importing exact empirical $T1/T2$ thermal relaxation channels and gate error rates.\n",
    "    \\item \\textbf{Baselines}: We baseline our tensor-network reconstructed energies against: (a) Exact Statevector Simulation and (b) Unpartitioned Noisy VQE (to demonstrate the fidelity drop of executing deep circuits directly on NISQ hardware).\n",
    "\\end{itemize}\n\n"
]

# Delete lines 134 to 227 (0-indexed 133 to 226)
del lines[133:227]

# Insert architecture then experimental setup at index 133
lines = lines[:133] + new_arch + ["\n"] + exp_setup + lines[133:]

with open("paper/main.tex", "w") as f:
    f.writelines(lines)
