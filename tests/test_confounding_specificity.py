"""Specificity: the confounding check must NEVER false-accuse a valid design.

A referee that cries wolf is worse than none. These cases pin the corrected nuisance
set — (model terms except target) ∪ batch — that distinguishes a genuine confound from
an ordinary unpaired design. Reviewed w/ Codex 2026-07-07; see docs/planning notes.
"""
import numpy as np
import pandas as pd
import pytest

from sc_referee import statuses as S
from sc_referee.checks.confounding import evaluate_confounding
from dataclasses import replace
from tests.factories import (
    fitted_design_declaration,
    make_design,
    single_bridge_obs,
    unpaired_crossed_obs,
    unpaired_nobatch_obs,
)


def test_valid_unpaired_crossed_batch_passes():
    """4 ctrl donors + 4 stim donors (unpaired), batch crossed with condition.
    Condition is estimable across donors -> PASS. The buggy 'donor in nuisance' rule
    would falsely BLOCK this."""
    f = evaluate_confounding(
        unpaired_crossed_obs(),
        make_design(sample_unit=("donor_id",), analyst_adjusted_for=["condition"]),
    )
    assert f.status == "pass", f.verdict


def test_valid_unpaired_no_batch_passes():
    f = evaluate_confounding(
        unpaired_nobatch_obs(), make_design(batch=(), sample_unit=("donor_id",),
                                            analyst_adjusted_for=["condition"])
    )
    assert f.status == "pass", f.verdict


def test_donor_in_model_and_aliased_is_blocker():
    """If the analyst PUTS donor in the model (~ donor_id + condition) on an unpaired
    design, condition IS aliased with donor (rank-deficient) -> BLOCKER. Donor enters
    the nuisance set here because it is a model term, not because it is the replicate."""
    f = evaluate_confounding(
        unpaired_crossed_obs(),
        make_design(model="~ donor_id + condition", batch=(), sample_unit=("donor_id",)),
    )
    assert f.status == "blocker", f.verdict


def test_single_bridge_stratum_is_major():
    f = evaluate_confounding(
        single_bridge_obs(),
        make_design(sample_unit=("donor_id",), analyst_adjusted_for=["condition"]),
    )
    assert f.status == "major", f.verdict


def test_every_layer1_abstention_renders_not_checked():
    from tests.frozen_oracles.cases import confounding_cases

    frozen = {
        name: evaluate_confounding(observations, design)
        for name, observations, design in confounding_cases()
    }
    unconfirmed_correct = evaluate_confounding(
        unpaired_crossed_obs(),
        make_design(sample_unit=("donor_id",), analyst_adjusted_for=["condition"],
                    confirmed=False),
    )
    cases = [
        frozen["alias_unconfirmed"],
        frozen["alias_low_condition"],
        frozen["missing_level"],
        frozen["varying_covariate"],
        unconfirmed_correct,
    ]
    assert [(f.status, f.coverage, S.human_state(f)) for f in cases] == [
        (S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED)
    ] * len(cases)


def test_upstream_handled_batch_abstains_in_named_omission_layer():
    from tests.factories import fitted_design_declaration, random_intercept_batch_declaration

    declaration = fitted_design_declaration(batch_modeling={
        "run": random_intercept_batch_declaration(modeled_as="upstream_handled")
    })
    design = make_design(
        sample_unit=("donor_id",), analyst_adjusted_for=["condition"],
        fitted_design=declaration,
        confidence={"condition": "high", "batch": "high", "analyst_adjusted_for": "high",
                    "fitted_design": "high"},
    )
    finding = evaluate_confounding(single_bridge_obs(), design)
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.NOT_CHECKED
    )
    assert finding.metrics["machine_reason"] == "upstream_handling_not_independently_certified"
    assert "batch corrected upstream" in finding.verdict.lower()


def _continuous_covariate_design():
    """`~ age + condition` with age declared CONTINUOUS — a valid, full-rank, estimable design."""
    obs = pd.DataFrame({
        "donor_id": ["D1", "D2", "D3", "D4"],
        "condition": ["ctrl", "ctrl", "stim", "stim"],
        "age": [20, 30, 40, 50],
    })
    fd = fitted_design_declaration(
        column_kinds={"age": "continuous", "condition": "categorical"},
        categorical_levels={"condition": ("ctrl", "stim")},
        transforms={"age": "identity", "condition": "identity"},
    )
    design = make_design(
        model="~ age + condition", batch=(), sample_unit=("donor_id",),
        analyst_adjusted_for=["age", "condition"], fitted_design=fd,
        confidence={"condition": "high", "analyst_adjusted_for": "high", "fitted_design": "high"},
    )
    return obs, design


def test_continuous_covariate_is_numeric_not_dummy_coded():
    """Regression (F8): a covariate declared CONTINUOUS in `column_kinds` must enter the design
    matrix as its single numeric column, not n-1 treatment dummies. `~ age + condition` on four
    donors with distinct ages is full rank and estimable; one-hot-coding age manufactured a spurious
    perfect alias (R²=1) and a FALSE BLOCKER — the worst error this tool can make."""
    obs, design = _continuous_covariate_design()
    f = evaluate_confounding(obs, design)
    assert f.status == S.PASS, f.verdict
    assert abs(f.metrics["r2"] - 0.8) < 1e-6, f.metrics     # numeric age, not a saturating dummy alias
    assert abs(f.metrics["vif"] - 5.0) < 1e-6, f.metrics
    assert "perfectly entangled" not in f.verdict and "R²=1.00" not in f.verdict


def test_categorical_alias_still_blocks_after_continuous_fix():
    """Positive control: encoding declared-continuous covariates numerically must NOT weaken the
    categorical batch-alias blocker. A categorical `run` perfectly aligned to condition is still
    rank-deficient and MUST block."""
    obs = pd.DataFrame({
        "donor_id": ["D1", "D2", "D3", "D4"],
        "condition": ["ctrl", "ctrl", "stim", "stim"],
        "run": ["R1", "R1", "R2", "R2"],   # perfectly aliased with condition
    })
    fd = fitted_design_declaration(
        column_kinds={"run": "categorical", "condition": "categorical"},
        categorical_levels={"condition": ("ctrl", "stim"), "run": ("R1", "R2")},
        transforms={"run": "identity", "condition": "identity"},
    )
    design = make_design(
        model="~ run + condition", batch=("run",), sample_unit=("donor_id",),
        analyst_adjusted_for=["run", "condition"], fitted_design=fd,
        confidence={"condition": "high", "batch": "high", "analyst_adjusted_for": "high",
                    "fitted_design": "high"},
    )
    f = evaluate_confounding(obs, design)
    assert f.status == S.BLOCKER, f.verdict
    assert f.metrics["r2"] >= 1.0 - 1e-6, f.metrics


def test_large_scale_continuous_exact_alias_still_blocks():
    """Regression (F1): mean-centering keeps the least-squares projection well-conditioned, so an
    EXACT affine alias in a large-magnitude continuous covariate is not numerically discarded.
    age = base + 30·(condition==stim) with base=1e10 puts the target exactly in span(1, age) and MUST
    block; before centering, `lstsq` silently discarded the contrast and returned PASS at R²≈3e-9."""
    obs = pd.DataFrame({
        "donor_id": ["D1", "D2", "D3", "D4"],
        "condition": ["ctrl", "ctrl", "stim", "stim"],
        "age": [1e10, 1e10, 1e10 + 30, 1e10 + 30],
    })
    fd = fitted_design_declaration(
        column_kinds={"age": "continuous", "condition": "categorical"},
        categorical_levels={"condition": ("ctrl", "stim")},
        transforms={"age": "identity", "condition": "identity"},
    )
    design = make_design(
        model="~ age + condition", batch=(), sample_unit=("donor_id",),
        analyst_adjusted_for=["age", "condition"], fitted_design=fd,
        confidence={"condition": "high", "analyst_adjusted_for": "high", "fitted_design": "high"},
    )
    f = evaluate_confounding(obs, design)
    assert f.status == S.BLOCKER, f.verdict
    assert f.metrics["r2"] >= 1.0 - 1e-6, f.metrics


@pytest.mark.parametrize("bad_age", [
    [20.0, 30.0, 40.0, float("nan")],   # F2: NaN previously dummy-fell-back into a false BLOCKER
    [20.0, 30.0, 40.0, float("inf")],   # F4: inf previously CRASHED the SVD
    [20.0, 30.0, 40.0, float("-inf")],  # -inf
    [True, False, True, False],         # boolean: rejected by the canonical matrix builder
    ["20", "30", "40", "50"],           # numeric-looking STRING: not a numeric dtype, must be rejected
])
def test_invalid_continuous_covariate_abstains_never_blocks_or_crashes(bad_age):
    """Regression (F2/F4): a covariate declared continuous but not finite non-boolean numeric cannot
    form a design matrix — abstain as a configuration error, never a dummy-coded false blocker and
    never an SVD crash."""
    obs = pd.DataFrame({
        "donor_id": ["D1", "D2", "D3", "D4"],
        "condition": ["ctrl", "ctrl", "stim", "stim"],
        "age": bad_age,
    })
    fd = fitted_design_declaration(
        column_kinds={"age": "continuous", "condition": "categorical"},
        categorical_levels={"condition": ("ctrl", "stim")},
        transforms={"age": "identity", "condition": "identity"},
    )
    design = make_design(
        model="~ age + condition", batch=(), sample_unit=("donor_id",),
        analyst_adjusted_for=["age", "condition"], fitted_design=fd,
        confidence={"condition": "high", "analyst_adjusted_for": "high", "fitted_design": "high"},
    )
    f = evaluate_confounding(obs, design)
    assert f.status == S.NEEDS_EVIDENCE, f.verdict
    assert S.human_state(f) == S.NOT_CHECKED
    assert f.status != S.BLOCKER


def test_unratified_continuous_declaration_cannot_suppress_a_blocker():
    """Regression (F3): `column_kinds` is trusted to encode a covariate numerically ONLY when the
    fitted-design declaration is ratified (high confidence). A LOW-confidence 'continuous' claim on a
    genuinely aliasing categorical batch must NOT suppress the guaranteed blocker."""
    obs = pd.DataFrame({
        "donor_id": list("ABCDEF"),
        "condition": ["ctrl", "stim", "ctrl", "ctrl", "stim", "ctrl"],   # run==2 -> stim: confounded
        "run": [1, 2, 3, 1, 2, 3],
    })
    fd = fitted_design_declaration(
        column_kinds={"run": "continuous", "condition": "categorical"},   # mis-declared
        categorical_levels={"condition": ("ctrl", "stim")},
        transforms={"run": "identity", "condition": "identity"},
    )
    design = make_design(
        model="~ run + condition", batch=("run",), sample_unit=("donor_id",),
        analyst_adjusted_for=["run", "condition"], fitted_design=fd,
        confidence={"condition": "high", "analyst_adjusted_for": "high", "fitted_design": "low"},
    )
    f = evaluate_confounding(obs, design)
    assert f.status == S.BLOCKER, f.verdict


def test_multi_scale_continuous_alias_is_equilibrated_not_missed():
    """Regression (F1, deeper): with two continuous nuisances on wildly different scales, mean-centering
    ALONE is insufficient — `lstsq` mis-ranks the matrix and MISSES an exact alias (it returned a
    negative R²). Column equilibration restores it: `lib` (×1e20) affinely encodes the condition, so
    the contrast is not estimable and MUST block."""
    obs = pd.DataFrame({
        "donor_id": ["D1", "D2", "D3", "D4"],
        "condition": ["ctrl", "ctrl", "stim", "stim"],
        "age": [20.0, 30.0, 40.0, 50.0],
        "lib": [1e20, 1e20, 3e20, 3e20],    # aligned with condition, huge scale disparity vs age
    })
    fd = fitted_design_declaration(
        column_kinds={"age": "continuous", "lib": "continuous", "condition": "categorical"},
        categorical_levels={"condition": ("ctrl", "stim")},
        transforms={"age": "identity", "lib": "identity", "condition": "identity"},
    )
    design = make_design(
        model="~ age + lib + condition", batch=(), sample_unit=("donor_id",),
        analyst_adjusted_for=["age", "lib", "condition"], fitted_design=fd,
        confidence={"condition": "high", "analyst_adjusted_for": "high", "fitted_design": "high"},
    )
    f = evaluate_confounding(obs, design)
    assert f.status == S.BLOCKER, f.verdict
    assert f.metrics["r2"] >= 1.0 - 1e-6, f.metrics


def test_incomplete_high_confidence_column_kinds_abstains():
    """Regression (F4): a CONFIRMED (high-confidence) fitted design that omits the kind of a
    fitted-model nuisance term (here `age`) must ABSTAIN — the design matrix cannot be built soundly —
    not default the term to categorical and manufacture a false blocker (missing_column_kind)."""
    obs = pd.DataFrame({
        "donor_id": ["D1", "D2", "D3", "D4"],
        "condition": ["ctrl", "ctrl", "stim", "stim"],
        "age": [20, 30, 40, 50],
    })
    fd = fitted_design_declaration(
        column_kinds={"condition": "categorical"},   # 'age' (a fitted-model term) is NOT declared
        categorical_levels={"condition": ("ctrl", "stim")},
        transforms={"condition": "identity"},
    )
    design = make_design(
        model="~ age + condition", batch=(), sample_unit=("donor_id",),
        analyst_adjusted_for=["age", "condition"], fitted_design=fd,
        confidence={"condition": "high", "analyst_adjusted_for": "high", "fitted_design": "high"},
    )
    f = evaluate_confounding(obs, design)
    assert f.status == S.NEEDS_EVIDENCE, f.verdict
    assert f.status != S.BLOCKER


def test_dummy_continuous_name_collision_does_not_crash_leakage():
    """Regression (collision): a categorical column `x` (value 'b' -> a `[level=b]` dummy) and a
    continuous column literally named `x_b` previously produced duplicate encoded labels and crashed
    `_leakage`. The canonical builder yields unique ids and `_leakage` iterates positionally."""
    from sc_referee.checks.confounding import _leakage
    samples = pd.DataFrame({"x": ["a", "b", "a", "b", "a", "b"], "x_b": [0.0, 1, 2, 3, 4, 5]})
    t = np.array([0.0, 1, 0, 1, 0, 1])
    lam = _leakage(samples, t, [], ["x", "x_b"], {"x_b"})   # categorical x + continuous x_b
    assert isinstance(lam, dict) and len(lam) == 2          # both λ kept, disambiguated — none dropped


@pytest.mark.parametrize("levels,run", [
    (("R1", "R2"), ["R1", "R1", "R2", "R2", "R3", "R3"]),        # observed R3 not in the ratified ledger
    (("R1", "R2", "R3"), ["R1", "R1", "R2", "R2", "R1", "R2"]),  # ledger lists R3, but it is never observed
])
def test_ratified_categorical_ledger_mismatch_abstains(levels, run):
    """Regression (F4): a ratified categorical level ledger is a contract — a data level it does not
    list, or a listed level the data never show (checked against the full sample table), is a
    configuration inconsistency and must ABSTAIN, never silently re-derive the ledger and risk a false
    blocker."""
    obs = pd.DataFrame({
        "donor_id": list("ABCDEF"),
        "condition": ["ctrl", "stim", "ctrl", "stim", "ctrl", "stim"],
        "run": run,
    })
    fd = fitted_design_declaration(
        column_kinds={"run": "categorical", "condition": "categorical"},
        categorical_levels={"condition": ("ctrl", "stim"), "run": levels},
        transforms={"run": "identity", "condition": "identity"},
    )
    design = make_design(
        model="~ run + condition", batch=("run",), sample_unit=("donor_id",),
        analyst_adjusted_for=["run", "condition"], fitted_design=fd,
        confidence={"condition": "high", "batch": "high", "analyst_adjusted_for": "high",
                    "fitted_design": "high"},
    )
    f = evaluate_confounding(obs, design)
    assert f.status == S.NEEDS_EVIDENCE, f.verdict
    assert f.status != S.BLOCKER


@pytest.mark.parametrize("run,levels", [
    ([None, None, "R2", "R2"], ("None", "R2")),   # a MISSING value stringifies to a ledger literal
    ([1, 1, 2, 2], ("1", "2")),                    # integer data vs a string-typed ledger
    ([1, 1, "1", "1"], (1, "1")),                  # type-distinct levels colliding under string encoding
])
def test_ratified_ledger_typed_validation_catches_missing_and_type_mismatch(run, levels):
    """Regression (F4 normalization): the ledger check uses the canonical builder's TYPED comparison,
    so a missing value (None → 'None'), a type-distinct observation (int 1 vs level '1'), or a ledger
    whose type-distinct levels collide under the string encoding (1 vs '1') can no longer be conflated
    and slip through into a false blocker (or, for the collision, a false PASS on a real alias)."""
    obs = pd.DataFrame({
        "donor_id": ["D1", "D2", "D3", "D4"],
        "condition": ["ctrl", "ctrl", "stim", "stim"],
        "run": run,
    })
    fd = fitted_design_declaration(
        column_kinds={"run": "categorical", "condition": "categorical"},
        categorical_levels={"condition": ("ctrl", "stim"), "run": levels},
        transforms={"run": "identity", "condition": "identity"},
    )
    design = make_design(
        model="~ run + condition", batch=("run",), sample_unit=("donor_id",),
        analyst_adjusted_for=["run", "condition"], fitted_design=fd,
        confidence={"condition": "high", "batch": "high", "analyst_adjusted_for": "high",
                    "fitted_design": "high"},
    )
    f = evaluate_confounding(obs, design)
    assert f.status == S.NEEDS_EVIDENCE, f.verdict
    assert f.status != S.BLOCKER


def test_large_integer_continuous_covariate_abstains_not_false_blocks():
    """Regression (F6): an integer continuous covariate whose values exceed exact float64 precision
    (>2^53) collapses on the cast and would manufacture a false blocker — abstain instead of testing
    estimability on corrupted values."""
    obs = pd.DataFrame({
        "donor_id": ["D1", "D2", "D3", "D4"],
        "condition": ["ctrl", "ctrl", "stim", "stim"],
        "age": np.array([10**18, 10**18 + 1, 10**18 + 256, 10**18 + 257], dtype="int64"),
    })
    fd = fitted_design_declaration(
        column_kinds={"age": "continuous", "condition": "categorical"},
        categorical_levels={"condition": ("ctrl", "stim")},
        transforms={"age": "identity", "condition": "identity"},
    )
    design = make_design(
        model="~ age + condition", batch=(), sample_unit=("donor_id",),
        analyst_adjusted_for=["age", "condition"], fitted_design=fd,
        confidence={"condition": "high", "analyst_adjusted_for": "high", "fitted_design": "high"},
    )
    f = evaluate_confounding(obs, design)
    assert f.status == S.NEEDS_EVIDENCE, f.verdict
    assert f.status != S.BLOCKER
