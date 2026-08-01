from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.migrate_v0_10_to_v0_11 import (
    PublicMigrationError,
    migrate_public_bundle,
    report_standalone_metric_set,
)


def _load(root: Path, name: str) -> dict[str, object]:
    return json.loads((root / "examples" / name).read_text(encoding="utf-8"))


def _metric_bundle(root: Path) -> dict[str, object]:
    bundle = _load(root, "audit-bundle.example.json")
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
    bundle["detector_case_outcomes"] = [deepcopy(outcome)]
    bundle["qualification_metric_sets"] = [deepcopy(metric_set)]
    bundle["detector_qualifications"] = [deepcopy(qualification)]
    return bundle


def test_v010_bundle_migration_preserves_incomplete_evidence_fail_closed(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.10.0"
    target_root = project_root / "reference" / "schemas-v0.11.0"
    source = _metric_bundle(source_root)
    source_path = tmp_path / "source-v010.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    migrated = migrate_public_bundle(source_path, source_root, target_root, tmp_path / "migration")

    LocalSchemaRegistry(target_root).validate(migrated)
    assert migrated["schema_version"] == "0.11.0"
    assert migrated["qualification_metric_sets"] == []
    assert migrated["storage_manifests"] == []

    outcome = migrated["detector_case_outcomes"][0]
    assert outcome["metric_input_status"] == "legacy_source_projection_unavailable"
    assert outcome["detector_result_outcomes"] == []
    assert outcome["metric_eligible"] is False
    assert outcome["promotion_evidence_eligible"] is False
    assert outcome["extensions"]["x-v0-10-metric-eligible"] is True
    assert outcome["extensions"]["x-v0-10-promotion-evidence-eligible"] is False

    preserved = migrated["extensions"]["x-v0-10-unverified-qualification-metric-sets"]
    assert preserved == source["qualification_metric_sets"]
    assert preserved[0]["schema_version"] == "0.10.0"
    qualification = migrated["detector_qualifications"][0]
    assert qualification["quantitative_metrics"] is None
    assert qualification["extensions"]["x-v0-10-unverified-quantitative-metrics"]

    report = json.loads(
        (tmp_path / "migration" / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
    )
    assert report["detector_result_states_invented"] is False
    assert report["opportunity_projections_invented"] is False
    assert report["qualification_metrics_invented"] is False
    assert report["legacy_metric_sets_authoritative"] is False


def test_v010_standalone_metric_set_is_reported_but_not_migrated(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.10.0"
    metric_set = _load(source_root, "qualification-metric-set.example.json")
    source_path = tmp_path / "metric-v010.json"
    source_path.write_text(json.dumps(metric_set), encoding="utf-8")

    report = report_standalone_metric_set(source_path, source_root, tmp_path / "standalone")

    assert report["authoritative_v0_11_record_emitted"] is False
    assert report["classification"] == "non_authoritative_legacy_evidence"
    preserved = json.loads(
        (tmp_path / "standalone" / "qualification-metric-set.v0.10.0.json").read_text(
            encoding="utf-8"
        )
    )
    assert preserved == metric_set
    assert not (tmp_path / "standalone" / "qualification-metric-set.v0.11.0.json").exists()


def test_v010_migration_rejects_mixed_schema_versions(project_root: Path, tmp_path: Path) -> None:
    source_root = project_root / "reference" / "schemas-v0.10.0"
    target_root = project_root / "reference" / "schemas-v0.11.0"
    source = _metric_bundle(source_root)
    source["detector_case_outcomes"][0]["schema_version"] = "0.9.0"
    source_path = tmp_path / "mixed.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(PublicMigrationError, match="Mixed or unsupported"):
        migrate_public_bundle(source_path, source_root, target_root, tmp_path / "rejected")
