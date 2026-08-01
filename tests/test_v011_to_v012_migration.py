from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from sc_referee.core.ids import semantic_digest
from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.migrate_v0_11_to_v0_12 import (
    PublicMigrationError,
    migrate_public_bundle,
    migrate_standalone_fixture,
    report_standalone_metric_set,
)


def _load(root: Path, name: str) -> dict[str, object]:
    return json.loads((root / "examples" / name).read_text(encoding="utf-8"))


def _positive_fixture(root: Path) -> dict[str, object]:
    fixture = _load(root, "benchmark-fixture.example.json")
    fixture["fixture_kind"] = "positive_issue_fixture"
    fixture["fixture_id"] = "fixture:case-1"
    fixture["adjudication_ref"] = {
        "record_type": "benchmark_adjudication",
        "record_id": "benchmark-adjudication:case-1",
    }
    fixture["expected_issue_labels"] = ["claim_result_disagreement"]
    fixture["expected_root_cause_refs"] = [
        {
            "record_type": "adjudicated_root_cause",
            "record_id": "adjudicated-root-cause:case-1",
        }
    ]
    fixture["scientific_contract_refs"] = []
    fixture["proof_obligations"]["positive_root_cause_documented"] = True
    return fixture


def _metric_bundle(root: Path) -> dict[str, object]:
    bundle = _load(root, "audit-bundle.example.json")
    fixture = _positive_fixture(root)
    outcome = _load(root, "detector-case-outcome.example.json")
    metric_set = _load(root, "qualification-metric-set.example.json")
    qualification = _load(root, "detector-qualification.example.json")
    qualification["quantitative_metrics"] = {
        "metric_profile": "root-cause-clustered-metrics-v1",
        "metric_set_refs": [
            {
                "record_type": "qualification_metric_set",
                "record_id": metric_set["metric_set_id"],
            }
        ],
    }
    bundle["benchmark_fixtures"] = [deepcopy(fixture)]
    bundle["detector_case_outcomes"] = [deepcopy(outcome)]
    bundle["qualification_metric_sets"] = [deepcopy(metric_set)]
    bundle["detector_qualifications"] = [deepcopy(qualification)]
    return bundle


def test_v011_bundle_migration_preserves_fixture_evidence_fail_closed(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.11.0"
    target_root = project_root / "reference" / "schemas-v0.12.0"
    source = _metric_bundle(source_root)
    source_path = tmp_path / "source-v011.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    migrated = migrate_public_bundle(source_path, source_root, target_root, tmp_path / "migration")

    LocalSchemaRegistry(target_root).validate(migrated)
    assert migrated["schema_version"] == "0.12.0"
    assert migrated["qualification_metric_sets"] == []
    assert migrated["storage_manifests"] == []

    fixture = migrated["benchmark_fixtures"][0]
    assert fixture["qualification_proof_status"] == "legacy_proof_projection_unavailable"
    assert fixture["proof_evidence"] is None

    outcome = migrated["detector_case_outcomes"][0]
    assert outcome["fixture_semantic_digest"] == semantic_digest(fixture)
    assert outcome["qualification_proof_status"] == "legacy_proof_projection_unavailable"
    assert outcome["metric_eligible"] is False
    assert outcome["promotion_evidence_eligible"] is False
    assert outcome["extensions"]["x-v0-11-metric-eligible"] is True
    assert outcome["extensions"]["x-v0-11-promotion-evidence-eligible"] is False
    assert outcome["case_outcome_id"] != source["detector_case_outcomes"][0]["case_outcome_id"]

    preserved = migrated["extensions"]["x-v0-11-unverified-qualification-metric-sets"]
    assert preserved == source["qualification_metric_sets"]
    qualification = migrated["detector_qualifications"][0]
    assert qualification["quantitative_metrics"] is None
    assert qualification["extensions"]["x-v0-11-unverified-quantitative-metrics"]

    report = json.loads(
        (tmp_path / "migration" / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
    )
    for key in (
        "fixture_proof_invented",
        "capture_identity_invented",
        "chronology_invented",
        "clean_execution_invented",
        "hard_negative_evidence_invented",
        "qualification_metrics_invented",
    ):
        assert report[key] is False
    assert report["legacy_metric_sets_authoritative"] is False


def test_v011_outcome_without_exact_fixture_is_preserved_only_as_legacy_evidence(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.11.0"
    target_root = project_root / "reference" / "schemas-v0.12.0"
    source = _load(source_root, "audit-bundle.example.json")
    outcome = _load(source_root, "detector-case-outcome.example.json")
    source["detector_case_outcomes"] = [deepcopy(outcome)]
    source_path = tmp_path / "unresolved-v011.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    migrated = migrate_public_bundle(source_path, source_root, target_root, tmp_path / "migration")

    assert migrated["detector_case_outcomes"] == []
    preserved = migrated["extensions"]["x-v0-11-unresolved-detector-case-outcomes"]
    assert preserved == [outcome]
    assert preserved[0]["schema_version"] == "0.11.0"
    report = json.loads(
        (tmp_path / "migration" / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
    )
    assert report["unresolved_case_outcome_count"] == 1


def test_v011_ambiguous_fixture_migrates_to_explicit_excluded_label(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.11.0"
    target_root = project_root / "reference" / "schemas-v0.12.0"
    fixture = _positive_fixture(source_root)
    fixture["fixture_kind"] = "ambiguous_fixture"
    fixture["expected_issue_labels"] = []
    fixture["expected_root_cause_refs"] = []
    fixture["proof_obligations"]["positive_root_cause_documented"] = False
    fixture_path = tmp_path / "ambiguous-v011.json"
    fixture_path.write_text(json.dumps(fixture), encoding="utf-8")

    migrated = migrate_standalone_fixture(
        fixture_path, source_root, target_root, tmp_path / "standalone"
    )

    assert migrated["qualification_proof_status"] == "excluded_label"
    assert migrated["proof_evidence"] is None


def test_v011_standalone_metric_set_is_reported_but_not_migrated(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.11.0"
    metric_set = _load(source_root, "qualification-metric-set.example.json")
    source_path = tmp_path / "metric-v011.json"
    source_path.write_text(json.dumps(metric_set), encoding="utf-8")

    report = report_standalone_metric_set(source_path, source_root, tmp_path / "standalone")

    assert report["authoritative_v0_12_record_emitted"] is False
    assert report["classification"] == "non_authoritative_legacy_evidence"
    preserved = json.loads(
        (tmp_path / "standalone" / "qualification-metric-set.v0.11.0.json").read_text(
            encoding="utf-8"
        )
    )
    assert preserved == metric_set
    assert not (tmp_path / "standalone" / "qualification-metric-set.v0.12.0.json").exists()


def test_v011_migration_rejects_mixed_schema_versions(project_root: Path, tmp_path: Path) -> None:
    source_root = project_root / "reference" / "schemas-v0.11.0"
    target_root = project_root / "reference" / "schemas-v0.12.0"
    source = _metric_bundle(source_root)
    source["detector_case_outcomes"][0]["schema_version"] = "0.10.0"
    source_path = tmp_path / "mixed.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(PublicMigrationError, match="Mixed or unsupported"):
        migrate_public_bundle(source_path, source_root, target_root, tmp_path / "rejected")
