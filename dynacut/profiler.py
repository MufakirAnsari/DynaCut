import tracemalloc
import time

def measure_peak_memory(func, *args, **kwargs):
    tracemalloc.start()
    start_time = time.time()
    
    try:
        result = func(*args, **kwargs)
    except Exception as e:
        tracemalloc.stop()
        raise e
        
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Peak memory in MB
    peak_mb = peak / 1024 / 1024
    
    return result, peak_mb, (end_time - start_time)

def exact_statevector_vram_mb(num_qubits):
    """
    Returns the exact theoretical VRAM footprint of a statevector 
    in MB assuming complex128 (16 bytes per amplitude).
    """
    bytes_needed = (2 ** num_qubits) * 16
    return bytes_needed / 1024 / 1024
