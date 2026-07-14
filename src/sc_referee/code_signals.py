"""Parse (never execute) the analysis code into signals.

The single most informative signal is `unit_of_test`: a call to `rank_genes_groups` /
`FindMarkers` / a per-cell Wilcoxon means the analyst tested CELLS as replicates. That is what
routes `experimental_unit`. When we cannot tell, we say "sample" — the conservative answer,
because it means the check does not fire rather than firing on an analysis we misread.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# APIs that are UNAMBIGUOUSLY per-cell: they take an AnnData/Seurat object and test cells.
DE_CELL = ("rank_genes_groups", "scanpy.tl.rank_genes_groups", "findmarkers", "findallmarkers")
# Calls that imply the unit is a SAMPLE: count models, or an explicit pseudobulk step.
DE_SAMPLE = ("deseqdataset", "deseqstats", "deseq2", "pydeseq2", "edger", "limma", "voom",
             "muscat", "pseudobulk", "aggregate_across_cells", "sceptre", "glmmtmb", "lmer")
# Tests that say NOTHING about the unit. `ttest_ind` on a 12 GB AnnData and `ttest_ind` on a
# 16-row pseudobulk matrix are the same three tokens. Treating these as per-cell (as we did)
# routed the pseudobulk-t-test failure to `experimental_unit`, whose recompute agrees on the unit
# and therefore finds nothing — making `count_model` UNREACHABLE. (Opus review 2026-07-08.)
DE_AMBIGUOUS = ("mannwhitneyu", "ranksums", "ttest_ind", "ttest_rel", "wilcoxon",
                "smf.ols", "sm.ols", "linregress")
CLUSTER = ("leiden", "louvain", "kmeans", "findclusters")
DA = ("milo", "sccoda", "propeller", "speckle", "dacseq")
# Selection-aware safeguards. Their PRESENCE is evidence for REVIEW, not a clearance: a keyword does
# not prove the safeguard is correctly applied (naive row-splitting can stay anti-conservative), so a
# detected safeguard yields `needs_evidence`, never a pass, until its contract is verified. (Detected,
# never executed.) See checks/double_dipping.py and the rev.5 spec §5.
SAFEGUARD = ("countsplit", "count_split", "count-split", "datathin", "data_thin", "data thinning",
             "clusterde", "cluster_de", "train_test_split", "train/test", "holdout", "held-out",
             "held_out", "heldout", "selective_inference", "selectiveinference")

# Tests that model the count distribution (NB / voom-weighted linear model).
# NB: `pseudobulk` is an AGGREGATION step, not a count model — it must not appear here, or a
# pseudobulk t-test would be laundered into "a count model was used".
COUNT_METHODS = ("deseqdataset", "deseqstats", "deseq2", "pydeseq2", "edger", "voom", "limma",
                 "glmmtmb", "negative_binomial", "nbinom")
# Tests that assume Gaussian / rank structure — applied to counts or log-CPM, they are the
# measured frontier failure (gpt-5.5: "OLS on log2(CPM+1) ... not a count-based method").
NON_COUNT_TESTS = DE_AMBIGUOUS

_IMPORT_PY = re.compile(r"^\s*(?:import|from)\s+([\w.]+)", re.M)
_IMPORT_R = re.compile(r"(?:library|require)\(\s*([\w.]+)\s*\)")
CODE_SUFFIXES = (".py", ".ipynb", ".R", ".r")


def _read(path: Path) -> str:
    text = path.read_text(errors="ignore")
    if path.suffix == ".ipynb":
        try:
            nb = json.loads(text)
        except json.JSONDecodeError:
            return text
        return "\n".join("".join(c.get("source", [])) for c in nb.get("cells", []))
    return text


_FINDMARKERS_CALL = re.compile(r"\bFindMarkers\s*\(", re.I)
_IDENTS_COLUMN = re.compile(
    r"\bIdents\s*\([^\n)]*\)\s*<-\s*[A-Za-z.][\w.]*\$([A-Za-z.][\w.]*)",
    re.I,
)


def _balanced_call_body(source: str, match: re.Match) -> str | None:
    """Text inside one already-matched call, or None when its parentheses are incomplete.

    This is deliberately a tiny lexical reader, not an R evaluator. It understands nesting,
    comments, and quoted strings solely so commas inside ``c(...)`` do not split arguments.
    """
    start = match.end()
    depth, quote, escaped, comment = 1, None, False, False
    for index in range(start, len(source)):
        char = source[index]
        if comment:
            if char == "\n":
                comment = False
            continue
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char == "#":
            comment = True
        elif char in ("'", '"'):
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[start:index]
    return None


def _split_call_arguments(body: str) -> list[str]:
    parts, start = [], 0
    depth, quote, escaped, comment = 0, None, False, False
    for index, char in enumerate(body):
        if comment:
            if char == "\n":
                comment = False
            continue
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char == "#":
            comment = True
        elif char in ("'", '"'):
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}" and depth:
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(body[start:index].strip())
            start = index + 1
    parts.append(body[start:].strip())
    return [part for part in parts if part]


def _quoted_values(expression: str) -> tuple[str, ...] | None:
    expression = expression.strip()
    scalar = re.fullmatch(r"(['\"])(.*?)\1", expression, re.S)
    if scalar:
        return (scalar.group(2),)
    vector = re.fullmatch(r"c\s*\((.*)\)", expression, re.I | re.S)
    if not vector:
        return None
    values = []
    for item in _split_call_arguments(vector.group(1)):
        parsed = re.fullmatch(r"(['\"])(.*?)\1", item.strip(), re.S)
        if not parsed:
            return None
        values.append(parsed.group(2))
    return tuple(values)


def _seurat_findmarkers_contract(sources: list[str]) -> dict | None:
    """A narrow, exact read of one Seurat FindMarkers call.

    More than one call, an unparseable argument, or conflicting Idents assignments returns no
    contract. Absence of ``latent.vars`` in the single call means that test itself adjusted for no
    extra observation columns; it says nothing broader about upstream preprocessing.
    """
    bodies = []
    identity_columns = set()
    for source in sources:
        identity_columns.update(_IDENTS_COLUMN.findall(source))
        for match in _FINDMARKERS_CALL.finditer(source):
            body = _balanced_call_body(source, match)
            if body is None:
                return None
            bodies.append(body)
    if len(bodies) != 1:
        return None
    named = {}
    for argument in _split_call_arguments(bodies[0]):
        if "=" not in argument:
            continue
        name, value = argument.split("=", 1)
        named[name.strip().lower()] = value.strip()
    ident_1 = _quoted_values(named.get("ident.1", ""))
    ident_2 = _quoted_values(named.get("ident.2", ""))
    if not ident_1 or len(ident_1) != 1 or not ident_2 or len(ident_2) != 1:
        return None
    latent = (() if "latent.vars" not in named
              else _quoted_values(named["latent.vars"]))
    return {
        "ident_1": ident_1[0],
        "ident_2": ident_2[0],
        "latent_vars": None if latent is None else list(latent),
        "identity_column": next(iter(identity_columns)) if len(identity_columns) == 1 else None,
    }


# directories that never hold the analyst's own code — do not wander into them (finding 11)
_EXCLUDE_DIRS = frozenset({".venv", "venv", "env", ".env", "__pycache__", ".git", "node_modules",
                           ".tox", ".mypy_cache", ".pytest_cache", ".ipynb_checkpoints",
                           "site-packages", "dist", "build", ".eggs"})


def _walk(folder: Path):
    """Every code file anywhere in the tree (finding 11: one-level globbing missed scripts/steps/…),
    skipping virtualenvs / caches / vendored dependencies."""
    for suffix in CODE_SUFFIXES:
        for p in sorted(folder.rglob(f"*{suffix}")):
            if any(part in _EXCLUDE_DIRS for part in p.relative_to(folder).parts[:-1]):
                continue
            yield p


_SCAFFOLDING_EXACT = frozenset({"__init__.py", "conftest.py", "setup.py"})
_SCAFFOLDING_PREFIXES = ("make_fixture", "make_data", "make_dataset", "generate_data",
                         "gen_data", "create_data", "simulate_data", "synthesize_data",
                         "build_data", "test_")


def _is_scaffolding(name: str) -> bool:
    """Data-generation / test / build scaffolding, not the analysis under audit. Excluding it keeps an
    unrelated script (e.g. a synthetic-data generator that also writes the reported paths, or uses a
    dynamic output path) from failing the producer scoper closed and silently degrading real catches to
    NOT CHECKED (#53). Both failure directions are safe (NOT CHECKED), so an over-broad name only costs
    coverage, never a false accusation."""
    return (name in _SCAFFOLDING_EXACT
            or name.endswith("_test.py")
            or any(name.startswith(prefix) for prefix in _SCAFFOLDING_PREFIXES))


def parse_code_signals(folder) -> dict:
    folder = Path(folder)
    imports, files, sources = set(), [], []
    hits = {"de_calls": set(), "cluster_calls": set(), "da_calls": set(), "safeguards": set()}

    for path in _walk(folder):
        # scaffolding, not analysis code — don't show it to a human or a model
        if _is_scaffolding(path.name):
            continue
        source = _read(path)
        files.append(path.name)
        # retain the RAW text (notebooks as JSON) so Layer-2 provenance can parse it itself
        try:
            sources.append(path.read_text(errors="ignore"))
        except OSError:
            sources.append(source)
        low = source.lower()
        imports.update(m.split(".")[0] for m in _IMPORT_PY.findall(source))
        imports.update(_IMPORT_R.findall(source))
        for token in DE_CELL + DE_SAMPLE + DE_AMBIGUOUS:
            if token in low:
                hits["de_calls"].add(token)
        for token in CLUSTER:
            if token in low:
                hits["cluster_calls"].add(token)
        for token in DA:
            if token in low:
                hits["da_calls"].add(token)
        for token in SAFEGUARD:
            if token in low:
                hits["safeguards"].add(token)

    return {"imports": sorted(imports), "files": files, "sources": sources,
            "seurat_findmarkers": _seurat_findmarkers_contract(sources),
            **{k: sorted(v) for k, v in hits.items()}}


def unit_of_test_from(code_signals: dict):
    """"cell" | "sample" | None. (C7)

    Returns **None** when the code cannot settle the question — a bare `ttest_ind` or `wilcoxon`
    is applied to cells and to pseudobulk matrices alike. Guessing here silently mis-routes the
    checks; `None` is the honest answer and it is exactly what the human confirm exists to
    resolve. `init` reports it as `unresolved`, and a design whose unit is still `None` at audit
    time yields `not_audited` rather than a silent skip. (Opus review 2026-07-08.)
    """
    de = {str(c).lower() for c in code_signals.get("de_calls", ())}
    units = set()
    if de & set(DE_CELL):
        units.add("cell")
    if de & set(DE_SAMPLE):
        units.add("sample")
    return next(iter(units)) if len(units) == 1 else None


def _unit_from_contract(contract):
    """The replicate unit a resolved sink treats as the row: for a MARKER test the grouping is over
    cells; for a DE test it is the response's accepted unit. "cell" iff the port accepts ONLY cell;
    "sample" iff it accepts only sample/aggregate (never cell); None when it accepts both (e.g. a bare
    scipy t-test — the same three tokens on cells and on a pseudobulk matrix, genuinely unsettleable)."""
    role = "grouping" if contract.sink_kind == "marker" else "response"
    port = next((p for p in contract.inputs
                 if p.role == role or (role == "response" and p.role.startswith("response"))), None)
    if port is None or not port.accepted_units:
        return None
    if port.accepted_units == frozenset({"cell"}):
        return "cell"
    if "cell" not in port.accepted_units:
        return "sample"
    return None


def unit_of_test_from_sinks(sources):
    """(unit, resolved_any). Derive the tested unit from the TYPED sink contracts SinkUse resolves in the
    Python code — precise where the substring scan is coarse: it binds `sc.tl.rank_genes_groups` the TEST
    (not `sc.pl.rank_genes_groups` the plot) and reads the unit from the contract, not a name-list.

    `unit` is "cell"/"sample" only when every unit-bearing sink agrees; CONFLICTING sinks (a marker QC
    step plus a DESeq2 DE) yield None — we cannot tell which produced the reported table, and guessing is
    how the substring scan mis-routes. `resolved_any` is True iff at least one marker/DE sink resolved, so
    a caller knows whether to trust this verdict or fall back to the token scan (R / unparseable code)."""
    from sc_referee.sink_use import bind_sinks

    units, resolved_any = set(), False
    for u in bind_sinks(sources).uses:
        if u.contract.sink_kind not in ("marker", "de"):
            continue
        resolved_any = True
        unit = _unit_from_contract(u.contract)
        if unit is not None:
            units.add(unit)
    settled = next(iter(units)) if len(units) == 1 else None
    return settled, resolved_any


def resolve_unit_of_test(code_signals: dict):
    """The tested unit: SinkUse-precise for Python, the substring scan as the fallback. A resolved Python
    marker/DE sink is AUTHORITATIVE (so its honest None on a conflicting bundle wins over the token scan's
    wrong "cell"); only when NO Python sink resolves — R code, unparseable steps, bare unimported calls —
    do we defer to `unit_of_test_from`, which still covers Seurat FindMarkers."""
    sources = (code_signals or {}).get("sources", []) or []
    unit, resolved_any = unit_of_test_from_sinks(sources) if sources else (None, False)
    return unit if resolved_any else unit_of_test_from(code_signals)
