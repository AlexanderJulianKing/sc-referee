import ast, sys, copy
sys.path.insert(0, "/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext/src"); sys.path.insert(0,".")
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v1 as M
from harness import case_inputs
from pathlib import Path
case, p = sys.argv[1], Path(sys.argv[2])
kw = case_inputs(case, p)
tree = M._bounded_parse(kw["content"])
scope, setup, helpers, reason = M._chosen_scope(tree)
top = {i.name: i for i in tree.body if isinstance(i, ast.FunctionDef) and i.name != "main"}
helpers = {**top, **helpers}
r1, _ = M._resolver((*setup, *scope))
norm = M._mt_expand_outcome_iterations(scope, resolver=r1, outcome_columns=kw["outcome_columns"])
print("normalized:", "None" if norm is None else f"{len(norm)} statements")
exp = M._expand_relevant_helpers(scope=norm, helpers=helpers, resolver=r1)
print("expansion reason:", exp.reason)
if exp.scope is not None:
    es = tuple(i for i in exp.scope if not isinstance(i, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
    r3, rr = M._resolver((*setup, *es))
    print("expanded resolver reason:", rr)
    calls = [n for st in es for n in ast.walk(st) if isinstance(n, ast.Call) and r3 and r3.qualified(n.func) in M._MT_TEST_APIS]
    print("family calls found:", len(calls), "expected", len(kw["outcome_columns"]))
    src = "\n".join(ast.unparse(s) for s in es)
    Path("expanded_dump.py").write_text(src)
    print("wrote expanded_dump.py", len(src.splitlines()), "lines")
