from __future__ import annotations

from sc_referee import statuses as S
from sc_referee.checks.contamination_confound import ContaminationConfoundCheck
from tests.contamination_factories import contamination_obligation_pair


def test_contamination_with_vs_without_ratified_rho_flips_only_containment():
    without_rho, without_bundle, with_rho, with_bundle = contamination_obligation_pair()
    omitted = ContaminationConfoundCheck().run(without_rho, without_bundle)
    contained = ContaminationConfoundCheck().run(with_rho, with_bundle)
    assert without_rho.target_coefficient == with_rho.target_coefficient
    assert omitted.metrics["row_ledger_identity"] == contained.metrics["row_ledger_identity"]
    assert (omitted.status, S.human_state(omitted)) == (S.MAJOR, S.FLAGGED)
    assert (contained.status, S.human_state(contained)) == (S.PASS, S.CLEAR)
    assert omitted.metrics["column_space_state"] == "not_certified"
    assert contained.metrics["column_space_state"] == "certified"


def test_contamination_fixture_is_explicitly_test_only_and_does_not_claim_true_rho():
    without_rho, _, _, _ = contamination_obligation_pair()
    record = without_rho.csp_contracts[0]
    evidence = record.fields["positive_evidence"].value
    assert evidence["kind"] == "empty_droplet_derived_external_fraction"
    assert "test-only" in record.contract_id
