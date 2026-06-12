import os

latex_path = "/home/ansari/Desktop/Papers/Quantum/Dy-Part-V2/paper/DynaCut.tex"
with open(latex_path, "r", encoding="utf-8") as f:
    text = f.read()

# Fix Figure 2 inconsistency: text says Ry/CNOT, image shows Rx/Rz/CNOT
target = r"VQE employs 2 layers of interleaved $R_y(\theta)$ and CNOT entangling gates."
replace = r"VQE employs 2 layers of interleaved parameterized single-qubit rotations ($R_x(\theta), R_z(\theta)$) and CNOT entangling gates."
text = text.replace(target, replace)

with open(latex_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Applied M_Fig2 fix successfully!")
