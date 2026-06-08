from setuptools import setup, find_packages

setup(
    name="dynacut",
    version="0.1.0",
    description="SOTA Hybrid Tensor-Network Quantum Circuit Knitting Framework",
    packages=find_packages(),
    install_requires=[
        "qiskit>=1.0.0",
        "qiskit-aer>=0.14.0",
        "qiskit-addon-cutting>=0.7.0",
        "quimb>=1.8.2",
        "opt-einsum>=3.3.0",
        "networkx>=3.0",
        "numpy",
        "scipy",
        "matplotlib"
    ],
    python_requires=">=3.9",
)
