from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.migrate_v0_15_to_v0_16 import migrate_public_bundle


def _load(root: Path, name: str) -> dict[str, object]:
    return json.loads((root / "examples" / name).read_text(encoding="utf-8"))


def test_v015_bundle_migration_is_fail_closed(project_root: Path, tmp_path: Path) -> None:
    source_root = project_root / "reference" / "schemas-v0.15.0"
    target_root = project_root / "reference" / "schemas-v0.16.0"
    source = source_root / "examples" / "audit-bundle.example.json"
    output = tmp_path / "migration"

    migrated = migrate_public_bundle(source, source_root, target_root, output)
    LocalSchemaRegistry(target_root).validate(migrated)
    assert migrated["schema_version"] == "0.16.0"
    assert migrated["static_qualification_profiles"] == []
    assert migrated["static_qualification_proofs"] == []
    assert migrated["qualification_metric_sets"] == []
    assert migrated["storage_manifests"] == []

    report = json.loads((output / "MIGRATION_REPORT.json").read_text(encoding="utf-8"))
    assert report["profile_or_proof_invented"] is False
    assert report["answer_invented"] is False
    assert report["finding_authority_created"] is False
    assert report["execution_launched"] is False


def test_v015_static_evidence_becomes_namespaced_history_not_v016_authority(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.15.0"
    target_root = project_root / "reference" / "schemas-v0.16.0"
    bundle = _load(source_root, "audit-bundle.example.json")
    profile = _load(source_root, "static-qualification-profile.example.json")
    proof = _load(source_root, "static-qualification-proof.example.json")
    fixture = _load(source_root, "benchmark-fixture.static-good.example.json")
    bundle["static_qualification_profiles"] = [profile]
    bundle["static_qualification_proofs"] = [proof]
    bundle["benchmark_fixtures"] = [fixture]
    source_path = tmp_path / "source.bundle.json"
    source_path.write_text(json.dumps(bundle), encoding="utf-8")
    LocalSchemaRegistry(source_root).validate(bundle)

    migrated = migrate_public_bundle(
        source_path,
        source_root,
        target_root,
        tmp_path / "static-migration",
    )
    assert migrated["static_qualification_profiles"] == []
    assert migrated["static_qualification_proofs"] == []
    assert migrated["benchmark_fixtures"] == []
    legacy = migrated["extensions"]["x-v0-15-static-qualification-evidence"]
    assert legacy["static_qualification_profiles"] == [profile]
    assert legacy["static_qualification_proofs"] == [proof]
    assert legacy["benchmark_fixtures"] == [fixture]
    assert all(value["schema_version"] == "0.15.0" for value in legacy["benchmark_fixtures"])
    LocalSchemaRegistry(target_root).validate(migrated)


def test_migration_does_not_modify_v015_source_bundle(project_root: Path, tmp_path: Path) -> None:
    source_root = project_root / "reference" / "schemas-v0.15.0"
    source = _load(source_root, "audit-bundle.example.json")
    before = deepcopy(source)
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    migrate_public_bundle(
        source_path,
        source_root,
        project_root / "reference" / "schemas-v0.16.0",
        tmp_path / "out",
    )
    assert source == before
