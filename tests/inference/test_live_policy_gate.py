from __future__ import annotations

from types import SimpleNamespace

import pytest

from sc_referee.inference.live import LivePolicyContract, build_engine_verifiers


NON_FLAGSHIP_CASES = {
    "confounding.v2": "condition_contrast_DE",
    "pseudoreplication.v1": "condition_contrast_DE",
    "enrichment_universe.v1": "differential_abundance",
    "coordinate_consumption.v1": "other",
    "spatial_iid.v1": "condition_contrast_DE",
    "trajectory_circularity.v1": "trajectory",
}


def _check(policy_id):
    return next(check for check in build_engine_verifiers() if check.policy_id == policy_id)


@pytest.mark.parametrize("policy_id", NON_FLAGSHIP_CASES)
def test_non_flagship_policies_honestly_abstain_even_with_folder_proposals(policy_id):
    contract = LivePolicyContract(
        policy_id,
        ("reported = source\n",),
        {"analysis_name": "route-only"},
        ({"fact_type": "design_unit", "value": "donor"},),
    )
    bundle = SimpleNamespace(
        code_signals={"sources": list(contract.sources)},
        _inference_live_contracts={policy_id: contract},
    )
    design = SimpleNamespace(
        analysis_type=NON_FLAGSHIP_CASES[policy_id],
        confirmed_by_human=True,
        confidence={},
        name="claim",
    )

    finding = _check(policy_id).run(design, bundle, None)

    assert finding.status in {"needs_evidence", "not_audited"}
    assert finding.metrics["engine_outcome"] == "ABSTAIN"


def test_single_source_eqtl_does_not_route_the_joint_harmonization_policy():
    check = _check("allele_harmonization.v1")
    design = SimpleNamespace(analysis_type="eqtl")
    bundle = SimpleNamespace(code_signals={"sources": ["fit_single_source_eqtl()\n"]})

    assert check.applies_to(design, bundle) is False
    assert check.cannot_evaluate(design, bundle) is None


def test_registry_replaces_only_double_dipping_and_keeps_other_overlap_checks_legacy():
    from sc_referee.checks.confounding import ConfoundingCheck
    from sc_referee.checks.experimental_unit import ExperimentalUnitCheck
    from sc_referee.registry import build_checks

    by_id = {check.id: check for check in build_checks("simple")}

    assert type(by_id["double_dipping"]).__module__ == "sc_referee.inference.live"
    assert isinstance(by_id["confounding"], ConfoundingCheck)
    assert isinstance(by_id["experimental_unit"], ExperimentalUnitCheck)
    assert "inference.double_dipping" not in by_id


def test_all_eight_policy_definitions_remain_available_but_only_one_has_computed_live_facts():
    verifiers = build_engine_verifiers()

    assert len(verifiers) == 8
    assert {check.policy_id for check in verifiers} == {
        "double_dipping.v1",
        "confounding.v2",
        "pseudoreplication.v1",
        "allele_harmonization.v1",
        "enrichment_universe.v1",
        "coordinate_consumption.v1",
        "spatial_iid.v1",
        "trajectory_circularity.v1",
    }
