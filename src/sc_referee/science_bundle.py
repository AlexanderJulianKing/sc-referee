"""Ingest a Claude Science (or similar) EXPORT BUNDLE — a multi-step analysis package: numbered
scripts, data files, and a narrative report — into a structured INVENTORY the referee can reason over.

A real workflow is not one clean result; it is a chain of steps, each of which can go wrong, and a
report that makes confident claims tied to those steps. This module UNPACKS and PARSES a bundle
(folder or `.zip`) — reading text, **never executing anything** (same stance as `code_signals`), so a
downstream check can audit step by step and trace each claim to the code + data that produced it.
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

from sc_referee import code_signals as _cs
from sc_referee.checks.double_dipping import evaluate_double_dipping
from sc_referee.provenance import groupby_provenance

# Reuse the analysis-call vocabulary the checks already key on, so a step's methods are named the same.
_CALL_GROUPS = {
    "de_cell": _cs.DE_CELL,
    "de_sample": _cs.DE_SAMPLE,
    "de_ambiguous": _cs.DE_AMBIGUOUS,
    "cluster": _cs.CLUSTER,
    "differential_abundance": _cs.DA,
    "safeguard": _cs.SAFEGUARD,
}
_TEXT_SUFFIXES = (".py", ".ipynb", ".r", ".md", ".txt", ".yml", ".yaml", ".toml", ".cfg")
_ORDER_RE = re.compile(r"^(\d+)")
_INPUTS_RE = re.compile(r"Inputs?\s*:\s*\[([^\]]*)\]", re.I)
_LINEAGE_RE = re.compile(r"lineage\s*\(version\s*([0-9a-fA-F-]{8,})", re.I)
# Claim extraction. A claim is a sentence carrying a QUANTITATIVE assertion — a number bound to a
# statistical/count context — not merely a digit next to a keyword (which swept up gene IDs and prose).
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")            # [text](url) -> text
_MD_INLINE = re.compile(r"\*\*|__|\*|`|~~")                # bold / italic / code / strike markers
_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+(?=["“(A-Z])')     # ender + space + capital/quote/paren (keeps 0.05 intact)
_QUANT = re.compile(r"""
      \d+(?:\.\d+)?\s*%                                                  # 94%
    | \b(?:padj|p-?val(?:ue)?|q-?val(?:ue)?|fdr|adj\.?\s*p|adjusted\s*p)\b[^.\n]{0,15}?\d  # padj<0.05, adjusted P of 0.01
    | \b[pq]\s*[<=>]{1,2}\s*\d                                          # p < 0.05, q <= 0.05, p = 0.01
    | \d+(?:\.\d+)?\s*[-\s]?fold\b                                      # 2.3-fold, 3 fold
    | \b\d[\d,]*\s+(?:markers?|genes?|degs?|cells?|clusters?|samples?|donors?|
                     transcripts?|exons?|tissues?|populations?|cell[\s-]?types?)\b  # 42 marker genes, 1,024 cells
""", re.I | re.X)


@dataclass
class BundleStep:
    name: str                                  # filename, e.g. "02_as_summary.py"
    order: int | None                          # numeric filename prefix — the pipeline position
    imports: list = field(default_factory=list)
    calls: dict = field(default_factory=dict)  # {de_cell: [...], de_sample: [...], cluster: [...], ...}
    declared_inputs: list = field(default_factory=list)   # from a docstring "Inputs: [...]" line
    lineage: str | None = None                 # the conversation/artifact lineage id, if the script notes one
    source: str = ""                           # the raw code, retained for provenance/data-flow analysis


@dataclass
class DataFile:
    name: str
    size: int


@dataclass
class Report:
    name: str
    headings: list = field(default_factory=list)
    claims: list = field(default_factory=list)   # sentences that assert a number about the biology


@dataclass
class BundleCoverage:
    """The honest answer to 'can sc-referee actually audit this bundle?' — computed, not asserted."""
    status: str                                   # "auditable" | "not_audited"
    auditable_steps: list = field(default_factory=list)   # step names a wired check could evaluate
    reason: str = ""
    notes: list = field(default_factory=list)     # cross-step observations, e.g. double_dipping shape


# The analysis groups a wired sc-referee check actually evaluates today: every check keys off a
# differential-expression contrast. Clustering/DA alone are not yet audited on their own.
_AUDITABLE_GROUPS = ("de_cell", "de_sample", "de_ambiguous")


def coverage_verdict(inv: "BundleInventory") -> BundleCoverage:
    """Which steps a current check can evaluate — and, when none can, say so plainly instead of
    letting a green run read as 'clean'. This is the specificity rule applied to a whole pipeline."""
    auditable = [s.name for s in inv.steps if any(g in s.calls for g in _AUDITABLE_GROUPS)]
    calls = inv.analysis_calls
    notes = []
    if "cluster" in calls and ("de_cell" in calls or "de_ambiguous" in calls):
        notes.append("clustering and cell-level DE in the same pipeline — double_dipping applies")
    if auditable:
        reason = (f"{len(auditable)} of {len(inv.steps)} step(s) run a differential-expression analysis "
                  f"sc-referee checks; confirm a design to audit them.")
        return BundleCoverage(status="auditable", auditable_steps=auditable, reason=reason, notes=notes)
    reason = ("no step runs an analysis sc-referee checks yet (no differential-expression call found) — "
              "a green run here would mean 'not looked at', not 'clean'.")
    return BundleCoverage(status="not_audited", auditable_steps=[], reason=reason, notes=notes)


@dataclass
class BundleInventory:
    root: str
    steps: list = field(default_factory=list)     # BundleStep, in pipeline order
    data: list = field(default_factory=list)       # DataFile
    reports: list = field(default_factory=list)    # Report
    requirements: list = field(default_factory=list)   # declared deps (requirements.txt / environment.yml)

    @property
    def analysis_calls(self) -> dict:
        """Union of recognized analysis calls across all steps — what the pipeline actually did."""
        out: dict = {}
        for s in self.steps:
            for group, calls in s.calls.items():
                out.setdefault(group, set()).update(calls)
        return {g: sorted(v) for g, v in out.items()}


def _collect(path):
    """(root_name, [(relpath, size, text_or_None)]) — text read EAGERLY, never executed. Handles a
    `.zip` (read members in place) or an already-unpacked folder."""
    path = Path(path)
    out = []
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                text = None
                if info.filename.lower().endswith(_TEXT_SUFFIXES):
                    try:
                        text = z.read(info.filename).decode("utf-8", "replace")
                    except Exception:
                        text = None
                out.append((info.filename, info.file_size, text))
        return path.stem, out
    for p in sorted(path.rglob("*")):
        if p.is_dir():
            continue
        text = None
        if p.suffix.lower() in _TEXT_SUFFIXES:
            try:
                text = p.read_text(errors="replace")
            except Exception:
                text = None
        out.append((p.relative_to(path).as_posix(), p.stat().st_size, text))
    return path.name, out


def _parse_step(rel: str, text: str) -> BundleStep:
    name = Path(rel).name
    m = _ORDER_RE.match(name)
    low = text.lower()
    calls = {g: sorted({tok for tok in toks if tok in low}) for g, toks in _CALL_GROUPS.items()}
    calls = {g: v for g, v in calls.items() if v}
    di = _INPUTS_RE.search(text)
    inputs = [s.strip().strip("'\"") for s in di.group(1).split(",")] if di and di.group(1).strip() else []
    lin = _LINEAGE_RE.search(text)
    return BundleStep(
        name=name,
        order=int(m.group(1)) if m else None,
        imports=sorted(set(_cs._IMPORT_PY.findall(text))),
        calls=calls,
        declared_inputs=[i for i in inputs if i],
        lineage=lin.group(1) if lin else None,
        source=text,
    )


def _clean_md(s: str) -> str:
    return _MD_INLINE.sub("", _MD_LINK.sub(r"\1", s))


def _parse_report(rel: str, text: str) -> Report:
    text = text.replace("≤", "<=").replace("≥", ">=").replace("−", "-")   # normalize unicode operators
    headings = [ln.lstrip("#").strip() for ln in text.splitlines() if ln.lstrip().startswith("#")]
    # Group non-heading lines into paragraphs (blank-line separated) so a wrapped sentence stays whole,
    # stripping markdown scaffolding; a heading / blank line / fence ends a paragraph. Fenced code is
    # skipped (it is not prose) and each table row is its own unit (finding 10: never merge rows).
    paragraphs, buf, in_fence = [], [], False

    def flush():
        if buf:
            paragraphs.append(" ".join(buf))
            buf.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            flush()
            continue
        if in_fence:
            continue
        if not stripped or stripped.startswith("#"):
            flush()
            continue
        if set(stripped) <= set("|-: "):                       # markdown table separator row
            continue
        if "|" in stripped:                                    # a table row -> its own unit, not joined
            flush()
            cell = _clean_md(stripped).replace("|", " ").strip()
            if cell:
                paragraphs.append(cell)
            continue
        cleaned = _clean_md(stripped).lstrip("-*>+ ").strip()
        if cleaned:
            buf.append(cleaned)
    flush()

    claims, seen = [], set()
    for para in paragraphs:
        for sent in _SENT_SPLIT.split(para):
            s = " ".join(sent.split()).strip()                 # collapse whitespace
            if not s or len(s) > 300 or s in seen:
                continue
            if _QUANT.search(s):
                claims.append(s)
                seen.add(s)
    return Report(name=Path(rel).name, headings=headings, claims=claims)


def inventory_bundle(path) -> BundleInventory:
    root, members = _collect(path)
    inv = BundleInventory(root=root)
    for rel, size, text in members:
        low = rel.lower()
        base = Path(rel).name.lower()
        if low.endswith((".py", ".ipynb", ".r")):
            inv.steps.append(_parse_step(rel, text or ""))
        elif low.endswith(".md"):
            inv.reports.append(_parse_report(rel, text or ""))
        elif base in ("requirements.txt", "environment.yml", "environment.yaml", "pyproject.toml"):
            inv.requirements.append(rel)
        else:
            inv.data.append(DataFile(name=rel, size=size))
    inv.steps.sort(key=lambda s: (s.order is None, s.order or 0, s.name))
    return inv


# ---------------------------------------------------------------------------
# bundle -> check bridge
# ---------------------------------------------------------------------------
# Run sc-referee's STRUCTURAL checks over a parsed bundle by feeding it through the SAME decision
# ladder the single-contrast audit path uses. A bundle carries no human ratification, so the
# strongest verdict it can reach is `needs_evidence`: the structure is caught, but a blocker still
# requires confirming the specific contrast (`init` -> `confirm` -> `audit`).

_PVAL_TOKENS = ("padj", "p-value", "pvalue", "pval", "p <", "p<", "q-value", "qval", "qvalue",
                "q <", "q<", "fdr", "adj_p", "adjusted p", "p =", "p=")
_MARKER_TOKENS = ("marker", "cluster", "leiden", "louvain", "subpopulation", "subtype",
                  "de novo", "de-novo")
# a claim that DENIES reporting a p-value is not a post-clustering-inference claim (finding 10).
_NEGATION_TOKENS = ("did not", "didn't", "not report", "no p-value", "no p value", "without p")


def _code_signals(inv: "BundleInventory") -> dict:
    """Collapse the per-step call groups back into the {de_calls, cluster_calls, safeguards} shape the
    checks consume, so the bundle path speaks the audit path's vocabulary exactly."""
    de, cluster, da, safe = set(), set(), set(), set()
    for s in inv.steps:
        de.update(s.calls.get("de_cell", ()))
        de.update(s.calls.get("de_sample", ()))
        de.update(s.calls.get("de_ambiguous", ()))
        cluster.update(s.calls.get("cluster", ()))
        da.update(s.calls.get("differential_abundance", ()))
        safe.update(s.calls.get("safeguard", ()))
    return {"de_calls": sorted(de), "cluster_calls": sorted(cluster),
            "da_calls": sorted(da), "safeguards": sorted(safe)}


@dataclass
class AttributedClaim:
    """A numeric report claim linked (statically, no execution) to the test that produced it."""
    claim: str                     # the report sentence
    report: str                    # the report file it came from
    grouping: str | None           # the producing test's grouping column, if uniquely attributed
    origin: str                    # "data_derived" | "unresolved_attribution"
    status: str                    # "needs_evidence" | "unresolved"


def _is_marker_pvalue_claim(claim: str) -> bool:
    low = claim.lower()
    if any(neg in low for neg in _NEGATION_TOKENS):          # "did not report … p-values" is not a claim
        return False
    return any(p in low for p in _PVAL_TOKENS) and any(m in low for m in _MARKER_TOKENS)


def _names_column(claim: str, col: str) -> bool:
    """Whole-word match, so a grouping named 'g' does not match every sentence with a 'g' (finding 8)."""
    return re.search(r"\b" + re.escape(col) + r"\b", claim, re.I) is not None


def attribute_claims(inv: "BundleInventory") -> list:
    """Backward-attribute each numeric report claim to the marker test that produced it, and attach
    that test's provenance verdict to the sentence — without executing anything. Attribution is
    deliberately conservative (adversarial review: ambiguous producers must abstain, not be force-attributed):
    a claim is flagged `needs_evidence` only when it uniquely resolves to a single data-derived marker
    test — either it names that test's grouping column (whole-word), or the bundle has EXACTLY ONE
    marker test (counting unresolved ones) and it is data-derived. Any other marker inference is
    `unresolved`. The verdict certifies the claim's METHOD, never that the reported number reproduces."""
    tests = groupby_provenance([s.source for s in inv.steps])
    origins_by_col: dict = {}
    for t in tests:
        if t.groupby:
            origins_by_col.setdefault(t.groupby, set()).add(t.origin)
    literal_cols = list(origins_by_col)                                        # distinct literal grouping columns
    # a column is confidently data-derived only if EVERY marker test on it is — a name reused by a
    # data-derived AND a predefined invocation is ambiguous and must not be attributed (re-review #5).
    dd_cols = {c for c, origins in origins_by_col.items() if origins == {"data_derived"}}
    out = []
    for r in inv.reports:
        for claim in r.claims:
            if not _is_marker_pvalue_claim(claim):
                continue
            named = {c for c in literal_cols if _names_column(claim, c)}
            if len(named) == 1 and next(iter(named)) in dd_cols:
                out.append(AttributedClaim(claim, r.name, next(iter(named)), "data_derived", "needs_evidence"))
            elif not named and len(tests) == 1 and literal_cols and literal_cols[0] in dd_cols:
                # the ONLY marker test in the whole bundle (unresolved competitors excluded by len(tests))
                out.append(AttributedClaim(claim, r.name, literal_cols[0], "data_derived", "needs_evidence"))
            else:
                out.append(AttributedClaim(claim, r.name, None, "unresolved_attribution", "unresolved"))
    return out


def bundle_findings(inv: "BundleInventory") -> list:
    """Structural findings for a parsed bundle. Today: double_dipping.

    The double-dipping structure is de-novo clustering feeding a per-cell marker test. Predefined-group
    DE alone (pydeseq2/edgeR -> `de_sample`, no clustering) never lands here — that omission is the
    specificity guarantee: a legitimate condition contrast is not this check's business.
    """
    findings = []
    cs = _code_signals(inv)
    # Layer 2 (provenance) EXTENDS the vocabulary gate: a marker test whose grouping column traces back
    # to the expression matrix is the double-dipping structure even when the clustering method carries
    # no recognized token (the `pbmc_dex` GMM case, or any bespoke function). Taint follows the data.
    prov = groupby_provenance([s.source for s in inv.steps])
    prov_data_derived = sorted({t.groupby for t in prov if t.origin == "data_derived" and t.groupby})
    prov_unresolved = any(t.origin == "unresolved" for t in prov)   # a marker test we couldn't resolve
    vocab_gate = bool(cs["cluster_calls"]) and bool(set(map(str.lower, cs["de_calls"])) & set(_cs.DE_CELL))
    if vocab_gate or prov_data_derived or prov_unresolved:
        # p-values count as claimed for the DIP only if a claim actually attributes to a data-derived
        # test — a predefined test's padj claim must not make a descriptive cluster test inferential
        # (finding 5). An UNRESOLVED grouping can't be attributed, so conservatively assume calibrated
        # claims (escalate to needs_evidence rather than clear it as informational).
        dip_has_pvalues = prov_unresolved or any(a.status == "needs_evidence" for a in attribute_claims(inv))
        reported = SimpleNamespace(columns=(["padj"] if dip_has_pvalues else []))
        design = SimpleNamespace(confirmed_by_human=False)   # a bundle is never ratified in place
        f = evaluate_double_dipping(design, SimpleNamespace(code_signals=cs), reported)
        # Enrich with the bundle context the shared ladder does not carry: which steps are implicated.
        f.metrics = {**f.metrics,
                     "clustering": cs["cluster_calls"] or (["<provenance>"] if prov_data_derived else []),
                     "data_derived_groupings": prov_data_derived,
                     "marker_test": sorted(set(map(str.lower, cs["de_calls"])) & set(_cs.DE_CELL)),
                     "cluster_steps": [s.name for s in inv.steps if s.calls.get("cluster")],
                     "marker_steps": [s.name for s in inv.steps
                                      if set(map(str.lower, s.calls.get("de_cell", ()))) & set(_cs.DE_CELL)]}
        findings.append(f)
    return findings
