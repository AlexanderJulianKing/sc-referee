from __future__ import annotations

import json
from pathlib import Path

from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.migrate_v0_14_to_v0_15 import migrate_public_bundle


def test_v014_bundle_migration_is_fail_closed(project_root: Path, tmp_path: Path) -> None:
    source_root = project_root / "reference" / "schemas-v0.14.0"
    target_root = project_root / "reference" / "schemas-v0.15.0"
    source = source_root / "examples" / "audit-bundle.example.json"
    output = tmp_path / "migration"

    migrated = migrate_public_bundle(source, source_root, target_root, output)
    LocalSchemaRegistry(target_root).validate(migrated)
    assert migrated["schema_version"] == "0.15.0"
    assert migrated["static_qualification_profiles"] == []
    assert migrated["static_qualification_proofs"] == []
    assert migrated["qualification_metric_sets"] == []
    assert migrated["storage_manifests"] == []
    assert all(
        fixture["fixture_kind"] not in {"static_scope_verified_good", "static_scope_hard_negative"}
        for fixture in migrated["benchmark_fixtures"]
    )

    report = json.loads((output / "MIGRATION_REPORT.json").read_text(encoding="utf-8"))
    assert report["static_profile_created"] is False
    assert report["static_proof_created"] is False
    assert report["static_fixture_created"] is False
    assert report["finding_authority_created"] is False
    assert report["execution_launched"] is False
