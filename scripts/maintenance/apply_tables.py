import os

latex_path = "/home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex"
with open(latex_path, "r", encoding="utf-8") as f:
    text = f.read()

# TABLE I CHANGES
text = text.replace(r"\textbf{Resource Bound} & Unbounded $\mathcal{O}(6^K)$ & Bounded by $V_{\max}$ \\",
                    r"\textbf{Resource Bound} & Exponential $\mathcal{O}(6^K)$ overhead & Bounded by $V_{\max}$ \\")

text = text.replace(r"\textbf{Hardware Scaling} & Memory exhaustion & Flat temporal execution \\",
                    r"\textbf{Hardware Scaling} & Memory exhaustion & Bounded exponential runtime \\")

text = text.replace(r"\textbf{Target Topology} & Theoretical graphs & Simulated Heron topologies \\",
                    r"\textbf{Target Topology} & Abstract regular graphs & Simulated Heron topologies \\")

# TABLE II & TEXT CHANGES: \mathcal{O}(\chi^2 2^{tw}) -> \mathcal{O}(\chi^2 6^{tw})
text = text.replace(r"\mathcal{O}(\chi^2 2^{tw})", r"\mathcal{O}(\chi^2 6^{tw})")
text = text.replace(r"\mathcal{O}(2^{tw})", r"\mathcal{O}(6^{tw})")

# TABLE III & TEXT CHANGES: MaxCut (E-R p=0.3) -> MaxCut (SBM p_out=0.1)
text = text.replace(r"MaxCut (E-R $p=0.3$) & $10 - 26$ & Dense topology fragmentation. \\",
                    r"MaxCut (SBM $p_{out}=0.1$) & $10 - 26$ & Dense topology fragmentation. \\")

with open(latex_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Applied table updates successfully!")
