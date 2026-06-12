import re

file_path = "/home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Preamble: Add algorithm and algpseudocode
preamble_target = r"\usepackage{bm}% bold math"
preamble_replacement = r"\usepackage{bm}% bold math" + "\n" + r"\usepackage{algorithm}" + "\n" + r"\usepackage{algpseudocode}"
text = text.replace(preamble_target, preamble_replacement)

# Eq 1
eq1_target = r"""To circumvent the $N$-qubit physical constraint, we employ Quasiprobability Decomposition (QPD). A non-local two-qubit gate (e.g., CNOT) acting across a partition boundary is decomposed into a linear combination of local tensor-product operations:
\begin{equation}
    \mathcal{U}_{\text{CX}}(\rho) = \sum_{i=1}^6 c_i \mathcal{E}_{A,i} \otimes \mathcal{E}_{B,i} (\rho)
\end{equation}
where $c_i \in \mathbb{R}$ and $\sum |c_i| = \gamma$, with $\gamma$ representing the sampling overhead."""
eq1_replacement = r"""To circumvent the $N$-qubit physical constraint, we employ Quasiprobability Decomposition (QPD). A non-local two-qubit gate (e.g., CNOT) acting across a partition boundary is decomposed into an optimal linear combination of 6 local tensor-product operations:
\begin{equation}
    \mathcal{U}_{\text{CX}}(\rho) = \sum_{i=1}^6 c_i \mathcal{E}_{A,i} \otimes \mathcal{E}_{B,i} (\rho)
\end{equation}
where $c_i \in \{\pm 1/2, \pm 1\}$ such that the total sampling overhead $\gamma = \sum_{i=1}^6 |c_i| = 3$. Because each local basis channel $\mathcal{E}_{A,i}$ and $\mathcal{E}_{B,i}$ is constructed from completely positive trace-preserving (CPTP) maps (such as Pauli projections and rotations), the overall decomposition remains physically valid and trace-preserving within the density matrix formalism."""
text = text.replace(eq1_target, eq1_replacement)

# Alg 1
# Insert right before \subsubsection{KaHyPar Partitioning Engine}
alg_insert_target = r"\subsubsection{KaHyPar Partitioning Engine}"
alg_replacement = r"""
\begin{algorithm}[H]
\caption{Hypergraph Weight Generation}
\label{alg:weight_gen}
\begin{algorithmic}[1]
\Require Parameterized quantum circuit $U(\vec{\theta})$
\Ensure Weighted hypergraph $H_G = (V, E, \omega_V, \omega_E)$
\State $V \gets$ Initialize vertex set from qubits
\State $E \gets \emptyset$
\For{each gate $g \in U(\vec{\theta})$}
    \If{$g$ is single-qubit on $q_j$}
        \State $\omega_V(q_j) \gets \omega_V(q_j) + \text{duration}(g)$
    \ElsIf{$g$ is multi-qubit on $\{q_m, q_n\}$}
        \State $e \gets \{q_m, q_n\}$
        \State $E \gets E \cup \{e\}$
        \State $\omega_E(e) \gets \log_2(\gamma_g)$ \Comment{Multiplicative QPD penalty $\gamma_g$}
    \EndIf
\EndFor
\State \Return $H_G$
\end{algorithmic}
\end{algorithm}

\subsubsection{KaHyPar Partitioning Engine}"""
text = text.replace(alg_insert_target, alg_replacement)

# Eq 2/3
eq23_target = r"""\textbf{Mathematical Formulation:} The partitioner minimizes the objective function $\min \sum_{e \in E_{\text{cut}}} \omega(e)$, subject to the constraint $\log_2(V_{\text{frag}}) + K \log_2(6) \le \log_2(V_{\max})$, where $V_{\text{frag}}$ is the statevector size of the largest partition."""
eq23_replacement = r"""\textbf{Mathematical Formulation:} The partitioner is driven to minimize the sum of severed hyperedge weights (detailed in Algorithm~\ref{alg:weight_gen}):
\begin{equation}
    \min \sum_{e \in E_{\text{cut}}} \omega(e) = \min \sum_{e \in E_{\text{cut}}} \log_2(\gamma_e)
\end{equation}
which strictly minimizes the multiplicative QPD sampling overhead $\Gamma = \prod_{e \in E_{\text{cut}}} \gamma_e$. The classical memory threshold is explicitly enforced via the KaHyPar node-weight imbalance parameter, formalizing the memory penalty constraint:
\begin{equation}
    \mathcal{O}\left(\chi^2 6^K\right) \le V_{\max}
\end{equation}
ensuring the resulting tensor network contraction never exhausts classical compilation limits."""
text = text.replace(eq23_target, eq23_replacement)

# Eq 4
# I need to match carefully because it might have standard Schollwock cite
eq4_target = r"""\textbf{Truncation Error Bound:} When the classical memory threshold $V_{\max}$ forces SVD truncation, the framework formally transitions from exact reconstruction to a bounded-error approximation. Let $\lambda_i$ denote the singular values corresponding to the severed correlation cut. According to standard tensor network theory \cite{Schollwock2011}, the truncation error is formally bounded by the Frobenius norm of the discarded spectrum, defined as $\epsilon_{SVD} = \sqrt{\sum_{i > \chi_{\max}} \lambda_i^2}$. Because QPD basis tensors are quasi-probabilities rather than strictly positive distributions, the resulting error in the global expectation value must be amplified by the 1-norm of the network ($\Gamma$), rigorously bounding it by (see Appendix~\ref{app:eq5} for complete derivation):
\begin{equation}
    |\Delta \langle H \rangle| \le \Gamma \|H\| \cdot \epsilon_{SVD}
\end{equation}"""
# Wait, Schollwock is sometimes \cite{Schollw_ck_2011}. I will use regex or string replace for exactly what is there.
text = re.sub(
    r"\\textbf\{Truncation Error Bound:\}.*?\\end\{equation\}",
    r"""\\textbf{Truncation Error Bound:} When the classical memory threshold $V_{\\max}$ forces SVD truncation, the framework formally transitions from exact reconstruction to a bounded-error approximation. Let $\\lambda_i$ denote the singular values corresponding to the severed correlation cut. According to standard tensor network theory \\cite{Schollw_ck_2011}, the truncation error is strictly defined by the Schatten 2-norm (Frobenius norm) of the discarded spectrum:
\\begin{equation}
    \\epsilon_{SVD} = \\sqrt{\\sum_{i > \\chi_{\\max}} \\lambda_i^2}
\\end{equation}
We explicitly utilize the Schatten 2-norm over the looser spectral norm (Schatten $\\infty$-norm), as it provides a tighter expected bound on the average correlation error across the full probability distribution. Because QPD basis tensors are quasi-probabilities rather than strictly positive distributions, the resulting error in the global expectation value must be amplified by the 1-norm of the network ($\\Gamma$), rigorously bounding it by (see Appendix~\\ref{app:eq5} for complete derivation):
\\begin{equation}
    |\\Delta \\langle H \\rangle| \\le \\Gamma \\|H\\| \\cdot \\epsilon_{SVD}
\\end{equation}""",
    text, flags=re.DOTALL
)

# Eq 5/6
eq56_target = r"""The algorithmic complexity scales as:
\begin{itemize}
    \item \textbf{Classical Memory:} $\mathcal{O}(2^{N/P} \text{ floats})$.
    \item \textbf{Quantum Time:} $\mathcal{O}(\frac{\Gamma^2}{\epsilon^2} \cdot \max(D_A, D_B))$ circuit executions.
\end{itemize}
This mapping conclusively proves that memory-constrained QPD reduces exponential classical space complexity to bounded classical compilation overhead and a quantum execution time that scales exponentially only with the bounded cut count $K$, rather than the total system size $N$."""
eq56_replacement = r"""The algorithmic execution scales according to two distinct computational bounds. The classical tensor network reconstruction memory $M_{TN}$ scales exponentially with the contraction tree-width $tw$:
\begin{equation}
    M_{TN} = \mathcal{O}(\chi^2 2^{tw})
\end{equation}
Conversely, the quantum sampling overhead required to resolve the QPD variance scales independently with the cut parameter $K$:
\begin{equation}
    S \ge \mathcal{O}\left( \frac{\Gamma^2}{\epsilon^2} \|H\|^2 \right) \sim \mathcal{O}(9^K)
\end{equation}
Extracting these into formal equations explicitly delineates the quantum execution bottleneck ($K$) from the classical reconstruction bottleneck ($tw$). This mapping conclusively proves that memory-constrained QPD reduces exponential classical space complexity to bounded classical compilation overhead, shifting the exponential burden purely to a quantum execution time that scales only with the bounded cut count $K$, rather than the total system size $N$."""
text = text.replace(eq56_target, eq56_replacement)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)
print("Applied equation audit!")
