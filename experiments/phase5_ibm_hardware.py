"""
Phase 5: Real IBM Quantum Hardware Execution.

This script demonstrates submitting the memory-constrained QPD partitioned
fragments to a real superconducting IBM Quantum backend using Qiskit Runtime.
"""

from __future__ import annotations

import logging
import os
import sys

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("phase5")

from dynacut.executor import DynaCutExecutor, maxcut_hamiltonian
from dynacut.adaptive_scheduler import ResourceHypervisor
from experiments.phase1_math_rigor import generate_maxcut_graph


def run_hardware(num_qubits: int = 14):
    """Execute cut circuit on real hardware."""
    logger.info("=" * 70)
    logger.info("PHASE 5: IBM Quantum Hardware Execution")
    logger.info("=" * 70)

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    except ImportError:
        logger.error("qiskit-ibm-runtime is not installed. Please run: pip install qiskit-ibm-runtime")
        return False

    # 1. Authenticate with IBM Quantum
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if not token:
        logger.warning("No IBM_QUANTUM_TOKEN environment variable found. Checking saved accounts...")
        try:
            service = QiskitRuntimeService()
        except Exception as e:
            logger.error("Could not authenticate. Please set IBM_QUANTUM_TOKEN or save your account.")
            return False
    else:
        service = QiskitRuntimeService(channel="ibm_quantum", token=token)

    # 2. Select Least Busy Backend
    backend = service.least_busy(simulator=False, operational=True, min_num_qubits=10)
    logger.info("Selected backend: %s (Queue: %s)", backend.name, backend.status().pending_jobs)

    # 3. Setup Hardware Sampler
    sampler = SamplerV2(backend)
    # Note: For cutting, mid-circuit measurements and resets are heavily used.
    # We must ensure the backend supports dynamic circuits.
    
    # 4. Setup Problem
    edges = generate_maxcut_graph(num_qubits, edge_prob=0.3, seed=42)
    hamiltonian = maxcut_hamiltonian(edges, num_qubits)
    ansatz = DynaCutExecutor.build_ansatz(num_qubits, reps=1)
    
    hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_ram_gb=23.0, max_qubits_per_fragment=8)
    executor = DynaCutExecutor(hypervisor, sampler=sampler)
    
    strategy = hypervisor.find_optimal_strategy(ansatz)
    logger.info("Strategy: %s", strategy)
    
    np.random.seed(42)
    params = np.random.uniform(0, 0.1, size=ansatz.num_parameters)

    # 5. Execute 
    logger.info("Submitting QPD sub-experiments to %s. This may take a while depending on queue time...", backend.name)
    try:
        # Request 1024 shots per sub-experiment
        energy = executor.evaluate_energy(params, ansatz, hamiltonian, strategy, num_samples=1024)
        logger.info("✅ PASS: Successfully evaluated on hardware. Reconstructed Energy: %.6f", energy)
        return True
    except Exception as e:
        logger.error("Hardware execution failed: %s", e)
        return False


if __name__ == "__main__":
    success = run_hardware()
    sys.exit(0 if success else 1)
