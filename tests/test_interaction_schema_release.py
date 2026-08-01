from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_interaction_schema_release import RELEASE_VERSION, build_release
from scripts.migrate_v0_6_to_v0_7 import PublicMigrationError, migrate_public_bundle


def test_committed_interaction_release_is_accepted_exact_v070(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.7.0"
    status = json.loads((release / "RELEASE_STATUS.json").read_text(encoding="utf-8"))
    assert status == {
        "accepted": True,
        "baseline_version": "0.6.0",
        "public_release": True,
        "release_version": "0.7.0",
        "source_adr": "docs/implementation/ADR-0004-TYPED-SEMANTIC-INTERACTION-PLANE.md",
    }
    assert RELEASE_VERSION == "0.7.0"
    assert LocalSchemaRegistry(release).validate_example_directory() == 54


def test_interaction_release_manifest_binds_every_file(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.7.0"
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


def test_interaction_release_builder_is_reproducible_and_preserves_v060(
    project_root: Path, tmp_path: Path
) -> None:
    baseline_manifest = project_root / "reference" / "schemas-v0.6.0" / "MANIFEST.sha256"
    before = baseline_manifest.read_bytes()
    output = tmp_path / "schemas-v0.7.0"
    assert build_release(output) == 54
    committed = project_root / "reference" / "schemas-v0.7.0"
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


def test_public_v060_bundle_migrates_without_inventing_interaction_history(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.6.0"
    target_root = project_root / "reference" / "schemas-v0.7.0"
    source = source_root / "examples" / "audit-bundle.example.json"

    bundle = migrate_public_bundle(source, source_root, target_root, tmp_path / "migration")

    LocalSchemaRegistry(target_root).validate(bundle)
    assert bundle["schema_version"] == "0.7.0"
    assert bundle["work_items"] == []
    assert bundle["answers"] == []
    assert bundle["storage_manifests"] == []
    report = json.loads(
        (tmp_path / "migration" / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
    )
    assert report["interaction_history_invented"] is False
    assert report["storage_manifest_carried_forward"] is False


def test_public_v060_migration_rejects_mixed_schema_versions(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.6.0"
    target_root = project_root / "reference" / "schemas-v0.7.0"
    source = json.loads(
        (source_root / "examples" / "audit-bundle.example.json").read_text(encoding="utf-8")
    )
    source["claims"][0]["schema_version"] = "0.5.0"
    source_path = tmp_path / "mixed.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(PublicMigrationError, match="Mixed or unsupported"):
        migrate_public_bundle(source_path, source_root, target_root, tmp_path / "rejected")
