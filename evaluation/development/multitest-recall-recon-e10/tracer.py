"""Step-through tracer that mirrors analyze_code_csv_multiple_testing_dataflow's prologue.

It never modifies the repo; it imports the module's private helpers and re-runs the
same gates with instrumentation, plus a traced clone of _resolver.
"""
import ast, sys, json
from pathlib import Path
sys.path.insert(0, "/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext/src")
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v1 as M
from harness import case_inputs, ROLES, CASES

def src_line(src, node):
    try:
        return src.splitlines()[node.lineno - 1].strip()
    except Exception:
        return "?"

def traced_resolver(statements, src, label, out):
    """Clone of M._resolver with reporting. Returns (resolver, reason)."""
    imports, constants, literals, tuples, sequence_kinds = {}, {}, {}, {}, {}
    file_parents, accepted_names = set(), set()
    def fail(node, why):
        out.append((label, why, getattr(node, "lineno", None), src_line(src, node) if node is not None else ""))
        return None, "api-resolution-ambiguous"
    for statement in statements:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                qualified = alias.name if alias.asname else alias.name.split(".", 1)[0]
                if bound in imports:
                    return fail(statement, f"duplicate import binding {bound!r}")
                imports[bound] = qualified
                accepted_names.add(bound)
        elif isinstance(statement, ast.ImportFrom):
            if statement.level or statement.module is None or any(i.name == "*" for i in statement.names):
                return fail(statement, "relative/star import")
            for alias in statement.names:
                bound = alias.asname or alias.name
                if bound in imports:
                    return fail(statement, f"duplicate import binding {bound!r}")
                imports[bound] = f"{statement.module}.{alias.name}"
                accepted_names.add(bound)
    resolver = M._Resolver(imports, constants, literals, tuples, sequence_kinds, file_parents,
                           set(accepted_names & M._UNSHADOWED_BUILTINS), accepted_names)
    for statement in statements:
        if not (isinstance(statement, ast.Assign) and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)):
            continue
        name = statement.targets[0].id
        if isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, (int, float, bool)):
            if name in constants or name in literals or name in tuples or name in imports:
                return fail(statement, f"rebinding of {name!r} (numeric literal)")
            literals[name] = statement.value.value
            continue
        if isinstance(statement.value, ast.Name) and statement.value.id in literals:
            if name in constants or name in literals or name in tuples or name in imports:
                return fail(statement, f"rebinding of {name!r} (literal alias)")
            literals[name] = literals[statement.value.id]
            continue
        if (isinstance(statement.value, (ast.Tuple, ast.List))
                and (seq := M._closed_sequence_elements(statement.value.elts)) is not None):
            if name in constants or name in literals or name in tuples or name in imports:
                return fail(statement, f"rebinding of {name!r} (sequence)")
            tuples[name] = tuple(seq)
            sequence_kinds[name] = "list" if isinstance(statement.value, ast.List) else "tuple"
            continue
        if M._file_parent_expression(statement.value, resolver):
            if (name in constants or name in literals or name in tuples or name in imports
                    or name in file_parents):
                return fail(statement, f"rebinding of {name!r} (file parent)")
            file_parents.add(name)
            continue
        string = resolver.string(statement.value)
        if string is None:
            string = M._static_path(statement.value, resolver)
        if string is not None:
            if (name in constants or name in literals or name in tuples or name in imports
                    or name in file_parents):
                return fail(statement, f"rebinding of {name!r} (string/path)")
            constants[name] = string
        if name in M._UNSHADOWED_BUILTINS:
            resolver.builtins_shadowed.add(name)
    for node in M._walk_statements(statements):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            hits = {n for t in targets for n in M._store_names(t) if n in accepted_names}
            if hits:
                return fail(node, f"assignment rebinds imported name(s) {sorted(hits)}")
    if resolver.builtins_shadowed:
        return fail(None, f"builtins shadowed: {sorted(resolver.builtins_shadowed)}")
    return resolver, None

def trace(case_id):
    kw = case_inputs(case_id)
    content = kw["content"]
    src = content.decode()
    out = []
    tree = M._bounded_parse(content)
    # gate 1
    shadow = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in M._UNSHADOWED_BUILTINS:
            shadow.append(("def", node.name, node.lineno))
        if isinstance(node, ast.arg) and node.arg in M._UNSHADOWED_BUILTINS:
            shadow.append(("arg", node.arg, node.lineno))
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)) and node.id in M._UNSHADOWED_BUILTINS:
            shadow.append(("store", node.id, node.lineno))
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                b = alias.asname or alias.name.split(".", 1)[0]
                if b in M._UNSHADOWED_BUILTINS:
                    shadow.append(("import", b, node.lineno))
    if shadow:
        return [("gate:_definition_shadows_builtin", f"builtin shadowed {shadow[:6]}", shadow[0][2], src_line(src, ast.parse('x').body[0]) if False else src.splitlines()[shadow[0][2]-1].strip())]
    scope, setup, helpers, reason = M._chosen_scope(tree)
    if reason is not None or scope is None:
        return [("gate:_chosen_scope", reason, None, "")]
    if any(isinstance(n, (ast.Global, ast.Nonlocal)) for s in scope for n in ast.walk(s)):
        return [("gate:global-nonlocal", "helper-global-nonlocal-unsupported", None, "")]
    r1, reason1 = traced_resolver((*setup, *scope), src, "_resolver(setup+scope)", out)
    if reason1:
        return out
    full_scope = tuple(i for i in tree.body if not M._is_docstring(i))
    r2, reason2 = traced_resolver(full_scope, src, "_resolver(full module scope)", out)
    if reason2:
        return out
    readers = M._v3_full_scope_reader_census(full_scope, resolver=r2, csv_header=tuple(kw["csv_header"]),
                                             unit_column=kw["outcome_columns"][0], group_column=kw["group_column"])
    out.append(("reader_census", f"readers={readers} authorized={kw['authorized_path']}", None, ""))
    if len(readers) > 1:
        return out + [("gate:readers", "additional-accepted-reader-present", None, "")]
    if len(readers) != 1 or readers[0] != kw["authorized_path"]:
        return out + [("gate:readers", "authorized-reader-lineage-unavailable", None, "")]
    census, creason = M._mt_call_census(tree, resolver=r2, outcome_columns=kw["outcome_columns"])
    if creason is not None:
        return out + [("gate:_mt_call_census", creason, None, "")]
    out.append(("census", f"n={len(census)} apis={sorted({c.api for c in census})} lines={[c.call.lineno for c in census]}", None, ""))
    fam = len(kw["outcome_columns"])
    if len(census) < fam:
        return out + [("gate:census", "authorized-family-test-census-incomplete", None, "")]
    if len(census) > fam:
        return out + [("gate:census", "extra-registered-test-outside-authorized-family", None, "")]
    if len({c.api for c in census}) != 1:
        return out + [("gate:census", "mixed-test-api-family", None, "")]
    normalized = M._mt_expand_outcome_iterations(scope, resolver=r1, outcome_columns=kw["outcome_columns"])
    if normalized is None:
        return out + [("gate:_mt_expand_outcome_iterations", "test-battery-cardinality-unresolved", None, "")]
    expansion = M._expand_relevant_helpers(scope=normalized, helpers={**{i.name: i for i in tree.body if isinstance(i, ast.FunctionDef) and i.name != 'main'}, **helpers}, resolver=r1)
    if expansion.reason is not None or expansion.scope is None:
        return out + [("gate:_expand_relevant_helpers", expansion.reason, None, "")]
    expanded = tuple(i for i in expansion.scope if not isinstance(i, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
    r3, reason3 = traced_resolver((*setup, *expanded), src, "_resolver(setup+expanded scope)", out)
    if reason3:
        return out
    out.append(("prologue", "passed; engine.run() decides", None, ""))
    return out

if __name__ == "__main__":
    ids = sys.argv[1:] or [i["case_id"] for i in ROLES]
    role = {i["case_id"]: i["role"] for i in ROLES}
    for cid in ids:
        print(f"=== {role.get(cid,'?')} {cid}")
        for row in trace(cid):
            print("   ", row)
