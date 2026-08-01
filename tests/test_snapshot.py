import os
import shutil
from pathlib import Path

import pytest

from sc_referee.controller import run_demo
from sc_referee.core.ids import sha256_digest
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.snapshot.identity import (
    build_asset_identity,
    full_digest_evidence,
    immutable_external_evidence,
    manifest_evidence,
    unidentified_evidence,
    weak_fingerprint_evidence,
)
from sc_referee.snapshot.repository import (
    AssetIdentityPolicy,
    capture_repository,
    detect_workspace_divergence,
)


def test_snapshot_digest_stable(project_root, tmp_path) -> None:
    fixture = project_root / "examples" / "walking-skeleton"
    first = capture_repository(
        fixture, tmp_path / "one", "run:test", captured_at="2026-07-27T20:00:00Z"
    )
    second = capture_repository(
        fixture, tmp_path / "two", "run:test", captured_at="2026-07-27T20:00:00Z"
    )
    assert first.snapshot_record["snapshot_digest"] == second.snapshot_record["snapshot_digest"]


def test_snapshot_prioritizes_explicitly_selected_surface_within_full_digest_budget(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "analysis.r").write_bytes(b"a" * 12)
    selected = source / "selected.Rmd"
    selected.write_text("```{r}\nstrength_mvmr(r_input = x, gencov = 0)\n```\n", encoding="utf-8")

    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-07-29T20:00:00Z",
        identity_policy=AssetIdentityPolicy(
            full_digest_byte_budget=selected.stat().st_size,
            sampled_fingerprint_byte_budget=0,
        ),
        preferred_full_digest_paths=("selected.Rmd",),
    )

    records = {item["path"]: item for item in snapshot.file_records}
    assert records["selected.Rmd"]["digest"] == sha256_digest(selected.read_bytes())
    assert records["analysis.r"]["digest"] is None
    assert (snapshot.materialized_root / "selected.Rmd").is_file()
    assert not (snapshot.materialized_root / "analysis.r").exists()
    assert snapshot.snapshot_record["extensions"]["x-preferred-full-digest-paths"] == [
        "selected.Rmd"
    ]


def test_snapshot_uses_separate_finite_budget_for_explicit_material_inputs(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    material = source / "selected.h5ad"
    material.write_bytes(b"material-input")
    unselected = source / "unselected.h5ad"
    unselected.write_bytes(b"unselected-input")

    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-08-01T00:00:00Z",
        identity_policy=AssetIdentityPolicy(
            full_digest_byte_budget=0,
            sampled_fingerprint_byte_budget=64,
            material_full_digest_byte_budget=len(material.read_bytes()),
        ),
        material_full_digest_paths=("selected.h5ad",),
    )

    records = {item["path"]: item for item in snapshot.file_records}
    assert records["selected.h5ad"]["digest"] == sha256_digest(material.read_bytes())
    assert records["unselected.h5ad"]["digest"] is None
    assert (snapshot.materialized_root / "selected.h5ad").read_bytes() == material.read_bytes()
    assert not (snapshot.materialized_root / "unselected.h5ad").exists()
    extensions = snapshot.snapshot_record["extensions"]
    assert extensions["x-material-full-digest-paths"] == ["selected.h5ad"]
    assert extensions["x-material-full-digest-byte-reads"] == len(material.read_bytes())
    assert extensions["x-material-input-identities"] == [
        {"path": "selected.h5ad", "tier": "full_digest"}
    ]


def test_snapshot_material_input_over_budget_remains_weak_and_missing_path_fails(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "selected.h5ad").write_bytes(b"too-large-for-material-budget")

    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-08-01T00:00:00Z",
        identity_policy=AssetIdentityPolicy(
            full_digest_byte_budget=0,
            sampled_fingerprint_byte_budget=12,
            material_full_digest_byte_budget=4,
        ),
        material_full_digest_paths=("selected.h5ad",),
    )
    selected = snapshot.snapshot_record["extensions"]["x-material-input-identities"]
    assert selected == [{"path": "selected.h5ad", "tier": "weak_fingerprint"}]
    assert not (snapshot.materialized_root / "selected.h5ad").exists()

    with pytest.raises(ValueError, match="material input paths must identify regular files"):
        capture_repository(
            source,
            tmp_path / "missing-snapshot",
            "run:test",
            material_full_digest_paths=("missing.h5ad",),
        )


def test_snapshot_does_not_follow_external_symlink(project_root: Path, tmp_path: Path) -> None:
    fixture = tmp_path / "fixture"
    shutil.copytree(project_root / "examples" / "walking-skeleton", fixture)
    outside = tmp_path / "outside-secret.txt"
    outside.write_text("do not copy", encoding="utf-8")
    (fixture / "external-link.txt").symlink_to(outside)
    result = capture_repository(
        fixture, tmp_path / "snapshot", "run:test", captured_at="2026-07-27T20:00:00Z"
    )
    assert not (result.materialized_root / "external-link.txt").exists()
    symlink_record = next(
        item for item in result.file_records if item["path"] == "external-link.txt"
    )
    assert symlink_record["role"] == "symlink_not_followed"
    assert symlink_record["digest"] is None
    symlink_identity = next(
        item
        for item in result.asset_identity_records
        if item["asset_ref"]["record_id"] == symlink_record["file_id"]
    )
    assert symlink_identity["tier"] == "weak_fingerprint"


def test_workspace_divergence_detects_added_modified_and_deleted_paths(
    project_root: Path, tmp_path: Path
) -> None:
    fixture = tmp_path / "fixture"
    shutil.copytree(project_root / "examples" / "walking-skeleton", fixture)
    snapshot = capture_repository(
        fixture, tmp_path / "snapshot", "run:test", captured_at="2026-07-27T20:00:00Z"
    )
    (fixture / "report.md").write_text("changed\n", encoding="utf-8")
    (fixture / "analysis.py").unlink()
    (fixture / "added.txt").write_text("new\n", encoding="utf-8")
    state = detect_workspace_divergence(
        fixture,
        snapshot.file_records,
        detected_at="2026-07-27T20:01:00Z",
    )
    assert state == {
        "status": "workspace_diverged",
        "mix_live_content_into_run": False,
        "detected_at": "2026-07-27T20:01:00Z",
        "changed_paths": ["added.txt", "analysis.py", "report.md"],
    }


def test_live_edit_never_enters_current_run(project_root, schema_root, tmp_path) -> None:
    fixture = tmp_path / "fixture"
    shutil.copytree(project_root / "examples" / "walking-skeleton", fixture)
    original_report = (fixture / "report.md").read_text(encoding="utf-8")

    def edit_live_workspace(repository: Path) -> None:
        (repository / "report.md").write_text(
            "# Changed live report\n\nTreatment decreased expression relative to control.\n",
            encoding="utf-8",
        )

    output = tmp_path / "audit"
    bundle = run_demo(
        fixture,
        output,
        schema_root,
        after_snapshot=edit_live_workspace,
    )
    state = bundle["repository_snapshots"][0]["live_workspace_state"]
    assert state["status"] == "workspace_diverged"
    assert state["changed_paths"] == ["report.md"]
    assert state["mix_live_content_into_run"] is False
    assert len(bundle["findings"]) == 1
    assert (output / "observed" / "snapshot" / "materialized" / "report.md").read_text(
        encoding="utf-8"
    ) == original_report
    assert (fixture / "report.md").read_text(encoding="utf-8") != original_report
    assert "continued only against the immutable snapshot" in (output / "report.html").read_text(
        encoding="utf-8"
    )


def test_tiered_identity_factories_produce_public_records(schema_root: Path) -> None:
    digest = sha256_digest(b"content")
    manifest_ref = {
        "source_kind": "file_span",
        "locator": "checksums.sha256:1",
        "path": "checksums.sha256",
        "start_line": 1,
        "end_line": 1,
    }
    evidences = [
        full_digest_evidence(digest),
        immutable_external_evidence("doi:10.0000/example", "version-2", digest=digest),
        manifest_evidence(manifest_ref, digest),
        weak_fingerprint_evidence(
            "data/large.bin",
            100,
            digest,
            limitations=("Only bounded samples were read.",),
            profile="test-profile",
        ),
        unidentified_evidence(
            "The remote location was unavailable.",
            reported_location="remote://dataset",
        ),
    ]
    validator = LocalSchemaRegistry(schema_root)
    for index, evidence in enumerate(evidences):
        record = build_asset_identity(
            audit_run_id="run:test",
            asset_record_type="file_record",
            asset_record_id=f"file:{index}",
            evidence=evidence,
            created_at="2026-07-27T20:00:00Z",
        )
        validator.validate(record)
    assert [evidence.tier for evidence in evidences] == [
        "full_digest",
        "immutable_external",
        "manifest",
        "weak_fingerprint",
        "unidentified",
    ]


def test_byte_read_policy_uses_weak_identity_without_full_large_read(
    schema_root: Path, tmp_path: Path
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    analysis_payload = b"print('safe')\n"
    (source / "analysis.py").write_bytes(analysis_payload)
    (source / "large.bin").write_bytes(b"A" * 200)
    policy = AssetIdentityPolicy(
        full_digest_byte_budget=len(analysis_payload),
        sampled_fingerprint_byte_budget=12,
        sample_chunk_bytes=4,
    )

    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-07-27T20:00:00Z",
        identity_policy=policy,
    )
    identities = {
        file_record["path"]: next(
            identity
            for identity in snapshot.asset_identity_records
            if identity["asset_ref"]["record_id"] == file_record["file_id"]
        )
        for file_record in snapshot.file_records
    }
    assert identities["analysis.py"]["tier"] == "full_digest"
    assert identities["large.bin"]["tier"] == "weak_fingerprint"
    assert not (snapshot.materialized_root / "large.bin").exists()
    assert snapshot.snapshot_record["extensions"]["x-identity-byte-reads"] == {
        "full_digest": len(analysis_payload),
        "sampled_fingerprint": 12,
    }
    validator = LocalSchemaRegistry(schema_root)
    for identity in snapshot.asset_identity_records:
        validator.validate(identity)

    with (source / "large.bin").open("r+b") as handle:
        handle.seek(100)
        handle.write(b"B")
    state = detect_workspace_divergence(
        source,
        snapshot.file_records,
        detected_at="2026-07-27T20:01:00Z",
        initial_asset_identities=snapshot.asset_identity_records,
        identity_policy=policy,
    )
    assert state["changed_paths"] == ["large.bin"]


def test_root_checksum_manifest_identifies_large_asset_without_full_target_read(
    schema_root: Path, tmp_path: Path
) -> None:
    source = tmp_path / "source"
    (source / "data").mkdir(parents=True)
    large_asset = source / "data" / "large.h5ad"
    with large_asset.open("wb") as handle:
        handle.truncate(10_000_000_000)
    declared_digest = "sha256:" + "a" * 64
    manifest_payload = f"{declared_digest.removeprefix('sha256:')}  data/large.h5ad\n".encode()
    (source / "checksums.sha256").write_bytes(manifest_payload)
    policy = AssetIdentityPolicy(
        full_digest_byte_budget=len(manifest_payload),
        sampled_fingerprint_byte_budget=12,
        sample_chunk_bytes=4,
    )

    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-07-27T20:00:00Z",
        identity_policy=policy,
    )
    file_by_path = {record["path"]: record for record in snapshot.file_records}
    identity_by_file_id = {
        record["asset_ref"]["record_id"]: record for record in snapshot.asset_identity_records
    }
    identity = identity_by_file_id[file_by_path["data/large.h5ad"]["file_id"]]

    assert identity["tier"] == "manifest"
    assert identity["identity_evidence"] == {
        "kind": "manifest",
        "manifest_ref": {
            "source_kind": "file_span",
            "locator": "checksums.sha256:1",
            "path": "checksums.sha256",
            "start_line": 1,
            "end_line": 1,
            "content_digest": sha256_digest(manifest_payload),
            "quoted_text": manifest_payload.decode().rstrip("\n"),
        },
        "manifest_digest": declared_digest,
    }
    assert "does not verify the target bytes" in identity["limitations"][0]
    assert identity["extensions"]["x-checksum-manifest-profile"] == ("root-sha256sum-two-space-v1")
    assert snapshot.snapshot_record["extensions"]["x-identity-byte-reads"] == {
        "full_digest": len(manifest_payload),
        "sampled_fingerprint": 12,
    }
    assert snapshot.snapshot_record["extensions"]["x-checksum-manifest-inspection"] == {
        "profile": "root-sha256sum-two-space-v1",
        "candidate_paths": ["checksums.sha256"],
        "parsed_paths": ["checksums.sha256"],
        "invalid_paths": [],
        "unavailable_paths": [],
        "ambiguous_targets": [],
        "unambiguous_declarations": 1,
        "upgraded_targets": ["data/large.h5ad"],
    }
    assert not (snapshot.materialized_root / "data" / "large.h5ad").exists()
    LocalSchemaRegistry(schema_root).validate(identity)

    unchanged = detect_workspace_divergence(
        source,
        snapshot.file_records,
        detected_at="2026-07-27T20:01:00Z",
        initial_asset_identities=snapshot.asset_identity_records,
        identity_policy=policy,
    )
    assert unchanged == {"status": "unchanged", "mix_live_content_into_run": False}
    observed_stat = large_asset.stat()
    os.utime(
        large_asset,
        ns=(observed_stat.st_atime_ns, observed_stat.st_mtime_ns + 1_000_000_000),
    )
    changed = detect_workspace_divergence(
        source,
        snapshot.file_records,
        detected_at="2026-07-27T20:02:00Z",
        initial_asset_identities=snapshot.asset_identity_records,
        identity_policy=policy,
    )
    assert changed["changed_paths"] == ["data/large.h5ad"]


def test_checksum_manifest_conflict_or_invalid_path_never_upgrades_identity(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "large.bin").write_bytes(b"x" * 200)
    first = ("a" * 64 + "  large.bin\n").encode()
    second = ("b" * 64 + "  large.bin\n").encode()
    (source / "first.sha256").write_bytes(first)
    (source / "second.sha256").write_bytes(second)
    policy = AssetIdentityPolicy(
        full_digest_byte_budget=len(first) + len(second),
        sampled_fingerprint_byte_budget=12,
        sample_chunk_bytes=4,
    )

    conflicted = capture_repository(
        source,
        tmp_path / "conflicted",
        "run:conflicted",
        captured_at="2026-07-27T20:00:00Z",
        identity_policy=policy,
    )
    file_by_path = {record["path"]: record for record in conflicted.file_records}
    identity_by_file_id = {
        record["asset_ref"]["record_id"]: record for record in conflicted.asset_identity_records
    }
    assert identity_by_file_id[file_by_path["large.bin"]["file_id"]]["tier"] == ("weak_fingerprint")
    assert conflicted.snapshot_record["extensions"]["x-checksum-manifest-inspection"][
        "ambiguous_targets"
    ] == ["large.bin"]

    unsafe_source = tmp_path / "unsafe-source"
    unsafe_source.mkdir()
    (unsafe_source / "large.bin").write_bytes(b"x" * 200)
    unsafe_manifest = ("a" * 64 + "  ../large.bin\n").encode()
    (unsafe_source / "checksums.sha256").write_bytes(unsafe_manifest)
    unsafe = capture_repository(
        unsafe_source,
        tmp_path / "unsafe",
        "run:unsafe",
        captured_at="2026-07-27T20:00:00Z",
        identity_policy=AssetIdentityPolicy(
            full_digest_byte_budget=len(unsafe_manifest),
            sampled_fingerprint_byte_budget=12,
            sample_chunk_bytes=4,
        ),
    )
    unsafe_files = {record["path"]: record for record in unsafe.file_records}
    unsafe_identities = {
        record["asset_ref"]["record_id"]: record for record in unsafe.asset_identity_records
    }
    assert unsafe_identities[unsafe_files["large.bin"]["file_id"]]["tier"] == ("weak_fingerprint")
    assert unsafe.snapshot_record["extensions"]["x-checksum-manifest-inspection"][
        "invalid_paths"
    ] == ["checksums.sha256"]


def test_over_budget_checksum_manifest_is_unavailable_and_never_upgrades_identity(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "large.bin").write_bytes(b"x" * 200)
    manifest = ("a" * 64 + "  large.bin\n").encode()
    (source / "checksums.sha256").write_bytes(manifest)

    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-07-27T20:00:00Z",
        identity_policy=AssetIdentityPolicy(
            full_digest_byte_budget=0,
            sampled_fingerprint_byte_budget=24,
            sample_chunk_bytes=4,
        ),
    )
    file_by_path = {record["path"]: record for record in snapshot.file_records}
    identity_by_file_id = {
        record["asset_ref"]["record_id"]: record for record in snapshot.asset_identity_records
    }
    assert identity_by_file_id[file_by_path["large.bin"]["file_id"]]["tier"] == ("weak_fingerprint")
    assert snapshot.snapshot_record["extensions"]["x-checksum-manifest-inspection"] == {
        "profile": "root-sha256sum-two-space-v1",
        "candidate_paths": ["checksums.sha256"],
        "parsed_paths": [],
        "invalid_paths": [],
        "unavailable_paths": ["checksums.sha256"],
        "ambiguous_targets": [],
        "unambiguous_declarations": 0,
        "upgraded_targets": [],
    }


def test_full_digest_wins_and_nested_checksum_manifest_stays_out_of_profile(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    (source / "checksums").mkdir(parents=True)
    payload = b"small exact bytes"
    (source / "small.bin").write_bytes(payload)
    manifest = ("0" * 64 + "  small.bin\n").encode()
    (source / "checksums.sha256").write_bytes(manifest)
    (source / "checksums" / "inputs.sha256").write_bytes(manifest)

    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-07-27T20:00:00Z",
    )
    file_by_path = {record["path"]: record for record in snapshot.file_records}
    identity_by_file_id = {
        record["asset_ref"]["record_id"]: record for record in snapshot.asset_identity_records
    }
    assert identity_by_file_id[file_by_path["small.bin"]["file_id"]]["tier"] == "full_digest"
    assert identity_by_file_id[file_by_path["small.bin"]["file_id"]]["identity_evidence"][
        "digest"
    ] == sha256_digest(payload)
    inspection = snapshot.snapshot_record["extensions"]["x-checksum-manifest-inspection"]
    assert inspection["candidate_paths"] == ["checksums.sha256"]
    assert inspection["parsed_paths"] == ["checksums.sha256"]
    assert inspection["ambiguous_targets"] == []
    assert inspection["upgraded_targets"] == []


def test_snapshot_records_special_paths_without_reading_them(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    fifo = source / "events.fifo"
    os.mkfifo(fifo)
    (source / ".git").mkdir()
    (source / ".git" / "secret").write_text("excluded", encoding="utf-8")

    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-07-27T20:00:00Z",
    )
    assert [record["path"] for record in snapshot.file_records] == ["events.fifo"]
    assert snapshot.file_records[0]["role"] == "unsupported_special_file"
    assert snapshot.asset_identity_records[0]["tier"] == "unidentified"


def test_in_repository_snapshot_destination_must_be_excluded(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "analysis.py").write_text("value = 1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="excluded audit directory"):
        capture_repository(source, source / "audit-output", "run:test")

    snapshot = capture_repository(
        source,
        source / ".sc-referee" / "runs" / "test" / "snapshot",
        "run:test",
        captured_at="2026-07-27T20:00:00Z",
    )
    assert [record["path"] for record in snapshot.file_records] == ["analysis.py"]


def test_one_unreadable_file_is_localized_without_losing_other_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from sc_referee.snapshot import repository as repository_module

    source = tmp_path / "source"
    source.mkdir()
    unreadable = source / "blocked.bin"
    unreadable.write_bytes(b"blocked")
    (source / "report.md").write_text("# Report\n", encoding="utf-8")
    original_reader = repository_module._read_stable_full_file

    def fail_one(path: Path, expected: os.stat_result) -> bytes:
        if path == unreadable:
            raise PermissionError("injected unreadable path")
        return original_reader(path, expected)

    monkeypatch.setattr(repository_module, "_read_stable_full_file", fail_one)
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-07-27T20:00:00Z",
    )
    identities = {
        file_record["path"]: next(
            identity
            for identity in snapshot.asset_identity_records
            if identity["asset_ref"]["record_id"] == file_record["file_id"]
        )
        for file_record in snapshot.file_records
    }
    assert identities["blocked.bin"]["tier"] == "unidentified"
    assert identities["report.md"]["tier"] == "full_digest"
    assert (snapshot.materialized_root / "report.md").is_file()


def test_demo_bundles_and_reports_asset_identity(project_root, schema_root, tmp_path) -> None:
    bundle = run_demo(
        project_root / "examples" / "walking-skeleton",
        tmp_path / "audit",
        schema_root,
    )
    assert bundle["asset_identities"]
    file_identities = [
        item
        for item in bundle["asset_identities"]
        if item["asset_ref"]["record_type"] == "file_record"
    ]
    assert {item["tier"] for item in file_identities} == {"full_digest"}
    assert any(
        item["tier"] == "unidentified" and item["asset_ref"]["record_type"] == "artifact"
        for item in bundle["asset_identities"]
    )
    report = (tmp_path / "audit" / "report.html").read_text(encoding="utf-8")
    assert "A weak or unidentified asset is a coverage and reproducibility limitation" in report


def test_weak_unrelated_asset_does_not_suppress_demonstrated_finding(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    fixture = tmp_path / "fixture"
    shutil.copytree(project_root / "examples" / "walking-skeleton", fixture)
    (fixture / "unrelated-large.bin").write_bytes(b"x" * 5_100_000)

    bundle = run_demo(fixture, tmp_path / "audit", schema_root)

    assert len(bundle["findings"]) == 1
    weak = [item for item in bundle["asset_identities"] if item["tier"] == "weak_fingerprint"]
    assert len(weak) == 1
    known_gaps = bundle["coverage_records"][0]["known_gaps"]
    assert any("only dependent conclusions are limited" in gap for gap in known_gaps)
