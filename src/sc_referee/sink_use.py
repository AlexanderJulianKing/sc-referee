"""SinkUse — bind a detected call site to a resolved sink contract (spine step 1b).

The layer every downstream check queries. For each recognized inferential call it maps the contract's
InputPorts onto the actual arguments and records HOW each was bound. Checks then reason over
`contract.sink_kind`, `InputPort.role`, and `ValueType` facets — they never re-derive method name-lists
(that divergence is what the registry exists to kill). An unknown facet means abstain/review.

Callee identity is a PROVED fact, not a name match. A call resolves to a library sink only through the
per-source import table (`import scanpy as sx` still resolves; a user's own `def ttest_ind` does NOT bind
to scipy). This is what keeps a false sink match from ever driving a false accusation, and stops an
aliased real sink from silently disappearing. (adversarial review #1/#2.)

v1 is deliberately STRUCTURAL. It does NOT infer assay scale, raw-count status, or experimental unit
from a bare call — `DeseqDataSet(counts=x)` is not proof `x` is raw counts. Those facets are computed
per-check, on demand, behind the unknown->abstain rule. The one value fact bound here is the grouping
port's ORIGIN, reused from the already-approved provenance taint (via the shared callsite id).

Safety over coverage: a `**kwargs`/`*args` splat that could hide an argument makes a port `unsupported`,
never a false `missing` (absence unproven). A step that fails to parse is surfaced as a DIAGNOSTIC, not
silently dropped, so a downstream check can force review instead of a false clean. (adversarial review #3/#6.)

Known gaps, all fail-safe (they under-cover or over-abstain; they never bind a wrong contract):
 - Only Python-parseable sources are bound. A Seurat `FindMarkers` in an `.R` file yields no SinkUse
   here; such R sinks are still surfaced for the bundle verdict by `code_signals`. An R-aware binder is
   future work.
 - Callee identity is resolved from STATIC imports + AST-visible rebinding/monkey-patching (Store
   targets, namespace subscripts/updates, setattr/patch.object). Rebinding through fully opaque dynamic
   channels — `exec`/`eval` of a string, aliased `globals()`, `sys.modules` swaps, `importlib` — is not
   AST-resolvable. Such obfuscation does not occur in single-cell analysis code and is outside the
   product's threat model; the resolver stays sound (abstains) rather than chasing it (frozen after
   adversarial re-review rounds 1-5).
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field

from sc_referee.provenance import groupby_provenance
from sc_referee.sinks import ValueType, resolve_sink_status, sink_symbols
from sc_referee.source_ast import (
    const_str,
    iter_call_sites,
    parse_sources,
    resolve_callee,
    source_env,
    terminal_symbol,
)

# provenance origin -> the ValueType.origins vocabulary (adversarial review Q2: reuse the approved taint fact only).
_ORIGIN_MAP = {"data_derived": "primary_data", "predefined_within_program": "metadata",
               "unresolved": "unknown"}


@dataclass(frozen=True)
class BoundPort:
    role: str
    status: str                    # bound | missing_optional | missing_required | unsupported | ambiguous | invalid_call
    expr: object | None            # the ast node bound to this port (None when not bound)
    source_text: str | None
    locator_used: object | None    # the PortLocator that matched, or None
    literal_value: object | None = None
    value_type: ValueType = field(default_factory=ValueType)


@dataclass(frozen=True)
class SinkUse:
    callsite_id: str
    contract: object               # SinkContract
    resolution_status: str         # "exact" | "version_unknown"  (only these two reach here)
    bound_ports: dict              # role -> BoundPort
    module: str                    # canonical module the callee resolved to
    symbol: str
    source_span: tuple             # (source_index, lineno, col_offset)


@dataclass(frozen=True)
class SinkBindResult:
    uses: list                     # list[SinkUse]
    diagnostics: list              # list[dict]: parse failures etc. — a step we could not analyze


def _literal(node):
    # NB: a bound non-literal and a literal `None` both yield None here; no consumer distinguishes them
    # in v1 (a future `literal_known` flag would). Only ast.Constant is treated as a known literal.
    return node.value if isinstance(node, ast.Constant) else None


def _bind_port(port, call: ast.Call) -> tuple:
    """Resolve one InputPort against a call. Keyword wins over positional; a param supplied BOTH ways is
    an invalid call; a splat that could hide the argument yields `unsupported` (not `missing`). Returns
    (status, expr, locator, literal_value)."""
    has_kwargs_splat = any(k.arg is None for k in call.keywords)          # **kwargs present
    kw_by_name = {k.arg: k.value for k in call.keywords if k.arg is not None}
    star_positions = [i for i, a in enumerate(call.args) if isinstance(a, ast.Starred)]
    first_star = star_positions[0] if star_positions else None

    kw_hits = [(loc, kw_by_name[loc.name]) for loc in port.locators
               if loc.kind == "kw" and loc.name in kw_by_name]
    arg_hits = [(loc, call.args[loc.index]) for loc in port.locators
                if loc.kind == "arg" and loc.index is not None
                and (first_star is None or loc.index < first_star) and loc.index < len(call.args)]
    recv_hits = [(loc, call.func.value) for loc in port.locators
                 if loc.kind == "receiver" and isinstance(call.func, ast.Attribute)]

    if len({id(e) for _, e in kw_hits}) > 1:          # two DISTINCT keyword sources for one role
        return "ambiguous", None, None, None
    if kw_hits and arg_hits:                           # same parameter given positionally AND by keyword
        return "invalid_call", None, None, None
    for hits in (kw_hits, arg_hits, recv_hits):        # keyword wins, then positional, then receiver
        if hits:
            loc, e = hits[0]
            return "bound", e, loc, _literal(e)

    if has_kwargs_splat or first_star is not None:     # the arg could be hidden in a splat -> can't prove absent
        return "unsupported", None, None, None
    return ("missing_required" if port.required else "missing_optional"), None, None, None


def _candidate(source_index, symbol, lineno, detail):
    return {"kind": "unresolved_sink_candidate", "source_index": source_index,
            "symbol": str(symbol).lower(), "lineno": lineno, "detail": detail}


def _referenced_sink_symbol(site, env, known):
    """The registered sink symbol a non-binding call references, or None. Its terminal name may BE a sink
    symbol, or its bare name may be a from-import alias whose ORIGINAL symbol is a sink — including an
    ambiguous or RELATIVE import (`welch` <- `ttest_ind`; `test` <- a relative `ttest_ind`). Reporting
    the underlying sink symbol keeps an abstained alias from silently vanishing (adversarial re-review #1/#6)."""
    if site.symbol in known:
        return site.symbol
    f = site.call.func
    if isinstance(f, ast.Name):
        b = env.imports.get(f.id)
        if b is not None and b.symbol is not None and b.symbol.lower() in known:
            return b.symbol.lower()
        for orig in env.alias_symbols.get(f.id, ()):     # ambiguous / relative alias of a sink symbol
            if orig.lower() in known:
                return orig.lower()
    return None


def _indirect_candidates(parsed, known) -> list:
    """Sink references that never appear as a direct resolvable call: a sink function taken as a VALUE
    (`test = sc.tl.rank_genes_groups`) or fetched via `getattr(x, "ttest_ind")`. Abstain + diagnose so
    the reference does not silently vanish (adversarial re-review #5). Emitting a review candidate — never a
    binding — for these keeps the never-false-accuse guarantee."""
    out = []
    for ps in parsed:
        if ps.tree is None:
            continue
        call_func_ids = {id(n.func) for n in ast.walk(ps.tree) if isinstance(n, ast.Call)}
        for node in ast.walk(ps.tree):
            if (isinstance(node, ast.Call)
                    and terminal_symbol(node) in ("getattr", "__getattribute__")):
                for a in node.args:                   # getattr(x,"n") -> arg1; x.__getattribute__("n") -> arg0
                    s = const_str(a)
                    if s is not None and s.lower() in known:
                        out.append(_candidate(ps.source_index, s, node.lineno,
                                              "a known sink referenced via getattr/__getattribute__"))
            elif isinstance(node, ast.Subscript):
                s = const_str(node.slice)             # `stats.__dict__["ttest_ind"](...)` etc.
                if s is not None and s.lower() in known:
                    out.append(_candidate(ps.source_index, s, node.lineno,
                                          "a known sink referenced via a subscript lookup"))
            elif (isinstance(node, ast.Attribute) and node.attr.lower() in known
                  and id(node) not in call_func_ids):
                out.append(_candidate(ps.source_index, node.attr, node.lineno,
                                      "a known sink referenced indirectly (aliased, not called directly)"))
    return out


def _dedupe(diags) -> list:
    seen, out = set(), []
    for d in diags:
        key = (d.get("kind"), d.get("source_index"), d.get("symbol"), d.get("lineno"))
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def bind_sinks(sources) -> SinkBindResult:
    """Every recognized inferential call in `sources`, bound to its contract, plus diagnostics for steps
    or references that could not be bound. Only import-proven, registry-known, case-exact calls become
    SinkUses; parse failures AND every sink-shaped call/reference that does not bind become diagnostics
    (never a silent drop). Sound over complete: it may abstain, but it never binds a wrong contract."""
    parsed = parse_sources(sources)
    diagnostics = [{"kind": "parse_error", "source_index": ps.source_index, "detail": ps.parse_error}
                   for ps in parsed if ps.tree is None]

    envs = {ps.source_index: source_env(ps) for ps in parsed}   # per-source name environments
    known = sink_symbols()
    origin_by_cid = {mt.callsite_id: mt.origin for mt in groupby_provenance(sources)
                     if mt.callsite_id is not None}

    uses = []
    for site in iter_call_sites(parsed):
        env = envs[site.source_index]
        canon = resolve_callee(site, env)                       # proved identity, or None
        contract = status = None
        if canon is not None:
            contract, status = resolve_sink_status(canon[1], canon[0])
        if contract is None:
            # a sink-shaped call that produced no SinkUse (unresolved / unknown module / version_mismatch
            # / ambiguous / monkey-patched) must be surfaced, not dropped (adversarial re-review #1/#6).
            ref = _referenced_sink_symbol(site, env, known)
            if ref is not None:
                diagnostics.append(_candidate(site.source_index, ref, site.lineno,
                                              "a call named like a known sink did not resolve to one"))
            continue
        bound = {}
        for port in contract.inputs:
            pstatus, expr, locator, literal = _bind_port(port, site.call)
            vt = ValueType()
            if port.role == "grouping":               # reuse the approved taint origin (adversarial review Q2)
                origin = _ORIGIN_MAP.get(origin_by_cid.get(site.id, "unresolved"), "unknown")
                vt = ValueType(kind="labels", unit="cell", origins=frozenset({origin}))
            bound[port.role] = BoundPort(
                role=port.role, status=pstatus, expr=expr,
                source_text=(ast.unparse(expr) if expr is not None else None),
                locator_used=locator, literal_value=literal, value_type=vt)
        uses.append(SinkUse(
            callsite_id=site.id, contract=contract, resolution_status=status, bound_ports=bound,
            module=contract.module, symbol=contract.symbol,   # the registry's canonical identity
            source_span=(site.source_index, site.lineno, site.col_offset)))

    diagnostics += _indirect_candidates(parsed, known)
    return SinkBindResult(uses, _dedupe(diagnostics))
