from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_stage3_schema_release import RELEASE_VERSION, build_release
from scripts.migrate_v0_9_to_v0_10 import PublicMigrationError, migrate_public_bundle


def _load(root: Path, name: str) -> dict[str, object]:
    return json.loads((root / "examples" / name).read_text(encoding="utf-8"))


def _v090_stage3_legacy_bundle(root: Path) -> dict[str, object]:
    bundle = _load(root, "audit-bundle.example.json")

    fixture = _load(root, "benchmark-fixture.example.json")
    adjudication = _load(root, "benchmark-adjudication.example.json")
    adjudication["stage3_detector_comparison_refs"] = [
        {
            "record_type": "detector_evaluation",
            "record_id": "evaluation-private:legacy-stage3",
        }
    ]
    qualification = _load(root, "detector-qualification.example.json")
    qualification["quantitative_metrics"] = {
        "recall": 0.9,
        "precision": 0.8,
        "confidence_interval": "legacy free-form payload",
    }

    bundle["benchmark_fixtures"] = [deepcopy(fixture)]
    bundle["benchmark_adjudications"] = [deepcopy(adjudication)]
    bundle["detector_qualifications"] = [deepcopy(qualification)]
    return bundle


def test_committed_stage3_release_is_accepted_exact_v0100(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.10.0"
    status = json.loads((release / "RELEASE_STATUS.json").read_text(encoding="utf-8"))
    assert status == {
        "accepted": True,
        "baseline_version": "0.9.0",
        "public_release": True,
        "release_version": "0.10.0",
        "source_adr": ("docs/implementation/ADR-0009-STAGE3-ROOT-CAUSE-EQUIVALENCE-AND-METRICS.md"),
    }
    assert RELEASE_VERSION == "0.10.0"
    assert LocalSchemaRegistry(release).validate_example_directory() == 67


def test_stage3_release_manifest_binds_every_file(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.10.0"
    manifest = {}
    for line in (release / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", maxsplit=1)
        manifest[relative] = digest
    actual = {
        path.relative_to(release).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in release.rglob("*")
        if path.is_file()
        and path.name != "MANIFEST.sha256"
        and not any(part.startswith(".") or part == "__pycache__" for part in path.parts)
    }
    assert manifest == actual


def test_stage3_release_builder_is_reproducible_and_preserves_v090(
    project_root: Path, tmp_path: Path
) -> None:
    baseline_manifest = project_root / "reference" / "schemas-v0.9.0" / "MANIFEST.sha256"
    before = baseline_manifest.read_bytes()
    output = tmp_path / "schemas-v0.10.0"
    assert build_release(output) == 67
    committed = project_root / "reference" / "schemas-v0.10.0"
    generated_files = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    committed_files = {
        path.relative_to(committed).as_posix(): path.read_bytes()
        for path in committed.rglob("*")
        if path.is_file()
        and not any(part.startswith(".") or part == "__pycache__" for part in path.parts)
    }
    assert generated_files == committed_files
    assert baseline_manifest.read_bytes() == before


def test_public_v090_migration_is_fail_closed_for_stage3_evidence(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.9.0"
    target_root = project_root / "reference" / "schemas-v0.10.0"
    source = _v090_stage3_legacy_bundle(source_root)
    source_path = tmp_path / "source-v090.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    bundle = migrate_public_bundle(source_path, source_root, target_root, tmp_path / "migration")

    LocalSchemaRegistry(target_root).validate(bundle)
    assert bundle["schema_version"] == "0.10.0"
    assert bundle["detector_evaluation_candidates"] == []
    assert bundle["stage3_comparison_reviews"] == []
    assert bundle["detector_case_outcomes"] == []
    assert bundle["qualification_metric_sets"] == []
    assert bundle["benchmark_fixtures"][0]["corpus_partition"] == "public_development"

    adjudication = bundle["benchmark_adjudications"][0]
    assert adjudication["stage3_detector_comparison_refs"] == []
    assert adjudication["extensions"]["x-v0-9-stage3-detector-comparison-refs"] == [
        {
            "record_type": "detector_evaluation",
            "record_id": "evaluation-private:legacy-stage3",
        }
    ]

    qualification = bundle["detector_qualifications"][0]
    assert qualification["outcome"] == "deferred"
    assert qualification["effective_maturity"] == "experimental"
    assert qualification["quantitative_metrics"] is None
    assert qualification["extensions"]["x-v0-9-outcome"] == "promoted"
    assert qualification["extensions"]["x-v0-9-effective-maturity"] == "validated"
    assert qualification["extensions"]["x-v0-9-quantitative-metrics"]["recall"] == 0.9

    report = json.loads(
        (tmp_path / "migration" / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
    )
    assert report["evaluation_candidates_invented"] is False
    assert report["detector_root_equivalence_invented"] is False
    assert report["case_outcomes_invented"] is False
    assert report["qualification_metrics_invented"] is False
    assert report["legacy_promotions_retained"] is False
    assert report["held_out_status_invented"] is False


def test_public_v090_migration_rejects_mixed_schema_versions(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.9.0"
    target_root = project_root / "reference" / "schemas-v0.10.0"
    source = _load(source_root, "audit-bundle.example.json")
    claims = source["claims"]
    assert isinstance(claims, list)
    claims[0]["schema_version"] = "0.8.0"
    source_path = tmp_path / "mixed.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(PublicMigrationError, match="Mixed or unsupported"):
        migrate_public_bundle(source_path, source_root, target_root, tmp_path / "rejected")
