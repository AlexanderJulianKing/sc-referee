"""`double_dipping` — the STRUCTURAL detector of inference-after-selection. (design doc §9.4)

The failure: the analyst clusters cells from the expression matrix, then tests for differential
expression BETWEEN those clusters using the SAME cells/counts, and reports "marker" p-values. The
groups were chosen to separate the cells, so the between-cluster test is anti-conservative — it
reports "significant" markers even when there is no true subpopulation structure.

WHY THIS IS A STRUCTURAL-ONLY BLOCKER (GPT-5.5 Pro consult, 2026-07-08):
The verdict must be about CALIBRATION, not truth — "the reported p-values are not valid for
post-clustering inference," NEVER "the markers are false." A count-split *recompute* (how many
claimed markers survive a selection-aware reanalysis) is a separate NON-blocking diagnostic and is
deferred: low survival does not prove the markers are artifacts (it can fall from lost power,
unstable reclustering, a changed estimand, split variance, or dispersion misspecification). So this
check earns its `blocker` from the STRUCTURE of the pipeline alone — power-independent, the analog
of `confounding`.

Specificity scoping (the check must never false-accuse):
  - a documented selection-aware safeguard (count-splitting / held-out set / ClusterDE) →
    `needs_evidence` (verify its contract; a keyword is not proof it is correctly applied — rev.5 §5);
  - marker RANKINGS with no calibrated p-value claim → `informational` (descriptive, not inference);
  - predefined groups (donor/genotype/treatment/FACS/time) → not `marker_detection`, so not our
    business (`applies_to` is False);
  - marker_detection with NO clustering call → not de-novo selection, `applies_to` is False;
  - nothing blocks before `confirmed_by_human`.
"""
from __future__ import annotations

import math

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.citations import CITATIONS
from sc_referee.code_signals import DE_CELL
from sc_referee.design import Design
from sc_referee.provenance import groupby_provenance

CHECK_ID = "double_dipping"


def _f(status, verdict, *, coverage=S.COMPLETE, judgment=None, **metrics) -> Finding:
    return Finding(CHECK_ID, status, verdict, metrics=metrics, citations=CITATIONS[CHECK_ID],
                   coverage=coverage, judgment=judgment)


def _has_cell_marker_call(code_signals: dict) -> bool:
    """A per-cell between-group marker DE call — the unambiguous ones (rank_genes_groups /
    FindMarkers). A bare wilcoxon/ttest is ambiguous and does not, by itself, earn a blocker."""
    return bool(set(map(str.lower, code_signals.get("de_calls", ()))) & set(DE_CELL))


def _provenance_gate(code_signals: dict):
    """Layer-2 provenance over the tested groupings. Returns (fire, has_verdict): `fire` is True when
    some marker test's grouping is data-derived or unresolved (the de-novo structure, even with no
    recognized clustering token); `has_verdict` is True when provenance saw ANY parseable marker test,
    so an all-predefined result can VETO an incidental clustering hit (finding 1)."""
    origins = [t.origin for t in groupby_provenance(code_signals.get("sources", ()))]
    fire = any(o in ("data_derived", "unresolved") for o in origins)
    return fire, bool(origins)


# p-value / q-value column names, case-normalized. Includes scanpy's own `pvals` / `pvals_adj`
# (their omission exonerated real Scanpy analyses — finding 2).
_PVALUE_COLUMNS = frozenset({
    "padj", "pvalue", "p_value", "p-value", "pval", "pvals", "pvals_adj", "adj_p_value", "adj_pval",
    "adjusted_pvalue", "qvalue", "qval", "qvals", "fdr", "adj_p",
    "p_val", "p_val_adj", "adj.p.val", "p.value",          # Seurat FindMarkers / limma topTable names
})


def _claims_calibrated_pvalues(reported) -> bool:
    """The analyst reported inferential significance (a p-value / adjusted p-value / q-value column),
    as opposed to a descriptive score/rank. Only the former is a post-clustering-inference claim."""
    if reported is None or not hasattr(reported, "columns") or not hasattr(reported, "__getitem__"):
        return False
    for column in reported.columns:
        if str(column).strip().lower() not in _PVALUE_COLUMNS:
            continue
        for item in reported[column]:
            try:
                value = float(item)
            except (TypeError, ValueError):
                continue
            if math.isfinite(value) and 0 <= value <= 1:
                return True
    return False


def _has_nonempty_calibrated_pvalue_claim(reported) -> bool:
    """Strict claim-presence predicate for the newly widened cross-route only."""
    if not _claims_calibrated_pvalues(reported) or not hasattr(reported, "__len__") or len(reported) == 0:
        return False
    for column in reported.columns:
        if str(column).strip().lower() not in _PVALUE_COLUMNS:
            continue
        for item in reported[column]:
            try:
                value = float(item)
            except (TypeError, ValueError):
                continue
            if math.isfinite(value) and 0 <= value <= 1:
                return True
    return False


def evaluate_double_dipping(design: Design, bundle, reported) -> Finding:
    cs = bundle.code_signals or {}
    safeguards = list(cs.get("safeguards", ()))
    # marker_detection centres on neither condition nor replicate, so no role-confidence gate fits;
    # the human confirming analysis_type=marker_detection with these signals IS the ratification.
    blocking_allowed = design.confirmed_by_human

    # No inferential claim → not the error at all, regardless of any safeguard: descriptive rankings
    # can't be circular. (Checked first so a ranking-only report resolves to the most specific answer.)
    if not _claims_calibrated_pvalues(reported):
        return _f(S.INFORMATIONAL,
                  "you grouped the cells into clusters that the data itself defined, then listed "
                  "genes that mark those clusters — but you report only rankings or scores, not "
                  "p-values or false-discovery numbers. A ranking is just descriptive, so nothing "
                  "here is circular. Only attach significance values to these markers if you "
                  "compute them with a selection-aware method (count-splitting, a held-out set, or "
                  "ClusterDE).")

    # A safeguard KEYWORD is evidence for review, not a sanitizer. A keyword does not prove the
    # safeguard is correctly applied — naive sample-splitting can remain anti-conservative (Chen &
    # Witten 2023, JMLR), and BH does not erase post-clustering selection dependence. So it is
    # `needs_evidence` (verify the contract), never a clean pass and never a blocker. (spec rev.5 §5;
    # verifying a safeguard's contract to restore `pass` is deferred — see the provenance spec.)
    if safeguards:
        return _f(S.NEEDS_EVIDENCE,
                  f"your code does mention a method meant to keep marker testing honest after "
                  f"clustering ({', '.join(safeguards)}) — but seeing its name isn't proof it was "
                  f"correctly applied, and a naive version (for instance, just splitting the cells "
                  f"in half) can still make the p-values look better than they really are. Verify "
                  f"that the safeguard actually covers this analysis — its contract: the groups it "
                  f"protects and the test it wraps match what you ran — before trusting the "
                  f"p-values. I'm flagging this for review, not blocking it.",
                  safeguards=safeguards, coverage=S.NOT_RUN)

    if not blocking_allowed:
        return _f(S.NEEDS_EVIDENCE,
                  "you defined the cell groups by clustering the same expression data you then used "
                  "to test which genes mark those groups, with no safeguard against the circularity "
                  "— and the setup isn't confirmed yet, so I'm flagging it for review rather than "
                  "blocking. Re-run the marker test on data independent of the clustering "
                  "(count-splitting, a held-out set, or ClusterDE).", coverage=S.NOT_RUN)

    # Phase A: provenance is MAY-level, so the strongest verdict is `needs_evidence` — it ESCALATES,
    # it does not accuse. A `blocker` is deferred to the must/overlap machinery, so a may-level read
    # (e.g. `np.where(X>0, gt, gt)`) can never produce a false accusation (finding 1).
    return _f(S.NEEDS_EVIDENCE,
              "the cell groups here appear to be discovered by clustering the SAME expression data "
              "you then used to test which genes mark them, with no safeguard against the "
              "circularity — this is the 'double-dipping' pattern. Choosing the groups to separate "
              "the cells and then testing those same cells makes the p-values look more significant "
              "than they really are, so they can't be trusted as marker significance (this says "
              "nothing about whether any individual marker is real — only that the numbers are "
              "miscalibrated). The evidence is suggestive, not conclusive, so I'm flagging it for "
              "review rather than blocking. Re-run the marker test on data independent of the "
              "clustering (count-splitting, a held-out set, or ClusterDE).",
              clustering=list(cs.get("cluster_calls", ())), judgment=S.CONCERN,
              marker_test=sorted(set(map(str.lower, cs.get("de_calls", ()))) & set(DE_CELL)))


class DoubleDippingCheck:
    """Structural detector. Fires on a confirmed cell-level marker_detection with de-novo clustering
    and no documented safeguard. Power-independent; earns a `blocker` from the pipeline structure."""

    id = CHECK_ID
    analysis_types = ("marker_detection",)
    audit_dimensions = ("selection",)
    proof_basis = "provenance/static"
    contract_fields = ("analysis_type", "unit_of_test", "name")
    max_status = S.BLOCKER   # structural, like confounding — the recompute (deferred) never blocks

    def applies_to(self, design: Design, bundle) -> bool:
        if design.analysis_type not in {"marker_detection", "condition_contrast_DE"}:
            return False
        if getattr(design, "unit_of_test", None) != "cell":
            return False
        if bundle is None:
            return False
        cs = bundle.code_signals or {}
        # Provenance decides on the ACTUAL tested grouping. If it saw a parseable marker test, trust it
        # (a provably-predefined grouping vetoes an incidental clustering hit — finding 1). Only fall
        # back to the coarse vocabulary co-occurrence when provenance had nothing to judge.
        fire, has_verdict = _provenance_gate(cs)
        if design.analysis_type == "condition_contrast_DE":
            # Cross-routing must be strictly stronger than the legacy marker route: a confirmed,
            # report-bound inferential claim and an EXACT data-derived tested grouping.  Unresolved
            # provenance and coarse cluster+DE token co-occurrence are not enough to widen scope.
            origins = [t.origin for t in groupby_provenance(cs.get("sources", ()))]
            return bool(
                design.confirmed_by_human
                and _has_nonempty_calibrated_pvalue_claim(
                    getattr(bundle, "reported_results", None))
                and _has_cell_marker_call(cs)
                and "data_derived" in origins
            )
        if has_verdict:
            return fire
        return bool(cs.get("cluster_calls")) and _has_cell_marker_call(cs)

    def cannot_evaluate(self, design: Design, bundle):
        if design.analysis_type != "marker_detection":
            return None
        if getattr(design, "unit_of_test", None) is None:
            return ("the unit of analysis is unresolved (cell vs sample), so double dipping was NOT "
                    "checked — resolve `unit_of_test` in the design and re-run.")
        return None

    def run(self, design: Design, bundle, reported) -> Finding:
        return evaluate_double_dipping(design, bundle, reported)
