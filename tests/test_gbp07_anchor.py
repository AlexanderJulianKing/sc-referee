"""GB-P07 real-data anchor: the allele-orientation gate on the exact analysis Claude Science shipped.

Skips unless the GeneBench-Pro GB-P07 data zip is present (gitignored; see bench/gbp07_anchor.py).
The point is not a magnitude — it is that sc-referee refuses to certify an unratified per-allele sign,
which is the seam that produced Claude's +0.4839 vs the -0.60 truth.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from bench.gbp07_anchor import default_zip, run_gbp07_anchor

pytestmark = pytest.mark.skipif(
    not default_zip().exists(),
    reason="GB-P07 data not present — set GBP07_ZIP; see bench/gbp07_anchor.py",
)


def test_contamination_orientation_gate_refuses_to_certify_the_unratified_sign():
    finding, info = run_gbp07_anchor()

    # The referee neither rubber-stamps (+0.48) nor false-accuses: it abstains at the seam.
    assert finding.status == "needs_evidence"
    assert finding.status not in ("blocker", "major", "pass")
    assert "effect_allele" in finding.metrics["unresolved_contract"]

    # The finding surfaces the honest orientation-agnostic facts: frequency (which at 0.5 cannot orient)
    # and, because the reported estimator is NB not the supported OLS, an explicit recompute-unavailable note.
    assert finding.metrics["effect_allele_frequency"] == pytest.approx(0.5)
    assert "negative_binomial" in finding.metrics["independent_recompute"]

    # Honest boundary, on the real data. Frequency cannot orient (0.5). A naive same-data OLS slope is
    # NOT a stand-in: it is population-sensitive (near-zero on the audited activated subset, positive on all
    # cells) and estimator-mismatched (OLS, not Claude's NB) — so it can neither confirm nor refute +0.48.
    # This is exactly why the gate, not a recompute, is the only honest catch.
    assert info["eff_allele_freq_mean_g_over_2"] == pytest.approx(0.5)
    assert abs(info["activated_subset_ols_slope_on_g"]) < abs(info["all_cells_ols_slope_on_g"])
    assert abs(info["activated_subset_ols_slope_on_g"]) < 0.2  # essentially null on the audited subpopulation
