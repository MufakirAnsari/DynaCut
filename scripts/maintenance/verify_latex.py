import sys

def check_latex_syntax(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check mismatched braces
    braces = 0
    for i, char in enumerate(content):
        if char == '{' and (i == 0 or content[i-1] != '\\'):
            braces += 1
        elif char == '}' and (i == 0 or content[i-1] != '\\'):
            braces -= 1
            if braces < 0:
                print(f"Error: Too many closing braces at position {i}")
                return False
    if braces > 0:
        print(f"Error: {braces} unclosed braces.")
        return False

    # Check mismatched environments
    import re
    begins = re.findall(r'\\begin\{([^}]+)\}', content)
    ends = re.findall(r'\\end\{([^}]+)\}', content)
    
    begin_counts = {}
    end_counts = {}
    for b in begins:
        begin_counts[b] = begin_counts.get(b, 0) + 1
    for e in ends:
        end_counts[e] = end_counts.get(e, 0) + 1
        
    for k in begin_counts:
        if begin_counts[k] != end_counts.get(k, 0):
            print(f"Error: Environment '{k}' has {begin_counts[k]} begins and {end_counts.get(k, 0)} ends.")
            return False
            
    print("Syntax verification passed: Braces and environments match.")
    return True

check_latex_syntax('paper/DynaCut.tex')
