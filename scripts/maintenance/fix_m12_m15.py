import re

file_path = "/home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

new_abstract = "Simulating combinatorial landscapes via Variational Quantum Algorithms (VQAs) is constrained by the memory footprint of classical simulation and the finite coherence of Noisy Intermediate-Scale Quantum (NISQ) devices. Quasiprobability Decomposition (QPD) can partition physical qubit interactions to execute deep circuits across smaller processors. However, existing static partitioning triggers a large $\\mathcal{O}(6^K)$ compilation overhead, bottlenecking scalability. We introduce DynaCut, a resource-aware scheduler that couples quantum circuit partitioning with strict classical hardware boundaries. By modeling parameterized ansätze as weighted hypergraphs, DynaCut leverages multi-level partitioning to minimize severed cross-boundary entanglement while enforcing limits on partition dimensions. To circumvent the reconstruction overhead, the framework toggles between exact tensor network contraction and approximate Singular Value Decomposition (SVD) truncation. We validate this methodology via 26-qubit noisy simulations parameterized by IBM Heron profiles. By bounding the cut dimension based on available classical RAM, DynaCut mitigates the circuit explosion. For sparse graphs, we strictly bound the peak classical memory footprint of single TN reconstructions below 256 MB. When memory limits are saturated on dense graphs, DynaCut transitions to a bounded-error SVD approximation. By mapping classical compilation limits onto physical NISQ constraints, DynaCut establishes a scalable paradigm for executing circuits approaching the limits of classical simulatability."

# Safe regex replace using lambda
text = re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}', lambda m: '\\begin{abstract}\n' + new_abstract + '\n\\end{abstract}', text, flags=re.DOTALL)

# m13: hyperbolic
text = text.replace("profound scaling bottleneck", "significant scaling bottleneck")
text = text.replace("profound scientific insight", "significant scientific insight")
text = text.replace("unassailable", "robust") # just in case

# m14: define \chi
text = text.replace(r"To survive the $\mathcal{O}(\chi^2 2^{tw})$ reconstruction penalty, the system dynamically toggles",
                    r"To survive the $\mathcal{O}(\chi^2 2^{tw})$ reconstruction penalty (where $\chi$ is the tensor network bond dimension), the system dynamically toggles")
text = text.replace("This ties the hypergraph edge-cut capacity directly to the tensor network bond dimension via rigorous",
                    "This ties the hypergraph edge-cut capacity directly to this bond dimension via rigorous")


# m15: hypervisor -> scheduler
text = text.replace("hypervisor", "scheduler")
text = text.replace("Hypervisor", "Scheduler")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)
print("Replacements done.")
