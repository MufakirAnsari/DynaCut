import os

latex_path = "/home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex"
with open(latex_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Remove chemistry / materials claims
target_1 = "This framework provides a critical pathway toward achieving quantum utility in quantum chemistry simulation, materials science, and combinatorial optimization, ensuring that"
replace_1 = "This framework provides a critical pathway toward achieving quantum utility in many-body physics simulation and combinatorial optimization, ensuring that"
if target_1 in text:
    text = text.replace(target_1, replace_1)
else:
    print("WARNING: target 1 not found")

# 2. P=4 justification
target_2 = r"The $P=4$ disjoint sub-graphs are then independently routed using Qiskit's \texttt{SABRE} algorithm"
replace_2 = r"To specifically balance the resulting sub-graph size ($N_p \approx 6.5$) against the strict $256$ MB tensor network tree-width memory constraint, we empirically fix $P=4$. These $P=4$ disjoint sub-graphs are then independently routed using Qiskit's \texttt{SABRE} algorithm"
if target_2 in text:
    text = text.replace(target_2, replace_2)
else:
    print("WARNING: target 2 not found")

# 3. K<=2 justification
target_3 = r"By bounding $K \le 2$ on 26-qubit MaxCut graphs, $\epsilon_{\text{stat}}$ remains heavily constrained ($\Gamma^2 \le 81$), while $\epsilon_{\text{trunc}} = 0$ as the exact dense contraction fits exactly within the $V_{\max}$ bounds."
replace_3 = r"While our theoretical framework accommodates arbitrary $K$, practical experiments are strictly bounded to $K \le 2$. This is because $K \ge 3$ triggers an exponential sampling overhead ($\Gamma^2 \approx 9^3 = 729$) that requires millions of physical executions, severely exceeding the $\approx 100\text{k}$ shot quotas typical of public IBM Quantum cloud services. By enforcing $K \le 2$ on 26-qubit MaxCut graphs, $\epsilon_{\text{stat}}$ remains heavily constrained ($\Gamma^2 \le 81$), while $\epsilon_{\text{trunc}} = 0$ as the exact dense contraction fits exactly within the $V_{\max}$ bounds."
if target_3 in text:
    text = text.replace(target_3, replace_3)
else:
    print("WARNING: target 3 not found")

# 4. ZNE explicit mapping
target_4 = r"The physical error $\epsilon_{\text{phys}}$ is mitigated via Zero-Noise Extrapolation (ZNE)."
replace_4 = r"To resolve the second term in the error bound, the physical hardware error $\epsilon_{\text{phys}}$ is mitigated directly via Zero-Noise Extrapolation (ZNE)."
if target_4 in text:
    text = text.replace(target_4, replace_4)
else:
    print("WARNING: target 4 not found")

with open(latex_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Applied theory consistency updates successfully!")
