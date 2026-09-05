import ast, sys
sys.path.insert(0, "/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext/src"); sys.path.insert(0,".")
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v1 as M
from harness import case_inputs
kw = case_inputs("dfc9f20a94ecefc7f7b5")
src = kw["content"].decode(); lines = src.splitlines()
tree = M._bounded_parse(kw["content"])
full = tuple(i for i in tree.body if not M._is_docstring(i))
r, _ = M._resolver(full)
helpers = {i.name: i for i in tree.body if isinstance(i, ast.FunctionDef)}
print("helpers:", sorted(helpers))
main = helpers["main"]
for st in ast.walk(main):
    if isinstance(st, (ast.For,)):
        factor = M._mt_exact_outcome_factor(st.iter, r, kw["outcome_columns"])
        carries = M._mt_contains_family_call(st, r, helpers)
        print(f"L{st.lineno}: for {ast.unparse(st.target)} in {ast.unparse(st.iter)}  factor={factor} carries_family_call={carries}")
