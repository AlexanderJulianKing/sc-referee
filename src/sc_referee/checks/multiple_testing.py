"""The `multiple_testing` check — recompute BH over the analyst's OWN p-values.

The purest expression of the tool's thesis: no data, no code, no model. Take the reported
p-values, apply Benjamini-Hochberg, and count how many of the claimed discoveries survive.
The verdict is arithmetic on numbers the analyst themselves published.

BH is ALWAYS recomputed. An earlier version returned `pass` the moment `padj` differed from
`pvalue`, which let a fabricated adjustment (`p=0.04`, `padj=0.001`) sail through. (adversarial review 2026-07-08.)

Adjusted values below raw p-values are not universally impossible: Storey q-values may legitimately
be smaller. Adverse conclusions are therefore restricted to an exact confirmed BH/FDR contract over
a complete family. Every other contract receives only a descriptive comparison or an abstention.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.citations import CITATIONS
from sc_referee.design import Design
# The "fraction of claimed discoveries surviving a recompute -> verdict" ladder is ONE policy,
# owned by engine.py (the earned-verdict home). BH-survival here uses the same cuts as replicate-
# aware survival there; a single source keeps them from drifting. (<=0.10 -> blocker, <0.60 -> major.)
from sc_referee.engine import BLOCKER_AT, MAJOR_BELOW

CHECK_ID = "multiple_testing"

_TOL = 1e-9


def _cols(reported: pd.DataFrame):
    p = pd.to_numeric(reported["pvalue"], errors="coerce").to_numpy(dtype=float) \
        if "pvalue" in reported.columns else np.array([])
    padj = pd.to_numeric(reported["padj"], errors="coerce").to_numpy(dtype=float) \
        if "padj" in reported.columns else np.full(p.shape, np.nan)
    return p, padj


def reported_is_uncorrected(reported: pd.DataFrame) -> bool:
    """True iff `padj` is absent, or elementwise equal to the raw p-values."""
    p, padj = _cols(reported)
    if p.size == 0 or not np.isfinite(padj).any():
        return True
    both = np.isfinite(p) & np.isfinite(padj)
    return bool(both.any() and np.allclose(p[both], padj[both], rtol=_TOL, atol=1e-12))


def reported_adjustment_is_impossible(reported: pd.DataFrame) -> bool:
    """Compatibility shim: no universal adjustment-ordering impossibility exists."""
    return False


def _f(status, verdict, *, coverage=S.COMPLETE, judgment=None, **metrics) -> Finding:
    if judgment is None:
        judgment = {S.BLOCKER: S.VIOLATION, S.MAJOR: S.CONCERN, S.PASS: S.CONFORMANT}.get(status)
    return Finding(CHECK_ID, status, verdict, metrics=metrics, citations=CITATIONS[CHECK_ID],
                   coverage=coverage, judgment=judgment)


def evaluate_multiple_testing(reported, design: Design, alpha: float = 0.05) -> Finding:
    contract = design.multiplicity_contract
    bh_fdr_contract = bool(
        design.confirmed_by_human
        and contract is not None
        and contract.claim_type == "error_controlled_discovery"
        and contract.error_criterion == "fdr"
        and contract.adjustment_method == "benjamini_hochberg"
        and contract.family_complete
    )

    if reported is None or len(reported) == 0:
        return _f(S.NEEDS_EVIDENCE, "no reported result found to check against", coverage=S.NOT_RUN)

    p, padj = _cols(reported)
    if p.size == 0 or not np.isfinite(p).any():
        return _f(S.NEEDS_EVIDENCE,
                  "your results table has no raw p-values, so I can't recompute the multiple-testing "
                  "correction that controls false discoveries. Include the raw (uncorrected) p-value "
                  "for each gene.", coverage=S.NOT_RUN)

    finite = np.isfinite(p)
    # The analyst's OWN significance calls: whatever they put in `padj`, else the raw p.
    called = np.where(np.isfinite(padj), padj, p)
    claimed_mask = finite & (called <= alpha)
    n_claimed = int(claimed_mask.sum())
    family = int(finite.sum())

    bh = np.ones_like(p)
    bh[finite] = multipletests(p[finite], method="fdr_bh")[1]
    both = np.isfinite(p) & np.isfinite(padj)
    adjustment_reproduced = bool(
        both.any() and np.allclose(padj[both], bh[both], rtol=_TOL, atol=1e-12)
    )
    if n_claimed == 0:
        if both.any() and not (bh_fdr_contract and adjustment_reproduced):
            return _f(
                S.NEEDS_EVIDENCE,
                "nothing is reported significant, but the supplied adjusted column does not have "
                "a bound, exactly reproduced adjustment method. I did not treat zero calls as "
                "evidence that the adjustment is valid.",
                coverage=S.NOT_RUN, claimed=0, family_size=family,
                contract_bound=bh_fdr_contract,
                adjustment_reproduced=adjustment_reproduced,
            )
        return _f(S.PASS, "no supplied value is at or below the significance cutoff",
                  claimed=0, family_size=family, contract_bound=bh_fdr_contract,
                  adjustment_reproduced=adjustment_reproduced)
    if n_claimed == family:
        return _f(S.NEEDS_EVIDENCE,
                  "every gene in your results table is marked significant — which usually means the "
                  "table holds only the hits, not the full set of genes that were tested. Multiple-"
                  "testing correction needs the complete tested set to work, so I couldn't recompute "
                  "it. Provide the full results (every gene tested, not just the significant ones).",
                  coverage=S.NOT_RUN, claimed=n_claimed, family_size=family)

    survivors = int((claimed_mask & (bh <= alpha)).sum())
    survival = survivors / n_claimed

    below_raw = bool(both.any() and np.any(padj[both] < p[both] - _TOL))
    uncorrected = reported_is_uncorrected(reported)
    metrics = dict(corrected=not uncorrected, adjusted_below_raw=below_raw,
                   impossible_adjustment=False, contract_bound=bh_fdr_contract,
                   adjustment_reproduced=adjustment_reproduced,
                   claimed=n_claimed, survivors=survivors, survival_rate=round(survival, 4),
                   family_size=family, alpha=alpha)

    # High survival supports only the arithmetic comparison performed here. An uncorrected table is
    # descriptive rather than conformant because no correction was established.
    if survival >= MAJOR_BELOW:
        ordering = (" Reported adjusted values below raw p-values are method-dependent and do not "
                    "establish an error." if below_raw else "")
        if uncorrected:
            return _f(S.INFORMATIONAL, "the reported calls are unadjusted, but all of them also "
                      f"survive a descriptive BH comparison over the supplied family.{ordering}", **metrics)
        if not bh_fdr_contract or not adjustment_reproduced:
            return _f(
                S.NEEDS_EVIDENCE,
                "the reported calls survive a descriptive BH comparison, but the adjusted column "
                "is not bound to and exactly reproduced by a declared complete-family BH/FDR "
                "method, so I did not certify the correction.",
                coverage=S.NOT_RUN, **metrics,
            )
        return _f(S.PASS, "the supplied adjusted column exactly reproduces the declared "
                  f"complete-family Benjamini-Hochberg calculation{ordering}", **metrics)

    # A different or absent error-control contract cannot be judged against BH as a defect.
    if not bh_fdr_contract:
        method = contract.adjustment_method if contract is not None else "unbound"
        if not uncorrected:
            if below_raw and contract is None:
                return _f(
                    S.NEEDS_EVIDENCE,
                    f"{survivors} of {n_claimed} reported discoveries survive a descriptive BH "
                    "comparison, but adjusted values below raw p-values require the declared method "
                    "semantics (for example, Storey q-values can legitimately have this ordering). "
                    "Without that contract I did not adjudicate the adjustment.",
                    coverage=S.NOT_RUN,
                    **metrics,
                )
            return _f(
                S.INFORMATIONAL,
                f"{survivors} of {n_claimed} reported discoveries survive a descriptive BH comparison. "
                f"The declared adjustment method is {method}, so BH attrition is not treated as a "
                "defect and no individual row is adjudicated. A method such as Storey q-values may "
                "legitimately be less conservative than BH.",
                **metrics,
            )
        return _f(
            S.NEEDS_EVIDENCE,
            f"{survivors} of {n_claimed} reported discoveries survive a descriptive BH comparison, "
            f"but the declared adjustment method is {method} and there is no confirmed complete-family "
            "BH/FDR discovery contract to adjudicate. No reported row is classified as false.",
            coverage=S.NOT_RUN,
            **metrics,
        )

    # Exact BH/FDR contract: attrition is contract nonconformance, regardless of padj ordering.
    if not uncorrected:
        if survival >= MAJOR_BELOW:
            return _f(S.PASS, "the reported discoveries conform to the declared BH/FDR comparison", **metrics)
    body = (f"the confirmed contract declares BH control of the false-discovery rate over this complete "
            f"family, but only {survivors} of {n_claimed} reported discoveries conform when BH is "
            f"recomputed over all {family} supplied p-values at {alpha:.0%}. This is family-level "
            "nonconformance; it does not label any individual non-survivor false")
    if survival <= BLOCKER_AT:
        return _f(S.BLOCKER, body, **metrics)
    return _f(S.MAJOR, body, **metrics)


class MultipleTestingCheck:
    """Reads only `bundle.reported_results`. (Trivially generalizes to marker_detection /
    differential_abundance; scoped to the confirmed contrast type for now.)"""

    id = CHECK_ID
    analysis_types = ("condition_contrast_DE",)
    audit_dimensions = ("inclusion_set", "calibration")
    proof_basis = "independent recompute"
    contract_fields = ("condition", "reference", "test", "name", "multiplicity_contract")
    # DOES earn a blocker: a confirmed analysis that reported UNCORRECTED p-values whose claims do
    # not survive a recomputed BH (≤10%) is overwhelmingly false positives. Engine-independent — BH
    # is recomputed here, not via the DE engine. (A less-conservative but valid correction, e.g.
    # Storey q ≤ BH, is never accused; that path returns informational.) adversarial Phase-2 review caught
    # a mislabel here: max_status=major would have CLAMPED that legitimate blocker to major.
    max_status = S.BLOCKER

    def applies_to(self, design: Design, bundle) -> bool:
        return (design.analysis_type in self.analysis_types
                and bundle is not None and bundle.reported_results is not None)

    def cannot_evaluate(self, design: Design, bundle):
        return None   # needs only the reported table; absence is handled by applies_to

    def run(self, design: Design, bundle, reported=None) -> Finding:
        return evaluate_multiple_testing(reported if reported is not None else bundle.reported_results, design)
