import logging
import time
from qiskit.transpiler.coupling import CouplingMap
from dynacut.adaptive_scheduler import ResourceHypervisor
from dynacut.executor import DynaCutExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vf2_test")

def main():
    logger.info("Testing VF2 layout embeddability...")
    
    topologies = {
        "Falcon (HeavyHex-3)": CouplingMap.from_heavy_hex(3),
        "Eagle (HeavyHex-5)": CouplingMap.from_heavy_hex(5),
        "Osprey (HeavyHex-7)": CouplingMap.from_heavy_hex(7)
    }
    
    # A simple linear circuit that should embed perfectly
    circuit_linear = DynaCutExecutor.build_ansatz(10, reps=1, entanglement="linear")
    
    # A complete graph circuit that won't embed
    from experiments.phase1_math_rigor import generate_maxcut_graph
    edges_complete = generate_maxcut_graph(10, edge_prob=1.0)
    circuit_complete = DynaCutExecutor.build_ansatz(10, reps=1, entanglement=edges_complete)
    
    for name, cmap in topologies.items():
        logger.info(f"--- Testing topology: {name} ---")
        hypervisor = ResourceHypervisor(max_vram_gb=4.0, max_qubits_per_fragment=14, coupling_map=cmap)
        
        res_linear = hypervisor.check_hardware_embeddability(circuit_linear)
        logger.info(f"10q Linear Circuit embeddable: {res_linear}")
        
        res_complete = hypervisor.check_hardware_embeddability(circuit_complete)
        logger.info(f"10q Complete Graph Circuit embeddable: {res_complete}")
    
    logger.info("Done VF2 testing!")

if __name__ == "__main__":
    main()
