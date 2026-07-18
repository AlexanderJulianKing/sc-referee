from __future__ import annotations

from unittest.mock import patch

from sc_referee import statuses as S
from sc_referee.checks.base import ConditionalPremise
from sc_referee.checks.contamination_confound import ContaminationConfoundCheck
from tests.contamination_factories import eqtl_contamination_case, contamination_obligation_pair


def test_eqtl_omitted_rho_is_conditional_major_and_not_contained():
    design, bundle = eqtl_contamination_case(adjusted=("genotype",))
    finding = ContaminationConfoundCheck().run(design, bundle)

    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.MAJOR, S.COMPLETE, S.FLAGGED,
    )
    assert finding.metrics["column_space_state"] == "not_certified"
    assert finding.metrics["excluded_exposure_columns"] == ["genotype"]
    assert isinstance(finding.conditional_on, ConditionalPremise)


def test_eqtl_adjusted_rho_is_conditional_pass_and_contained():
    design, bundle = eqtl_contamination_case(
        adjusted=("genotype", "rho_external")
    )
    finding = ContaminationConfoundCheck().run(design, bundle)

    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.PASS, S.COMPLETE, S.CLEAR,
    )
    assert finding.metrics["column_space_state"] == "certified"
    assert finding.metrics["excluded_exposure_columns"] == ["genotype"]
    assert isinstance(finding.conditional_on, ConditionalPremise)


def test_unratified_eqtl_is_not_checked_without_reaching_geometry():
    design, bundle = eqtl_contamination_case(
        adjusted=("genotype",), ratified=False
    )
    with patch(
        "sc_referee.checks.contamination_confound.certify_column_space",
        side_effect=AssertionError("geometry unreachable"),
    ):
        finding = ContaminationConfoundCheck().run(design, bundle)

    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED,
    )
    assert finding.conditional_on is None


def test_condition_contrast_contamination_behavior_is_unchanged():
    without_rho, without_bundle, with_rho, with_bundle = contamination_obligation_pair()
    omitted = ContaminationConfoundCheck().run(without_rho, without_bundle)
    contained = ContaminationConfoundCheck().run(with_rho, with_bundle)

    assert (omitted.status, omitted.metrics["column_space_state"]) == (
        S.MAJOR, "not_certified",
    )
    assert (contained.status, contained.metrics["column_space_state"]) == (
        S.PASS, "certified",
    )
