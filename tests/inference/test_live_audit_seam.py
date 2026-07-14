from __future__ import annotations

import hashlib
import json

import yaml


def _digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write_live_coordinate_fixture(root, *, human=True, source_matches=True):
    from fixtures.confounding_alias.make_fixture import build
    from dataclasses import asdict
    from sc_referee.inference.live import trusted_live_summary_binding

    build(root)
    config_path = root / "sc-referee.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["analysis_type"] = "other"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))

    source = "reported = source\n"
    source_path = root / "analysis.py"
    source_path.write_text(source)
    report_path = root / "results" / "de.csv"
    report_digest = _digest(report_path)
    source_digest = "sha256:" + hashlib.sha256(source.encode()).hexdigest()
    if not source_matches:
        source_digest = "sha256:mismatched"
    payload = {
        "version": 1,
        "contracts": [{
            "policy_id": "coordinate_consumption.v1",
            "claim_root_grade": "accusation_grade",
            "source_digests": [source_digest],
            "claim_root": {
                "claim_id": "claim:coordinate",
                "report_artifact_digest": report_digest,
                "report_span_or_field": "table.coordinate",
                "producing_value": "reported",
                "producer_binding_digest": "sha256:value",
                "claim_role": "reported_value",
                "ratification_fact_id": "fact:root",
            },
            "relations": [
                "ExactContigIdentityAndLengthBound", "CoordinateUnavoidablyConsumed",
                "CoordinateMateriallyAffectsClaim",
            ],
            "facts": {
                "CoordinateValue": 102, "ConsumerLowerBound": 0, "ConsumerUpperBound": 101,
                "ConsumerLowerInclusive": True, "ConsumerUpperInclusive": True,
                "CoordinateConsumerContract": "linear_closed.v1",
            },
            "assumptions": [],
            "artifact": {
                "logical_role": "report", "format": "csv", "schema_digest": "sha256:schema",
                "content_digest": report_digest, "writer_version": "writer:1",
                "serializer_contract": "csv.v1", "path_resolved": True,
                "unique_writer": True, "field_correspondence": True,
                "no_later_mutation": True,
            },
            "summary_bindings": [asdict(trusted_live_summary_binding(
                "coordinate_consumption.v1"
            ))],
            "ratification": {
                "ratified_by": {"kind": "human" if human else "model", "id": "reviewer"},
                "fact_ids": ["fact:root", "fact:semantics"],
                "all_external_facts_ratified": True,
            },
            "closed_world_complete": True,
            "observed": {
                "report_artifact_digest": report_digest,
                "report_locator_digest": "sha256:locator",
                "producing_value_digest": "sha256:value",
            },
            "binding": {
                "report_locator_digest": "sha256:locator",
                "producing_value_digest": "sha256:value",
            },
        }],
    }
    (root / "sc-referee.inference.json").write_text(json.dumps(payload, indent=2))


def test_shipped_audit_rejects_a_self_ratified_coordinate_contract(tmp_path):
    from sc_referee.audit import run_audit

    _write_live_coordinate_fixture(tmp_path)
    result = run_audit(tmp_path, engine="simple")
    finding = next(item for item in result.findings
                   if item.check_id == "inference.coordinate_consumption")
    assert finding.status == "not_audited"
    assert finding.metrics["engine_outcome"] == "ABSTAIN"
    assert result.ci_fails() is False


def test_shipped_audit_keeps_nonhuman_or_source_changed_contracts_nonadverse(tmp_path):
    from sc_referee.audit import run_audit

    _write_live_coordinate_fixture(tmp_path, human=False)
    nonhuman = run_audit(tmp_path, engine="simple")
    finding = next(item for item in nonhuman.findings
                   if item.check_id == "inference.coordinate_consumption")
    assert finding.status == "not_audited"
    assert nonhuman.ci_fails() is False

    _write_live_coordinate_fixture(tmp_path, source_matches=False)
    changed = run_audit(tmp_path, engine="simple")
    finding = next(item for item in changed.findings
                   if item.check_id == "inference.coordinate_consumption")
    assert finding.status == "not_audited"
    assert changed.ci_fails() is False


def test_without_contract_the_only_change_is_policy_specific_not_audited(tmp_path):
    from fixtures.confounding_alias.make_fixture import build
    from sc_referee.audit import run_audit

    build(tmp_path)
    config_path = tmp_path / "sc-referee.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["analysis_type"] = "trajectory"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    result = run_audit(tmp_path, engine="simple")
    assert [(item.check_id, item.status) for item in result.findings] == [
        ("inference.trajectory_circularity", "not_audited")
    ]
