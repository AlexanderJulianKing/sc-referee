"""Bounded report-producer summaries layered on the frozen SinkUse resolver.

The original Phase 3a binder proves one narrow must-flow retained for consumers that need it:

``rank_genes_groups(adata)`` -> ``adata.uns[key]`` ->
``rank_genes_groups_df(adata, key=key)`` -> ``frame.to_csv/to_parquet(path)``.

It is intentionally incomplete.  A missed binding only costs double-dipping coverage; a guessed
binding could attach one analysis's accusation to another report, so every uncertain state change
abstains.  Analyzed code is parsed, never executed.

Double-dipping claim *scoping* uses the shorter local trace implemented by
``bind_marker_extraction_report_producers``: exact marker extraction -> local DataFrame variable ->
literal report egress.  That trace deliberately does not inspect AnnData identity or ``uns`` state.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import os.path

from sc_referee.inference.contracts.schema import EffectContract
from sc_referee.source_ast import (
    const_str,
    iter_call_sites,
    parse_sources,
    resolve_callee,
    source_env,
    terminal_symbol,
)


@dataclass(frozen=True)
class ClaimProducer:
    callsite_id: str
    contract_id: str
    symbol: str
    sink_kind: str
    marker_family: str | None = None


@dataclass(frozen=True)
class ProducerSummary:
    """The reviewed effects of one supported producer-chain operation."""

    operation: str
    identities: tuple[tuple[str, str], ...]
    effects: EffectContract


# This is the complete, deliberately small producer-summary set.  The symbolic effect names are
# instantiated only after object identity, literal key/path, and exact callee identity are proved.
PRODUCER_SUMMARIES = (
    ProducerSummary(
        "marker_uns_write",
        (("scanpy.tl", "rank_genes_groups"),),
        EffectContract(
            reads=("arg0.expression",),
            writes=("arg0.uns[literal:key_added|rank_genes_groups]",),
        ),
    ),
    ProducerSummary(
        "marker_uns_read",
        (("scanpy.get", "rank_genes_groups_df"),),
        EffectContract(
            reads=("arg0.uns[literal:key|rank_genes_groups]",),
            return_from=(0,),
            allocates=True,
        ),
    ),
    ProducerSummary(
        "report_egress",
        (("pandas.core.generic", "DataFrame.to_csv"),
         ("pandas.core.generic", "DataFrame.to_parquet")),
        EffectContract(reads=("receiver",), egresses=("literal:path",)),
    ),
)


_DEFAULT_MARKER_KEY = "rank_genes_groups"
_MARKER_CONTRACTS = frozenset({"scanpy.tl.rank_genes_groups.v1"})
_EXTRACT_IDENTITIES = frozenset(PRODUCER_SUMMARIES[1].identities)
_EGRESS_METHODS = frozenset(identity[1].removeprefix("DataFrame.")
                            for identity in PRODUCER_SUMMARIES[2].identities)
_MARKER_EXTRACT_CONTRACT = "scanpy.get.rank_genes_groups_df.v1"
# No general call is currently proved unable to rebind a global/closure name or patch an egress
# method.  Keep this explicit allowlist empty until a callee has an accusation-grade effect summary.
_LIVE_FRAME_SAFE_CALLEES: frozenset[tuple[str, str]] = frozenset()


@dataclass(frozen=True)
class _Writer:
    source_index: int
    statement_index: int
    object_name: str
    key: str
    producer: ClaimProducer


@dataclass(frozen=True)
class _Extract:
    source_index: int
    statement_index: int
    object_name: str
    key: str
    table_name: str


@dataclass(frozen=True)
class _Egress:
    source_index: int
    statement_index: int
    table_name: str
    path: str


def _arg(call: ast.Call, keyword: str, position: int) -> ast.AST | None:
    hits = [item.value for item in call.keywords if item.arg == keyword]
    if len(hits) != 1:
        if hits or any(item.arg is None for item in call.keywords):
            return None
        return call.args[position] if position < len(call.args) else None
    if position < len(call.args):
        return None
    return hits[0]


def _literal_keyword(call: ast.Call, keyword: str, default: str) -> str | None:
    hits = [item.value for item in call.keywords if item.arg == keyword]
    if any(item.arg is None for item in call.keywords) or len(hits) > 1:
        return None
    if not hits:
        return default
    return const_str(hits[0])


def _name(node: ast.AST | None) -> str | None:
    return node.id if isinstance(node, ast.Name) else None


def _root_name(node: ast.AST) -> str | None:
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _statement_call(statement: ast.stmt) -> ast.Call | None:
    if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
        return statement.value
    return None


def _assignment_call(statement: ast.stmt) -> tuple[str, ast.Call] | None:
    if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
        return None
    targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
    value = statement.value
    if (len(targets) == 1 and isinstance(targets[0], ast.Name)
            and isinstance(value, ast.Call)):
        return targets[0].id, value
    return None


def _path_arg(call: ast.Call) -> ast.AST | None:
    keyword = "path_or_buf" if call.func.attr == "to_csv" else "path"
    return _arg(call, keyword, 0)


def _normalize_relative_report_path(path: str) -> str | None:
    """Return one lexical key for a relative literal, or ``None`` when comparison is unsafe."""
    if not path or "\x00" in path or os.path.isabs(path):
        return None
    normalized = os.path.normpath(path)
    if normalized in {"", os.curdir} or os.path.isabs(normalized):
        return None
    return normalized


def _names_loaded(node: ast.AST) -> set[str]:
    return {item.id for item in ast.walk(node)
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)}


def _has_opaque_call(statement: ast.stmt, sites_by_node, env) -> bool:
    """Whether a statement can invoke code not proved safe for every live marker frame."""
    for call in (item for item in ast.walk(statement) if isinstance(item, ast.Call)):
        site = sites_by_node.get(id(call))
        resolved = resolve_callee(site, env) if site is not None else None
        if resolved not in _LIVE_FRAME_SAFE_CALLEES:
            return True
    return False


def _targets_root(statement: ast.stmt, name: str) -> bool:
    targets: list[ast.AST] = []
    if isinstance(statement, ast.Assign):
        targets = list(statement.targets)
    elif isinstance(statement, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
        targets = [statement.target]
    return any(_root_name(target) == name for target in targets)


def _is_direct_uns_write(statement: ast.stmt, object_name: str) -> bool:
    targets: list[ast.AST] = []
    if isinstance(statement, ast.Assign):
        targets = list(statement.targets)
    elif isinstance(statement, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
        targets = [statement.target]
    for target in targets:
        if (isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Attribute)
                and target.value.attr == "uns"
                and _name(target.value.value) == object_name):
            return True
        if (isinstance(target, ast.Attribute) and target.attr == "uns"
                and _name(target.value) == object_name):
            return True
    return False


def _object_may_be_mutated(statement: ast.stmt, object_name: str) -> bool:
    """Opaque access after the writer may change or alias the shared ``uns`` dictionary."""
    if _targets_root(statement, object_name) or _is_direct_uns_write(statement, object_name):
        return True
    # No other call summary is admitted inside this tiny chain.  Even a no-argument call may mutate
    # module state or an alias retained before the marker write, so every intervening call is opaque
    # havoc rather than being declared harmless from lack of a visible ``adata`` argument.
    if any(isinstance(item, ast.Call) for item in ast.walk(statement)):
        return True
    # Escaping the identity through an assignment is enough to lose must-flow: a later alias
    # mutation need not mention the original name.
    return object_name in _names_loaded(statement)


def _table_may_be_mutated(statement: ast.stmt, table_name: str) -> bool:
    return (_targets_root(statement, table_name)
            or table_name in _names_loaded(statement)
            or any(isinstance(item, ast.Call) for item in ast.walk(statement)))


def _contains_object_identity(node: ast.AST, object_name: str) -> bool:
    """Whether an expression can retain the AnnData/uns identity (not merely a detached value)."""
    if isinstance(node, ast.Name):
        return node.id == object_name
    if isinstance(node, ast.Attribute) and _name(node.value) == object_name:
        # These values do not expose the parent AnnData's ``uns`` dictionary.  In particular this
        # keeps the ordinary ``fit_predict(adata.X)`` selection path in scope.
        return node.attr not in {"X", "obs", "var"}
    return any(_contains_object_identity(child, object_name) for child in ast.iter_child_nodes(node))


def _identity_was_aliased(statements: list[ast.stmt], object_name: str) -> bool:
    """Reject a pre-existing alias that could mutate the same object/key under another name."""
    for statement in statements:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        if _contains_object_identity(statement.value, object_name):
            return True
    return False


def _names_egress_method(text: str) -> bool:
    """True if a string literal names an egress method — exactly (`"to_csv"`) or as a dotted patch
    target (`"pandas.core.generic.DataFrame.to_csv"`). Its presence signals egress dispatch may be
    monkeypatched, so the marker scoper must fail closed (#52)."""
    return text in _EGRESS_METHODS or any(text.endswith("." + method) for method in _EGRESS_METHODS)


def bind_marker_extraction_report_producers(sources) -> dict[str, ClaimProducer]:
    """Bind marker claims by exact extractor -> local variable -> literal egress flow.

    This is intentionally independent of the upstream marker call and AnnData object.  It classifies
    the report family, not the shared ``uns`` value's full provenance.  A parse gap, dynamic path,
    patched egress, competing filesystem-equivalent path writer, nested/opaque egress, DataFrame
    reassignment, or any opaque call while a marker DataFrame is live abstains rather than guessing.
    """
    parsed = parse_sources(sources)
    if any(item.tree is None for item in parsed):
        return {}

    sites_by_node = {id(site.call): site for site in iter_call_sites(parsed)}
    path_counts: dict[str, int] = {}
    dynamic_path = False

    for parsed_source in parsed:
        assert parsed_source.tree is not None
        if any(terminal_symbol(item) in {
            "exec", "eval", "globals", "locals", "vars", "getattr", "setattr",
            "__getattribute__", "__setattr__",
        } for item in ast.walk(parsed_source.tree) if isinstance(item, ast.Call)):
            return {}
        # A string literal naming an egress method (e.g. `patch("pandas...DataFrame.to_csv")` or
        # `mp.setattr("...to_parquet", fake)`) is the tell-tale of a monkeypatch of the output method,
        # which makes the `<df>.to_csv(path)` link unsound. No honest analysis references its own output
        # method by string, so fail closed (#52, red-team blocker 6).
        if any(_names_egress_method(item.value)
               for item in ast.walk(parsed_source.tree)
               if isinstance(item, ast.Constant) and isinstance(item.value, str)):
            return {}
        for call in (item for item in ast.walk(parsed_source.tree)
                     if isinstance(item, ast.Call)
                     and isinstance(item.func, ast.Attribute)
                     and item.func.attr in _EGRESS_METHODS):
            path_node = _path_arg(call)
            literal = const_str(path_node) if path_node is not None else None
            path = (_normalize_relative_report_path(literal)
                    if literal is not None else None)
            if path is None:
                dynamic_path = True
            else:
                path_counts[path] = path_counts.get(path, 0) + 1
    if dynamic_path:
        return {}

    bindings: dict[str, ClaimProducer] = {}
    for parsed_source in parsed:
        assert parsed_source.tree is not None
        env = source_env(parsed_source)
        if _EGRESS_METHODS & env.patched_attrs:
            return {}

        # A name is present only while its current value is proved to be marker-extracted.  The
        # producer summary follows aliases, while any other assignment clears the target name.
        live: dict[str, ClaimProducer] = {}
        for statement in parsed_source.tree.body:
            egress = _statement_call(statement)
            if (egress is not None and isinstance(egress.func, ast.Attribute)
                    and egress.func.attr in _EGRESS_METHODS):
                path_node = _path_arg(egress)
                literal = const_str(path_node) if path_node is not None else None
                path = (_normalize_relative_report_path(literal)
                        if literal is not None else None)
                receiver = _name(egress.func.value)
                producer = live.get(receiver) if receiver is not None else None
                nested_calls = sum(isinstance(item, ast.Call) for item in ast.walk(statement)) > 1
                if (path is not None and path_counts.get(path) == 1 and producer is not None
                        and not nested_calls):
                    # Preserve the pre-hardening raw binding key: normalization may only discover
                    # collisions, never make a previously unmatched spelling classify a claim.
                    assert literal is not None
                    bindings[literal] = producer
                if producer is not None and not nested_calls:
                    # Direct ``to_csv``/``to_parquet`` on a proved frame is the one reviewed call.
                    continue
                if live:
                    # An egress-shaped call on any other receiver (or with a nested call) is opaque.
                    live.clear()
                continue

            assignment = None
            if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                targets = (statement.targets if isinstance(statement, ast.Assign)
                           else [statement.target])
                if len(targets) == 1 and isinstance(targets[0], ast.Name):
                    assignment = (targets[0].id, statement.value)
            if assignment is not None:
                target, value = assignment
                site = sites_by_node.get(id(value))
                resolved = resolve_callee(site, env) if site is not None else None
                nested_calls = sum(isinstance(item, ast.Call)
                                   for item in ast.walk(statement)) > 1
                if resolved in _EXTRACT_IDENTITIES and not nested_calls:
                    live[target] = ClaimProducer(
                        site.id,
                        _MARKER_EXTRACT_CONTRACT,
                        "rank_genes_groups_df",
                        "marker_extract",
                        marker_family="rank_genes_groups",
                    )
                    continue
                if isinstance(value, ast.Name) and value.id in live:
                    live[target] = live[value.id]
                    continue
                live.pop(target, None)

            # A call that is not the exact extractor or direct reviewed live-frame egress may
            # rebind a global/closure alias or patch DataFrame egress without naming the frame.
            if live and _has_opaque_call(statement, sites_by_node, env):
                live.clear()
                continue

            # Compound control flow and in-place/opaque uses are outside the short proof.  Clear any
            # live name they load or store; unrelated preamble code cannot affect a future frame.
            touched = {item.id for item in ast.walk(statement)
                       if isinstance(item, ast.Name)}
            touched_producers = {live[name] for name in touched & live.keys()}
            if touched_producers:
                live = {name: producer for name, producer in live.items()
                        if producer not in touched_producers}

    return bindings


def bind_uns_marker_report_producers(sources) -> dict[str, ClaimProducer]:
    """Return only report paths with a proved marker-test must-producer.

    Supported chains are straight-line, top-level, and contained in one parsed source.  Literal
    paths are globally unique across ``to_csv``/``to_parquet`` egresses.  Marker keys are
    last-writer state, but multiple or dynamic writers make that state ambiguous and therefore
    produce no binding.
    """
    from sc_referee.sink_use import bind_sinks

    parsed = parse_sources(sources)
    if any(item.tree is None for item in parsed):
        return {}
    sites = iter_call_sites(parsed)
    sites_by_node = {id(site.call): site for site in sites}
    sink_uses = {use.callsite_id: use for use in bind_sinks(sources).uses}

    writers: list[_Writer] = []
    extracts: list[_Extract] = []
    egresses: list[_Egress] = []
    statements_by_source: dict[int, list[ast.stmt]] = {}
    dynamic_marker_writer = False
    dynamic_path = False
    unsafe_reflection = False
    all_path_counts: dict[str, int] = {}

    for parsed_source in parsed:
        assert parsed_source.tree is not None
        statements = list(parsed_source.tree.body)
        statements_by_source[parsed_source.source_index] = statements
        env = source_env(parsed_source)
        # Every egress-shaped call counts as a possible writer, including nested/chained calls that
        # are outside the supported producer chain.  Otherwise an unmodelled competing writer could
        # be ignored merely because it occurred under a branch.
        for possible_egress in (item for item in ast.walk(parsed_source.tree)
                                if isinstance(item, ast.Call)
                                and isinstance(item.func, ast.Attribute)
                                and item.func.attr in _EGRESS_METHODS):
            path_node = _path_arg(possible_egress)
            path = const_str(path_node) if path_node is not None else None
            if path is None:
                dynamic_path = True
            else:
                all_path_counts[path] = all_path_counts.get(path, 0) + 1
        if any(terminal_symbol(item) in {
            "exec", "eval", "globals", "locals", "vars", "getattr", "setattr",
            "__getattribute__", "__setattr__",
        } for item in ast.walk(parsed_source.tree) if isinstance(item, ast.Call)):
            unsafe_reflection = True
        for statement_index, statement in enumerate(statements):
            call = _statement_call(statement)
            if call is not None:
                site = sites_by_node.get(id(call))
                use = sink_uses.get(site.id) if site is not None else None
                if use is not None and use.contract.contract_id in _MARKER_CONTRACTS:
                    object_name = _name(_arg(call, "adata", 0))
                    key = _literal_keyword(call, "key_added", _DEFAULT_MARKER_KEY)
                    if object_name is None or key is None:
                        dynamic_marker_writer = True
                    else:
                        writers.append(_Writer(
                            parsed_source.source_index,
                            statement_index,
                            object_name,
                            key,
                            ClaimProducer(
                                use.callsite_id,
                                use.contract.contract_id,
                                use.contract.symbol,
                                use.contract.sink_kind,
                            ),
                        ))
                if (isinstance(call.func, ast.Attribute)
                        and call.func.attr in _EGRESS_METHODS
                        and call.func.attr not in env.patched_attrs):
                    path_node = _path_arg(call)
                    path = const_str(path_node) if path_node is not None else None
                    table_name = _name(call.func.value)
                    if path is not None and table_name is not None:
                        egresses.append(_Egress(
                            parsed_source.source_index, statement_index, table_name, path,
                        ))

            assignment = _assignment_call(statement)
            if assignment is None:
                continue
            table_name, extract_call = assignment
            site = sites_by_node.get(id(extract_call))
            resolved = resolve_callee(site, env) if site is not None else None
            if resolved not in _EXTRACT_IDENTITIES:
                continue
            object_name = _name(_arg(extract_call, "adata", 0))
            key = _literal_keyword(extract_call, "key", _DEFAULT_MARKER_KEY)
            if object_name is not None and key is not None:
                extracts.append(_Extract(
                    parsed_source.source_index, statement_index, object_name, key, table_name,
                ))

    # Nested marker writers are not in the straight-line inventory.  If SinkUse saw one, it is a
    # competing possible writer and defeats the must-flow proof.
    if len([use for use in sink_uses.values()
            if use.contract.contract_id in _MARKER_CONTRACTS]) != len(writers):
        return {}
    if dynamic_marker_writer or dynamic_path or unsafe_reflection:
        return {}

    writer_counts: dict[str, int] = {}
    for writer in writers:
        writer_counts[writer.key] = writer_counts.get(writer.key, 0) + 1
    bindings: dict[str, ClaimProducer] = {}
    for extract in extracts:
        if writer_counts.get(extract.key) != 1:
            continue
        reaching = [writer for writer in writers
                    if writer.source_index == extract.source_index
                    and writer.object_name == extract.object_name
                    and writer.key == extract.key
                    and writer.statement_index < extract.statement_index]
        if len(reaching) != 1:
            continue
        writer = reaching[0]
        statements = statements_by_source[extract.source_index]
        if _identity_was_aliased(statements[:writer.statement_index], extract.object_name):
            continue
        if any(_object_may_be_mutated(statement, extract.object_name)
               for statement in statements[writer.statement_index + 1:extract.statement_index]):
            continue

        matching_egresses = [egress for egress in egresses
                             if egress.source_index == extract.source_index
                             and egress.table_name == extract.table_name
                             and egress.statement_index > extract.statement_index]
        for egress in matching_egresses:
            if all_path_counts.get(egress.path) != 1:
                continue
            if any(_table_may_be_mutated(statement, extract.table_name)
                   for statement in statements[extract.statement_index + 1:egress.statement_index]):
                continue
            bindings[egress.path] = writer.producer
    return bindings
