"""Specificity: the confounding check must NEVER false-accuse a valid design.

A referee that cries wolf is worse than none. These cases pin the corrected nuisance
set — (model terms except target) ∪ batch — that distinguishes a genuine confound from
an ordinary unpaired design. Reviewed w/ Codex 2026-07-07; see docs/planning notes.
"""
from sc_referee import statuses as S
from sc_referee.checks.confounding import evaluate_confounding
from dataclasses import replace
from tests.factories import (
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
