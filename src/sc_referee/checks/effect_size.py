"""`effect_size_threshold` — significance without an effect-size gate. (Item 4)

With enough cells, an arbitrarily small |log2FC| reaches FDR significance. An analysis that claims
every FDR-significant gene, with no effect-size threshold, produces a discovery list dominated by
biologically negligible effects. This check reads only the reported table and reports the fraction
of claimed-significant discoveries whose |effect| is below a minimal meaningful cut.

ADVISORY BY DESIGN: an effect-size cutoff is a policy choice, not a mathematical fact, so this check
NEVER blocks (max_status = major). It reports the fraction and names the concern; it does not
overrule the analyst on where the biological-relevance line sits.
"""
from __future__ import annotations

import numpy as np

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.citations import CITATIONS
from sc_referee.design import Design

CHECK_ID = "effect_size_threshold"

ALPHA = 0.05
# Display convention only. It may describe magnitudes but can never authorize MAJOR.
NEGLIGIBLE_LOG2FC = 0.25
MAJOR_FRACTION = 0.50   # most claimed discoveries are negligible -> significance driven by power
INFO_FRACTION = 0.10    # a meaningful minority are negligible -> worth noting


def _f(status, verdict, *, coverage=S.COMPLETE, judgment=None, **metrics) -> Finding:
    if judgment is None:
        judgment = {S.MAJOR: S.CONCERN, S.PASS: S.CONFORMANT}.get(status)
    return Finding(CHECK_ID, status, verdict, metrics=metrics, citations=CITATIONS[CHECK_ID],
                   coverage=coverage, judgment=judgment)


def evaluate_effect_size(design: Design, reported, alpha: float = ALPHA) -> Finding:
    if reported is None or "effect" not in getattr(reported, "columns", []):
        return _f(S.NEEDS_EVIDENCE, "your results table has no effect-size (fold-change) column, so I "
                                    "couldn't check whether your significant genes actually change by a "
                                    "meaningful amount", coverage=S.NOT_RUN)

    padj = np.asarray(reported["padj"], dtype=float) if "padj" in reported.columns else None
    pval = np.asarray(reported["pvalue"], dtype=float) if "pvalue" in reported.columns else None
    called = padj if padj is not None else pval
    if called is None:
        return _f(S.NEEDS_EVIDENCE, "your results table has no p-value column, so I couldn't tell which "
                  "genes you called significant", coverage=S.NOT_RUN)
    effect = np.asarray(reported["effect"], dtype=float)

    sig = np.isfinite(called) & (called <= alpha)
    if not sig.any():
        return _f(S.PASS, "nothing was called significant, so there's no discovery list to size", claimed=0)

    claimed = sig & np.isfinite(effect)
    n_claimed = int(claimed.sum())
    if n_claimed == 0:
        return _f(S.NEEDS_EVIDENCE, "your significant genes have no reported effect size (fold-change), "
                                    "so I couldn't check their magnitude", coverage=S.NOT_RUN)

    contract = design.effect_relevance_contract
    contract_bound = bool(
        design.confirmed_by_human
        and contract is not None
        and contract.claim_type == "biologically_relevant_discovery"
        and contract.threshold_scale == contract.reported_effect_scale == "log2_fold_change"
    )
    if contract is not None and not contract_bound:
        return _f(
            S.NEEDS_EVIDENCE,
            "an effect-relevance threshold was declared, but it is not confirmed on the exact "
            "log2 fold-change scale of the reported effect column, so I did not adjudicate "
            "biological relevance",
            coverage=S.NOT_RUN,
        )

    threshold = contract.threshold if contract_bound else NEGLIGIBLE_LOG2FC
    negligible = int((np.abs(effect[claimed]) < threshold).sum())
    frac = negligible / n_claimed
    metrics = dict(claimed=n_claimed, negligible=negligible, negligible_fraction=round(frac, 4),
                   threshold_log2fc=threshold, relevance_contract_bound=contract_bound)

    body = (f"{negligible} of your {n_claimed} significant genes ({frac:.0%}) change by less than "
            f"|log2FC| {threshold}")
    if frac >= MAJOR_FRACTION:
        if not contract_bound:
            return _f(
                S.NEEDS_EVIDENCE,
                f"{body}, using the conventional |log2FC| {NEGLIGIBLE_LOG2FC} display line. You did "
                "not declare a biological-relevance claim or threshold, so this magnitude summary "
                "does not establish a defect",
                coverage=S.NOT_RUN,
                **metrics,
            )
        return _f(S.MAJOR, f"{body}, below the relevance floor declared for these discoveries. "
                           "The reported discovery list does not conform to that declared claim.",
                  **metrics)
    if frac >= INFO_FRACTION:
        return _f(S.INFORMATIONAL, f"{body}. Some of your significant genes are biologically marginal — "
                                   f"using the display convention; no relevance defect is inferred.", **metrics)
    qualifier = "declared relevance floor" if contract_bound else "display magnitude line"
    return _f(S.PASS, f"the reported effect magnitudes are above the {qualifier}: only "
              f"{negligible} of {n_claimed} ({frac:.0%}) are below |log2FC| {threshold}. "
              "This comparison does not establish that the effects are biologically real.", **metrics)


class EffectSizeCheck:
    """Reads only `bundle.reported_results`. Advisory — never blocks."""

    id = CHECK_ID
    analysis_types = ("condition_contrast_DE",)
    audit_dimensions = ("advisory_policy",)
    proof_basis = "provenance/static"
    contract_fields = ("condition", "reference", "test", "name", "effect_relevance_contract")
    max_status = S.MAJOR   # an effect-size cutoff is policy, not math — reported, never a blocker

    def applies_to(self, design: Design, bundle) -> bool:
        return (design.analysis_type in self.analysis_types
                and bundle is not None and bundle.reported_results is not None)

    def cannot_evaluate(self, design: Design, bundle):
        return None

    def run(self, design: Design, bundle, reported=None) -> Finding:
        return evaluate_effect_size(design, reported if reported is not None else bundle.reported_results)
