"""Exact shadow projections of the shipped provenance and sink-use public outputs.

This module consumes the already-parsed ``SourceUnit`` objects in an ``AnalysisSnapshot``.  It does
not call either legacy public implementation; those remain independent differential oracles.
"""
from __future__ import annotations

import ast

from sc_referee.provenance import MarkerTest
from sc_referee.sink_use import BoundPort, SinkBindResult, SinkUse
from sc_referee.sinks import ValueType, resolve_sink_status, sink_symbols
from sc_referee.source_ast import (
    callsite_id,
    const_str,
    func_name,
    iter_call_sites,
    ordered_statements,
    resolve_callee,
    source_env,
    terminal_symbol,
)


_DATA_ATTRS = ("X", "raw")
_EXPRESSION_OBSM_PREFIX = "X_"
_EXPRESSION_OBSM_EXTRA = frozenset({"X"})
_CLUSTER_KEYS = {"leiden": "leiden", "louvain": "louvain"}
_MARKER_FUNCS = ("rank_genes_groups", "findmarkers", "findallmarkers")
_CLUSTER_INPUT_KWARGS = ("adjacency", "obsp", "connectivity")
_ADATA_NAMES = frozenset({"adata", "ad", "andata", "adata_raw"})
_ADATA_READERS = frozenset({"anndata", "read", "read_h5ad", "read_10x_h5", "read_10x_mtx",
                            "read_loom", "read_text", "read_mtx", "read_visium", "read_umi_tools"})
_ORIGIN_MAP = {"data_derived": "primary_data", "predefined_within_program": "metadata",
               "unresolved": "unknown"}


def _receiver_is_adata(node, identities):
    if isinstance(node, ast.Name):
        return node.id in identities
    if isinstance(node, ast.Attribute) and node.attr == "raw":
        return _receiver_is_adata(node.value, identities)
    if isinstance(node, ast.Subscript):
        return _receiver_is_adata(node.value, identities)
    return (isinstance(node, ast.Call) and func_name(node) == "copy"
            and isinstance(node.func, ast.Attribute)
            and _receiver_is_adata(node.func.value, identities))


def _is_adata_expr(node, identities):
    if isinstance(node, ast.Name):
        return node.id in identities
    if isinstance(node, ast.Call):
        if func_name(node) in _ADATA_READERS:
            return True
        if func_name(node) == "copy" and isinstance(node.func, ast.Attribute):
            return _receiver_is_adata(node.func.value, identities)
    if isinstance(node, (ast.Subscript, ast.Attribute)):
        return _receiver_is_adata(node, identities)
    return False


def _reads_data(node, tainted, columns, obsm_data, identities):
    for child in ast.walk(node):
        if (isinstance(child, ast.Attribute) and child.attr in _DATA_ATTRS
                and _receiver_is_adata(child.value, identities)):
            return True
        if isinstance(child, ast.Subscript) and isinstance(child.value, ast.Attribute):
            attr, receiver = child.value.attr, child.value.value
            if attr == "layers" and _receiver_is_adata(receiver, identities):
                return True
            if attr == "obsm" and _receiver_is_adata(receiver, identities):
                key = const_str(child.slice)
                if key is not None and (key.startswith(_EXPRESSION_OBSM_PREFIX)
                                        or key in _EXPRESSION_OBSM_EXTRA or key in obsm_data):
                    return True
            if attr == "obs":
                key = const_str(child.slice)
                if key is not None and columns.get(key) == "data":
                    return True
        if isinstance(child, ast.Name) and child.id in tainted:
            return True
    return False


def _reads_opaque(node, obsm_opaque, columns, opaque_tainted, identities):
    """Shadow of provenance._reads_opaque: the opaque-taint mirror of `_reads_data`. Reads an
    `.obsm['K']` written in-script from an opaque call, an `.obs['G']` column classified `"opaque"`,
    or an already-opaque local — a grouping tracing to any is `unresolved`, not clean (#47)."""
    for child in ast.walk(node):
        if isinstance(child, ast.Subscript) and isinstance(child.value, ast.Attribute):
            attr, receiver = child.value.attr, child.value.value
            if attr == "obsm" and _receiver_is_adata(receiver, identities):
                key = const_str(child.slice)
                if key is not None and key in obsm_opaque:
                    return True
            if attr == "obs":
                key = const_str(child.slice)
                if key is not None and columns.get(key) == "opaque":
                    return True
        if isinstance(child, ast.Name) and child.id in opaque_tainted:
            return True
    return False


def _field_target(target, identities, attribute):
    if (isinstance(target, ast.Subscript) and isinstance(target.value, ast.Attribute)
            and target.value.attr == attribute
            and _receiver_is_adata(target.value.value, identities)):
        return const_str(target.slice)
    return None


def _cluster_key(call):
    key = _CLUSTER_KEYS[func_name(call)]
    for keyword in call.keywords:
        if keyword.arg == "key_added" and isinstance(keyword.value, ast.Constant) \
                and isinstance(keyword.value.value, str):
            key = keyword.value.value
    return key


def _cluster_is_data(call, tainted, columns, obsm_data, identities):
    for keyword in call.keywords:
        if keyword.arg in _CLUSTER_INPUT_KWARGS:
            return _reads_data(keyword.value, tainted, columns, obsm_data, identities)
    return True


def _assignment(statement):
    if isinstance(statement, ast.Assign):
        return statement.targets, statement.value
    if isinstance(statement, ast.AnnAssign) and statement.value is not None:
        return [statement.target], statement.value
    return [], None


def _leaves(target):
    if isinstance(target, (ast.Tuple, ast.List)):
        for element in target.elts:
            yield from _leaves(element)
    else:
        yield target


def _literal_groupby(call):
    for keyword in call.keywords:
        if keyword.arg in ("groupby", "group_by"):
            return const_str(keyword.value)
    if len(call.args) >= 2:
        return const_str(call.args[1])
    return None


def project_legacy_marker_tests(snapshot) -> list[MarkerTest]:
    units = snapshot.program.sources
    parse_failed_markers = 0
    for unit in units:
        if unit.parsed.tree is None and any(name in unit.normalized.lower() for name in _MARKER_FUNCS):
            parse_failed_markers += 1

    columns = {}
    may_data = set()
    may_opaque = set()                       # obs cols EVER written opaque, in ANY branch (may-union, #47)
    obsm_data = set()
    obsm_opaque = set()                      # obsm keys written in-script from an opaque call (#47)
    identities = set(_ADATA_NAMES)
    results = []
    for unit in units:
        if unit.parsed.tree is None:
            continue
        tainted = set()
        opaque_tainted = set()               # opaque-tainted local vars, reset per source (#47)
        for statement in ordered_statements(unit.parsed.tree.body):
            targets, rhs = _assignment(statement)
            if rhs is not None:
                is_data = _reads_data(rhs, tainted, columns, obsm_data, identities)
                is_opaque = (not is_data) and _reads_opaque(
                    rhs, obsm_opaque, columns, opaque_tainted, identities)
                is_adata = _is_adata_expr(rhs, identities)
                for target in targets:
                    for leaf in _leaves(target):
                        if isinstance(leaf, ast.Name):
                            if is_data:
                                tainted.add(leaf.id); opaque_tainted.discard(leaf.id)
                            elif is_opaque:
                                opaque_tainted.add(leaf.id); tainted.discard(leaf.id)
                            else:
                                tainted.discard(leaf.id); opaque_tainted.discard(leaf.id)
                            if is_adata:
                                identities.add(leaf.id)
                        column = _field_target(leaf, identities, "obs")
                        if column is not None:
                            if is_data:
                                columns[column] = "data"
                                may_data.add(column)
                            elif is_opaque:
                                columns[column] = "opaque"
                                may_opaque.add(column)
                            else:
                                columns[column] = "meta"
                        key = _field_target(leaf, identities, "obsm")
                        if key is not None:
                            if is_data:
                                obsm_data.add(key); obsm_opaque.discard(key)
                            elif isinstance(rhs, ast.Call):
                                obsm_opaque.add(key); obsm_data.discard(key)
                            else:
                                obsm_data.discard(key); obsm_opaque.discard(key)
            expression = statement.value if isinstance(statement, ast.Expr) else rhs
            if expression is None:
                continue
            for node in ast.walk(expression):
                if not isinstance(node, ast.Call):
                    continue
                name = func_name(node)
                if name in _CLUSTER_KEYS:
                    if _cluster_is_data(node, tainted, columns, obsm_data, identities):
                        columns[_cluster_key(node)] = "data"
                elif name in _MARKER_FUNCS:
                    grouping = _literal_groupby(node)
                    if grouping is None:
                        origin = "unresolved"
                    elif columns.get(grouping) == "data":
                        origin = "data_derived"
                    elif columns.get(grouping) == "opaque":
                        origin = "unresolved"            # opaque-written embedding (#47)
                    elif grouping in may_data:
                        origin = "unresolved"
                    elif grouping in may_opaque:
                        origin = "unresolved"            # opaque in some branch -> escalate (#47)
                    else:
                        origin = "predefined_within_program"
                    results.append(MarkerTest(grouping, origin,
                                              callsite_id=callsite_id(unit.source_index, node)))
    results.extend(MarkerTest(None, "unresolved") for _ in range(parse_failed_markers))
    return results


def _literal(node):
    return node.value if isinstance(node, ast.Constant) else None


def _bind_port(port, call):
    kwargs_splat = any(keyword.arg is None for keyword in call.keywords)
    keyword_values = {keyword.arg: keyword.value for keyword in call.keywords if keyword.arg is not None}
    stars = [index for index, argument in enumerate(call.args) if isinstance(argument, ast.Starred)]
    first_star = stars[0] if stars else None
    keyword_hits = [(locator, keyword_values[locator.name]) for locator in port.locators
                    if locator.kind == "kw" and locator.name in keyword_values]
    positional_hits = [(locator, call.args[locator.index]) for locator in port.locators
                       if locator.kind == "arg" and locator.index is not None
                       and (first_star is None or locator.index < first_star)
                       and locator.index < len(call.args)]
    receiver_hits = [(locator, call.func.value) for locator in port.locators
                     if locator.kind == "receiver" and isinstance(call.func, ast.Attribute)]
    if len({id(expression) for _, expression in keyword_hits}) > 1:
        return "ambiguous", None, None, None
    if keyword_hits and positional_hits:
        return "invalid_call", None, None, None
    for hits in (keyword_hits, positional_hits, receiver_hits):
        if hits:
            locator, expression = hits[0]
            return "bound", expression, locator, _literal(expression)
    if kwargs_splat or first_star is not None:
        return "unsupported", None, None, None
    return ("missing_required" if port.required else "missing_optional"), None, None, None


def _candidate(source_index, symbol, lineno, detail):
    return {"kind": "unresolved_sink_candidate", "source_index": source_index,
            "symbol": str(symbol).lower(), "lineno": lineno, "detail": detail}


def _referenced_sink_symbol(site, environment, known):
    if site.symbol in known:
        return site.symbol
    if isinstance(site.call.func, ast.Name):
        binding = environment.imports.get(site.call.func.id)
        if binding is not None and binding.symbol is not None and binding.symbol.lower() in known:
            return binding.symbol.lower()
        for original in environment.alias_symbols.get(site.call.func.id, ()):
            if original.lower() in known:
                return original.lower()
    return None


def _indirect_candidates(units, known):
    diagnostics = []
    for unit in units:
        if unit.parsed.tree is None:
            continue
        call_functions = {id(node.func) for node in ast.walk(unit.parsed.tree) if isinstance(node, ast.Call)}
        for node in ast.walk(unit.parsed.tree):
            if isinstance(node, ast.Call) and terminal_symbol(node) in ("getattr", "__getattribute__"):
                for argument in node.args:
                    symbol = const_str(argument)
                    if symbol is not None and symbol.lower() in known:
                        diagnostics.append(_candidate(unit.source_index, symbol, node.lineno,
                                                      "a known sink referenced via getattr/__getattribute__"))
            elif isinstance(node, ast.Subscript):
                symbol = const_str(node.slice)
                if symbol is not None and symbol.lower() in known:
                    diagnostics.append(_candidate(unit.source_index, symbol, node.lineno,
                                                  "a known sink referenced via a subscript lookup"))
            elif (isinstance(node, ast.Attribute) and node.attr.lower() in known
                  and id(node) not in call_functions):
                diagnostics.append(_candidate(unit.source_index, node.attr, node.lineno,
                                              "a known sink referenced indirectly (aliased, not called directly)"))
    return diagnostics


def _dedupe(diagnostics):
    seen, result = set(), []
    for diagnostic in diagnostics:
        key = (diagnostic.get("kind"), diagnostic.get("source_index"),
               diagnostic.get("symbol"), diagnostic.get("lineno"))
        if key not in seen:
            seen.add(key)
            result.append(diagnostic)
    return result


def project_legacy_sink_uses(snapshot) -> SinkBindResult:
    units = snapshot.program.sources
    parsed = [unit.parsed for unit in units]
    diagnostics = [{"kind": "parse_error", "source_index": unit.source_index,
                    "detail": unit.parsed.parse_error}
                   for unit in units if unit.parsed.tree is None]
    environments = {unit.source_index: source_env(unit.parsed) for unit in units}
    known = sink_symbols()
    origins = {test.callsite_id: test.origin for test in project_legacy_marker_tests(snapshot)
               if test.callsite_id is not None}
    uses = []
    for site in iter_call_sites(parsed):
        environment = environments[site.source_index]
        canonical = resolve_callee(site, environment)
        contract = status = None
        if canonical is not None:
            contract, status = resolve_sink_status(canonical[1], canonical[0])
        if contract is None:
            referenced = _referenced_sink_symbol(site, environment, known)
            if referenced is not None:
                diagnostics.append(_candidate(site.source_index, referenced, site.lineno,
                                              "a call named like a known sink did not resolve to one"))
            continue
        bound = {}
        for port in contract.inputs:
            port_status, expression, locator, literal = _bind_port(port, site.call)
            value_type = ValueType()
            if port.role == "grouping":
                origin = _ORIGIN_MAP.get(origins.get(site.id, "unresolved"), "unknown")
                value_type = ValueType(kind="labels", unit="cell", origins=frozenset({origin}))
            bound[port.role] = BoundPort(
                role=port.role, status=port_status, expr=expression,
                source_text=ast.unparse(expression) if expression is not None else None,
                locator_used=locator, literal_value=literal, value_type=value_type)
        uses.append(SinkUse(site.id, contract, status, bound, contract.module, contract.symbol,
                            (site.source_index, site.lineno, site.col_offset)))
    diagnostics += _indirect_candidates(units, known)
    return SinkBindResult(uses, _dedupe(diagnostics))
