# DynaCut → EPJ Quantum Technology: Submission Task List

> **Target**: EPJ Quantum Technology (Springer, Open Access)  
> **Estimated total effort**: 3–5 days  
> **APC**: ~€1690 / $1890 upon acceptance

---

## Phase 1: Fix Critical Inconsistencies (Day 1, ~4 hours)

These are the items that will cause **instant reviewer rejection** if left unfixed.

---

### Task 1.1: Resolve the KaHyPar vs KL Bisection Contradiction

**Problem**: The main paper text says "native KL bisection" everywhere, but three other locations say "KaHyPar."

**What a reviewer sees**: "The authors don't even know which algorithm they used."

**Files and exact locations to fix**:

- [ ] [tables.tex](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/tables.tex) **Line 50**: `Partitioner & KaHyPar` → change to `Partitioner & KL Bisection`
- [ ] [architecture.mmd](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/figures/architecture.mmd) **Line 8**: `KaHyPar Multi-level Hypergraph Partitioner` → change to `KL Bisection Hypergraph Partitioner`
- [ ] [scheduler.mmd](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/figures/scheduler.mmd) **Line 5**: `Can KaHyPar find cuts` → change to `Can KL Bisection find cuts`
- [ ] [DynaCut.tex](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex) **Line 5** in architecture.mmd caption reference: verify the rendered PDF of architecture.pdf and scheduler.pdf match after regenerating from the corrected .mmd files

**Decision you must make**: Did you actually use KaHyPar or your own KL bisection implementation? If you used KaHyPar under the hood, then flip the main text to say KaHyPar (and cite Schlag 2022 as you already do). If you wrote a native KL bisection, then fix the three files above. **Do not leave both.**

**Time**: 30 minutes (text edits) + 30 minutes (regenerate architecture.pdf and scheduler.pdf from corrected .mmd)

---

### Task 1.2: Fix the COBYLA vs SPSA Contradiction in tables.tex

**Problem**: [tables.tex](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/tables.tex) line 48 says `VQE Optimizer & COBYLA`, but the main paper uses SPSA throughout (line 439, 656, 670, etc.).

**Fix**:

- [ ] [tables.tex](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/tables.tex) **Line 48**: `VQE Optimizer & COBYLA` → `VQE Optimizer & SPSA`

**Additionally**: tables.tex has **empty data tables** (lines 20–28, 30–40 have `\hline \hline` with no data rows). Either:
- [ ] **Option A (Recommended)**: Delete tables.tex entirely if it's not `\input{}` anywhere in DynaCut.tex. Verify by searching for `\input{tables}` in the main file.
- [ ] **Option B**: Populate the tables with actual data or remove the empty ones.

**Time**: 15 minutes

---

### Task 1.3: Fix the KL Bisection Complexity Claim

**Problem**: [DynaCut.tex](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex) **Line 292** states:
> `$\mathcal{O}(|V| + |E|)$ time complexity due to the multi-level coarsening approach`

Standard KL bisection is **O(|V|² log|V|)** per pass. The O(|V|+|E|) claim is only defensible for a single coarsening pass in a multi-level scheme, not the full partitioning.

**Fix**: Change line 292 to one of:
- [ ] `$\mathcal{O}(|V|^2 \log |V|)$ time complexity per bisection pass, amortized via multi-level coarsening \cite{Heuer_2017}.`
- [ ] Or if you truly use multi-level coarsening: `$\mathcal{O}(|V| + |E|)$ amortized time complexity per coarsening level in the multi-level scheme \cite{Heuer_2017}, with $\mathcal{O}(\log P)$ levels for $P$ partitions.`

Also fix the same claim in [Table 3](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex#L357):
- [ ] **Line 357**: `$\mathcal{O}(|V|+|E|)$ / Minimize $K$` → `$\mathcal{O}(|V|^2 \log |V|)$ / Minimize $K$` (or the amortized version)

**Time**: 15 minutes

---

### Task 1.4: Reframe Theorems as Known Results

**Problem**: Theorem 1 (sampling variance inflation) restates Piveteau 2024. Theorem 2 (ZNE+QPD variance) composes two known bounds. Lemma 1 is standard TN contraction theory. A knowledgeable reviewer will flag these as novelty inflation.

**Fix** — change the framing, not the content:

- [ ] [DynaCut.tex](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex) **Line 188**: Change `\textbf{Theorem 1 (Sampling Variance Inflation).}` → `\textbf{Proposition 1 (Sampling Variance Inflation, cf.~\cite{Piveteau_2024}).}` and add after the statement: `This result follows directly from the QPD framework established in \cite{Piveteau_2024}; we restate it here for completeness and to establish notation.`

- [ ] [DynaCut.tex](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex) **Line 217**: Change `\textbf{Theorem 2 (ZNE-Amplified QPD Variance Bound).}` → `\textbf{Proposition 2 (ZNE-Amplified QPD Variance Bound).}` and add: `This bound follows from composing the standard Richardson extrapolation variance (cf.~Temme et al., 2017) with the QPD overhead from Proposition~1.`

- [ ] [DynaCut.tex](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex) **Line 204**: Change `\textbf{Lemma 1` → `\textbf{Lemma 1 (Standard TN contraction bound, cf.~\cite{Schollw_ck_2011})`

- [ ] Update Appendix headers accordingly:
  - **Line 950**: `Proof of Theorem 1` → `Proof of Proposition 1`
  - **Line 941**: `Proof of Lemma 1` → keep as is (lemma is fine)

**Time**: 30 minutes

---

### Task 1.5: Temper Overstated Claims

**Problem**: Several claims go beyond what the evidence supports. EPJ QT reviewers will be applied-quantum-computing experts who will catch these.

**Specific lines to soften**:

- [ ] **Line 82 (Abstract)**: `"successfully establishes a scalable, bounded-error paradigm for distributing highly entangled quantum workloads"` → `"establishes a bounded-error framework for distributing moderately entangled quantum workloads on sparse topologies"`

- [ ] **Line 107**: `"ensuring that the exponential advantages of quantum ansatz topologies can be exploited long before the realization of large-scale fault-tolerant quantum computers"` → `"providing a practical pathway for exploiting quantum ansatz topologies on near-term hardware with sparse connectivity"`

- [ ] **Line 653**: `"establishing a new framework for hybrid quantum-classical condensed matter simulation"` → `"suggesting a potential framework for hybrid quantum-classical condensed matter simulation on sparse systems"`

- [ ] **Line 920**: `"Condensed matter physicists can now smoothly tune..."` → `"Condensed matter physicists may, in principle, tune..."`

- [ ] **Line 924**: `"DynaCut demonstrates that the boundary of classically intractable quantum simulation is not an absolute hardware wall"` → add qualifier: `"For sparse topologies where $K \le 2$, DynaCut demonstrates..."`

**Time**: 30 minutes

---

## Phase 2: Add Classical MaxCut Baseline (Day 1–2, ~8 hours)

This is the single most impactful new experiment. It contextualizes your results for EPJ QT reviewers.

---

### Task 2.1: Implement Goemans-Williamson SDP Baseline

**What**: Run the Goemans-Williamson 0.878-approximation SDP relaxation on every graph instance you already tested.

**Why**: Without this, a reviewer asks: "Why use a noisy quantum computer at all? Can classical algorithms solve these MaxCut instances better?"

**Implementation steps**:

- [ ] Install `cvxpy` (SDP solver) in your environment: `pip install cvxpy`
- [ ] Write a script `gw_baseline.py` that:
  1. Loads each of your saved graph instances (the same JSON adjacency matrices from your benchmarks)
  2. Solves the GW SDP relaxation for MaxCut
  3. Performs randomized rounding (100 rounds) to get the best cut value
  4. Records: best cut value, approximation ratio (cut/optimal), wall-clock time
  5. Saves results to JSON
- [ ] Run on all graph sizes: N = 10, 14, 18, 22, 26
- [ ] Run on all topologies: 1D chain, 3-regular, SBM (p_out=0.1)
- [ ] Average over the same 10 random seeds/graph instances you already use

**Expected time**: 4–5 hours (implementation + runs)

---

### Task 2.2: Implement Simulated Annealing Baseline

**What**: A classical metaheuristic that is the standard industrial MaxCut solver.

**Implementation steps**:

- [ ] Write `sa_baseline.py`:
  1. Standard SA with geometric cooling schedule
  2. T_init = 10, T_final = 0.001, cooling rate = 0.995
  3. 10,000 iterations per run
  4. Record: best cut value, approximation ratio, wall-clock time
  5. Average over 10 runs per graph
- [ ] Run on same graph instances as GW

**Expected time**: 2 hours

---

### Task 2.3: Create the Approximation Ratio Comparison Table

**What**: Add a new table to DynaCut.tex showing how DynaCut's solution quality compares.

**Table format**:

```latex
\begin{table}[h!]
\centering
\caption{MaxCut Approximation Ratio Comparison: DynaCut vs.\ Classical Solvers on 3-Regular SBM Graphs ($p_{out}=0.1$, averaged over 10 instances).}
\label{tab:classical_comparison}
\resizebox{\linewidth}{!}{%
\begin{tabular}{l|ccc|ccc}
\toprule
\textbf{Method} & \multicolumn{3}{c|}{\textbf{Approx. Ratio ($C/C^*$)}} & \multicolumn{3}{c}{\textbf{Wall-Clock Time (s)}} \\
\cmidrule(lr){2-4} \cmidrule(lr){5-7}
 & $N=10$ & $N=14$ & $N=26$ & $N=10$ & $N=14$ & $N=26$ \\
\midrule
Exact (Brute Force) & 1.000 & 1.000 & --- & 0.01 & 0.5 & OOM \\
GW (SDP + Rounding) & & & & & & \\
Simulated Annealing & & & & & & \\
DynaCut (Noisy, ZNE) & & & & & & \\
\bottomrule
\end{tabular}%
}
\end{table}
```

**Where to insert**: After the existing baseline comparison (after line 511), or in the Discussion section (after line 749).

- [ ] Generate the data
- [ ] Fill in the table
- [ ] Add 2–3 sentences interpreting the results

**Important**: Be honest. If GW or SA achieves better approximation ratios (which they likely will at N=26 given the QPD noise), say so explicitly and frame DynaCut's value as *memory-bounded quantum simulation* rather than *MaxCut solving*.

**Expected time**: 1–2 hours (table creation + interpretation paragraph)

---

## Phase 3: Minor Content Improvements (Day 2, ~3 hours)

These are not blockers but significantly strengthen the paper for EPJ QT.

---

### Task 3.1: Add the Missing "Data Availability" and "Author Contributions" Sections

**Problem**: EPJ QT (Springer) requires these declarations. Your current paper only has Acknowledgments.

**Fix**: Add after the Acknowledgments section (after line 985):

- [ ] Add the following sections before `\bibliography`:

```latex
\section*{Availability of data and materials}
The datasets generated and analysed during the current study, along with the
full orchestration pipeline, are available in the DynaCut GitHub repository:
\url{https://github.com/MufakirAnsari/DynaCut}.

\section*{Competing interests}
The authors declare that they have no competing interests.

\section*{Funding}
[State your funding source, or "This research received no specific grant
from any funding agency."]

\section*{Authors' contributions}
MQA designed and implemented the DynaCut framework, conducted all experiments,
and wrote the manuscript. MQA (Mudabir) contributed to [specify contribution].
All authors read and approved the final manuscript.
```

**Time**: 20 minutes

---

### Task 3.2: Add Keywords

**Problem**: EPJ QT requires keywords. Your paper has the `\keywords` line commented out (line 85).

- [ ] Uncomment and add keywords on **line 85–86**:

```latex
\keywords{circuit knitting, quasiprobability decomposition, tensor networks,
variational quantum algorithms, resource-aware compilation, NISQ}
```

**Time**: 5 minutes

---

### Task 3.3: Convert from REVTeX to Springer LaTeX Template

**Problem**: Your paper uses `revtex4-2` (APS format). EPJ QT uses the Springer Nature LaTeX template.

**Steps**:

- [ ] Download the Springer Nature LaTeX template from https://www.springernature.com/gp/authors/campaigns/latex-author-support
- [ ] Change the document class (line 21–41): Replace `\documentclass[...]{revtex4-2}` with `\documentclass[smallextended]{svjour3}` and add `\usepackage{svmult}` or the appropriate Springer package
- [ ] Replace `\colrule` and `\botrule` with `\midrule` and `\bottomrule` (you already use booktabs in some tables, but REVTeX defines its own rules)
- [ ] Move the abstract from `\begin{abstract}...\end{abstract}` to the Springer format
- [ ] Update bibliography style from APS to Springer's numbered style: change `\bibliography{apssamp}` to include `\bibliographystyle{sn-basic}` (or `sn-mathphys`)
- [ ] Remove REVTeX-specific commands: `\preprint{APS/123-QED}` (line 65), `\thanks{}` (line 71)
- [ ] Adjust `\affiliation` to Springer's `\institute` syntax

> [!IMPORTANT]
> **Alternative**: EPJ QT also accepts manuscripts in any reasonable LaTeX format for initial submission, converting to their template only upon acceptance. If time is short, **submit in REVTeX format first** and convert only if accepted. This is common practice. But remove the `\preprint{APS/123-QED}` line regardless.

- [ ] At minimum: remove line 65 (`\preprint{APS/123-QED}`)

**Time**: 2 hours if full conversion; 5 minutes if minimal cleanup

---

### Task 3.4: Verify the GitHub Repository is Public and Complete

**Problem**: You cite `https://github.com/MufakirAnsari/DynaCut` for reproducibility. If a reviewer clicks it and sees a 404 or empty repo, it's an instant red flag.

- [ ] Verify the repo is **public**
- [ ] Verify it contains:
  - [ ] All source code for DynaCut (partitioner, TN knitter, QPD generator, scheduler)
  - [ ] All benchmark scripts
  - [ ] All JSON experimental result datasets
  - [ ] The FakeHeronV2 noise profiles
  - [ ] A `README.md` with clear setup instructions
  - [ ] A `requirements.txt` or `environment.yml` with pinned dependency versions
  - [ ] The graph adjacency matrices for all tested instances
- [ ] Add the **GW and SA baseline scripts** (from Phase 2) to the repo
- [ ] Add a `LICENSE` file (MIT or Apache 2.0 recommended)

**Time**: 1–2 hours (verification + any missing files)

---

## Phase 4: Small but Important Text Fixes (Day 2, ~1.5 hours)

---

### Task 4.1: Add a "Simulator Limitation" Paragraph

**Why**: EPJ QT reviewers will note the absence of real hardware. Pre-empt this by honestly addressing it.

- [ ] Add to Section 7.6 (Limitations, line 872), a new bullet:

```latex
\item \textbf{Simulator-Only Validation:} All experiments in this work are
conducted on the Qiskit \texttt{AerSimulator} with empirical noise models
derived from IBM's calibration data. While these noise models capture the
dominant error channels (depolarizing, thermal relaxation, readout), they
do not fully reproduce device-specific phenomena such as spatially correlated
crosstalk, leakage to non-computational states, and temporal drift. Validation
on physical quantum hardware remains an important direction for future work.
```

**Time**: 10 minutes

---

### Task 4.2: Fix the Warm-Start Provenance

**Why**: Reviewers will ask: "Where did the warm-start parameters come from?" If from exact simulation, that's information leakage.

- [ ] Add explicit documentation in Section 5.5 (Hyperparameters, line 439) or Section 6.6 (Convergence Paths, line 656):

```latex
Warm-start parameters were obtained via a preliminary noiseless
statevector optimization (COBYLA, 50 iterations) on the identical
graph instance, providing an approximate initial point to isolate
noise-induced plateau effects from expressibility limitations.
This warm-starting protocol does not constitute information leakage
for the purposes of our analysis, as our objective is to evaluate
whether the DynaCut estimator preserves the VQA optimization
landscape---not to demonstrate ab initio convergence from random
initialization (which is separately evaluated in the cold-start
ablation of Section~\ref{subsubsec:cold_start}).
```

**Time**: 15 minutes

---

### Task 4.3: Add Missing Temme (2017) and Spall (1998) References

**Why**: You reframe Theorem 2 as building on Temme's ZNE work and use SPSA throughout, but neither the original ZNE nor SPSA papers are in your bibliography.

- [ ] Add to [apssamp.bib](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/apssamp.bib):

```bibtex
@article{Temme_2017,
  title={Error Mitigation for Short-Depth Quantum Circuits},
  author={Temme, Kristan and Bravyi, Sergey and Gambetta, Jay M.},
  journal={Physical Review Letters},
  volume={119},
  pages={180509},
  year={2017},
  publisher={APS}
}

@article{Spall_1998,
  title={Implementation of the simultaneous perturbation algorithm
         for stochastic optimization},
  author={Spall, James C.},
  journal={IEEE Transactions on Aerospace and Electronic Systems},
  volume={34},
  number={3},
  pages={817--823},
  year={1998},
  publisher={IEEE}
}
```

- [ ] Cite `\cite{Temme_2017}` in the reframed Proposition 2 and ZNE discussions
- [ ] Cite `\cite{Spall_1998}` where SPSA is first introduced (line 439)

**Time**: 15 minutes

---

### Task 4.4: Clarify the K vs tw Inconsistency

**Problem**: Equation 9 (line 288) uses K (cut count) in the constraint $O(\chi^2 6^K) \le V_{\max}$, but Section 3.3 (line 202) correctly distinguishes between K and tw (tree-width). For a simple bipartition K = tw, but not in general.

- [ ] Add a clarifying sentence after Equation 9 (line 289):

```latex
For the bipartite and hierarchical multi-partitions considered in this work,
the tree-width $tw$ of the resulting contraction graph is at most $K$
(the total number of severed hyperedges), as each partition boundary
introduces at most one additional bond index. Thus, the constraint
$\mathcal{O}(\chi^2 6^K) \le V_{\max}$ provides a conservative upper
bound on the reconstruction memory.
```

**Time**: 10 minutes

---

### Task 4.5: Fix the "Quantum Phase Decomposition" Typo

**Problem**: Line 339 says "Quantum Phase Decomposition" — should be "Quasiprobability Decomposition."

- [ ] **Line 339**: `Quantum Phase Decomposition` → `Quasiprobability Decomposition`

**Time**: 2 minutes

---

## Phase 5: Pre-Submission Checklist (Day 3, ~2 hours)

---

### Task 5.1: Compile and Verify

- [ ] Full LaTeX compile with no errors or warnings
- [ ] All figures render correctly (especially regenerated architecture.pdf, scheduler.pdf)
- [ ] All internal references (`\ref{}`, `\cite{}`) resolve
- [ ] No orphan references in bibliography (run `bibtex` and check for undefined citations)
- [ ] No duplicate figure/table labels
- [ ] Page count is within EPJ QT norms (typically 15–25 pages for a full article)

**Time**: 30 minutes

---

### Task 5.2: Figure Quality Check

EPJ QT requires high-resolution figures (typically 300 DPI for raster, vector preferred).

- [ ] Verify all `.pdf` figures are vector format (they should be since they're generated programmatically)
- [ ] The two `.png` files ([circuit_diagram_uncut.png](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/figures/circuit_diagram_uncut.png), [circuit_diagram_cut.png](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/figures/circuit_diagram_cut.png), [vqe_cold_start.png](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/figures/vqe_cold_start.png), [partitioner_ablation.png](file:///home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/figures/partitioner_ablation.png)): verify resolution ≥ 300 DPI
- [ ] If any PNGs are low-res, regenerate as PDF vector plots

**Time**: 30 minutes

---

### Task 5.3: Write the Cover Letter

- [ ] Draft a cover letter addressing:
  1. Brief summary of the work (2–3 sentences)
  2. Why EPJ QT is the right venue: "applied quantum computing framework for NISQ circuit knitting"
  3. Statement of novelty: "closed-loop resource-aware scheduling for QPD"
  4. Confirmation: no simultaneous submission, all authors approved
  5. Suggested reviewers (2–3 names from the circuit knitting / TN simulation community)

**Time**: 30 minutes

---

### Task 5.4: Final Proofread of Changed Sections

- [ ] Re-read all modified paragraphs for consistency
- [ ] Search the entire document for remaining instances of "KaHyPar" (should be 0 or consistent)
- [ ] Search for "COBYLA" — should only appear in the optimizer comparison section, not as the default optimizer
- [ ] Search for "Theorem" — should now say "Proposition" where changed
- [ ] Verify all new citations (Temme_2017, Spall_1998) compile correctly

**Time**: 30 minutes

---

## Summary: Complete Task Order

| Day | Phase | Tasks | Total Time |
|-----|-------|-------|------------|
| **Day 1 AM** | Phase 1 | Fix all inconsistencies (1.1–1.5) | ~4 hours |
| **Day 1 PM** | Phase 2 | Implement GW baseline (2.1) | ~4 hours |
| **Day 2 AM** | Phase 2 | Implement SA baseline (2.2), create table (2.3) | ~3 hours |
| **Day 2 PM** | Phase 3 | Add declarations, keywords, verify repo (3.1–3.4) | ~3 hours |
| **Day 2 PM** | Phase 4 | Text fixes (4.1–4.5) | ~1 hour |
| **Day 3** | Phase 5 | Compile, figures, cover letter, proofread (5.1–5.4) | ~2 hours |
| | | **Total** | **~17 hours** |

> [!TIP]
> **If you only have 1 day**: Do Phase 1 (inconsistency fixes) + Task 3.1 (declarations) + Task 4.5 (typo) + Phase 5 (compile/submit). Skip the classical baseline — it strengthens the paper significantly but EPJ QT may accept without it given your existing baselines (Exact Statevector, CutQC, MPS/DMRG).
