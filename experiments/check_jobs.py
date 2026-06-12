import os
from qiskit_ibm_runtime import QiskitRuntimeService

token = os.environ.get("IBMQ_TOKEN")

try:
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    print("Successfully connected to IBM Quantum.")
    
    # Fetch the most recent job
    jobs = service.jobs(limit=1)
    if not jobs:
        print("No jobs found in your IBM Quantum account.")
    else:
        job = jobs[0]
        print(f"Latest Job ID: {job.job_id()}")
        print(f"Status: {job.status()}")
        print(f"Backend: {job.backend().name}")
        print(f"Creation Date: {job.creation_date}")
        print(f"Time in queue: {job.metrics().get('usage', {}).get('quantum_seconds', 'Unknown')} seconds (QPU time)")
        
        if job.status() == "DONE":
            print("Job completed successfully! Results are saved on IBM's servers.")
        elif job.status() in ["QUEUED", "RUNNING"]:
            print("Job is still in progress on IBM's servers.")
        elif job.status() == "ERROR":
            print(f"Job failed with error: {job.error_message()}")
        elif job.status() == "CANCELLED":
            print("Job was cancelled.")
except Exception as e:
    print(f"Failed to check jobs: {e}")
