import urllib.request
import urllib.parse
import json
import time

more_papers = [
    "Quantum supremacy using a programmable superconducting processor",
    "Characterizing quantum supremacy in near-term devices",
    "Quantum chemistry calculations on a trapped-ion quantum simulator",
    "Quantum computational supremacy",
    "Information-theoretic bounds on quantum advantage in machine learning",
    "Supervised learning with quantum-enhanced feature spaces",
    "Quantum algorithms for topological and geometric analysis of data",
    "Tensor network algorithms for quantum algorithms",
    "Quantum circuit cutting with maximum likelihood tomography",
    "Optimal cutting of parameterized quantum circuits",
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

with open("paper/references.bib", "a") as f:
    for i, title in enumerate(more_papers):
        print(f"[{i+1}/{len(more_papers)}] Searching for: {title}")
        bib = search_crossref(title)
        if not bib:
            bib = search_arxiv(title)
        
        if bib:
            f.write(bib + "\n\n")
            print("  -> Found!")
        else:
            print("  -> Not found.")
        time.sleep(0.2)
