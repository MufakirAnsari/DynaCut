import os

latex_path = "/home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex"
with open(latex_path, "r", encoding="utf-8") as f:
    text = f.read()

# Fix M4: Misleading Memory Scaling
text = text.replace(r"\mathcal{O}(2^{N/P} \text{ floats})", r"\mathcal{O}(2^{N/P} \cdot 6^K \text{ floats})")

with open(latex_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Applied M4 fix successfully!")
