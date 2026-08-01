from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from sc_referee.core.errors import RecordValidationError
from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_fixture_proof_schema_release import RELEASE_VERSION, SOURCE_ADRS, build_release


def test_committed_fixture_proof_release_is_accepted_exact_v0120(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.12.0"
    status = json.loads((release / "RELEASE_STATUS.json").read_text(encoding="utf-8"))
    assert status == {
        "accepted": True,
        "baseline_version": "0.11.0",
        "public_release": True,
        "release_version": "0.12.0",
        "source_adrs": SOURCE_ADRS,
    }
    assert RELEASE_VERSION == "0.12.0"
    assert LocalSchemaRegistry(release).validate_example_directory() == 68


def test_fixture_proof_release_manifest_binds_every_file(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.12.0"
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


def test_fixture_proof_release_builder_is_reproducible_and_preserves_v0110(
    project_root: Path, tmp_path: Path
) -> None:
    baseline_manifest = project_root / "reference" / "schemas-v0.11.0" / "MANIFEST.sha256"
    before = baseline_manifest.read_bytes()
    output = tmp_path / "schemas-v0.12.0"
    assert build_release(output) == 68
    committed = project_root / "reference" / "schemas-v0.12.0"
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


def test_complete_fixture_requires_capture_bound_proof(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.12.0"
    registry = LocalSchemaRegistry(release)
    fixture = json.loads(
        (release / "examples" / "benchmark-fixture.example.json").read_text(encoding="utf-8")
    )
    registry.validate(fixture)

    fixture["proof_evidence"]["protocol_artifacts"]["review_captures"] = []
    with pytest.raises(RecordValidationError):
        registry.validate(fixture)


def test_legacy_fixture_and_case_are_fail_closed(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.12.0"
    registry = LocalSchemaRegistry(release)
    fixture = json.loads(
        (release / "examples" / "benchmark-fixture.example.json").read_text(encoding="utf-8")
    )
    fixture["qualification_proof_status"] = "legacy_proof_projection_unavailable"
    fixture["proof_evidence"] = None
    registry.validate(fixture)

    outcome = json.loads(
        (release / "examples" / "detector-case-outcome.example.json").read_text(encoding="utf-8")
    )
    outcome["qualification_proof_status"] = "legacy_proof_projection_unavailable"
    outcome["metric_eligible"] = False
    registry.validate(outcome)
    outcome["metric_eligible"] = True
    with pytest.raises(RecordValidationError):
        registry.validate(outcome)
