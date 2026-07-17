"""Correction coverage (v0) — a static disclosure, no data and no judgment.

Reports one fact: an analysis computed a per-key correction factor for keys K, applied it to A ⊂ K,
and never applied it to K∖A — and, where establishable, which of K∖A are read by a construct that
selects the analysis population.

Why this fact
-------------
On the motivating benchmark, all four transcripts do exactly this:

    genes = ["HBB","IFI6","ISG15","LST1","CXCL10"]
    p_amb = {g: empty[g].sum()/empty.total_umi.sum() for g in genes}   # computed for 5
    ...
    amb   = rho*tu*p_amb["CXCL10"]                                     # applied to 2
    rho   = c.HBB/(c.total_umi*p_amb["HBB"])

`p_amb["IFI6"]`, `p_amb["ISG15"]` and `p_amb["LST1"]` are computed and never used. Those three are
the inputs to the Gaussian-mixture gate that defines the analysis population — the stage where the
sign of the reported effect is decided.

Why it is sound
---------------
This is an *internal* inconsistency between what the program computes and what it uses. It asserts
nothing about physics: not that ambient RNA is additive, not that the gate ought to be corrected,
not that the analysis is wrong. Leaving a key uncorrected may be entirely right. The module reports
coverage and stops.

Contrast with the sibling module: `materialization` needs bound data and a per-row quantity, and it
reaches one of the four transcripts. This needs neither, and reaches four.
"""
from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict, dataclass

SCANNER_VERSION = "correction_coverage.v0"

# Same contract as materialization: mechanically determined, and NO STATUS MEANS "clean".
STATUS_NO_IN_SCOPE_CONSTRUCT = "NO_IN_SCOPE_CONSTRUCT"
STATUS_COMPLETE = "COMPLETE"
STATUS_PRECONDITION_FAILED = "PRECONDITION_FAILED"

DISCLOSURE = (
    "A per-key factor {name} was computed for {n_computed} key(s) and applied to {n_applied}. "
    "Key(s) {unapplied} were computed and never applied. This diagnostic reports coverage only. "
    "It does not establish that the unapplied keys should have been corrected, nor that the "
    "analysis is incorrect."
)

SELECTION_NOTE = (
    "Of the keys computed and never applied, {reached} are read by the construct at line "
    "{lineno} whose output is used to select rows. Reported as a dependency fact; whether the "
    "selection should read a corrected form is not established here."
)


@dataclass(frozen=True)
class FactorProducer:
    """A per-key factor the analysis built. Never judged."""

    name: str
    lineno: int
    expression: str
    computed_keys: tuple
    applied_keys: tuple
    unapplied_keys: tuple


@dataclass(frozen=True)
class SelectionRead:
    """A construct whose output selects rows, and the factor keys reachable from its input."""

    lineno: int
    call: str
    keys_read: tuple


@dataclass(frozen=True)
class CoverageRecord:
    scanner_version: str
    scanner_digest: str
    source_digest: str
    status: str
    scan_scope: tuple
    producers: tuple = ()
    selections: tuple = ()
    disclosures: tuple = ()

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True, default=str)


def _digest(payload: str) -> str:
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def _self_digest() -> str:
    from pathlib import Path
    return "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- producers


def _str_lists(tree):
    out = {}
    for stmt in ast.walk(tree):
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                and isinstance(stmt.targets[0], ast.Name) and isinstance(stmt.value, ast.List):
            items = [e.value for e in stmt.value.elts
                     if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if items and len(items) == len(stmt.value.elts):
                out[stmt.targets[0].id] = tuple(items)
    return out


def _keys_of(node, str_lists):
    """A list literal, or a name bound to one."""
    if isinstance(node, ast.List):
        vals = [e.value for e in node.elts
                if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        return tuple(vals) if len(vals) == len(node.elts) else None
    if isinstance(node, ast.Name):
        return str_lists.get(node.id)
    return None


def _find_producers(tree, str_lists):
    """Two shapes, both meaning 'a factor per key':

        NAME = {k: ... for k in KEYS}          # dict comprehension
        NAME = FRAME[KEYS].sum() / <expr>      # a Series indexed by KEYS
    """
    out = []
    for stmt in ast.walk(tree):
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        if not isinstance(stmt.targets[0], ast.Name):
            continue
        name, lineno = stmt.targets[0].id, getattr(stmt, "lineno", 0)

        if isinstance(stmt.value, ast.DictComp):
            keys = _keys_of(stmt.value.generators[0].iter, str_lists)
            if keys:
                out.append((name, lineno, ast.unparse(stmt.value), keys))
            continue

        # FRAME[KEYS].sum() / <expr>
        node = stmt.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            node = node.left
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "sum" and isinstance(node.func.value, ast.Subscript)):
            keys = _keys_of(node.func.value.slice, str_lists)
            if keys:
                out.append((name, lineno, ast.unparse(stmt.value), keys))
    return out


def _aliases(tree, names):
    """`b = amb` — one hop only. Anything richer is not resolved and simply is not counted."""
    out = {}
    for stmt in ast.walk(tree):
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                and isinstance(stmt.targets[0], ast.Name) and isinstance(stmt.value, ast.Name) \
                and stmt.value.id in names:
            out[stmt.targets[0].id] = stmt.value.id
    return out


def _applied_keys(tree, producer_name, alias_of):
    """Every `NAME[<literal>]` read, following one-hop aliases."""
    live = {producer_name} | {a for a, target in alias_of.items() if target == producer_name}
    used = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
                and node.value.id in live and isinstance(node.slice, ast.Constant)
                and isinstance(node.slice.value, str)):
            used.add(node.slice.value)
    return used


# --------------------------------------------------------------------------- selections


_SELECTOR_CALLS = ("fit", "fit_predict", "predict", "fit_transform")


def _last_writes(tree):
    out = {}
    for stmt in ast.walk(tree):
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                and isinstance(stmt.targets[0], ast.Name):
            out[stmt.targets[0].id] = stmt.value
    return out


def _reachable_strings(node, writes, str_lists, depth=0, seen=None):
    """String keys reachable from an expression, following Name -> its last write.

    Bounded, and deliberately over-approximate on the read side: it may report a key the construct
    does not truly depend on. That direction is safe here -- the output is disclosure, and an
    over-broad read set makes the disclosure weaker, never accusatory.
    """
    if depth > 6:
        return set()
    seen = seen if seen is not None else set()
    out = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            out.add(sub.value)
        elif isinstance(sub, ast.Name):
            if sub.id in str_lists:
                out.update(str_lists[sub.id])
            if sub.id in writes and sub.id not in seen:
                out.update(_reachable_strings(writes[sub.id], writes, str_lists,
                                              depth + 1, seen | {sub.id}))
    return out


def _find_selections(tree, str_lists):
    writes = _last_writes(tree)
    out = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr not in _SELECTOR_CALLS or not node.args:
            continue
        keys = _reachable_strings(node.args[0], writes, str_lists)
        out.append((getattr(node, "lineno", 0), ast.unparse(node)[:80], tuple(sorted(keys))))
    return out


# --------------------------------------------------------------------------- entry


def scan(source: str) -> CoverageRecord:
    """Report per-key correction coverage. Static only: no data is bound and none is needed."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return CoverageRecord(
            scanner_version=SCANNER_VERSION, scanner_digest=_self_digest(),
            source_digest=_digest(source), status=STATUS_PRECONDITION_FAILED,
            scan_scope=({"construct_class": "parse", "found": 0, "reason": str(exc)},),
        )

    str_lists = _str_lists(tree)
    raw = _find_producers(tree, str_lists)
    alias_of = _aliases(tree, {n for n, _, _, _ in raw})
    selections = [SelectionRead(ln, call, keys) for ln, call, keys in _find_selections(tree, str_lists)]

    producers, disclosures = [], []
    seen_facts = set()
    for name, lineno, expr, keys in raw:
        applied = _applied_keys(tree, name, alias_of) & set(keys)
        unapplied = tuple(k for k in keys if k not in applied)
        producers.append(FactorProducer(name, lineno, expr, tuple(keys),
                                        tuple(sorted(applied)), unapplied))

        # The reportable fact is PARTIAL application: some keys used, others not, from one
        # producer. That is an internal inconsistency in the program's own use of what it built.
        #
        # Two neighbouring cases are deliberately NOT this fact:
        #   applied == keys  -> nothing unapplied; nothing to say.
        #   applied == {}    -> the producer is dead or duplicated (run D builds the same dict
        #                       twice and uses one). That is unused-computation, a different and
        #                       weaker fact, and reporting it here buries the signal. On the
        #                       motivating benchmark, admitting it produced 6 disclosures on one
        #                       transcript, 5 of them noise.
        if not unapplied or not applied:
            continue

        # Same fact from two producers is one fact. Run B builds the profile twice, identically.
        fact_key = (tuple(sorted(keys)), tuple(sorted(applied)))
        if fact_key in seen_facts:
            continue
        seen_facts.add(fact_key)
        text = DISCLOSURE.format(name=name, n_computed=len(keys), n_applied=len(applied),
                                 unapplied=", ".join(unapplied))
        for sel in selections:
            reached = tuple(k for k in unapplied if k in sel.keys_read)
            if reached:
                text += " " + SELECTION_NOTE.format(reached=", ".join(reached), lineno=sel.lineno)
                break
        disclosures.append({"producer": name, "lineno": lineno, "text": text})

    status = STATUS_NO_IN_SCOPE_CONSTRUCT if not producers else STATUS_COMPLETE
    return CoverageRecord(
        scanner_version=SCANNER_VERSION,
        scanner_digest=_self_digest(),
        source_digest=_digest(source),
        status=status,
        scan_scope=(
            {"construct_class": "per_key_factor_producer", "found": len(producers)},
            {"construct_class": "partially_applied_producer",
             "found": sum(1 for p in producers if p.applied_keys and p.unapplied_keys)},
            {"construct_class": "unused_producer",
             "found": sum(1 for p in producers if not p.applied_keys), "in_scope": False,
             "note": "Computed and never applied at all: dead or duplicated. Recorded, not "
                     "disclosed as a coverage fact."},
            {"construct_class": "row_selecting_construct", "found": len(selections)},
        ),
        producers=tuple(producers), selections=tuple(selections),
        disclosures=tuple(disclosures),
    )
