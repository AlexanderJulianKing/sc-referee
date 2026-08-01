from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.migrate_v0_12_to_v0_13 import PublicMigrationError, migrate_public_bundle


def test_v012_bundle_migration_invents_no_execution_authority(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.12.0"
    target_root = project_root / "reference" / "schemas-v0.13.0"
    output = tmp_path / "migration"
    migrated = migrate_public_bundle(
        source_root / "examples" / "audit-bundle.example.json",
        source_root,
        target_root,
        output,
    )

    assert migrated["schema_version"] == "0.13.0"
    assert migrated["project_execution_authorizations"] == []
    assert migrated["storage_manifests"] == []
    assert all(
        capability["capability_evidence_status"]
        in {"not_supported", "legacy_probe_projection_unavailable"}
        for capability in migrated["sandbox_capabilities"]
    )
    assert all(
        capability["capability_evidence"] is None for capability in migrated["sandbox_capabilities"]
    )
    assert all(
        execution["authorization_evidence_status"]
        in {"not_required", "imported", "legacy_authorization_projection_unavailable"}
        for execution in migrated["executions"]
    )
    assert all(execution["project_execution"] is None for execution in migrated["executions"])

    report = json.loads((output / "MIGRATION_REPORT.json").read_text(encoding="utf-8"))
    assert report["authorization_invented"] is False
    assert report["capability_probe_invented"] is False
    assert report["controller_registry_entry_created"] is False
    assert report["execution_launched"] is False
    assert report["storage_manifest_carried_forward"] is False


def test_v012_project_execution_is_demoted_and_dependent_fixture_fails_closed(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.12.0"
    target_root = project_root / "reference" / "schemas-v0.13.0"
    source = json.loads(
        (source_root / "examples" / "audit-bundle.example.json").read_text(encoding="utf-8")
    )
    fixture = json.loads(
        (source_root / "examples" / "benchmark-fixture.example.json").read_text(encoding="utf-8")
    )
    source["benchmark_fixtures"] = [fixture]
    capability = json.loads(
        (source_root / "examples" / "sandbox-capability.example.json").read_text(encoding="utf-8")
    )
    execution = copy.deepcopy(fixture["proof_evidence"]["public_inputs"]["executions"][0])
    execution_record = json.loads(
        (source_root / "examples" / "execution.auditor-verification.example.json").read_text(
            encoding="utf-8"
        )
    )
    execution_record.update(
        {
            "actor": "project_workflow",
            "execution_id": execution["record_ref"]["record_id"],
            "execution_kind": "project_workflow",
            "sandbox": {
                "authorization_status": "authorized",
                "network_policy": "denied",
                "project_code_executed": True,
                "sandbox_capability_ref": {
                    "record_type": "sandbox_capability",
                    "record_id": capability["sandbox_capability_id"],
                },
            },
        }
    )
    source["sandbox_capabilities"] = [capability]
    source["executions"] = [execution_record]
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    migrated = migrate_public_bundle(source_path, source_root, target_root, tmp_path / "migration")
    assert migrated["sandbox_capabilities"][0]["project_code_execution_supported"] is False
    assert (
        migrated["sandbox_capabilities"][0]["capability_evidence_status"]
        == "legacy_probe_projection_unavailable"
    )
    assert (
        migrated["executions"][0]["authorization_evidence_status"]
        == "legacy_authorization_projection_unavailable"
    )
    assert migrated["benchmark_fixtures"][0]["qualification_proof_status"] == (
        "legacy_proof_projection_unavailable"
    )
    assert migrated["benchmark_fixtures"][0]["proof_evidence"] is None
    assert migrated["qualification_metric_sets"] == []


def test_v012_migration_rejects_mixed_versions(project_root: Path, tmp_path: Path) -> None:
    source_root = project_root / "reference" / "schemas-v0.12.0"
    source = json.loads(
        (source_root / "examples" / "audit-bundle.example.json").read_text(encoding="utf-8")
    )
    source["claims"][0]["schema_version"] = "0.11.0"
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(PublicMigrationError, match="Mixed or unsupported"):
        migrate_public_bundle(
            source_path,
            source_root,
            project_root / "reference" / "schemas-v0.13.0",
            tmp_path / "migration",
        )


def test_v012_migration_removes_metrics_when_outcome_identity_changes_without_downgrade(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.12.0"
    target_root = project_root / "reference" / "schemas-v0.13.0"
    source = json.loads(
        (source_root / "examples" / "audit-bundle.example.json").read_text(encoding="utf-8")
    )
    fixture = json.loads(
        (source_root / "examples" / "benchmark-fixture.example.json").read_text(encoding="utf-8")
    )
    outcome = json.loads(
        (source_root / "examples" / "detector-case-outcome.example.json").read_text(
            encoding="utf-8"
        )
    )
    metric_set = json.loads(
        (source_root / "examples" / "qualification-metric-set.example.json").read_text(
            encoding="utf-8"
        )
    )
    fixture["fixture_id"] = outcome["fixture_ref"]["record_id"]
    source["benchmark_fixtures"] = [fixture]
    source["detector_case_outcomes"] = [outcome]
    source["qualification_metric_sets"] = [metric_set]
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    migrated = migrate_public_bundle(source_path, source_root, target_root, tmp_path / "migration")

    assert migrated["detector_case_outcomes"][0]["case_outcome_id"] != outcome["case_outcome_id"]
    assert migrated["qualification_metric_sets"] == []
    assert "x-v0-12-unverified-qualification-metric-sets" in migrated["extensions"]
