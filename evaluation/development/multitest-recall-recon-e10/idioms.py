import ast, sys, json
sys.path.insert(0, "/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext/src"); sys.path.insert(0,".")
from harness import CASES, ROLES
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v1 as M

def scan(path):
    src = path.read_text()
    tree = ast.parse(src)
    f = {}
    def add(k, n=1): f[k] = f.get(k, 0) + n
    body = [i for i in tree.body if not M._is_docstring(i)]
    for st in body:
        if isinstance(st, ast.Assign) and len(st.targets)==1 and isinstance(st.targets[0], ast.Name):
            v = st.value
            if isinstance(v, (ast.List, ast.Tuple)) and M._closed_sequence_elements(v.elts) is None:
                if all(isinstance(e, (ast.Tuple, ast.List)) for e in v.elts):
                    add("module nested constant table (list of tuples)")
                else:
                    add("module list literal not all-constant")
            elif isinstance(v, ast.Dict):
                add("module dict constant table")
            elif isinstance(v, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                add("module comprehension-derived constant")
        if isinstance(st, ast.AnnAssign):
            add("module AnnAssign (annotated constant)")
    for n in ast.walk(tree):
        # boolean-mask group split  df[df[col] == v]
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Compare):
            add("boolean-mask row selection df[df[col] == value]")
        # read_csv with non-static arg
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "read_csv":
            arg = n.args[0] if n.args else None
            if isinstance(arg, ast.Name):
                add("read_csv(path) through a function parameter/name")
        # enumerate / zip family loop
        if isinstance(n, (ast.For,)) and isinstance(n.iter, ast.Call) and isinstance(n.iter.func, ast.Name) and n.iter.func.id in {"enumerate","zip"}:
            add(f"family loop wrapped in {n.iter.func.id}()")
        if isinstance(n, ast.comprehension) and isinstance(n.iter, ast.Call) and isinstance(n.iter.func, ast.Name) and n.iter.func.id in {"enumerate","zip"}:
            add(f"family comprehension wrapped in {n.iter.func.id}()")
        # tuple-unpack loop target over a table
        if isinstance(n, ast.For) and isinstance(n.target, ast.Tuple):
            add("tuple-unpacking loop target (for col, label in TABLE)")
        if isinstance(n, ast.comprehension) and isinstance(n.target, ast.Tuple):
            add("tuple-unpacking comprehension target")
        # named alpha threshold
        if isinstance(n, ast.Compare) and len(n.ops)==1 and isinstance(n.ops[0], (ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
            comp = n.comparators[0]
            if isinstance(comp, ast.Name):
                add("p-vs-threshold comparison against a NAMED constant")
            elif isinstance(comp, ast.Constant) and isinstance(comp.value, float) and comp.value not in (0.01,0.05,0.1):
                add(f"p-vs-threshold against an off-list literal ({comp.value})")
        # verdict ternary on a p comparison
        if isinstance(n, ast.IfExp):
            add("IfExp (ternary) anywhere")
    return f

if __name__ == "__main__":
    tot = {}
    per = {}
    for item in ROLES:
        p = CASES/item["case_id"]/"project/analysis.py"
        f = scan(p)
        per[item["role"]] = f
        for k, v in f.items():
            tot.setdefault(k, [0,set()])
            tot[k][0] += v
            tot[k][1].add(item["role"])
    for k, (v, roles) in sorted(tot.items(), key=lambda kv: -len(kv[1][1])):
        print(f"{len(roles):2} files, {v:3} sites  {k}")
        print(f"              roles: {' '.join(sorted(roles))}")
