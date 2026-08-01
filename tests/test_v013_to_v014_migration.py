from __future__ import annotations

import json
from pathlib import Path

import pytest

from sc_referee.core.ids import semantic_digest
from scripts.migrate_v0_13_to_v0_14 import PublicMigrationError, migrate_public_bundle


def _load(root: Path, name: str) -> dict[str, object]:
    return json.loads((root / "examples" / name).read_text(encoding="utf-8"))


def test_v013_migration_marks_old_work_and_authorization_semantics_fail_closed(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.13.0"
    target_root = project_root / "reference" / "schemas-v0.14.0"
    source = _load(source_root, "audit-bundle.example.json")
    old_work_item = _load(source_root, "work-item.ready.example.json")
    old_authorization = _load(source_root, "project-execution-authorization.example.json")
    old_execution = _load(source_root, "execution.project-workflow.example.json")
    source["work_items"] = [old_work_item]
    source["project_execution_authorizations"] = [old_authorization]
    source["executions"] = [old_execution]
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    migrated = migrate_public_bundle(source_path, source_root, target_root, tmp_path / "migration")

    item = migrated["work_items"][0]
    assert item["packet"]["packet_kind"] == "semantic_or_auditor_work_v1"
    packet_without_digest = dict(item["packet"])
    packet_without_digest.pop("packet_digest")
    assert item["packet"]["packet_digest"] == semantic_digest(packet_without_digest)
    assert all(candidate["kind"] != "project_execution" for candidate in migrated["work_items"])

    authorization = migrated["project_execution_authorizations"][0]
    assert authorization["scope"]["work_item_binding_status"] == (
        "legacy_work_item_semantics_unavailable"
    )
    assert authorization["scope"]["work_item_semantic_digest"] is None
    assert authorization["scope"]["purpose"] is None
    assert authorization["scope"]["target_refs"] is None
    assert migrated["executions"][0]["authorization_evidence_status"] == (
        "legacy_authorization_projection_unavailable"
    )
    assert migrated["executions"][0]["project_execution"] is None

    report = json.loads(
        (tmp_path / "migration" / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
    )
    assert report["execution_work_item_invented"] is False
    assert report["work_item_digest_invented"] is False
    assert report["controller_registry_entry_created"] is False
    assert report["execution_launched"] is False


def test_v013_migration_rejects_mixed_versions(project_root: Path, tmp_path: Path) -> None:
    source_root = project_root / "reference" / "schemas-v0.13.0"
    source = _load(source_root, "audit-bundle.example.json")
    source["claims"][0]["schema_version"] = "0.12.0"  # type: ignore[index]
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(PublicMigrationError, match="Mixed or unsupported"):
        migrate_public_bundle(
            source_path,
            source_root,
            project_root / "reference" / "schemas-v0.14.0",
            tmp_path / "migration",
        )
