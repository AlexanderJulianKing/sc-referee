from __future__ import annotations

import json

import pytest

from sc_referee.inference.proof.certificate import (
    Certificate,
    CertificateIntegrityError,
    ClaimRootBinding,
    ClaimRootGrade,
    external_status,
    load_certificate,
)


def _certificate(**overrides) -> Certificate:
    values = dict(
        policy_id="confounding.v2",
        outcome="VIOLATION_WITNESS",
        max_external_status="blocker",
        claim_root_grade=ClaimRootGrade.ACCUSATION_GRADE,
        claim_root_binding=ClaimRootBinding(
            kind="structured", claim_id="claim-1", report_artifact_digest="sha256:report",
            report_locator_digest="sha256:locator", producing_value_digest="sha256:value",
        ),
        claim_root_digest="sha256:root",
        claim_root_ratification="fact:root",
        external_fact_ratifications=("fact:root", "fact:design"),
        all_external_facts_ratified=True,
        closed_world_complete=True,
        inventory_complete=True,
        observed_report_artifact_digest="sha256:report",
        observed_report_locator_digest="sha256:locator",
        observed_producing_value_digest="sha256:value",
    )
    values.update(overrides)
    return Certificate(**values)


def test_certificate_blocker_requires_every_claim_root_gate():
    assert external_status(_certificate()) == "blocker"


@pytest.mark.parametrize(
    "change",
    (
        {"claim_root_binding": None},
        {"claim_root_digest": ""},
        {"claim_root_grade": ClaimRootGrade.CLEAN_ONLY}, {"claim_root_ratification": None},
        {"observed_report_artifact_digest": "sha256:changed"},
        {"observed_report_locator_digest": "sha256:changed"},
        {"observed_producing_value_digest": "sha256:changed"},
        {"all_external_facts_ratified": False}, {"closed_world_complete": False},
    ),
)
def test_blocker_entitled_witness_degrades_to_needs_evidence(change):
    assert external_status(_certificate(**change)) == "needs_evidence"


def test_incomplete_inventory_is_not_audited_even_with_a_witness():
    assert external_status(_certificate(inventory_complete=False)) == "not_audited"


def test_non_blocker_policy_caps_are_preserved_without_blocker_root_entitlement():
    assert external_status(_certificate(max_external_status="major")) == "major"
    assert external_status(_certificate(outcome="CLEAN_PROOF", max_external_status="pass")) == "pass"
    assert external_status(_certificate(outcome="ABSTAIN", max_external_status="not_audited")) == "needs_evidence"


def test_certificate_load_replays_gate_and_rejects_digest_mutation():
    certificate = _certificate()
    loaded, status = load_certificate(certificate.to_json())
    assert loaded == certificate and status == "blocker"
    changed = _certificate(observed_report_artifact_digest="sha256:changed")
    loaded, status = load_certificate(changed.to_json())
    assert loaded.observed_report_artifact_digest == "sha256:changed"
    assert status == "needs_evidence"
    tampered = json.loads(certificate.to_json())
    tampered["policy_id"] = "tampered"
    with pytest.raises(CertificateIntegrityError):
        load_certificate(json.dumps(tampered))


def test_certificate_load_rejects_unknown_or_malformed_data():
    payload = json.loads(_certificate().to_json())
    payload["unexpected"] = True
    with pytest.raises(CertificateIntegrityError):
        load_certificate(json.dumps(payload))
    with pytest.raises(CertificateIntegrityError):
        load_certificate("not-json")
