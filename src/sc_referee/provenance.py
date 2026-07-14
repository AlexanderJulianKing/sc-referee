"""Layer 2 — deterministic provenance / data-flow (Phase A, increment 1).

Classify each marker/DE test's grouping column by WHERE ITS VALUES CAME FROM, not by the name of the
method that produced them. A grouping is `data_derived` when its values trace — through visible
assignments and calls — back to the expression matrix or anything derived from it: `.X`, `.raw`,
`.layers[…]`, an expression embedding `.obsm['X_*']` (X_pca / X_umap / X_scvi / … — but NOT external
coordinates like `obsm['spatial']`), a data-derived `obs` column (annotated clusters,
`obs['ct']=obs['leiden'].map(...)`), or the output of a clustering call. It is
`predefined_within_program` when it traces only to row-metadata / literals / non-expression sources;
`unresolved` when the `groupby` is not a literal (or its origin cannot be seen). Method-agnostic by
construction: a bespoke `discover_subpops(X_pca)` is caught exactly like `leiden`, because taint
follows the *data*, not the name.

Scope (Phase A — see the design notes). This computes the MAY-level
origin that drives the bundle verdict (`data_derived` → needs_evidence) and the audit-path applies-to
gate. The finer machinery the spec requires for a *blocker* — must/definite dependence with reaching
definitions and pinned-path feasibility, proven selection/test overlap, the calibration/claim/
reachability tri-states, coverage completeness, and closed-world binding — is deferred to later
increments; until then a data-derived grouping *escalates* (it never silently accuses or clears).
Remaining known gaps, each failing SAFE (over-escalate/abstain, never a silent clean): the may/must
split (a syntactic read of `X` that does not semantically depend on it is treated as data-derived — an
over-escalation); coverage/havoc from opaque calls. A non-`X_` embedding written IN-SCRIPT from an
opaque call (e.g. `obsm['scVI'] = model.get_latent_representation()` — the scvi/harmony integration
pattern) is now `unresolved` (abstain), not a silent clean (task #47): we cannot prove it is
expression-derived, but neither can we prove it is external, so a grouping tracing to it escalates to
needs_evidence. Opacity propagates like data taint — through obs relabels, local variables, and (via a
monotonic may-set) across branches — so lexical branch order cannot silently clear. Residual: opaque
writes via tuple-unpacking or augmented assignment are not tracked (rare); and an in-script obsm write
from ANY call — including an external-coordinate loader like `obsm['spatial'] = load_coords(...)` —
abstains to `unresolved` (a deliberate, SAFE over-abstention: needs_evidence, never a false clean),
whereas external coordinates that arrive WITH the AnnData (no in-script write) stay predefined.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field

# The shared front-end (parse / normalize / enumerate) lives in source_ast so this taint pass and
# sink_use bind against the SAME calls and the SAME call-site ids (adversarial design consult, Q1).
# Imported under the old private names to keep this hardened engine's body unchanged.
from sc_referee.source_ast import (
    callsite_id,
    const_str as _const_str,
    func_name as _func_name,
    ordered_statements as _ordered_stmts,
    parse_sources,
    strip_magics as _strip_magics,
    to_python as _to_python,
)

# `obs`-object attributes that ARE the primary data. NB: `.obs` itself is ROW METADATA, not data.
_DATA_ATTRS = ("X", "raw")
# `.layers[...]` is always the expression matrix. `.obsm[...]` is expression ONLY for an expression
# embedding — scanpy writes those with an `X_` prefix (X_pca / X_umap / X_scvi / X_harmony / …).
# `obsm['spatial']` and other externally-supplied coordinates are NOT expression-derived, so clustering
# on them and testing genes is not circular w.r.t. the genes (adversarial review spatial-coords false-accuse, §4.1).
_EXPRESSION_OBSM_PREFIX = "X_"
_EXPRESSION_OBSM_EXTRA = frozenset({"X"})   # some pipelines store the reduction as obsm['X']
# clustering routines that write an `obs` column from the data, and their default column names.
_CLUSTER_KEYS = {"leiden": "leiden", "louvain": "louvain"}
_MARKER_FUNCS = ("rank_genes_groups", "findmarkers", "findallmarkers")
# keywords that redirect an implicit clustering call away from the AnnData's own (data-derived) graph.
_CLUSTER_INPUT_KWARGS = ("adjacency", "obsp", "connectivity")
# a receiver is treated as the primary AnnData only if it is a known identity: a conventional name or a
# variable bound to an AnnData constructor/reader (finding 9 — `metadata.X` must not be the matrix).
_ADATA_NAMES = frozenset({"adata", "ad", "andata", "adata_raw"})
# Readers/constructors that return an AnnData. NB: `read` covers scanpy's `sc.read(...)`; `pd.read_csv`
# (fn `read_csv`) is deliberately absent — it returns a DataFrame, not an AnnData.
_ADATA_READERS = frozenset({"anndata", "read", "read_h5ad", "read_10x_h5", "read_10x_mtx", "read_loom",
                            "read_text", "read_mtx", "read_visium", "read_umi_tools"})


@dataclass
class MarkerTest:
    groupby: str | None            # the literal groupby column, or None when it is not a literal
    origin: str                    # "data_derived" | "predefined_within_program" | "unresolved"
    evidence: list = field(default_factory=list)
    callsite_id: str | None = None  # shared source_ast id — joins this test to its SinkUse (step 5)


def _receiver_is_adata(node, adata_ids) -> bool:
    """Does this expression resolve to the primary AnnData object? (a tracked identity, `adata.raw`,
    `adata[mask]`, or `adata.copy()`)."""
    if isinstance(node, ast.Name):
        return node.id in adata_ids
    if isinstance(node, ast.Attribute) and node.attr == "raw":
        return _receiver_is_adata(node.value, adata_ids)
    if isinstance(node, ast.Subscript):
        return _receiver_is_adata(node.value, adata_ids)
    if isinstance(node, ast.Call) and _func_name(node) == "copy" and isinstance(node.func, ast.Attribute):
        return _receiver_is_adata(node.func.value, adata_ids)
    return False


def _is_adata_expr(value, adata_ids) -> bool:
    """Does this RHS produce an AnnData? (an alias, a reader/constructor call, a slice/copy)."""
    if isinstance(value, ast.Name):
        return value.id in adata_ids
    if isinstance(value, ast.Call):
        fn = _func_name(value)
        if fn in _ADATA_READERS:
            return True
        if fn == "copy" and isinstance(value.func, ast.Attribute):
            return _receiver_is_adata(value.func.value, adata_ids)
    if isinstance(value, (ast.Subscript, ast.Attribute)):
        return _receiver_is_adata(value, adata_ids)
    return False


def _reads_data(node: ast.AST, tainted: set, col_state: dict, obsm_data: set, adata_ids: set) -> bool:
    """True if the expression touches the primary AnnData's data — its `.X`/`.raw`, a `.layers[…]`, an
    expression `.obsm[…]` (X_-prefixed OR a key visibly written from data), a `.obs['G']` where G is a
    data-derived column (annotated clusters), or an already-tainted variable. Only a KNOWN AnnData
    receiver counts (`metadata.X` is not the matrix). Sticky: any such read anywhere taints the whole
    expression."""
    for n in ast.walk(node):
        if isinstance(n, ast.Attribute) and n.attr in _DATA_ATTRS and _receiver_is_adata(n.value, adata_ids):
            return True
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Attribute):
            attr, recv = n.value.attr, n.value.value
            if attr == "layers" and _receiver_is_adata(recv, adata_ids):
                return True
            if attr == "obsm" and _receiver_is_adata(recv, adata_ids):
                key = _const_str(n.slice)
                if key is not None and (key.startswith(_EXPRESSION_OBSM_PREFIX)
                                        or key in _EXPRESSION_OBSM_EXTRA or key in obsm_data):
                    return True
            if attr == "obs":
                key = _const_str(n.slice)
                if key is not None and col_state.get(key) == "data":
                    return True
        if isinstance(n, ast.Name) and n.id in tainted:
            return True
    return False


def _reads_opaque(node: ast.AST, obsm_opaque: set, col_state: dict, opaque_tainted: set,
                  adata_ids: set) -> bool:
    """The opaque-taint mirror of `_reads_data`: True if the expression reads an embedding of UNPROVEN
    provenance — an `.obsm['K']` written IN-SCRIPT from an opaque call (`obsm['scVI'] =
    model.get_latent_representation()`), an `.obs['G']` column already classified `"opaque"`, or an
    already-opaque local variable. Such a value is neither provably expression-derived (not
    `data_derived`) nor provably external (not a silent clean): a grouping tracing to it is
    `unresolved` (abstain). Propagating through obs columns and locals — exactly as data taint does —
    keeps branch order, relabels, and intermediates from silently clearing (task #47)."""
    for n in ast.walk(node):
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Attribute):
            attr, recv = n.value.attr, n.value.value
            if attr == "obsm" and _receiver_is_adata(recv, adata_ids):
                key = _const_str(n.slice)
                if key is not None and key in obsm_opaque:
                    return True
            if attr == "obs":
                key = _const_str(n.slice)
                if key is not None and col_state.get(key) == "opaque":
                    return True
        if isinstance(n, ast.Name) and n.id in opaque_tainted:
            return True
    return False


def _obs_target_col(target, adata_ids):
    """If `target` is `<adata>.obs['G']`, return 'G'; else None."""
    if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Attribute) \
            and target.value.attr == "obs" and _receiver_is_adata(target.value.value, adata_ids):
        return _const_str(target.slice)
    return None


def _obsm_target_key(target, adata_ids):
    """If `target` is `<adata>.obsm['K']`, return 'K'; else None (finding 4a)."""
    if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Attribute) \
            and target.value.attr == "obsm" and _receiver_is_adata(target.value.value, adata_ids):
        return _const_str(target.slice)
    return None


def _cluster_key_added(call: ast.Call) -> str:
    col = _CLUSTER_KEYS[_func_name(call)]
    for kw in call.keywords:
        if kw.arg == "key_added" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            col = kw.value.value
    return col


def _cluster_output_is_data(call, tainted, col_state, obsm_data, adata_ids) -> bool:
    """An implicit clustering call's output is data-derived only if its operative input is. If it
    redirects to an explicit adjacency/graph, judge THAT input; otherwise it clusters the AnnData's own
    (data-derived) neighbor graph (finding 4b: external adjacency must not be assumed data-derived)."""
    for kw in call.keywords:
        if kw.arg in _CLUSTER_INPUT_KWARGS:
            return _reads_data(kw.value, tainted, col_state, obsm_data, adata_ids)
    return True


def _assign_targets_value(stmt):
    """(targets, value) for a plain or annotated assignment; ([], None) otherwise. AnnAssign
    (`x: T = v`) must not lose taint (finding 7)."""
    if isinstance(stmt, ast.Assign):
        return stmt.targets, stmt.value
    if isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
        return [stmt.target], stmt.value
    return [], None


def _flat_targets(tgt):
    """Yield leaf targets, unpacking tuple/list destructuring (`labels, centers = …`, finding 7)."""
    if isinstance(tgt, (ast.Tuple, ast.List)):
        for e in tgt.elts:
            yield from _flat_targets(e)
    else:
        yield tgt


def _literal_groupby(call: ast.Call):
    """The marker call's grouping column as a literal string, or None when it is dynamic."""
    for kw in call.keywords:
        if kw.arg in ("groupby", "group_by"):
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                return kw.value.value
            return None                                   # present but not a literal → unresolved
    if len(call.args) >= 2:                               # scanpy positional: (adata, groupby, …)
        g = call.args[1]
        if isinstance(g, ast.Constant) and isinstance(g.value, str):
            return g.value
    return None


def groupby_provenance(sources: list) -> list:
    """Classify every marker/DE test's grouping across a bundle's step sources. Obs columns form one
    shared namespace across steps (a step writes `obs['G']`, a later step tests `groupby='G'`), so
    column origins accumulate across sources; local variables do not and are reset per source."""
    parsed = parse_sources(sources)          # shared front-end: same normalization + call-site ids
    parse_failed_markers = 0
    for ps in parsed:
        if ps.tree is None:
            # a step that won't parse but textually calls a marker function is a marker test we could
            # not analyze -> surface it as unresolved, never let it vanish (finding 3).
            code = _strip_magics(_to_python(sources[ps.source_index]))
            if any(fn in code.lower() for fn in _MARKER_FUNCS):
                parse_failed_markers += 1

    # Flow-sensitive single pass. State carried ACROSS sources (one shared `obs`/`obsm` namespace and
    # AnnData-identity set); local variable taint is reset per source. Statements are processed in
    # source order, so a later overwrite never re-interprets an earlier read (finding 6).
    col_state: dict = {}                     # obs col -> "data" | "opaque" | "meta"  (flow-sensitive, last write wins)
    may_data: set = set()                    # obs cols EVER written data-derived, in ANY branch (may-union)
    may_opaque: set = set()                  # obs cols EVER written opaque, in ANY branch (may-union, task #47)
    obsm_data: set = set()                   # obsm keys currently data-derived (finding 4a)
    obsm_opaque: set = set()                 # obsm keys written in-script from an opaque call (task #47)
    adata_ids: set = set(_ADATA_NAMES)       # AnnData identities (finding 9)
    results: list = []                       # (groupby, origin, callsite_id) at each marker test's position

    for ps in parsed:
        if ps.tree is None:
            continue
        tainted: set = set()                 # data-tainted local vars, reset per source
        opaque_tainted: set = set()          # opaque-tainted local vars, reset per source (task #47)
        for stmt in _ordered_stmts(ps.tree.body):
            # (A) assignment: propagate taint, track AnnData identity, obs columns, and obsm writes.
            targets, value = _assign_targets_value(stmt)
            if value is not None:
                is_data = _reads_data(value, tainted, col_state, obsm_data, adata_ids)
                # Opacity is a full mirror of data taint (never overrides it — is_data wins on a value
                # that visibly reads data). Evaluated once, against the pre-statement state, like is_data.
                is_opaque = (not is_data) and _reads_opaque(
                    value, obsm_opaque, col_state, opaque_tainted, adata_ids)
                is_adata = _is_adata_expr(value, adata_ids)
                for tgt in targets:
                    for leaf in _flat_targets(tgt):
                        if isinstance(leaf, ast.Name):
                            if is_data:
                                tainted.add(leaf.id); opaque_tainted.discard(leaf.id)
                            elif is_opaque:
                                opaque_tainted.add(leaf.id); tainted.discard(leaf.id)
                            else:
                                tainted.discard(leaf.id); opaque_tainted.discard(leaf.id)
                            if is_adata:
                                adata_ids.add(leaf.id)
                        col = _obs_target_col(leaf, adata_ids)
                        if col is not None:
                            if is_data:
                                col_state[col] = "data"
                                may_data.add(col)            # monotonic: possibly-data in SOME branch
                            elif is_opaque:
                                col_state[col] = "opaque"    # traces to an unproven-provenance embedding
                                may_opaque.add(col)          # monotonic: possibly-opaque in SOME branch
                            else:
                                col_state[col] = "meta"
                        okey = _obsm_target_key(leaf, adata_ids)
                        if okey is not None:
                            if is_data:                                  # provably expression-derived
                                obsm_data.add(okey); obsm_opaque.discard(okey)
                            elif isinstance(value, ast.Call):            # computed by an opaque call: provenance unknown
                                obsm_opaque.add(okey); obsm_data.discard(okey)
                            else:                                        # plain external value: clean
                                obsm_data.discard(okey); obsm_opaque.discard(okey)
            # (B) calls carried by THIS statement's own expression (nested statement bodies are yielded
            #     separately by _ordered_stmts, so scanning only `.value` avoids double-counting):
            #     implicit clustering writes, then marker tests, judged against the CURRENT state.
            expr = stmt.value if isinstance(stmt, ast.Expr) else value
            if expr is not None:
                for node in ast.walk(expr):
                    if not isinstance(node, ast.Call):
                        continue
                    fn = _func_name(node)
                    if fn in _CLUSTER_KEYS:
                        if _cluster_output_is_data(node, tainted, col_state, obsm_data, adata_ids):
                            col_state[_cluster_key_added(node)] = "data"
                    elif fn in _MARKER_FUNCS:
                        g = _literal_groupby(node)
                        if g is None:
                            origin = "unresolved"
                        elif col_state.get(g) == "data":
                            origin = "data_derived"
                        elif col_state.get(g) == "opaque":
                            origin = "unresolved"            # traces to an opaque-written embedding (task #47)
                        elif g in may_data:
                            origin = "unresolved"            # data-derived in some branch -> escalate (re-review #1)
                        elif g in may_opaque:
                            origin = "unresolved"            # opaque in some branch -> escalate, not order-dependent (#47)
                        else:
                            origin = "predefined_within_program"
                        cid = callsite_id(ps.source_index, node)
                        results.append((g, origin, cid))

    out = [MarkerTest(g, origin, callsite_id=cid) for g, origin, cid in results]
    for _ in range(parse_failed_markers):                 # marker calls in an unparseable step (finding 3)
        out.append(MarkerTest(None, "unresolved"))
    return out
