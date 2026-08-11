from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from sc_referee.core.errors import RecordValidationError
from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_method_promotion_schema_candidate import (
    CANDIDATE_VERSION,
    METHOD_V2,
    SOURCE_ADR,
    build_candidate,
)
from scripts.migrate_v0_18_to_v0_19 import migrate_public_bundle


def _load(root: Path, name: str) -> dict[str, Any]:
    return json.loads((root / "examples" / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def candidate(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("method-promotion-schema") / "v0.19.0"
    assert build_candidate(output) == 79
    return output


def test_candidate_is_explicitly_nonpublic_and_schema_complete(candidate: Path) -> None:
    status = json.loads((candidate / "PROPOSAL_STATUS.json").read_text(encoding="utf-8"))
    assert status == {
        "accepted": False,
        "baseline_version": "0.18.0",
        "candidate_version": CANDIDATE_VERSION,
        "public_release": False,
        "source_adr": SOURCE_ADR,
        "warning": (
            "Representation candidate only. Pilot-informed thresholds, independent held-out "
            "qualification, maintainer promotion, and an accepted public schema are absent."
        ),
    }
    for path in sorted((candidate / "schemas" / "v0.19.0").glob("*.json")):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
    assert LocalSchemaRegistry(candidate).validate_example_directory() == 79


def test_v03_static_profile_is_distinct_and_binding_complete(candidate: Path) -> None:
    registry = LocalSchemaRegistry(candidate)
    profile = _load(candidate, "static-qualification-profile.analysis-method.example.json")
    assert profile["profile_kind"] == METHOD_V2
    assert profile["target_detector"]["detector_version"] == "0.3.0"
    assert profile["method_binding"]["detector_version"] == "0.3.0"
    assert str(profile["method_binding"]["production_binding_digest"]).startswith("sha256:")
    registry.validate(profile)

    crossed = copy.deepcopy(profile)
    crossed["method_binding"]["detector_version"] = "0.2.0"
    with pytest.raises(RecordValidationError):
        registry.validate(crossed)

    crossed = copy.deepcopy(profile)
    crossed["profile_kind"] = "typed_static_method_conflict_v1"
    with pytest.raises(RecordValidationError):
        registry.validate(crossed)


def test_deferred_records_cannot_be_relabelled_as_promoted(candidate: Path) -> None:
    registry = LocalSchemaRegistry(candidate)
    metric_set = _load(candidate, "qualification-metric-set.example.json")
    qualification = _load(candidate, "detector-qualification.example.json")
    assert metric_set["binding_scope"] is None
    assert qualification["binding_scope"] is None
    registry.validate(metric_set)
    registry.validate(qualification)

    metric_set["promotion_permitted"] = True
    with pytest.raises(RecordValidationError):
        registry.validate(metric_set)

    qualification["outcome"] = "promoted"
    qualification["effective_maturity"] = "validated"
    with pytest.raises(RecordValidationError):
        registry.validate(qualification)


def test_v018_migration_to_candidate_is_fail_closed(
    project_root: Path, candidate: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.18.0"
    migrated = migrate_public_bundle(
        source_root / "examples" / "audit-bundle.example.json",
        source_root,
        candidate,
        tmp_path / "migration",
    )
    assert migrated["schema_version"] == "0.19.0"
    assert migrated["storage_manifests"] == []
    source = _load(source_root, "audit-bundle.example.json")
    assert len(migrated["findings"]) == len(source["findings"])
    assert migrated["detector_qualifications"] == []
    report = json.loads((tmp_path / "migration" / "MIGRATION_REPORT.json").read_text())
    assert report["binding_scope_invented"] is False
    assert report["numeric_threshold_invented"] is False
    assert report["qualification_invented"] is False
    assert report["finding_authority_created"] is False


def test_candidate_builder_preserves_immutable_v018(project_root: Path, tmp_path: Path) -> None:
    baseline = project_root / "reference" / "schemas-v0.18.0" / "MANIFEST.sha256"
    before = baseline.read_bytes()
    output = tmp_path / "candidate"
    build_candidate(output)
    assert baseline.read_bytes() == before
    with pytest.raises(ValueError, match="absent or empty"):
        build_candidate(output)
