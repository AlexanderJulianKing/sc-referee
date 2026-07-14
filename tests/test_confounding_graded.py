"""Graded confounding: exact design-matrix algebra, not stratum co-occurrence.

Three bugs these tests pin (all present in the joint-stratum + min_cell implementation):

  1. FALSE BLOCKER — condition = XOR(run, sex) makes every JOINT (run,sex) stratum pure, so
     `shares_common_support` fails. But the ADDITIVE model the analyst fits identifies
     condition perfectly (R²=0, VIF=1). Blocking here is the worst failure the tool can make.
  2. FALSE MAJOR  — a perfectly balanced design with one sample per cell (min_cell==1) is
     orthogonal (R²=0), yet the old heuristic called it fragile. Small ≠ confounded.
  3. LYING VERDICT — the `major` text always claimed "only one nuisance stratum".

And the positive behaviour: partial confounding is a CONTINUUM, and whether it biases you
depends on whether you actually adjusted for the nuisance.
"""
import numpy as np
import pandas as pd
import pytest

from sc_referee import statuses as S
from sc_referee.checks.confounding import evaluate_confounding
from tests.factories import make_design


def _obs(rows, cols):
    df = pd.DataFrame(rows, columns=cols)
    df.insert(0, "donor_id", [f"D{i + 1}" for i in range(len(df))])
    return df


def xor_obs():
    """condition = XOR(run, sex): every joint (run,sex) cell is pure, yet condition is
    orthogonal to BOTH nuisance main effects. Additively estimable."""
    rows = []
    for run in ("R1", "R2"):
        for sex in ("M", "F"):
            cond = "ctrl" if (run == "R1") == (sex == "M") else "stim"
            rows += [(cond, run, sex)] * 2
    return _obs(rows, ["condition", "run", "sex"])


def crossed_one_per_cell_obs():
    """3 runs, each holding exactly one ctrl and one stim. Perfectly orthogonal, min_cell==1."""
    rows = [(c, r) for r in ("R1", "R2", "R3") for c in ("ctrl", "stim")]
    return _obs(rows, ["condition", "run"])


def partial_31_13_obs():
    """R1: 3 ctrl / 1 stim, R2: 1 ctrl / 3 stim. Partially confounded (phi=0.5, VIF=1.33)."""
    rows = [("ctrl", "R1")] * 3 + [("stim", "R1")] + [("ctrl", "R2")] + [("stim", "R2")] * 3
    return _obs(rows, ["condition", "run"])


def complete_alias_obs():
    rows = [("ctrl", "R1")] * 4 + [("stim", "R2")] * 4
    return _obs(rows, ["condition", "run"])


def weak_leak_obs():
    """40 donors. λ = 2(a−b)/n with a=11 stim in R2, b=10 ctrl in R2 → λ = 0.05.
    Real but negligible association: below the flagging threshold, still reported."""
    rows = ([("ctrl", "R1")] * 10 + [("ctrl", "R2")] * 10
            + [("stim", "R1")] * 9 + [("stim", "R2")] * 11)
    return _obs(rows, ["condition", "run"])


def near_collinear_obs():
    """40 donors, R1 = 20 ctrl + 1 stim, R2 = 19 stim. R²≈0.90 → VIF≈10.5. Estimable, barely."""
    rows = [("ctrl", "R1")] * 20 + [("stim", "R1")] + [("stim", "R2")] * 19
    return _obs(rows, ["condition", "run"])


# --------------------------------------------------------------------------- #
# honesty: the measured number is always reported, the threshold is only a status cut
# --------------------------------------------------------------------------- #
def test_weak_leakage_is_reported_even_though_it_does_not_flag():
    d = make_design(model="~ condition", batch=("run",), sample_unit=("donor_id",),
                    analyst_adjusted_for=["condition"])
    f = evaluate_confounding(weak_leak_obs(), d)

    assert f.status == "pass", f.verdict
    assert f.metrics["max_leakage"] == pytest.approx(0.05, abs=1e-9)      # λ still reported per term
    assert f.metrics["omitted_partial_r2"] == pytest.approx(0.0025, abs=1e-4)
    assert "partial R²" in f.verdict                 # the number is surfaced, not hidden
    assert "policy" in f.verdict.lower()             # and the cut is named as a policy choice


# --------------------------------------------------------------------------- #
# near-collinearity when you DID adjust: an efficiency cost, not a confound
# --------------------------------------------------------------------------- #
def test_adjusted_estimable_vif_is_clear_efficiency_advisory():
    d = make_design(model="~ run + condition", batch=("run",), sample_unit=("donor_id",),
                    analyst_adjusted_for=["run", "condition"])
    f = evaluate_confounding(near_collinear_obs(), d)

    assert (f.status, f.judgment, f.coverage, S.human_state(f)) == (
        S.PASS, S.CONFORMANT, S.COMPLETE, S.CLEAR
    )
    assert f.metrics["vif"] > 10.0
    assert f.metrics["omitted"] == []
    assert "efficiency" in f.verdict.lower()


def test_informational_never_fails_ci():
    assert S.INFORMATIONAL not in S.FAIL_ON_DEFAULT


def test_bias_outranks_collinearity_when_both_present():
    """Same near-collinear data, but the batch is OMITTED -> bias dominates -> major."""
    d = make_design(model="~ condition", batch=("run",), sample_unit=("donor_id",),
                    analyst_adjusted_for=["condition"])
    f = evaluate_confounding(near_collinear_obs(), d)

    assert f.status == "major", f.verdict
    assert f.metrics["vif"] > 10.0          # it is ALSO near-collinear
    assert f.metrics["max_leakage"] > 0.9   # but the omitted-variable bias is the headline
    # the price of the fix must not be undersold: ×3.2 is not "only"
    assert "only" not in f.verdict.lower()
    assert "near-collinear" in f.verdict.lower()


def test_cheap_fix_is_not_described_as_near_collinear():
    """The 3/1,1/3 design costs ×1.15 to fix — no scary collinearity caveat there."""
    d = make_design(model="~ condition", batch=("run",), sample_unit=("donor_id",),
                    analyst_adjusted_for=["condition"])
    f = evaluate_confounding(partial_31_13_obs(), d)
    assert "near-collinear" not in f.verdict.lower()
    assert "×1.15" in f.verdict


# --------------------------------------------------------------------------- #
# BUG 1 — the false blocker
# --------------------------------------------------------------------------- #
def test_interaction_confounded_but_additively_estimable_is_not_blocked():
    """Every joint (run,sex) stratum is pure, but ~ run + sex + condition is full rank.
    Blocking this would be a false accusation on a valid design."""
    d = make_design(model="~ sex + condition", batch=("run",), sample_unit=("donor_id",),
                    analyst_adjusted_for=["sex", "condition"])
    f = evaluate_confounding(xor_obs(), d)

    assert f.status != "blocker", f.verdict
    assert f.status == "pass", f.verdict
    assert f.metrics["r2"] == pytest.approx(0.0, abs=1e-9)
    assert f.metrics["vif"] == pytest.approx(1.0, abs=1e-6)
    # but the interaction aliasing is still REPORTED, not silently dropped
    assert f.metrics["interaction_aliased"] is True


# --------------------------------------------------------------------------- #
# BUG 2 — the false major
# --------------------------------------------------------------------------- #
def test_perfectly_crossed_one_sample_per_cell_passes():
    d = make_design(batch=("run",), sample_unit=("donor_id",),
                    analyst_adjusted_for=["condition"])
    f = evaluate_confounding(crossed_one_per_cell_obs(), d)

    assert f.status == "pass", f.verdict
    assert f.metrics["r2"] == pytest.approx(0.0, abs=1e-9)
    assert f.metrics["max_leakage"] == pytest.approx(0.0, abs=1e-9)


# --------------------------------------------------------------------------- #
# the continuum: same data, different model
# --------------------------------------------------------------------------- #
def test_partial_confound_with_omitted_batch_is_major():
    """model omits `run` -> the condition estimate absorbs ~50% of any run effect."""
    d = make_design(model="~ condition", batch=("run",), sample_unit=("donor_id",),
                    analyst_adjusted_for=["condition"])
    f = evaluate_confounding(partial_31_13_obs(), d)

    assert f.status == "major", f.verdict
    assert f.metrics["vif"] == pytest.approx(4 / 3, abs=1e-6)
    assert f.metrics["max_leakage"] == pytest.approx(0.5, abs=1e-6)
    assert f.metrics["omitted"] == ["run"]


def test_same_data_with_batch_in_the_model_passes():
    """Adjusting for the batch removes the bias; you only pay variance inflation."""
    d = make_design(model="~ run + condition", batch=("run",), sample_unit=("donor_id",),
                    analyst_adjusted_for=["run", "condition"])
    f = evaluate_confounding(partial_31_13_obs(), d)

    assert f.status == "pass", f.verdict
    assert f.metrics["vif"] == pytest.approx(4 / 3, abs=1e-6)   # cost of adjusting: ×1.15 on SE
    assert f.metrics["omitted"] == []


# --------------------------------------------------------------------------- #
# BUG 3 — the verdict must name the trigger that actually fired
# --------------------------------------------------------------------------- #
def test_major_verdict_describes_leakage_not_single_bridge():
    d = make_design(model="~ condition", batch=("run",), sample_unit=("donor_id",),
                    analyst_adjusted_for=["condition"])
    f = evaluate_confounding(partial_31_13_obs(), d)
    assert "single bridge" not in f.verdict.lower()
    assert "run" in f.verdict
    assert "0.5" in f.verdict or "50" in f.verdict  # the leakage is quantified


# --------------------------------------------------------------------------- #
# regression: the guaranteed blocker still fires, and still explains itself
# --------------------------------------------------------------------------- #
def test_complete_alias_is_still_an_unarguable_blocker():
    d = make_design(model="~ condition", batch=("run",), sample_unit=("donor_id",))
    f = evaluate_confounding(complete_alias_obs(), d)

    assert f.status == "blocker"
    assert np.isinf(f.metrics["vif"])
    assert f.metrics["r2"] == pytest.approx(1.0, abs=1e-9)
    assert "run" in f.verdict


# --------------------------------------------------------------------------- #
# patsy wrappers: `~ C(run) + condition` DOES adjust for run (adversarial review 2026-07-08)
# --------------------------------------------------------------------------- #
def test_patsy_wrapped_covariate_counts_as_adjusted():
    """A correctly-adjusted model must not be reported as omitting the batch."""
    d = make_design(model="~ C(run) + condition", batch=("run",), sample_unit=("donor_id",),
                    analyst_adjusted_for=["run", "condition"])
    f = evaluate_confounding(partial_31_13_obs(), d)
    assert f.metrics["omitted"] == [], f.verdict
    assert f.status == "pass", f.verdict
