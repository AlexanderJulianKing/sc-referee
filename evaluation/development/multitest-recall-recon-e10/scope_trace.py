import ast, sys
sys.path.insert(0, "/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext/src")
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v1 as M
from harness import case_inputs, ROLES

def why(case_id):
    kw = case_inputs(case_id)
    src = kw["content"].decode()
    lines = src.splitlines()
    tree = M._bounded_parse(kw["content"])
    body = tuple(i for i in tree.body if not M._is_docstring(i))
    mains = [i for i in body if isinstance(i, ast.FunctionDef) and i.name == "main"]
    async_mains = [i for i in body if isinstance(i, ast.AsyncFunctionDef) and i.name == "main"]
    guards = [i for i in body if isinstance(i, ast.If) and M._exact_main_guard(i)]
    ifs = [i for i in body if isinstance(i, ast.If)]
    res = []
    res.append(f"mains={len(mains)} async={len(async_mains)} exact_guards={len(guards)} module_ifs={len(ifs)}")
    if not (mains or async_mains or guards):
        res.append("-> whole module body is the scope (no main path)")
        return res
    if len(mains) != 1 or async_mains or len(guards) != 1 or not (mains and M._valid_main(mains[0])):
        if ifs and not guards:
            for i in ifs:
                res.append(f"  non-exact __main__ guard at line {i.lineno}: {lines[i.lineno-1].strip()}"
                           f" ; body={[type(s).__name__ for s in i.body]}"
                           f" ; body src={[lines[s.lineno-1].strip() for s in i.body]}")
        if mains and not M._valid_main(mains[0]):
            res.append(f"  main() signature invalid at line {mains[0].lineno}: {lines[mains[0].lineno-1].strip()}")
        res.append("-> analysis-scope-ambiguous (main/guard shape)")
        return res
    main_loads = {n.id for n in ast.walk(mains[0]) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    setup = tuple(i for i in body if isinstance(i, (ast.Import, ast.ImportFrom)) or M._module_setup_assignment(i, main_loads))
    others = [i for i in body if i not in setup and i is not mains[0] and i is not guards[0]]
    bad = [i for i in others if not isinstance(i, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    for i in bad:
        seg = ast.get_source_segment(src, i) or lines[i.lineno-1]
        name = i.targets[0].id if isinstance(i, ast.Assign) and len(i.targets)==1 and isinstance(i.targets[0], ast.Name) else None
        reasons = []
        if isinstance(i, ast.Assign):
            if len(i.targets)!=1: reasons.append("multi-target assign")
            elif not isinstance(i.targets[0], ast.Name): reasons.append("non-Name target")
            else:
                v = i.value
                if isinstance(v, ast.Constant): reasons.append("(constant: should pass!)")
                elif isinstance(v,(ast.Tuple,ast.List)):
                    reasons.append("sequence not closed: " + ("len/elt rule" if M._closed_sequence_elements(v.elts) is None else "?"))
                elif M._file_path_expression_syntax(v): reasons.append("(path syntax: should pass!)")
                elif name in main_loads: reasons.append(f"name {name!r} is LOADED inside main() so pure-expression escape hatch is closed")
                elif not M._pure_module_expression(v): reasons.append("value is not a pure module expression")
        else:
            reasons.append(f"module-level {type(i).__name__}")
        res.append(f"  BAD module stmt line {i.lineno}: {seg.splitlines()[0][:110]}   [{'; '.join(reasons)}]")
    if bad:
        res.append("-> analysis-scope-ambiguous (non-def module statement)")
    else:
        res.append("-> scope resolved OK")
    return res

if __name__ == "__main__":
    role = {i["case_id"]: i["role"] for i in ROLES}
    for item in ROLES:
        cid = item["case_id"]
        print(f"=== {role[cid]} {cid}")
        for line in why(cid):
            print("   ", line)
