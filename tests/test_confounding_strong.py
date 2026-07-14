import numpy as np
from dataclasses import replace

from sc_referee import statuses as S
from sc_referee.checks.confounding import ConfoundingCheck, _dummy_block, _partial_r2, _r2, _with_intercept
from sc_referee.checks.confounding_strong import ConfoundingStrongCheck
from sc_referee.column_space import CertificationState
from tests.factories import fitted_design_declaration, make_design, pseudobulk_confounding_bundle


def _strong_design(*, adjusted, operator="ordinary_fixed_effects", intercept=True, with_w=False):
    declaration = fitted_design_declaration(
        operator_kind=operator,
        intercept=intercept,
        column_kinds={"condition": "categorical", "run": "categorical", **({"W": "categorical"} if with_w else {})},
        categorical_levels={"condition": ("ctrl", "stim"), "run": ("R1", "R2"), **({"W": ("A", "B", "C")} if with_w else {})},
        transforms={"condition": "identity", "run": "identity", **({"W": "identity"} if with_w else {})},
    )
    return make_design(
        batch=("run",), sample_unit=("donor_id",), aggregation_key=("donor_id",),
        model=("~ W + condition" if with_w else "~ condition"),
        analyst_adjusted_for=adjusted, fitted_design=declaration,
        confidence={"condition": "high", "batch": "high", "analyst_adjusted_for": "high",
                    "aggregation_key": "high", "fitted_design": "high"},
    )


def test_confounded_batch_omitted_from_fixed_effect_model_is_strong_major():
    finding = ConfoundingStrongCheck().run(
        _strong_design(adjusted=["condition"]), pseudobulk_confounding_bundle())
    assert finding.status == S.MAJOR
    assert S.human_state(finding) == S.FLAGGED
    assert finding.metrics["column_space_state"] == CertificationState.NOT_CERTIFIED.value
    assert finding.metrics["batch_partial_r2"] >= 0.01
    assert "does not condition on" in finding.verdict.lower()


def test_confounded_batch_spanned_by_fixed_effect_model_is_certified_clear():
    finding = ConfoundingStrongCheck().run(
        _strong_design(adjusted=["run", "condition"]), pseudobulk_confounding_bundle())
    assert finding.status == S.PASS
    assert S.human_state(finding) == S.CLEAR
    assert finding.judgment == S.CONFORMANT and finding.proof_grade == S.EXACT
    assert finding.metrics["column_space_state"] == CertificationState.CERTIFIED.value


def test_random_effect_model_is_not_audited_and_renders_not_checked():
    finding = ConfoundingStrongCheck().run(
        _strong_design(adjusted=["run", "condition"], operator="random_intercept_only"),
        pseudobulk_confounding_bundle())
    assert finding.status == S.NOT_AUDITED and finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == S.NOT_CHECKED
    assert finding.metrics["machine_reason"] == "no_verified_conditioning_operator"


def test_intercept_false_declaration_is_not_audited_even_when_otherwise_exact():
    finding = ConfoundingStrongCheck().run(
        _strong_design(adjusted=["run", "condition"], intercept=False),
        pseudobulk_confounding_bundle())
    assert finding.status == S.NOT_AUDITED
    assert S.human_state(finding) == S.NOT_CHECKED
    assert finding.metrics["machine_reason"] == "no_verified_intercept"


def test_partial_not_marginal_gate_agrees_with_layer1_clear():
    bundle = pseudobulk_confounding_bundle(with_w=True)
    design = _strong_design(adjusted=["W", "condition"], with_w=True)
    sub = bundle.observations.reset_index(drop=True)
    t = (sub["condition"] == "stim").to_numpy(dtype=float)
    marginal = _r2(t, _with_intercept(_dummy_block(sub, ["run"]), len(sub)))
    partial = _partial_r2(sub, t, ["W"], ["run"])
    assert marginal >= 0.01 and partial < 0.01
    strong = ConfoundingStrongCheck().run(design, bundle)
    layer1 = ConfoundingCheck().run(design, bundle)
    assert strong.status == S.PASS and S.human_state(strong) == S.CLEAR
    assert layer1.status == S.PASS and S.human_state(layer1) == S.CLEAR
    assert strong.metrics["batch_partial_r2"] == partial


def test_unratified_fitted_declaration_is_not_checked():
    design = _strong_design(adjusted=["condition"])
    design.confidence["fitted_design"] = "low"
    finding = ConfoundingStrongCheck().run(design, pseudobulk_confounding_bundle())
    assert finding.status == S.NOT_AUDITED and finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == S.NOT_CHECKED
    assert "biased" not in finding.verdict.lower()


def test_upstream_handled_batch_abstains_in_strong_layer():
    from tests.factories import random_intercept_batch_declaration

    design = _strong_design(adjusted=["condition"])
    entry = random_intercept_batch_declaration(modeled_as="upstream_handled")
    design = replace(design, fitted_design=replace(
        design.fitted_design, batch_modeling={"run": entry}
    ))
    finding = ConfoundingStrongCheck().run(design, pseudobulk_confounding_bundle())
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.NOT_CHECKED
    )
    assert finding.metrics["machine_reason"] == "upstream_handling_not_independently_certified"


def test_interaction_capture_is_not_audited_never_major():
    design = _strong_design(adjusted=["run", "condition"])
    design = replace(design, model="~ run * condition")
    finding = ConfoundingStrongCheck().run(design, pseudobulk_confounding_bundle())
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NOT_AUDITED, S.NOT_RUN, S.NOT_CHECKED
    )
    assert finding.metrics["machine_reason"] == "unsupported_operator"
    assert "unsupported_nonadditive_operator" in finding.verdict
