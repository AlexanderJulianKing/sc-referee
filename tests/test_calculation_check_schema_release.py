from __future__ import annotations

import json
from pathlib import Path

import pytest

from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_calculation_check_schema_release import build_release
from scripts.migrate_v0_17_to_v0_18 import migrate_public_bundle


def test_v018_release_is_byte_reproducible(project_root: Path, tmp_path: Path) -> None:
    output = tmp_path / "schemas-v0.18.0"
    build_release(output)
    committed = project_root / "reference" / "schemas-v0.18.0"
    generated = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and ".pytest_cache" not in path.parts
    }
    expected = {
        path.relative_to(committed).as_posix(): path.read_bytes()
        for path in committed.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and ".pytest_cache" not in path.parts
    }
    assert generated == expected
    with pytest.raises(ValueError):
        build_release(output)


def test_v018_example_and_bundle_validate(project_root: Path) -> None:
    root = project_root / "reference" / "schemas-v0.18.0"
    registry = LocalSchemaRegistry(root)
    observation = json.loads(
        (root / "examples" / "deterministic-check-observation.example.json").read_text(
            encoding="utf-8"
        )
    )
    bundle = json.loads(
        (root / "examples" / "audit-bundle.example.json").read_text(encoding="utf-8")
    )
    registry.validate(observation)
    registry.validate(bundle)
    assert bundle["deterministic_check_observations"] == []


def test_v017_migration_does_not_invent_calculation_evidence(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.17.0"
    target_root = project_root / "reference" / "schemas-v0.18.0"
    migrated = migrate_public_bundle(
        source_root / "examples" / "audit-bundle.example.json",
        source_root,
        target_root,
        tmp_path / "out",
    )
    assert migrated["schema_version"] == "0.18.0"
    assert migrated["deterministic_check_observations"] == []
    report = json.loads((tmp_path / "out" / "MIGRATION_REPORT.json").read_text())
    assert report["calculation_observation_invented"] is False
    assert report["finding_authority_created"] is False
    assert report["execution_launched"] is False
