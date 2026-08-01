from __future__ import annotations

import json
from pathlib import Path

import pytest
from sc_referee_evaluation.cli import main as evaluation_main
from sc_referee_evaluation.workspace import BlindWorkspaceError, build_blind_workspace

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.observed import build_file_records
from sc_referee.snapshot.repository import capture_repository


def _workspace_files() -> list[dict[str, str]]:
    return [
        {"path": "task.md", "role": "scientific_task"},
        {"path": "analysis.py", "role": "workflow_source"},
        {"path": "report.md", "role": "report"},
    ]


def _build_workspace(
    source: Path,
    destination: Path,
    manifest_path: Path,
    files: list[dict[str, str]],
    created_at: str = "2026-07-27T17:01:00Z",
    **kwargs: object,
) -> dict[str, object]:
    captured_at = "2026-07-27T17:00:00Z"
    captured = capture_repository(
        source,
        destination.parent / f".{destination.name}-snapshot",
        "audit:workspace:test",
        captured_at=captured_at,
    )
    public_files = build_file_records(
        captured.file_records,
        captured.asset_identity_records,
        str(captured.snapshot_record["snapshot_id"]),
        captured_at,
    )
    return build_blind_workspace(
        captured.materialized_root,
        destination,
        manifest_path,
        files,
        snapshot=captured.snapshot_record,
        file_records=public_files,
        asset_identities=captured.asset_identity_records,
        created_at=created_at,
        **kwargs,
    )


def test_blind_workspace_contains_only_allowlisted_non_answer_files(tmp_path: Path) -> None:
    source = tmp_path / "runner-case"
    source.mkdir()
    (source / "task.md").write_text("Estimate the treatment effect.\n", encoding="utf-8")
    (source / "analysis.py").write_text("effect = -0.42\n", encoding="utf-8")
    (source / "report.md").write_text("The estimated effect is -0.42.\n", encoding="utf-8")
    (source / "answer.json").write_text('{"effect": -0.42}\n', encoding="utf-8")
    (source / "grader.py").write_text("EXPECTED = -0.42\n", encoding="utf-8")
    destination = tmp_path / "agent-workspace"
    manifest_path = tmp_path / "blind-workspace.manifest.json"

    manifest = _build_workspace(
        source,
        destination,
        manifest_path,
        _workspace_files(),
        forbidden_source_paths={"answer.json", "grader.py"},
        forbidden_markers={"EXPECTED ="},
    )

    assert sorted(path.name for path in destination.iterdir()) == [
        "analysis.py",
        "report.md",
        "task.md",
    ]
    assert not (destination / "answer.json").exists()
    assert not (destination / "grader.py").exists()
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == manifest
    assert {item["role"] for item in manifest["files"]} == {
        "scientific_task",
        "workflow_source",
        "report",
    }
    assert manifest["answer_side_content_copied"] is False
    assert manifest["project_code_executed"] is False
    assert manifest["scanner"]["method"] == (
        "exact_path_digest_multiencoding_marker_and_forbidden_content_v2"
    )
    assert manifest["scanner"]["forbidden_source_content_variant_count"] > 0
    assert manifest["scanner"]["unresolved_forbidden_source_path_count"] == 0
    assert "forbidden_markers" not in manifest


def test_blind_workspace_rejects_forbidden_path_or_literal_marker(tmp_path: Path) -> None:
    source = tmp_path / "runner-case"
    source.mkdir()
    (source / "answer.json").write_text('{"effect": -0.42}\n', encoding="utf-8")
    (source / "task.md").write_text("Hidden answer: -0.42\n", encoding="utf-8")

    with pytest.raises(BlindWorkspaceError, match="forbidden answer-side path"):
        _build_workspace(
            source,
            tmp_path / "path-leak",
            tmp_path / "path-leak.json",
            [{"path": "answer.json", "role": "generated_output"}],
            forbidden_source_paths={"answer.json"},
        )

    with pytest.raises(BlindWorkspaceError, match="forbidden literal marker"):
        _build_workspace(
            source,
            tmp_path / "marker-leak",
            tmp_path / "marker-leak.json",
            [{"path": "task.md", "role": "scientific_task"}],
            forbidden_markers={"-0.42"},
        )

    with pytest.raises(BlindWorkspaceError, match="forbidden answer-side digest"):
        _build_workspace(
            source,
            tmp_path / "digest-leak",
            tmp_path / "digest-leak.json",
            [{"path": "task.md", "role": "scientific_task"}],
            forbidden_digests={sha256_digest((source / "task.md").read_bytes())},
        )


def test_blind_workspace_rejects_embedded_hidden_content_and_utf16_markers(
    tmp_path: Path,
) -> None:
    source = tmp_path / "runner-case"
    source.mkdir()
    (source / "answer.txt").write_bytes(b"expected effect = -0.42\r\n")
    (source / "normalized-copy.txt").write_bytes(b"Context\nexpected effect = -0.42\nEnd\n")

    with pytest.raises(BlindWorkspaceError, match="forbidden source"):
        _build_workspace(
            source,
            tmp_path / "content-leak",
            tmp_path / "content-leak.json",
            [{"path": "normalized-copy.txt", "role": "report"}],
            forbidden_source_paths={"answer.txt"},
        )

    marker = "BENCHMARK-ANSWER"
    (source / "encoded.bin").write_bytes(b"prefix" + marker.encode("utf-16-le") + b"suffix")
    with pytest.raises(BlindWorkspaceError, match="literal marker"):
        _build_workspace(
            source,
            tmp_path / "encoded-leak",
            tmp_path / "encoded-leak.json",
            [{"path": "encoded.bin", "role": "staged_data"}],
            forbidden_markers={marker},
        )


def test_blind_workspace_rejects_symlinks_and_existing_destinations(tmp_path: Path) -> None:
    source = tmp_path / "runner-case"
    source.mkdir()
    outside = tmp_path / "answer.txt"
    outside.write_text("secret\n", encoding="utf-8")
    (source / "linked.txt").symlink_to(outside)

    with pytest.raises(BlindWorkspaceError, match="regular-file"):
        _build_workspace(
            source,
            tmp_path / "symlink-workspace",
            tmp_path / "symlink-workspace.json",
            [{"path": "linked.txt", "role": "generated_output"}],
        )

    destination = tmp_path / "existing"
    destination.mkdir()
    with pytest.raises(BlindWorkspaceError, match="must not already exist"):
        _build_workspace(
            source,
            destination,
            tmp_path / "existing.json",
            [],
        )


def test_blind_workspace_manifest_is_deterministic_and_outside_workspace(tmp_path: Path) -> None:
    source = tmp_path / "runner-case"
    source.mkdir()
    (source / "task.md").write_text("Estimate the effect.\n", encoding="utf-8")
    first_manifest_path = tmp_path / "first.json"
    second_manifest_path = tmp_path / "second.json"

    first = _build_workspace(
        source,
        tmp_path / "first",
        first_manifest_path,
        [{"path": "task.md", "role": "scientific_task"}],
    )
    second = _build_workspace(
        source,
        tmp_path / "second",
        second_manifest_path,
        [{"path": "task.md", "role": "scientific_task"}],
    )

    assert first == second
    assert first_manifest_path.read_bytes() == second_manifest_path.read_bytes()
    assert not first_manifest_path.is_relative_to(tmp_path / "first")


def test_blind_workspace_cannot_predate_its_immutable_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "runner-case"
    source.mkdir()
    (source / "task.md").write_text("Estimate the effect.\n", encoding="utf-8")

    with pytest.raises(BlindWorkspaceError, match="cannot precede snapshot capture"):
        _build_workspace(
            source,
            tmp_path / "chronology-workspace",
            tmp_path / "chronology-workspace.json",
            [{"path": "task.md", "role": "scientific_task"}],
            created_at="2026-07-27T16:59:59Z",
        )


def test_cli_builds_blind_workspace_and_digest_bound_stage1_packet(tmp_path: Path) -> None:
    source = tmp_path / "runner-case"
    source.mkdir()
    (source / "task.md").write_text("Audit the reported result.\n", encoding="utf-8")
    (source / "answer.json").write_text('{"hidden": true}\n', encoding="utf-8")
    spec = tmp_path / "workspace-spec.json"
    spec.write_text(
        json.dumps(
            {
                "files": [{"path": "task.md", "role": "scientific_task"}],
                "forbidden_source_paths": ["answer.json"],
                "forbidden_markers": ["hidden answer"],
                "forbidden_digests": [],
            }
        ),
        encoding="utf-8",
    )
    destination = tmp_path / "blind-workspace"
    manifest = tmp_path / "blind-workspace.manifest.json"
    captured = capture_repository(
        source,
        tmp_path / "cli-snapshot",
        "audit:workspace:cli",
        captured_at="2026-07-27T17:00:00Z",
    )
    public_files = build_file_records(
        captured.file_records,
        captured.asset_identity_records,
        str(captured.snapshot_record["snapshot_id"]),
        "2026-07-27T17:00:00Z",
    )
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(json.dumps(captured.snapshot_record), encoding="utf-8")
    files_path = tmp_path / "files.jsonl"
    files_path.write_text(
        "".join(json.dumps(record) + "\n" for record in public_files), encoding="utf-8"
    )
    identities_path = tmp_path / "identities.jsonl"
    identities_path.write_text(
        "".join(json.dumps(record) + "\n" for record in captured.asset_identity_records),
        encoding="utf-8",
    )

    assert (
        evaluation_main(
            [
                "build-workspace",
                "--source-root",
                str(captured.materialized_root),
                "--snapshot",
                str(snapshot_path),
                "--file-records-jsonl",
                str(files_path),
                "--asset-identities-jsonl",
                str(identities_path),
                "--created-at",
                "2026-07-27T17:01:00Z",
                "--destination",
                str(destination),
                "--spec",
                str(spec),
                "--manifest",
                str(manifest),
            ]
        )
        == 0
    )
    assert (destination / "task.md").is_file()
    assert not (destination / "answer.json").exists()

    reviewer = tmp_path / "reviewer.json"
    reviewer.write_text(
        json.dumps(
            {
                "provider": "OpenAI",
                "agent_surface": "Codex",
                "model_name": "GPT-5.6 Sol",
                "model_id": "gpt-5.6-sol",
                "agent_version": "2026-07-28",
                "execution_context_id": "context:openai:stage1:1",
                "independent_context": True,
                "system_prompt_digest": "sha256:" + "1" * 64,
                "tool_policy_digest": "sha256:" + "2" * 64,
                "environment_digest": "sha256:" + "3" * 64,
            }
        ),
        encoding="utf-8",
    )
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Review only the supplied workflow.\r\n", encoding="utf-8")
    packet_path = tmp_path / "stage1.packet.json"

    assert (
        evaluation_main(
            [
                "stage1-packet",
                "--case-id",
                "case:cli",
                "--workspace-manifest",
                str(manifest),
                "--reviewer-agent",
                str(reviewer),
                "--prompt",
                str(prompt),
                "--created-at",
                "2026-07-27T17:02:00Z",
                "--output",
                str(packet_path),
            ]
        )
        == 0
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    digest = packet.pop("packet_digest")
    assert digest == semantic_digest(packet)
    assert packet["prompt"]["normalized_text"] == "Review only the supplied workflow."
    assert (
        packet["workspace"]["manifest_digest"]
        == json.loads(manifest.read_text(encoding="utf-8"))["manifest_digest"]
    )
    assert "detector_output_refs" not in packet
