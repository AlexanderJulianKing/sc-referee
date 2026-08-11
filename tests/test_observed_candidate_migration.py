from __future__ import annotations

import json
from pathlib import Path

import pytest

from sc_referee.controller import replay, run_demo
from sc_referee.core.ids import semantic_digest
from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.migrate_observed_schema_candidate import (
    CandidateMigrationError,
    _artifact_edge,
    _check_legacy_identity,
)
from scripts.migrate_v0_5_to_v0_6 import PublicMigrationError, migrate_public_bundle

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_V05 = ROOT / "reference" / "schemas-v0.5.0"
PUBLIC_V06 = ROOT / "reference" / "schemas-v0.6.0"
PUBLIC_ACTIVE = ROOT / "reference" / "schemas-v0.19.0"


@pytest.fixture(scope="module")
def public_audit(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, dict[str, object]]:
    output = tmp_path_factory.mktemp("public-observed-runtime") / "audit"
    bundle = run_demo(ROOT / "examples" / "walking-skeleton", output, PUBLIC_ACTIVE)
    return output, bundle


def test_generated_walking_skeleton_is_a_valid_active_public_bundle(
    public_audit: tuple[Path, dict[str, object]],
) -> None:
    output, bundle = public_audit
    LocalSchemaRegistry(PUBLIC_ACTIVE).validate(bundle)
    assert len(bundle["audit_runs"]) == 8
    assert len(bundle["stage_results"]) == 7
    assert len(bundle["file_records"]) == 10
    assert len(bundle["operations"]) == 17
    assert len(bundle["artifacts"]) == 4
    assert len(bundle["observed_results"]) == 1
    assert not (output / "observed" / "PROPOSAL_STATUS.json").exists()


def test_active_public_graph_has_resolvable_typed_edges(
    public_audit: tuple[Path, dict[str, object]],
) -> None:
    _, bundle = public_audit
    identities = {record["asset_identity_id"] for record in bundle["asset_identities"]}
    artifacts = {record["artifact_id"] for record in bundle["artifacts"]}
    operations = {record["operation_id"] for record in bundle["operations"]}
    parser_results = {record["parser_result_id"] for record in bundle["parser_results"]}
    snapshots = {record["snapshot_id"] for record in bundle["repository_snapshots"]}

    for run in bundle["audit_runs"]:
        if run["state"] == "created":
            assert "snapshot_ref" not in run
        else:
            assert run["snapshot_ref"]["record_id"] in snapshots
    for file_record in bundle["file_records"]:
        assert file_record["asset_identity_ref"]["record_id"] in identities
        assert file_record["snapshot_ref"]["record_id"] in snapshots
    for operation in bundle["operations"]:
        assert operation["parser_result_ref"]["record_id"] in parser_results
        assert all(ref["record_id"] in artifacts for ref in operation["input_refs"])
        assert all(ref["record_id"] in artifacts for ref in operation["output_refs"])
    for artifact in bundle["artifacts"]:
        assert artifact["asset_identity_ref"]["record_id"] in identities
        assert all(
            ref["record_id"] in operations
            for ref in [
                *artifact["producer_operation_refs"],
                *artifact["consumer_operation_refs"],
            ]
        )


def test_public_scalar_retains_unknown_semantic_slots(
    public_audit: tuple[Path, dict[str, object]],
) -> None:
    _, bundle = public_audit
    observed = bundle["observed_results"][0]
    assert observed["scalar_value"] == pytest.approx(-0.42)
    assert observed["observation_method"] == "deterministic_verification"
    assert observed["lineage_status"] == "complete"
    assert observed["comparison"]["state"] == "known"
    assert observed["orientation"]["state"] == "known"
    assert observed["scale"]["state"] == "known"
    assert observed["unit"]["state"] == "unknown"
    assert observed["population"]["state"] == "unknown"
    assert observed["timing"]["state"] == "unknown"


def test_replay_preserves_public_unknown_orientation_without_finding(
    public_audit: tuple[Path, dict[str, object]], tmp_path: Path
) -> None:
    output, _ = public_audit
    lock = json.loads((output / "semantic.lock.json").read_text(encoding="utf-8"))
    unknown = {
        "state": "unknown",
        "rationale": "The comparison orientation was deliberately withheld for this replay.",
        "evidence_refs": [],
    }
    lock["observed_result"]["orientation"] = unknown
    lock["observed_graph"]["observed_result"]["orientation"] = unknown
    lock["semantic_lock_digest"] = semantic_digest(
        {key: value for key, value in lock.items() if key != "semantic_lock_digest"}
    )
    lock_path = tmp_path / "unknown.lock.json"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")

    replayed = replay(lock_path, tmp_path / "replay", PUBLIC_ACTIVE)

    assert replayed["observed_results"][0]["orientation"]["state"] == "unknown"
    assert replayed["findings"] == []
    assert replayed["material_questions"]


def test_public_v05_bundle_migrates_without_inventing_observed_records(tmp_path: Path) -> None:
    source = PUBLIC_V05 / "examples" / "audit-bundle.example.json"
    bundle = migrate_public_bundle(source, PUBLIC_V05, PUBLIC_V06, tmp_path / "migration")
    LocalSchemaRegistry(PUBLIC_V06).validate(bundle)
    assert bundle["schema_version"] == "0.6.0"
    assert all(
        bundle[field] == []
        for field in (
            "audit_runs",
            "stage_results",
            "file_records",
            "operations",
            "artifacts",
            "observed_results",
        )
    )
    report = json.loads(
        (tmp_path / "migration" / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
    )
    assert report["observed_plane_evidence_invented"] is False
    assert report["storage_manifest_carried_forward"] is False


def test_public_migration_rejects_mixed_schema_versions(tmp_path: Path) -> None:
    source = json.loads(
        (PUBLIC_V05 / "examples" / "audit-bundle.example.json").read_text(encoding="utf-8")
    )
    source["claims"][0]["schema_version"] = "0.4.0"
    source_path = tmp_path / "mixed.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(PublicMigrationError):
        migrate_public_bundle(source_path, PUBLIC_V05, PUBLIC_V06, tmp_path / "rejected")


def test_legacy_provisional_conversion_still_rejects_ambiguous_evidence() -> None:
    with pytest.raises(CandidateMigrationError, match="no exact Artifact target"):
        _artifact_edge("artifact:missing", {"artifact:known"})

    file_record = {
        "file_id": "file:test",
        "identity_strength": "strong",
        "digest": "sha256:" + "a" * 64,
    }
    identity = {
        "tier": "full_digest",
        "identity_evidence": {"kind": "full_digest", "digest": "sha256:" + "b" * 64},
    }
    with pytest.raises(CandidateMigrationError, match="digest conflicts"):
        _check_legacy_identity(file_record, identity)
