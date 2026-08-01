from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.migrate_v0_16_to_v0_17 import migrate_public_bundle


def _load(root: Path, name: str) -> dict[str, object]:
    return json.loads((root / "examples" / name).read_text(encoding="utf-8"))


def test_v016_bundle_migration_is_fail_closed(project_root: Path, tmp_path: Path) -> None:
    source_root = project_root / "reference" / "schemas-v0.16.0"
    target_root = project_root / "reference" / "schemas-v0.17.0"
    source = source_root / "examples" / "audit-bundle.example.json"
    output = tmp_path / "migration"

    migrated = migrate_public_bundle(source, source_root, target_root, output)
    LocalSchemaRegistry(target_root).validate(migrated)
    assert migrated["schema_version"] == "0.17.0"
    assert migrated["static_qualification_profiles"] == []
    assert migrated["static_qualification_proofs"] == []
    assert migrated["qualification_metric_sets"] == []
    assert migrated["storage_manifests"] == []

    report = json.loads((output / "MIGRATION_REPORT.json").read_text(encoding="utf-8"))
    assert report["profile_or_proof_invented"] is False
    assert report["binding_invented"] is False
    assert report["qualification_adapter_invented"] is False
    assert report["finding_authority_created"] is False
    assert report["execution_launched"] is False


def test_v016_static_evidence_becomes_namespaced_history_not_v017_authority(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.16.0"
    target_root = project_root / "reference" / "schemas-v0.17.0"
    bundle = _load(source_root, "audit-bundle.example.json")
    profile = _load(source_root, "static-qualification-profile.analysis-method.example.json")
    proof = _load(source_root, "static-qualification-proof.analysis-method.example.json")
    fixture = _load(source_root, "benchmark-fixture.static-method-good.example.json")
    bundle["static_qualification_profiles"] = [profile]
    bundle["static_qualification_proofs"] = [proof]
    bundle["benchmark_fixtures"] = [fixture]
    source_path = tmp_path / "source.bundle.json"
    source_path.write_text(json.dumps(bundle), encoding="utf-8")
    LocalSchemaRegistry(source_root).validate(bundle)

    migrated = migrate_public_bundle(source_path, source_root, target_root, tmp_path / "out")
    assert migrated["static_qualification_profiles"] == []
    assert migrated["static_qualification_proofs"] == []
    legacy = migrated["extensions"]["x-v0-16-static-qualification-evidence"]
    assert legacy["static_qualification_profiles"] == [profile]
    assert legacy["static_qualification_proofs"] == [proof]
    assert all(value["schema_version"] == "0.16.0" for value in legacy["benchmark_fixtures"])
    LocalSchemaRegistry(target_root).validate(migrated)


def test_v017_migration_does_not_modify_v016_source(project_root: Path, tmp_path: Path) -> None:
    source_root = project_root / "reference" / "schemas-v0.16.0"
    source = _load(source_root, "audit-bundle.example.json")
    before = deepcopy(source)
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    migrate_public_bundle(
        source_path,
        source_root,
        project_root / "reference" / "schemas-v0.17.0",
        tmp_path / "out",
    )
    assert source == before
