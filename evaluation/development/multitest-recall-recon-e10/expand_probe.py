import ast, sys
sys.path.insert(0, "/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext/src"); sys.path.insert(0,".")
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v1 as M
from harness import case_inputs
from pathlib import Path
case, p = sys.argv[1], Path(sys.argv[2])
kw = case_inputs(case, p)
tree = M._bounded_parse(kw["content"])
scope, setup, helpers, reason = M._chosen_scope(tree)
full = tuple(i for i in tree.body if not M._is_docstring(i))
r1, _ = M._resolver((*setup, *scope))
print("outcome_columns", kw["outcome_columns"])
print("resolver.tuples", {k: v for k, v in r1.tuples.items()})
# per-statement expansion
for st in scope:
    if isinstance(st, ast.For) and M._mt_contains_family_call(st, r1, {}):
        f = M._mt_exact_outcome_factor(st.iter, r1, kw["outcome_columns"])
        print(f"For at L{st.lineno}: factor={f} target={ast.dump(st.target)[:60]} orelse={bool(st.orelse)}")
    else:
        t = M._mt_expand_comprehensions(__import__('copy').deepcopy(st), r1, kw["outcome_columns"])
        if t is None:
            print(f"comprehension expansion FAILED at L{st.lineno}: {ast.unparse(st).splitlines()[0][:100]}")
