import os

latex_path = "/home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex"
with open(latex_path, "r", encoding="utf-8") as f:
    text = f.read()

abstract_original = r"""\begin{abstract}
Simulating combinatorial landscapes via Variational Quantum Algorithms (VQAs) is constrained by the memory footprint of classical simulation and the finite coherence of Noisy Intermediate-Scale Quantum (NISQ) devices. Quasiprobability Decomposition (QPD) can partition physical qubit interactions to execute deep circuits across smaller processors. However, existing static partitioning triggers a large $\mathcal{O}(6^K)$ compilation overhead, bottlenecking scalability. We introduce DynaCut, a resource-aware scheduler that couples quantum circuit partitioning with strict classical hardware boundaries. By modeling parameterized ansätze as weighted hypergraphs, DynaCut leverages multi-level partitioning to minimize severed cross-boundary entanglement while enforcing limits on partition dimensions. To circumvent the reconstruction overhead, the framework toggles between exact tensor network contraction and approximate Singular Value Decomposition (SVD) truncation. We validate this methodology via 26-qubit noisy simulations parameterized by IBM Heron profiles. By bounding the cut dimension based on available classical RAM, DynaCut mitigates the circuit explosion. For sparse graphs, we strictly bound the peak classical memory footprint of single TN reconstructions below 256 MB. When memory limits are saturated on dense graphs, DynaCut transitions to a bounded-error SVD approximation. By mapping classical compilation limits onto physical NISQ constraints, DynaCut establishes a scalable paradigm for executing circuits approaching the limits of classical simulatability.
\end{abstract}"""

abstract_new = r"""\begin{abstract}
Simulating combinatorial landscapes and many-body systems via Variational Quantum Algorithms is constrained by the memory limits of classical simulators and the finite coherence of near-term quantum devices. Quasiprobability Decomposition (QPD) can partition physical qubit interactions to execute deep circuits across disjoint processors. However, existing static partitioning triggers an exponential $\mathcal{O}(6^K)$ execution overhead, rapidly saturating physical shot quotas. We introduce DynaCut, a resource-aware scheduler that dynamically couples quantum circuit partitioning with classical memory and execution boundaries. By modeling parameterized ans\"{a}tze as weighted hypergraphs, DynaCut leverages multi-level partitioning to minimize severed cross-boundary entanglement. To circumvent the resulting exponential post-processing bottleneck, the framework routes QPD basis distributions through a tensor network knitter, toggling between exact dense contraction and bounded-error Singular Value Decomposition (SVD) truncation. Validated via 26-qubit noisy physical simulations, DynaCut successfully maintains classical memory footprints below strict 256 MB bounds on sparse 1D hardware-native topologies. By mapping classical tensor network bounds directly onto physical quantum sampling constraints, DynaCut establishes a scalable paradigm for memory-constrained distributed quantum execution.
\end{abstract}"""

text = text.replace(abstract_original, abstract_new)

with open(latex_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Applied M12 fix successfully!")
