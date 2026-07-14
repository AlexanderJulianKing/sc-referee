import pandas as pd

from sc_referee import statuses as S
from sc_referee.checks.confounding import (
    OMITTED_R2_MAJOR, PartialR2Decision, _partial_r2, decide_partial_r2,
    evaluate_confounding,
)
from sc_referee.checks.confounding_random_intercept import ConfoundingRandomInterceptCheck
from sc_referee.checks.confounding_random_intercept_conditional import (
    ConfoundingRandomInterceptConditionalCheck,
)
from sc_referee.checks.confounding_strong import ConfoundingStrongCheck
from tests.csp_factories import bind_ratified_between_group_contract
from tests.factories import (
    fitted_design_declaration, make_design, pseudobulk_confounding_bundle,
    random_intercept_design,
)


def _phi_squared(a, b, c, d):
    return ((a * d - b * c) ** 2
            / ((a + b) * (c + d) * (a + c) * (b + d)))


def _table(a, b, c, d):
    rows = ([{"condition": "ctrl", "batch": "A"}] * a
            + [{"condition": "ctrl", "batch": "B"}] * b
            + [{"condition": "stim", "batch": "A"}] * c
            + [{"condition": "stim", "batch": "B"}] * d)
    return pd.DataFrame(rows)


def test_realistic_categorical_partial_r2_matches_closed_form_near_policy_cut():
    # Balanced and near-balanced 40/40-arm tables include the 21/19 vs 19/21 HC-5 case
    # and the nearest integer tables around the frozen 0.01 policy cut.
    worst = 0.0
    for a in range(16, 25):
        b, c, d = 40 - a, 40 - a, a
        rows = _table(a, b, c, d)
        target = (rows["condition"] == "stim").astype(float).to_numpy()
        observed = _partial_r2(rows, target, [], ["batch"])
        expected = _phi_squared(a, b, c, d)
        worst = max(worst, abs(observed - expected))
        if expected != OMITTED_R2_MAJOR:
            assert (observed >= OMITTED_R2_MAJOR) == (expected >= OMITTED_R2_MAJOR)
    assert worst < 1e-12


def test_exact_cut_80_sample_table_abstains_and_keeps_point_estimate():
    rows = _table(22, 18, 18, 22)
    rows["donor_id"] = [f"D{i}" for i in range(len(rows))]
    finding = evaluate_confounding(
        rows,
        make_design(batch=("batch",), sample_unit=("donor_id",),
                    analyst_adjusted_for=["condition"]),
    )
    assert finding.metrics["omitted_partial_r2"] == 0.01
    assert finding.metrics["partial_r2_decision"] == "indeterminate_near_cut"
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.NOT_CHECKED
    )


def test_partial_r2_band_is_narrow_and_distinct_values_still_decide():
    assert decide_partial_r2(0.011) is PartialR2Decision.MATERIAL
    assert decide_partial_r2(0.009) is PartialR2Decision.IMMATERIAL
    assert decide_partial_r2(OMITTED_R2_MAJOR) is PartialR2Decision.INDETERMINATE_NEAR_CUT


def _exact_cut_bundle():
    bundle = pseudobulk_confounding_bundle()
    rows = _table(22, 18, 18, 22).rename(columns={"batch": "run"})
    rows["run"] = rows["run"].map({"A": "R1", "B": "R2"})
    rows["donor_id"] = [f"D{i}" for i in range(len(rows))]
    bundle.observations = rows
    return bundle


def test_exact_cut_abstention_is_consumed_by_strong_stage1_and_stage2():
    bundle = _exact_cut_bundle()
    declaration = fitted_design_declaration(
        column_kinds={"condition": "categorical", "run": "categorical"},
        categorical_levels={"condition": ("ctrl", "stim"), "run": ("R1", "R2")},
        transforms={"condition": "identity", "run": "identity"},
    )
    strong_design = make_design(
        batch=("run",), sample_unit=("donor_id",), aggregation_key=("donor_id",),
        model="~ condition", analyst_adjusted_for=["condition"],
        fitted_design=declaration,
        confidence={"condition": "high", "batch": "high",
                    "analyst_adjusted_for": "high", "aggregation_key": "high",
                    "fitted_design": "high"},
    )
    strong = ConfoundingStrongCheck().run(strong_design, bundle)
    assert (strong.status, strong.coverage, S.human_state(strong)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.NOT_CHECKED
    )
    assert strong.metrics["partial_r2_decision"] == "indeterminate_near_cut"

    stage1_design = random_intercept_design(bundle, adjusted=["condition"])
    stage1_design = __import__("dataclasses").replace(
        stage1_design, estimand_id="condition-effect/v1"
    )
    stage1 = ConfoundingRandomInterceptCheck().run(stage1_design, bundle)
    assert (stage1.status, stage1.coverage, S.human_state(stage1)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.NOT_CHECKED
    )
    assert stage1.metrics["batch_outcomes"][0]["partial_r2_decision"] == (
        "indeterminate_near_cut"
    )

    ratified = bind_ratified_between_group_contract(stage1_design, bundle, batch="run")
    stage2 = ConfoundingRandomInterceptConditionalCheck().run(ratified, bundle)
    assert (stage2.status, stage2.coverage, S.human_state(stage2)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.NOT_CHECKED
    )
    assert stage2.metrics["batch_outcome"]["partial_r2_decision"] == (
        "indeterminate_near_cut"
    )
