from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.capture import (
    ReviewCaptureError,
    capture_review_submission,
    load_review_capture,
)
from sc_referee_evaluation.cli import main as evaluation_main
from sc_referee_evaluation.review_protocol import (
    ReviewProtocolError,
    build_stage1_review_packet,
    build_stage2_review_packet,
    freeze_scientific_label,
    freeze_stage1_panel,
    validate_stage1_review_submission,
    validate_stage2_review_submission,
)
from sc_referee_evaluation.workspace import build_blind_workspace

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.observed import build_file_records
from sc_referee.records.root_cause import root_cause_candidate_id
from sc_referee.snapshot.repository import capture_repository


def _example(project_root: Path, name: str) -> dict[str, Any]:
    return json.loads(
        (project_root / "reference" / "schemas-v0.19.0" / "examples" / name).read_text(
            encoding="utf-8"
        )
    )


def _workspace_manifest(tmp_path: Path) -> dict[str, Any]:
    source = tmp_path / "case"
    source.mkdir()
    (source / "task.md").write_text("Audit the reported scientific result.\n", encoding="utf-8")
    captured = capture_repository(
        source,
        tmp_path / "case-snapshot",
        "audit:review-protocol",
        captured_at="2026-07-27T17:00:00Z",
    )
    public_files = build_file_records(
        captured.file_records,
        captured.asset_identity_records,
        str(captured.snapshot_record["snapshot_id"]),
        "2026-07-27T17:00:00Z",
    )
    return build_blind_workspace(
        captured.materialized_root,
        tmp_path / "workspace",
        tmp_path / "workspace.manifest.json",
        [{"path": "task.md", "role": "scientific_task"}],
        snapshot=captured.snapshot_record,
        file_records=public_files,
        asset_identities=captured.asset_identity_records,
        created_at="2026-07-27T17:01:00Z",
    )


def _review_and_packet(
    project_root: Path,
    workspace_manifest: dict[str, Any],
    provider: str,
    index: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    review = deepcopy(_example(project_root, "agent-review.example.json"))
    slug = provider.lower()
    review["review_id"] = f"review:{slug}:{index}"
    review["case_id"] = "case:stage1-freeze"
    review["completed_at"] = f"2026-07-27T18:{index:02d}:00Z"
    review["reviewer_agent"]["provider"] = provider
    review["reviewer_agent"]["model_id"] = (
        "claude-opus-5" if provider == "Anthropic" else "gpt-5.6-sol"
    )
    review["reviewer_agent"]["model_name"] = (
        "Claude Opus 5" if provider == "Anthropic" else "GPT-5.6 Sol"
    )
    review["reviewer_agent"]["agent_surface"] = (
        "Claude Code" if provider == "Anthropic" else "Codex"
    )
    review["reviewer_agent"]["execution_context_id"] = f"context:{slug}:{index}"
    review["root_cause_identity"]["candidate_root_cause_id"] = root_cause_candidate_id(review)
    packet = build_stage1_review_packet(
        "case:stage1-freeze",
        workspace_manifest,
        review["reviewer_agent"],
        "Review only the supplied scientific workflow.\nReturn one AgentReview record.\n",
        created_at="2026-07-27T17:02:00Z",
    )
    review["reviewer_agent"] = deepcopy(packet["expected_reviewer_agent"])
    review["extensions"] = {"x-review-packet-digest": packet["packet_digest"]}
    return review, packet


def _capture_pairs(
    pairs: list[tuple[dict[str, Any], dict[str, Any]]],
    schema_root: Path,
    tmp_path: Path,
    *,
    prefix: str,
    captured_at: str,
) -> list[Path]:
    destinations: list[Path] = []
    for index, (review, packet) in enumerate(pairs, start=1):
        transcript_bytes = f"Synthetic {prefix} transcript {index}.\n".encode()
        review["transcript_digest"] = sha256_digest(transcript_bytes)
        transcript_path = tmp_path / f"{prefix}-{index}.transcript.txt"
        transcript_path.write_bytes(transcript_bytes)
        destination = tmp_path / f"{prefix}-{index}.capture"
        capture_review_submission(
            review,
            packet,
            transcript_path,
            schema_root,
            captured_at=captured_at,
            destination=destination,
        )
        destinations.append(destination)
    return destinations


def _capture_manifests(paths: list[Path], schema_root: Path) -> list[dict[str, Any]]:
    return [load_review_capture(path, schema_root)[2] for path in paths]


def test_stage1_packet_is_digest_bound_and_submission_is_exact(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    workspace_manifest = _workspace_manifest(tmp_path)
    review, packet = _review_and_packet(project_root, workspace_manifest, "Anthropic", 1)

    validate_stage1_review_submission(review, packet, schema_root)

    digest = packet.pop("packet_digest")
    assert digest == semantic_digest(packet)
    assert packet["blindness_required"] == {
        "answer_key_hidden": True,
        "benchmark_grade_hidden": True,
        "detector_identity_hidden": True,
        "other_reviews_hidden": True,
        "sc_referee_output_hidden": True,
    }
    assert packet["workspace"]["workspace_id"] == workspace_manifest["workspace_id"]
    assert "answer_side_evidence_refs" not in packet
    assert "detector_output_refs" not in packet
    assert "canonical_root_cause" not in json.dumps(packet)


def test_stage1_submission_recomputes_review_local_candidate_identity(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    workspace_manifest = _workspace_manifest(tmp_path)
    review, packet = _review_and_packet(project_root, workspace_manifest, "Anthropic", 1)
    review["root_cause"] = "mutated after the local candidate ID was derived"

    with pytest.raises(ReviewProtocolError, match="candidate ID"):
        validate_stage1_review_submission(review, packet, schema_root)


def test_stage1_submission_rejects_packet_or_reviewer_drift(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    workspace_manifest = _workspace_manifest(tmp_path)
    review, packet = _review_and_packet(project_root, workspace_manifest, "Anthropic", 1)
    review["extensions"]["x-review-packet-digest"] = "sha256:" + "0" * 64

    with pytest.raises(ReviewProtocolError, match="packet digest"):
        validate_stage1_review_submission(review, packet, schema_root)

    review["extensions"]["x-review-packet-digest"] = packet["packet_digest"]
    review["reviewer_agent"]["execution_context_id"] = "context:drifted"
    with pytest.raises(ReviewProtocolError, match="reviewer configuration"):
        validate_stage1_review_submission(review, packet, schema_root)


def test_cli_captures_exact_review_packet_and_transcript_without_claiming_authenticity(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    workspace_manifest = _workspace_manifest(tmp_path)
    review, packet = _review_and_packet(project_root, workspace_manifest, "OpenAI", 1)
    transcript_bytes = b"Synthetic reviewer transcript for capture testing.\n"
    review["transcript_digest"] = sha256_digest(transcript_bytes)
    review_path = tmp_path / "review.json"
    packet_path = tmp_path / "packet.json"
    transcript_path = tmp_path / "transcript.txt"
    review_path.write_text(json.dumps(review), encoding="utf-8")
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    transcript_path.write_bytes(transcript_bytes)
    destination = tmp_path / "captured-review"
    arguments = [
        "capture-review",
        "--review",
        str(review_path),
        "--packet",
        str(packet_path),
        "--transcript",
        str(transcript_path),
        "--schema-root",
        str(schema_root),
        "--captured-at",
        "2026-07-27T18:10:00Z",
        "--destination",
        str(destination),
    ]

    assert evaluation_main(arguments) == 0
    manifest = json.loads((destination / "capture.manifest.json").read_text(encoding="utf-8"))
    assert json.loads((destination / "review.json").read_text(encoding="utf-8")) == review
    assert json.loads((destination / "packet.json").read_text(encoding="utf-8")) == packet
    assert (destination / "transcript.bin").read_bytes() == transcript_bytes
    assert manifest["review_digest"] == semantic_digest(review)
    assert manifest["packet_digest"] == packet["packet_digest"]
    assert manifest["transcript_digest"] == review["transcript_digest"]
    assert manifest["model_invoked_by_capture"] is False
    assert manifest["reviewer_independence_verified"] is False
    loaded_review, loaded_packet, loaded_manifest = load_review_capture(destination, schema_root)
    assert loaded_review == review
    assert loaded_packet == packet
    assert loaded_manifest["capture_digest"] == manifest["capture_digest"]
    digest = manifest.pop("capture_digest")
    assert digest == semantic_digest(manifest)
    assert evaluation_main(arguments) == 2


def test_review_capture_rejects_transcript_or_chronology_mismatch(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    workspace_manifest = _workspace_manifest(tmp_path)
    review, packet = _review_and_packet(project_root, workspace_manifest, "Anthropic", 1)
    transcript = tmp_path / "transcript.txt"
    transcript.write_text("Different transcript.\n", encoding="utf-8")

    with pytest.raises(ReviewCaptureError, match="transcript_digest"):
        capture_review_submission(
            review,
            packet,
            transcript,
            schema_root,
            captured_at="2026-07-27T18:10:00Z",
            destination=tmp_path / "digest-mismatch",
        )

    review["transcript_digest"] = sha256_digest(transcript.read_bytes())
    with pytest.raises(ReviewCaptureError, match="cannot precede"):
        capture_review_submission(
            review,
            packet,
            transcript,
            schema_root,
            captured_at="2026-07-27T17:59:00Z",
            destination=tmp_path / "chronology-mismatch",
        )

    capture = tmp_path / "tampered-capture"
    capture_review_submission(
        review,
        packet,
        transcript,
        schema_root,
        captured_at="2026-07-27T18:10:00Z",
        destination=capture,
    )
    (capture / "transcript.bin").write_text("Tampered.\n", encoding="utf-8")
    with pytest.raises(ReviewCaptureError, match="does not match"):
        load_review_capture(capture, schema_root)


def test_stage1_panel_freezes_only_after_two_independent_reviews_per_provider(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    workspace_manifest = _workspace_manifest(tmp_path)
    pairs = [
        _review_and_packet(project_root, workspace_manifest, provider, index)
        for provider in ("Anthropic", "OpenAI")
        for index in (1, 2)
    ]
    output = tmp_path / "stage1.freeze.json"
    captures = _capture_pairs(
        pairs,
        schema_root,
        tmp_path,
        prefix="direct-stage1",
        captured_at="2026-07-27T18:20:00Z",
    )

    frozen = freeze_stage1_panel(
        [review for review, _packet in pairs],
        [packet for _review, packet in pairs],
        _capture_manifests(captures, schema_root),
        schema_root,
        frozen_at="2026-07-27T18:30:00Z",
        output=output,
    )

    assert frozen["provider_participation"] == {"Anthropic": 2, "OpenAI": 2}
    assert frozen["detector_output_observed"] is False
    assert frozen["answer_side_evidence_observed"] is False
    digest = frozen.pop("freeze_digest")
    assert digest == semantic_digest(frozen)

    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["freeze_digest"] == digest


def test_stage1_panel_rejects_context_reuse_or_incomplete_provider_pair(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    workspace_manifest = _workspace_manifest(tmp_path)
    pairs = [
        _review_and_packet(project_root, workspace_manifest, provider, index)
        for provider in ("Anthropic", "OpenAI")
        for index in (1, 2)
    ]
    reviews = [review for review, _packet in pairs]
    packets = [packet for _review, packet in pairs]
    captures = _capture_pairs(
        pairs,
        schema_root,
        tmp_path,
        prefix="invalid-stage1",
        captured_at="2026-07-27T18:20:00Z",
    )
    manifests = _capture_manifests(captures, schema_root)
    reviews[-1]["reviewer_agent"]["execution_context_id"] = reviews[0]["reviewer_agent"][
        "execution_context_id"
    ]

    with pytest.raises(ReviewProtocolError, match="reviewer configuration"):
        freeze_stage1_panel(
            reviews,
            packets,
            manifests,
            schema_root,
            frozen_at="2026-07-27T18:30:00Z",
            output=tmp_path / "reused.json",
        )

    with pytest.raises(ReviewProtocolError, match="two independent reviews"):
        freeze_stage1_panel(
            [review for review, _packet in pairs[:3]],
            [packet for _review, packet in pairs[:3]],
            manifests[:3],
            schema_root,
            frozen_at="2026-07-27T18:30:00Z",
            output=tmp_path / "incomplete.json",
        )


def test_stage2_packets_and_scientific_label_freeze_precede_detector_comparison(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    workspace_manifest = _workspace_manifest(tmp_path)
    stage1_pairs = [
        _review_and_packet(project_root, workspace_manifest, provider, index)
        for provider in ("Anthropic", "OpenAI")
        for index in (1, 2)
    ]
    stage1_captures = _capture_pairs(
        stage1_pairs,
        schema_root,
        tmp_path,
        prefix="stage1",
        captured_at="2026-07-27T18:20:00Z",
    )
    stage1_freeze_path = tmp_path / "stage1.json"
    stage1_freeze_arguments = ["freeze-stage1"]
    for capture in stage1_captures:
        stage1_freeze_arguments.extend(["--capture", str(capture)])
    stage1_freeze_arguments.extend(
        [
            "--schema-root",
            str(schema_root),
            "--frozen-at",
            "2026-07-27T18:30:00Z",
            "--output",
            str(stage1_freeze_path),
        ]
    )
    assert evaluation_main(stage1_freeze_arguments) == 0
    stage1_freeze = json.loads(stage1_freeze_path.read_text(encoding="utf-8"))
    stage2_reviews: list[dict[str, Any]] = []
    stage2_packets: list[dict[str, Any]] = []
    stage2_captures: list[Path] = []
    template = _example(project_root, "agent-review.stage2.example.json")
    stage2_prompt = tmp_path / "stage2.prompt.txt"
    stage2_prompt.write_text(
        "Adjudicate the frozen scientific reviews and actively test innocent explanations.\n",
        encoding="utf-8",
    )
    evidence_spec = tmp_path / "stage2.evidence.json"
    evidence_spec.write_text(
        json.dumps(
            {
                "answer_side_evidence_refs": [],
                "reference_analysis_refs": [],
                "execution_comparison_refs": [],
            }
        ),
        encoding="utf-8",
    )
    for provider, model, surface in (
        ("Anthropic", "claude-opus-5", "Claude Code"),
        ("OpenAI", "gpt-5.6-sol", "Codex"),
    ):
        review = deepcopy(template)
        review["review_id"] = f"review:{provider.lower()}:stage2"
        review["case_id"] = "case:stage1-freeze"
        review["completed_at"] = "2026-07-27T19:00:00Z"
        review["reviewer_agent"].update(
            {
                "provider": provider,
                "model_id": model,
                "agent_surface": surface,
                "execution_context_id": f"context:{provider.lower()}:stage2",
            }
        )
        reviewer_path = tmp_path / f"{provider.lower()}.stage2.reviewer.json"
        reviewer_path.write_text(json.dumps(review["reviewer_agent"]), encoding="utf-8")
        packet_path = tmp_path / f"{provider.lower()}.stage2.packet.json"
        stage2_packet_arguments = [
            "stage2-packet",
            "--stage1-freeze",
            str(stage1_freeze_path),
        ]
        for capture in stage1_captures:
            stage2_packet_arguments.extend(["--stage1-capture", str(capture)])
        stage2_packet_arguments.extend(
            [
                "--schema-root",
                str(schema_root),
                "--reviewer-agent",
                str(reviewer_path),
                "--prompt",
                str(stage2_prompt),
                "--evidence-spec",
                str(evidence_spec),
                "--created-at",
                "2026-07-27T18:31:00Z",
                "--output",
                str(packet_path),
            ]
        )
        assert evaluation_main(stage2_packet_arguments) == 0
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        review["reviewer_agent"] = deepcopy(packet["expected_reviewer_agent"])
        review["extensions"] = {
            "x-review-packet-digest": packet["packet_digest"],
            "x-stage1-freeze-digest": stage1_freeze["freeze_digest"],
        }
        selected_by_provider: dict[str, dict[str, Any]] = {}
        for frozen_review in packet["frozen_stage1_reviews"]:
            selected_by_provider.setdefault(
                str(frozen_review["provider"]),
                {
                    "review_ref": deepcopy(frozen_review["review_ref"]),
                    "candidate_root_cause_id": frozen_review["root_cause_identity"][
                        "candidate_root_cause_id"
                    ],
                },
            )
        review["root_cause_identity"]["reconciled_stage1_candidates"] = sorted(
            selected_by_provider.values(),
            key=lambda item: str(item["review_ref"]["record_id"]),
        )
        review["root_cause_identity"]["candidate_root_cause_id"] = root_cause_candidate_id(review)
        transcript_bytes = f"Synthetic {provider} Stage-2 transcript.\n".encode()
        review["transcript_digest"] = sha256_digest(transcript_bytes)
        validate_stage2_review_submission(review, packet, schema_root)
        transcript_path = tmp_path / f"{provider.lower()}.stage2.transcript.txt"
        transcript_path.write_bytes(transcript_bytes)
        capture_path = tmp_path / f"{provider.lower()}.stage2.capture"
        capture_review_submission(
            review,
            packet,
            transcript_path,
            schema_root,
            captured_at="2026-07-27T19:10:00Z",
            destination=capture_path,
        )
        stage2_reviews.append(review)
        stage2_packets.append(packet)
        stage2_captures.append(capture_path)

    resolution_spec = tmp_path / "root-cause-resolution.json"
    resolution_spec.write_text(
        json.dumps(
            {
                "statement_source_review_id": stage2_reviews[0]["review_id"],
                "required_scientific_premises": [
                    "The report and result use the same contrast orientation."
                ],
                "stronger_claims_excluded": [
                    "No global workflow correctness claim is established."
                ],
            }
        ),
        encoding="utf-8",
    )
    root_cause_path = tmp_path / "adjudicated-root-cause.json"
    reconcile_arguments = ["reconcile-root-cause"]
    for capture in stage1_captures:
        reconcile_arguments.extend(["--stage1-capture", str(capture)])
    for capture in stage2_captures:
        reconcile_arguments.extend(["--stage2-capture", str(capture)])
    reconcile_arguments.extend(
        [
            "--schema-root",
            str(schema_root),
            "--resolution-spec",
            str(resolution_spec),
            "--adjudicated-at",
            "2026-07-27T19:30:00Z",
            "--output",
            str(root_cause_path),
        ]
    )
    assert evaluation_main(reconcile_arguments) == 0
    root_cause = json.loads(root_cause_path.read_text(encoding="utf-8"))

    adjudication = _example(project_root, "benchmark-adjudication.example.json")
    adjudication["adjudication_id"] = "benchmark-adjudication:stage2-freeze"
    adjudication["case_id"] = "case:stage1-freeze"
    adjudication["adjudicated_at"] = "2026-07-27T19:30:00Z"
    adjudication["stage1_review_refs"] = [entry["review_ref"] for entry in stage1_freeze["reviews"]]
    adjudication["stage2_review_refs"] = [
        {"record_type": "agent_review", "record_id": review["review_id"]}
        for review in stage2_reviews
    ]
    adjudication["adjudicated_root_cause_refs"] = [
        {
            "record_type": "adjudicated_root_cause",
            "record_id": root_cause["adjudicated_root_cause_id"],
        }
    ]
    adjudication_path = tmp_path / "adjudication.json"
    label_freeze_path = tmp_path / "scientific-label.freeze.json"
    adjudication_path.write_text(json.dumps(adjudication), encoding="utf-8")
    label_freeze_arguments = [
        "freeze-label",
        "--adjudication",
        str(adjudication_path),
        "--stage1-freeze",
        str(stage1_freeze_path),
    ]
    for capture in stage2_captures:
        label_freeze_arguments.extend(["--stage2-capture", str(capture)])
    for capture in stage1_captures:
        label_freeze_arguments.extend(["--stage1-capture", str(capture)])
    label_freeze_arguments.extend(["--adjudicated-root-cause", str(root_cause_path)])
    label_freeze_arguments.extend(
        [
            "--schema-root",
            str(schema_root),
            "--frozen-at",
            "2026-07-27T20:00:00Z",
            "--output",
            str(label_freeze_path),
        ]
    )
    assert evaluation_main(label_freeze_arguments) == 0
    frozen = json.loads(label_freeze_path.read_text(encoding="utf-8"))

    assert frozen["label_status"] == "positive_demonstrated"
    assert frozen["detector_output_observed"] is False
    assert frozen["stage1_freeze_digest"] == stage1_freeze["freeze_digest"]
    assert frozen["adjudicated_root_causes"] == [
        {
            "root_cause_ref": {
                "record_type": "adjudicated_root_cause",
                "record_id": root_cause["adjudicated_root_cause_id"],
            },
            "root_cause_digest": semantic_digest(root_cause),
        }
    ]
    assert "detector_output_refs" not in stage2_packets[0]
    digest = frozen.pop("freeze_digest")
    assert digest == semantic_digest(frozen)

    replay_path = tmp_path / "scientific-label.replay.json"
    replay_arguments = [
        "replay-label-freeze",
        "--source-label-freeze",
        str(label_freeze_path),
        "--adjudication",
        str(adjudication_path),
        "--stage1-freeze",
        str(stage1_freeze_path),
    ]
    for capture in stage1_captures:
        replay_arguments.extend(["--stage1-capture", str(capture)])
    for capture in stage2_captures:
        replay_arguments.extend(["--stage2-capture", str(capture)])
    replay_arguments.extend(
        [
            "--adjudicated-root-cause",
            str(root_cause_path),
            "--schema-root",
            str(schema_root),
            "--output",
            str(replay_path),
        ]
    )
    assert evaluation_main(replay_arguments) == 0
    assert replay_path.read_bytes() == label_freeze_path.read_bytes()


def test_stage2_freeze_rejects_context_reuse_from_stage1(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    workspace_manifest = _workspace_manifest(tmp_path)
    stage1_pairs = [
        _review_and_packet(project_root, workspace_manifest, provider, index)
        for provider in ("Anthropic", "OpenAI")
        for index in (1, 2)
    ]
    stage1_reviews = [review for review, _packet in stage1_pairs]
    stage1_capture_paths = _capture_pairs(
        stage1_pairs,
        schema_root,
        tmp_path,
        prefix="context-stage1",
        captured_at="2026-07-27T18:20:00Z",
    )
    stage1_freeze = freeze_stage1_panel(
        stage1_reviews,
        [packet for _review, packet in stage1_pairs],
        _capture_manifests(stage1_capture_paths, schema_root),
        schema_root,
        frozen_at="2026-07-27T18:30:00Z",
        output=tmp_path / "stage1.json",
    )
    review = deepcopy(_example(project_root, "agent-review.stage2.example.json"))
    review["review_id"] = "review:anthropic:stage2"
    review["case_id"] = "case:stage1-freeze"
    review["completed_at"] = "2026-07-27T19:00:00Z"
    review["reviewer_agent"]["provider"] = "Anthropic"
    review["reviewer_agent"]["execution_context_id"] = stage1_freeze["reviews"][0][
        "execution_context_id"
    ]
    packet = build_stage2_review_packet(
        stage1_freeze,
        stage1_reviews,
        review["reviewer_agent"],
        "Adjudicate the frozen scientific reviews.",
        created_at="2026-07-27T18:31:00Z",
        answer_side_evidence_refs=[],
        reference_analysis_refs=[],
        execution_comparison_refs=[],
    )
    review["reviewer_agent"] = deepcopy(packet["expected_reviewer_agent"])
    review["extensions"] = {
        "x-review-packet-digest": packet["packet_digest"],
        "x-stage1-freeze-digest": stage1_freeze["freeze_digest"],
    }
    review["root_cause_identity"]["reconciled_stage1_candidates"] = [
        {
            "review_ref": deepcopy(item["review_ref"]),
            "candidate_root_cause_id": item["root_cause_identity"]["candidate_root_cause_id"],
        }
        for item in packet["frozen_stage1_reviews"]
        if item["provider"] in {"Anthropic", "OpenAI"}
    ][:2]
    review["root_cause_identity"]["candidate_root_cause_id"] = root_cause_candidate_id(review)
    transcript = tmp_path / "context-stage2.transcript.txt"
    transcript.write_text("Synthetic Stage-2 context-reuse transcript.\n", encoding="utf-8")
    review["transcript_digest"] = sha256_digest(transcript.read_bytes())
    stage2_capture_path = tmp_path / "context-stage2.capture"
    capture_review_submission(
        review,
        packet,
        transcript,
        schema_root,
        captured_at="2026-07-27T19:10:00Z",
        destination=stage2_capture_path,
    )
    stage2_manifest = load_review_capture(stage2_capture_path, schema_root)[2]

    adjudication = _example(project_root, "benchmark-adjudication.example.json")
    adjudication["adjudication_id"] = "benchmark-adjudication:invalid-context"
    adjudication["case_id"] = "case:stage1-freeze"
    adjudication["stage1_review_refs"] = [entry["review_ref"] for entry in stage1_freeze["reviews"]]
    adjudication["stage2_review_refs"] = [
        {"record_type": "agent_review", "record_id": review["review_id"]},
        {"record_type": "agent_review", "record_id": "review:openai:missing"},
    ]

    with pytest.raises(ReviewProtocolError, match="Stage-1 execution context"):
        freeze_scientific_label(
            adjudication,
            stage1_freeze,
            [review],
            [packet],
            [stage2_manifest],
            schema_root,
            frozen_at="2026-07-27T20:00:00Z",
            output=tmp_path / "invalid.json",
        )
