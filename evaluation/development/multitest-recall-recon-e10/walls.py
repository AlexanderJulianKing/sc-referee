import ast, sys
sys.path.insert(0, "/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext/src"); sys.path.insert(0,".")
from harness import CASES, ROLES
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v1 as M

PNAMES = ("pvalue","p_value","p_val","pval","p_adj","adjusted_p","p_corrected","p_raw","p_holm","p_bonf")
def p_ish(node):
    for n in ast.walk(node):
        if isinstance(n, ast.Attribute) and n.attr in ("pvalue","p_value"): return True
        if isinstance(n, ast.Name) and (n.id == "p" or any(k in n.id for k in PNAMES)): return True
        if isinstance(n, ast.Constant) and isinstance(n.value,str) and n.value in ("p_value","pvalue","significant"): return True
    return False

def controls(tree):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.If, ast.IfExp, ast.While, ast.Assert)):
            out.append(("if/ifexp/while/assert", n.test, n.lineno))
        elif isinstance(n, ast.comprehension):
            for t in n.ifs: out.append(("comprehension-if", t, getattr(t,'lineno',0)))
    return out

for item in ROLES:
    src = (CASES/item["case_id"]/"project/analysis.py").read_text()
    lines = src.splitlines()
    tree = ast.parse(src)
    hits = [(k, lineno, lines[lineno-1].strip()[:90]) for k, t, lineno in controls(tree) if p_ish(t)]
    print(f"{item['role']:3} {item['case_id']}  p-carrying control expressions: {len(hits)}")
    for k, ln, txt in hits[:4]:
        print(f"      L{ln} {k}: {txt}")
