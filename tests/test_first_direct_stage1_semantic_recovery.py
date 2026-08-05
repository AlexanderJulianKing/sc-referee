from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator
from sc_referee_evaluation.review_semantic_payload_v2 import (
    build_stage1_batch_output_schema_v2,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_stage1_recovery_calibration import (
    CALIBRATION_RELATIVE,
    EXPECTED_CALIBRATION_VERDICTS,
    SOURCE_PANEL_LEDGER_DIGEST,
    build_first_direct_stage1_recovery_calibration,
)
from scripts.build_first_direct_three_case_stage1_protocol import (
    CANONICAL_ISSUE_CLASS,
    CASE_IDS,
    REVIEW_RELATIVE,
)
from scripts.record_first_direct_stage1_recovery_calibration import (
    EXPECTED_CLAUDE_UI,
    build_claude_app_recovery_calibration_capture,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RECOVERY_ROOT = PROJECT_ROOT / CALIBRATION_RELATIVE


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(path: Path, digest_field: str) -> dict[str, Any]:
    record = _load(path)
    supplied = record.pop(digest_field)
    assert supplied == semantic_digest(record)
    record[digest_field] = supplied
    return record


def _semantic_review(verdict: str, questions: list[str]) -> dict[str, Any]:
    positive = verdict == "demonstrated_issue"
    return {
        "case_id": CASE_IDS[0],
        "verdict": verdict,
        "bounded_statement": "Bounded issue." if positive else None,
        "root_cause": "Narrow cause." if positive else None,
        "issue_class": CANONICAL_ISSUE_CLASS if positive else None,
        "evidence_atoms": [
            {
                "description": "Visible evidence.",
                "source_spans": [
                    {
                        "path": "task.md",
                        "start_line": 1,
                        "end_line": 1,
                        "quoted_text": "Visible task.",
                    }
                ],
            }
        ],
        "counterevidence_atoms": [
            {
                "description": "Visible counterevidence.",
                "source_spans": [
                    {
                        "path": "results/report.md",
                        "start_line": 1,
                        "end_line": 1,
                        "quoted_text": "Visible report.",
                    }
                ],
            }
        ],
        "falsification_attempt": "Test the strongest innocent explanation.",
        "cross_case_evidence_used": False,
        "unresolved_material_questions": questions,
        "self_reported_confidence": "high",
    }


def test_v2_schema_rejects_eligible_verdict_with_material_question() -> None:
    participant_id = "actor:test-reviewer"
    schema = build_stage1_batch_output_schema_v2(
        participant_id, [CASE_IDS[0]], CANONICAL_ISSUE_CLASS
    )
    eligible = {
        "reviewer_participant_id": participant_id,
        "reviews": [
            _semantic_review(
                "no_demonstrated_issue_within_scope",
                ["Could this reverse the verdict?"],
            )
        ],
    }
    assert list(Draft202012Validator(schema).iter_errors(eligible))

    conditional = deepcopy(eligible)
    conditional["reviews"][0]["verdict"] = "conditional_or_unknown"
    assert not list(Draft202012Validator(schema).iter_errors(conditional))


def test_recovery_freezes_the_exact_source_failure_and_fresh_panel() -> None:
    source_panel = _replay(
        PROJECT_ROOT / REVIEW_RELATIVE / "STAGE1_PANEL_LEDGER.json", "ledger_digest"
    )
    assert source_panel["ledger_digest"] == SOURCE_PANEL_LEDGER_DIGEST

    blocker = _replay(RECOVERY_ROOT / "STAGE1_LABEL_INELIGIBILITY_LEDGER.json", "ledger_digest")
    enrollment = _replay(RECOVERY_ROOT / "PARTICIPANT_ENROLLMENT.json", "enrollment_digest")
    calibration = _replay(RECOVERY_ROOT / "CALIBRATION_PROTOCOL.json", "protocol_digest")
    amendment = _replay(RECOVERY_ROOT / "RECOVERY_AMENDMENT.json", "amendment_digest")

    assert blocker["source_stage1_panel_ledger_digest"] == SOURCE_PANEL_LEDGER_DIGEST
    assert blocker["review_count"] == 12
    assert blocker["blocking_review_count"] == 4
    assert blocker["unresolved_material_question_count"] == 5
    assert blocker["label_eligibility"] == "blocked"
    assert blocker["scientific_label_count"] == blocker["detector_outcome_count"] == 0

    participants = enrollment["participants"]
    participant_ids = [str(item["participant_id"]) for item in participants]
    contexts = [str(item["execution_context_id"]) for item in participants]
    assert len(participant_ids) == len(set(participant_ids)) == 4
    assert len(contexts) == len(set(contexts)) == 4
    source_contexts = {
        str(item["execution_context_id"])
        for item in _load(
            PROJECT_ROOT
            / "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/reviewer-calibration-v4-app/PARTICIPANT_ENROLLMENT.json"
        )["participants"]
    }
    assert not set(contexts) & source_contexts
    for participant in participants:
        supplied = participant.pop("configuration_digest")
        assert supplied == semantic_digest(participant)
        participant["configuration_digest"] = supplied

    assert calibration["expected_verdicts"] == EXPECTED_CALIBRATION_VERDICTS
    assert len(calibration["assignments"]) == 4
    assert calibration["participant_enrollment_digest"] == enrollment["enrollment_digest"]
    for assignment in calibration["assignments"]:
        assert sha256_digest(assignment["prompt"]) == assignment["prompt_digest"]
        assert semantic_digest(assignment["output_schema"]) == assignment["output_schema_digest"]
        assert assignment["participant_id"] in assignment["prompt"]

    assert amendment["source_label_ineligibility_ledger_digest"] == blocker["ledger_digest"]
    assert amendment["recovery_participant_enrollment_digest"] == enrollment["enrollment_digest"]
    assert amendment["recovery_calibration_protocol_digest"] == calibration["protocol_digest"]
    assert amendment["semantic_contract"]["eligible_verdict_requires_empty_array"] is True
    assert amendment["scientific_label_count"] == amendment["detector_outcome_count"] == 0


def test_recovery_calibration_builder_is_write_once() -> None:
    before = sha256_digest((RECOVERY_ROOT / "RECOVERY_AMENDMENT.json").read_bytes())
    with pytest.raises(ValueError, match="already exists"):
        build_first_direct_stage1_recovery_calibration(PROJECT_ROOT)
    assert sha256_digest((RECOVERY_ROOT / "RECOVERY_AMENDMENT.json").read_bytes()) == before


def test_claude_recovery_calibration_capture_binds_frozen_ui() -> None:
    capture = build_claude_app_recovery_calibration_capture(
        PROJECT_ROOT,
        "actor:stage1-recovery-claude-01",
        "{}",
        started_at="2026-08-05T07:21:00Z",
        completed_at="2026-08-05T07:22:00Z",
        captured_at="2026-08-05T07:22:01Z",
    )
    supplied = capture.pop("capture_digest")
    assert supplied == semantic_digest(capture)
    assert capture["transport"]["ui_evidence"] == EXPECTED_CLAUDE_UI
    assert capture["transport"]["conversation_url"] == "claude.ai/new?incognito="

    with pytest.raises(ValueError, match="only a frozen Claude"):
        build_claude_app_recovery_calibration_capture(
            PROJECT_ROOT,
            "actor:stage1-recovery-codex-01",
            "{}",
            started_at="2026-08-05T07:21:00Z",
            completed_at="2026-08-05T07:22:00Z",
        )
