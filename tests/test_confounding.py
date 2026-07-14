"""Behavioural tests for the `confounding` check — the guaranteed, power-independent blocker.

The check decides whether the target (condition/perturbation) effect is ESTIMABLE.
It is exact design-matrix algebra on a sample-level factor table, so its verdicts are
verified here on constructed cases of known structure — not as a rate.

Specificity cases (valid designs that must PASS) live in `test_confounding_specificity.py`.
"""
import pandas as pd

from sc_referee import statuses as S
from sc_referee.checks.confounding import evaluate_confounding
from tests.factories import alias_obs, make_design, paired_crossed_obs


def test_complete_batch_alias_is_blocker():
    f = evaluate_confounding(alias_obs(), make_design(sample_unit=("donor_id",)))
    assert f.status == "blocker"
    assert f.check_id == "confounding"


def test_paired_crossed_design_passes():
    f = evaluate_confounding(
        paired_crossed_obs(), make_design(sample_unit=("donor_id", "condition"),
                                          analyst_adjusted_for=["condition"])
    )
    assert f.status == "pass"


def test_unconfirmed_setup_never_blocks():
    f = evaluate_confounding(
        alias_obs(), make_design(confirmed=False, sample_unit=("donor_id",))
    )
    assert f.status == "needs_evidence"


def test_low_condition_confidence_downgrades_blocker():
    """confounding gates on the CONDITION confidence (the role it reasons about), not the replicate:
    an unsure condition assignment could mean a mis-identified alias, so it abstains. (2026-07-08.)"""
    f = evaluate_confounding(
        alias_obs(), make_design(condition_confidence_high=False, sample_unit=("donor_id",))
    )
    assert f.status == "needs_evidence"

    # ...but LOW replicate confidence must NOT downgrade it — confounding never uses the replicate
    keeps = evaluate_confounding(
        alias_obs(), make_design(confidence_high=False, sample_unit=("donor_id",))
    )
    assert keeps.status == "blocker"


def test_missing_test_level_is_a_config_error_not_a_blocker():
    """`blocker` means "your science is wrong", never "your YAML is wrong". A level that does not
    exist in the data must not exit CI under the banner `confounding: BLOCKER`, and must never
    report fabricated r2/vif. (Opus review 2026-07-08.)"""
    obs = pd.DataFrame(
        {
            "donor_id": [f"D{i}" for i in range(1, 7)],
            "condition": ["ctrl"] * 6,
            "run": ["R1", "R2"] * 3,
        }
    )
    f = evaluate_confounding(obs, make_design(sample_unit=("donor_id",)))
    assert f.status == "needs_evidence"
    assert f.coverage == S.NOT_RUN
    assert S.human_state(f) == "not_checked"
    assert "configuration error" in f.verdict
    assert "r2" not in f.metrics and "vif" not in f.metrics   # nothing fabricated


def test_varying_covariate_prevents_confounding_comparison_and_is_not_checked():
    obs = pd.DataFrame({
        "donor_id": ["D1", "D1", "D2", "D2"],
        "condition": ["ctrl", "ctrl", "stim", "stim"],
        "run": ["R1", "R2", "R2", "R2"],
    })
    finding = evaluate_confounding(obs, make_design(sample_unit=("donor_id",)))

    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == "not_checked"


def test_carries_citation():
    f = evaluate_confounding(alias_obs(), make_design(sample_unit=("donor_id",)))
    assert any("Leek" in c for c in f.citations)
