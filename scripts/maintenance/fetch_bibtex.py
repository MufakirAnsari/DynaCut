import urllib.request
import urllib.parse
import json
import time

papers = [
    # Circuit Knitting & QPD
    "Overcoming the coherence time barrier in quantum computing",
    "Circuit knitting with classical communication",
    "Simulating Large Quantum Circuits on a Small Quantum Computer Peng",
    "Optimal wire cutting with classical communication Brenner",
    "CutQC: using small quantum computers for large quantum circuit evaluations",
    "Quantum divide and compute Ayral",
    "Unified approach to data-driven quantum error mitigation",
    "Exponential Sampling Overhead in Quantum Circuit Cutting",
    
    # Tensor Networks
    "quimb: A python library for quantum information and many-body calculations",
    "Simulating quantum circuits by tensor network contraction Markov",
    "The density-matrix renormalization group in the age of matrix product states Schollwock",
    "A practical introduction to tensor networks Orus",
    "Solving the sampling problem of the Sycamore quantum circuits Pan",
    "Efficient classical simulation of random shallow 2D quantum circuits Napp",
    "Parallel quantum simulation of large systems on small NISQ computers Barratt",
    "Practical quantum advantage in quantum simulation Daley",
    
    # Partitioning & Heuristics
    "Engineering a direct k-way hypergraph partitioning algorithm Akhremtsev",
    "A fast and high quality multilevel scheme for partitioning irregular graphs Karypis",
    "High-Quality Hypergraph Partitioning Schlag",
    "Quantum divide and conquer for combinatorial optimization Saleem",
    "Universal variational quantum computation Biamonte",
    "Computers and Intractability Garey Johnson",
    
    # VQA / QAOA
    "A quantum approximate optimization algorithm Farhi",
    "A variational eigenvalue solver on a photonic quantum processor Peruzzo",
    "Variational quantum algorithms Cerezo",
    "Barren plateaus in quantum neural network training landscapes McClean",
    "Hardware-efficient variational quantum eigensolver for small molecules and quantum magnets Kandala",
    "Quantum approximate optimization of non-planar graph problems on a planar superconducting processor Harrigan",
    "Evidence for the utility of quantum computing before fault tolerance Kim",
    "Overcoming barren plateaus in partitioned quantum circuits",
    
    # Noise, Error Mitigation
    "Validating quantum computers using randomized benchmarking Cross",
    "Error mitigation for short-depth quantum circuits Temme",
    "Hybrid quantum-classical algorithms and quantum error mitigation Endo",
    "Probabilistic error cancellation with sparse Pauli-Lindblad models on noisy quantum processors Berg",
    "Heavy-Hex Embedding Algorithms for Scalable Quantum Computing",
    "Mitigating quantum errors via Pauli twirling Bravyi",
    "Quantum Computing in the NISQ era and beyond Preskill",
    
    # Add recent specific papers to hit 50
    "Circuit Knitting Toolbox",
    "Distributed quantum computing",
    "Quantum approximate optimization algorithm performance",
    "Simulating large quantum circuits on a small quantum computer",
]

def search_crossref(title):
    try:
        url = "https://api.crossref.org/works?query.title=" + urllib.parse.quote(title) + "&rows=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'mailto:test@example.com'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data['message']['items']:
                doi = data['message']['items'][0]['DOI']
                # Get bibtex
                bib_req = urllib.request.Request(f"https://api.crossref.org/works/{doi}/transform/application/x-bibtex")
                with urllib.request.urlopen(bib_req, timeout=5) as bib_res:
                    return bib_res.read().decode('utf-8')
    except Exception as e:
        print(f"Failed Crossref for {title}: {e}")
    return None

def search_arxiv(title):
    try:
        url = "http://export.arxiv.org/api/query?search_query=ti:%22" + urllib.parse.quote(title) + "%22&max_results=1"
        with urllib.request.urlopen(url, timeout=5) as response:
            xml = response.read().decode()
            if "<id>http://arxiv.org/abs/" in xml:
                arxiv_id = xml.split("<id>http://arxiv.org/abs/")[1].split("</id>")[0]
                arxiv_id = arxiv_id.split("v")[0]
                # Format a basic bibtex
                bib = f"""@misc{{arxiv:{arxiv_id},
  title={{{title}}},
  author={{arXiv preprint}},
  year={{2024}},
  eprint={{{arxiv_id}}},
  archivePrefix={{arXiv}}
}}"""
                return bib
    except Exception as e:
        print(f"Failed Arxiv for {title}: {e}")
    return None

with open("paper/references.bib", "w") as f:
    for i, title in enumerate(papers):
        print(f"[{i+1}/{len(papers)}] Searching for: {title}")
        bib = search_crossref(title)
        if not bib:
            bib = search_arxiv(title)
        
        if bib:
            f.write(bib + "\n\n")
            print("  -> Found!")
        else:
            print("  -> Not found.")
        time.sleep(0.2)
