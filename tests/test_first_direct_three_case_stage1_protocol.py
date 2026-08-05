from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
from sc_referee_evaluation.capture import capture_review_submission, load_review_capture
from sc_referee_evaluation.review_protocol import (
    freeze_stage1_panel,
    validate_stage1_freeze_evidence,
    validate_stage1_review_submission,
)
from sc_referee_evaluation.review_semantic_payload import (
    ReviewSemanticPayloadError,
    project_stage1_semantic_batch,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_three_case_stage1_protocol import (
    CANONICAL_ISSUE_CLASS,
    CASE_IDS,
    REVIEW_RELATIVE,
    STAGE1_REVIEWERS,
    VISIBLE_FILES,
    build_first_direct_three_case_stage1_protocol,
)
from scripts.record_first_direct_three_case_stage1_reviews import (
    build_stage1_call_capture,
    validate_stage1_call_capture,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = PROJECT_ROOT / "reference/schemas-v0.18.0"
REVIEW_ROOT = PROJECT_ROOT / REVIEW_RELATIVE


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _workspace_payloads(case_id: str) -> dict[str, bytes]:
    workspace = REVIEW_ROOT / "case-preparations" / case_id.removeprefix("case:") / "workspace"
    return {
        str(item["path"]): (workspace / str(item["path"])).read_bytes() for item in VISIBLE_FILES
    }


def _exact_span(
    payloads: dict[str, bytes], path: str, contains: str | None = None
) -> dict[str, Any]:
    lines = payloads[path].decode("utf-8").splitlines()
    index = 0 if contains is None else next(i for i, line in enumerate(lines) if contains in line)
    return {
        "path": path,
        "start_line": index + 1,
        "end_line": index + 1,
        "quoted_text": lines[index],
    }


def _semantic_review(case_id: str, payloads: dict[str, bytes]) -> dict[str, Any]:
    positive = case_id == CASE_IDS[1]
    task_span = _exact_span(payloads, "task.md")
    result_span = _exact_span(payloads, "results/report.md", "[selected-result]")
    return {
        "case_id": case_id,
        "verdict": ("demonstrated_issue" if positive else "no_demonstrated_issue_within_scope"),
        "bounded_statement": (
            "The selected complete-network occurrence rate uses only the retained stations as its exposure denominator."
            if positive
            else None
        ),
        "root_cause": "retained-subset denominator for a complete-domain target"
        if positive
        else None,
        "issue_class": CANONICAL_ISSUE_CLASS if positive else None,
        "evidence_atoms": [
            {
                "description": "Exact visible task or selected-result evidence.",
                "source_spans": [result_span if positive else task_span],
            }
        ],
        "counterevidence_atoms": [
            {
                "description": "Exact visible evidence used for the falsification attempt.",
                "source_spans": [task_span if positive else result_span],
            }
        ],
        "falsification_attempt": "Test whether the visible task and report instead define the same population.",
        "cross_case_evidence_used": False,
        "unresolved_material_questions": [],
        "self_reported_confidence": "high",
    }


def test_frozen_stage1_protocol_replays_without_answer_side_leakage() -> None:
    protocol = _load(REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json")
    supplied = protocol.pop("protocol_digest")
    assert supplied == semantic_digest(protocol)
    protocol["protocol_digest"] = supplied
    assert protocol["execution_state"] == "frozen_not_started"
    assert protocol["case_ids"] == CASE_IDS
    assert protocol["stage1_review_count"] == 0
    assert protocol["scientific_label_count"] == 0
    assert protocol["detector_outcome_count"] == 0
    assert protocol["review_design"] == {
        "answer_side_evidence_visible": False,
        "batching_prospectively_declared": True,
        "case_order_frozen_per_reviewer": True,
        "cases_per_call": 3,
        "detector_output_visible": False,
        "external_call_count": 4,
        "one_agent_review_per_case_per_reviewer": True,
        "one_packet_and_capture_per_agent_review": True,
        "other_reviews_visible": False,
        "project_code_execution_permitted": False,
        "providers_per_case": 2,
        "reviews_per_case": 4,
        "reviews_per_provider_per_case": 2,
        "shared_transcript_within_reviewer_batch": True,
    }

    expected_paths = sorted(str(item["path"]) for item in VISIBLE_FILES)
    for case_id in CASE_IDS:
        root = REVIEW_ROOT / "case-preparations" / case_id.removeprefix("case:")
        preparation = _load(root / "case-preparation.json")
        digest = preparation.pop("preparation_digest")
        assert digest == semantic_digest(preparation)
        preparation["preparation_digest"] = digest
        manifest = _load(root / "workspace-manifest.json")
        manifest_digest = manifest.pop("manifest_digest")
        assert manifest_digest == semantic_digest(manifest)
        manifest["manifest_digest"] = manifest_digest
        assert sorted(item["path"] for item in manifest["files"]) == expected_paths
        assert manifest["answer_side_content_copied"] is False
        assert manifest["project_code_executed"] is False
        assert manifest["scanner"]["unresolved_forbidden_source_path_count"] == 0
        assert manifest["scanner"]["forbidden_path_count"] == 10
        assert {
            path.relative_to(root / "workspace").as_posix()
            for path in (root / "workspace").rglob("*")
            if path.is_file()
        } == set(expected_paths)
        task = (root / "workspace/task.md").read_text(encoding="utf-8")
        assert "construction_constraints" not in task
        assert "error-bearing" not in task
        assert "corrected-twin" not in task
        assert "valid-alternative" not in task

    assert [item["participant_id"] for item in protocol["calls"]] == STAGE1_REVIEWERS
    for call in protocol["calls"]:
        assert sha256_digest(call["prompt"]) == call["prompt_digest"]
        assert semantic_digest(call["output_schema"]) == call["output_schema_digest"]
        assert set(call["case_order"]) == set(CASE_IDS)
        assert len(call["packet_refs"]) == 3
        assert "error-bearing" not in call["prompt"]
        assert "corrected-twin" not in call["prompt"]
        assert "valid-alternative" not in call["prompt"]
        assert "causal-triad" not in call["prompt"]
        assert "check:complete-domain-exposure-denominator" not in call["prompt"]
        for packet_ref in call["packet_refs"]:
            packet = _load(REVIEW_ROOT / packet_ref["relative_path"])
            packet_digest = packet.pop("packet_digest")
            assert packet_digest == semantic_digest(packet)
            packet["packet_digest"] = packet_digest
            assert packet_digest == packet_ref["packet_digest"]
            assert packet["prompt"]["normalized_text"] == call["prompt"]
            assert packet["prompt"]["prompt_digest"] == call["prompt_digest"]


def test_shared_batch_transcripts_project_to_complete_per_case_panels(tmp_path: Path) -> None:
    protocol = _load(REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json")
    reviews_by_case: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in CASE_IDS}
    packets_by_case: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in CASE_IDS}
    manifests_by_case: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in CASE_IDS}

    for call_index, call in enumerate(protocol["calls"], start=1):
        participant_id = str(call["participant_id"])
        packets = {
            str(item["case_id"]): _load(REVIEW_ROOT / str(item["relative_path"]))
            for item in call["packet_refs"]
        }
        payloads = {case_id: _workspace_payloads(case_id) for case_id in CASE_IDS}
        semantic_payload = {
            "reviewer_participant_id": participant_id,
            "reviews": [
                _semantic_review(case_id, payloads[case_id]) for case_id in call["case_order"]
            ],
        }
        transcript = normalized = json.dumps(semantic_payload, sort_keys=True).encode("utf-8")
        with pytest.raises(ReviewSemanticPayloadError, match="participant does not match"):
            project_stage1_semantic_batch(
                semantic_payload,
                output_schema=call["output_schema"],
                participant_id="actor:wrong-reviewer",
                participant_reviewer_agent=call["reviewer_agent_base"],
                packets_by_case=packets,
                workspace_payloads_by_case=payloads,
                canonical_issue_class=CANONICAL_ISSUE_CLASS,
                transcript=transcript,
                completed_at=f"2026-08-05T06:{10 + call_index:02d}:00Z",
                schema_root=SCHEMA_ROOT,
            )
        reviews = project_stage1_semantic_batch(
            semantic_payload,
            output_schema=call["output_schema"],
            participant_id=participant_id,
            participant_reviewer_agent=call["reviewer_agent_base"],
            packets_by_case=packets,
            workspace_payloads_by_case=payloads,
            canonical_issue_class=CANONICAL_ISSUE_CLASS,
            transcript=transcript,
            completed_at=f"2026-08-05T06:{10 + call_index:02d}:00Z",
            schema_root=SCHEMA_ROOT,
        )
        transcript_path = tmp_path / f"reviewer-{call_index}.json"
        transcript_path.write_bytes(normalized)
        call_digests = set()
        call_capture_ids = set()
        for review in reviews:
            case_id = str(review["case_id"])
            packet = packets[case_id]
            validate_stage1_review_submission(review, packet, SCHEMA_ROOT)
            destination = tmp_path / f"capture-{call_index}-{case_id.removeprefix('case:')}"
            manifest = capture_review_submission(
                review,
                packet,
                transcript_path,
                SCHEMA_ROOT,
                captured_at=f"2026-08-05T06:{20 + call_index:02d}:00Z",
                destination=destination,
            )
            loaded_review, loaded_packet, loaded_manifest = load_review_capture(
                destination, SCHEMA_ROOT
            )
            assert (loaded_review, loaded_packet, loaded_manifest) == (
                review,
                packet,
                manifest,
            )
            call_digests.add(manifest["transcript_digest"])
            call_capture_ids.add(manifest["capture_id"])
            reviews_by_case[case_id].append(review)
            packets_by_case[case_id].append(packet)
            manifests_by_case[case_id].append(manifest)
        assert len(call_digests) == 1
        assert len(call_capture_ids) == 3

    for case_index, case_id in enumerate(CASE_IDS, start=1):
        reviews = reviews_by_case[case_id]
        providers = [review["reviewer_agent"]["provider"] for review in reviews]
        contexts = [review["reviewer_agent"]["execution_context_id"] for review in reviews]
        assert providers.count("Anthropic") == 2
        assert providers.count("OpenAI") == 2
        assert len(contexts) == len(set(contexts)) == 4
        frozen = freeze_stage1_panel(
            reviews,
            packets_by_case[case_id],
            manifests_by_case[case_id],
            SCHEMA_ROOT,
            frozen_at=f"2026-08-05T06:{30 + case_index:02d}:00Z",
            output=tmp_path / f"freeze-{case_index}.json",
        )
        validate_stage1_freeze_evidence(
            deepcopy(frozen),
            reviews,
            packets_by_case[case_id],
            manifests_by_case[case_id],
            SCHEMA_ROOT,
        )
        assert frozen["case_id"] == case_id
        assert frozen["provider_participation"] == {"Anthropic": 2, "OpenAI": 2}


def test_stage1_protocol_builder_is_write_once() -> None:
    before = sha256_digest((REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json").read_bytes())
    with pytest.raises(ValueError, match="already exists"):
        build_first_direct_three_case_stage1_protocol(PROJECT_ROOT)
    assert sha256_digest((REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json").read_bytes()) == before


def test_stage1_raw_call_capture_validates_without_writing_reviews() -> None:
    existing_ledgers = {
        path.name: sha256_digest(path.read_bytes())
        for path in (REVIEW_ROOT / "stage1-call-ledgers").glob("*.json")
    }
    protocol = _load(REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json")
    call = protocol["calls"][0]
    payloads = {case_id: _workspace_payloads(case_id) for case_id in CASE_IDS}
    semantic_payload = {
        "reviewer_participant_id": call["participant_id"],
        "reviews": [_semantic_review(case_id, payloads[case_id]) for case_id in call["case_order"]],
    }
    raw_response = json.dumps(semantic_payload, sort_keys=True).encode("utf-8")
    capture = build_stage1_call_capture(
        PROJECT_ROOT,
        str(call["participant_id"]),
        raw_response,
        started_at="2026-08-05T06:10:00Z",
        completed_at="2026-08-05T06:11:00Z",
        captured_at="2026-08-05T06:12:00Z",
        transport={"surface": "synthetic_test_only"},
    )
    supplied = capture.pop("capture_digest")
    assert supplied == semantic_digest(capture)
    capture["capture_digest"] = supplied
    reviews = validate_stage1_call_capture(PROJECT_ROOT, capture)
    assert [review["case_id"] for review in reviews] == sorted(CASE_IDS)
    assert {review["transcript_digest"] for review in reviews} == {sha256_digest(raw_response)}
    assert existing_ledgers == {
        path.name: sha256_digest(path.read_bytes())
        for path in (REVIEW_ROOT / "stage1-call-ledgers").glob("*.json")
    }

    wrong = deepcopy(semantic_payload)
    wrong["reviewer_participant_id"] = STAGE1_REVIEWERS[1]
    wrong_response = json.dumps(wrong, sort_keys=True).encode("utf-8")
    wrong_capture = build_stage1_call_capture(
        PROJECT_ROOT,
        str(call["participant_id"]),
        wrong_response,
        started_at="2026-08-05T06:10:00Z",
        completed_at="2026-08-05T06:11:00Z",
        captured_at="2026-08-05T06:12:00Z",
        transport={"surface": "synthetic_test_only"},
    )
    with pytest.raises(ValueError, match="semantic payload is invalid"):
        validate_stage1_call_capture(PROJECT_ROOT, wrong_capture)
