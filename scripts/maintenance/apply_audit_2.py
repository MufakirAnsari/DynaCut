import re

file_path = "/home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Eq 2 (Old)
eq2_old_target = r"""For $K$ severed gates, the global expectation value is reconstructed as:
\begin{equation}
    \langle H \rangle = \sum_{\vec{\imath}} \left( \prod_{k=1}^K c_{i_k} \right) \prod_{p=1}^P \langle H_p \rangle_{\vec{\imath}}
\end{equation}"""
eq2_old_replacement = r"""For a target Hamiltonian $H = \sum_j h_j O_j$ and $K$ severed gates, the global expectation value is reconstructed as:
\begin{equation}
    \langle H \rangle = \sum_j h_j \sum_{\vec{\imath} \in \{1,\dots,6\}^K} \left( \prod_{k=1}^K c_{i_k} \right) \prod_{p=1}^P \langle O_{j,p} \rangle_{\vec{\imath}}
\end{equation}
where $\vec{\imath}$ explicitly runs over all $6^K$ possible basis configurations of the severed gates, and $\langle O_{j,p} \rangle_{\vec{\imath}}$ is the local expectation value of the Hamiltonian sub-term $O_j$ on partition $p$ evaluated under the specific measurement basis defined by $\vec{\imath}$."""
text = text.replace(eq2_old_target, eq2_old_replacement)

# Eq 4 (Old)
eq4_old_target = r"""The global estimation error derives from three sources: the QPD sampling variance ($\epsilon_{\text{stat}}$), the physical hardware noise ($\epsilon_{\text{phys}}$), and the SVD truncation error in the tensor network ($\epsilon_{\text{trunc}}$).
\begin{equation}
    |\Delta \langle H \rangle| \le |\epsilon_{\text{stat}}| + |\epsilon_{\text{phys}}| + |\epsilon_{\text{trunc}}|
\end{equation}
By keeping $K \le 2$ on 26-qubit MaxCut graphs, $\epsilon_{\text{stat}}$ remains negligible ($\Gamma^2 \le 81$), while $\epsilon_{\text{trunc}} = 0$ as the dense contraction fits exactly in RAM ($< 5$ GB). The physical error $\epsilon_{\text{phys}}$ is mitigated by Zero-Noise Extrapolation (ZNE)."""
eq4_old_replacement = r"""Assuming the errors across independent physical and algorithmic domains sum linearly, the global estimation error derives from five distinct sources: the QPD sampling variance ($\epsilon_{\text{stat}}$) from finite physical shots, the unmitigated physical hardware noise ($\epsilon_{\text{phys}}$), the SVD truncation error in the classical tensor network ($\epsilon_{\text{trunc}}$), the heuristic optimizer convergence error ($\epsilon_{\text{opt}}$), and the transpilation routing overhead ($\epsilon_{\text{trans}}$). The upper bound on the estimation error is given by:
\begin{equation}
    |\Delta \langle H \rangle| \le |\epsilon_{\text{stat}}| + |\epsilon_{\text{phys}}| + |\epsilon_{\text{trunc}}| + |\epsilon_{\text{opt}}| + |\epsilon_{\text{trans}}|
\end{equation}
By bounding $K \le 2$ on 26-qubit MaxCut graphs, $\epsilon_{\text{stat}}$ remains heavily constrained ($\Gamma^2 \le 81$), while $\epsilon_{\text{trunc}} = 0$ as the exact dense contraction fits exactly within the $V_{\max}$ bounds. The physical error $\epsilon_{\text{phys}}$ is mitigated via Zero-Noise Extrapolation (ZNE). Because KaHyPar natively partitions prior to hardware transpilation, heavy-hex SWAP routing is confined to the disjoint sub-clusters ($N_p \le 7$), keeping $\epsilon_{\text{trans}}$ marginal compared to monolithic execution."""
text = text.replace(eq4_old_target, eq4_old_replacement)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)
print("Applied audit 2!")
