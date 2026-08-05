from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, cast

from sc_referee_evaluation.direct_qualification_lane import validate_participant_enrollment

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_app_reviewer_calibration import (
    APP_CALIBRATION_RELATIVE,
    APP_ENVIRONMENT,
    APP_TOOL_POLICY,
    build_first_direct_app_reviewer_calibration,
)
from scripts.build_first_direct_reviewer_calibration_protocol import (
    load_effective_execution_configuration,
)
from scripts.record_first_direct_app_reviewer_calibration import (
    EXPECTED_UI_EVIDENCE,
    parse_app_calibration_response,
    validate_app_capture_input,
)


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_frozen_app_reviewer_calibration_rebuilds_exactly(project_root: Path) -> None:
    rebuilt = build_first_direct_app_reviewer_calibration(project_root)
    for name, artifact in rebuilt.items():
        assert artifact == _load(project_root / APP_CALIBRATION_RELATIVE / name)

    enrollment = validate_participant_enrollment(rebuilt["PARTICIPANT_ENROLLMENT.json"])
    replacement = rebuilt["ADJUDICATION_PROTOCOL_AMENDMENT.json"]
    protocol = rebuilt["CALIBRATION_PROTOCOL.json"]
    replacement_digest = replacement.pop("amendment_digest")
    protocol_digest = protocol.pop("protocol_digest")
    assert replacement_digest == semantic_digest(replacement)
    assert protocol_digest == semantic_digest(protocol)
    assert enrollment["enrollment_digest"] == replacement["replacement_enrollment_digest"]


def test_app_enrollment_changes_only_three_unexposed_claude_reviewers(
    project_root: Path,
) -> None:
    artifacts = build_first_direct_app_reviewer_calibration(project_root)
    original = _load(
        project_root
        / "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/"
        "PARTICIPANT_ENROLLMENT.json"
    )
    replacement = artifacts["PARTICIPANT_ENROLLMENT.json"]
    amendment = artifacts["ADJUDICATION_PROTOCOL_AMENDMENT.json"]
    original_by_id = {item["participant_id"]: item for item in original["participants"]}
    replacement_by_id = {item["participant_id"]: item for item in replacement["participants"]}
    changed = {
        participant_id
        for participant_id in original_by_id
        if original_by_id[participant_id] != replacement_by_id[participant_id]
    }

    assert changed == {
        "actor:stage1-claude-01",
        "actor:stage1-claude-02",
        "actor:stage2-claude-01",
    }
    assert changed == set(amendment["replaced_participant_ids"])
    assert amendment["precase_state"] == {
        "author_brief_exposure_count": 0,
        "authored_case_count": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
    }
    assert amendment["qualification_authority"] == ("none_adjudication_protocol_amendment_only")
    for participant_id in changed:
        participant = replacement_by_id[participant_id]
        assert participant["agent_surface"] == "Claude Desktop App chat"
        assert participant["agent_version"] == "1.25927.0"
        assert participant["model_id"] == "claude-opus-5"
        assert participant["reasoning_configuration"] == "extra"
        assert participant["tool_policy_digest"] == semantic_digest(APP_TOOL_POLICY)
        assert participant["environment_digest"] == semantic_digest(APP_ENVIRONMENT)


def test_app_protocol_freezes_three_fresh_tool_free_contexts_without_case_exposure(
    project_root: Path,
) -> None:
    protocol = build_first_direct_app_reviewer_calibration(project_root)[
        "CALIBRATION_PROTOCOL.json"
    ]
    assignments = protocol["assignments"]

    assert len(assignments) == 3
    assert Counter(item["role"] for item in assignments) == {
        "stage1_reviewer": 2,
        "stage2_reviewer": 1,
    }
    assert len({item["call_identity_id"] for item in assignments}) == 3
    assert len({item["execution_context_id"] for item in assignments}) == 3
    assert len(protocol["retained_pass_refs"]) == 3
    assert protocol["execution_policy"] == {
        "one_fresh_chat_per_assignment": True,
        "incognito_chat_required": True,
        "one_attempt_per_assignment": True,
        "replacement_permitted": False,
        "all_attempts_retained": True,
        "parallel_execution_required": False,
        "repository_or_project_context_permitted": False,
        "tools_or_connectors_permitted": False,
        "external_information_permitted": False,
        "response_capture": "full_visible_assistant_response_and_conversation_url",
    }
    for assignment in assignments:
        assert assignment["app_prompt_digest"] == sha256_digest(assignment["app_prompt"])
        assert assignment["output_schema_digest"] == semantic_digest(assignment["output_schema"])
        assert assignment["interaction_profile"]["model_menu_label"] == "Opus 5"
        assert assignment["interaction_profile"]["effort_menu_label"] == "Extra"
        assert assignment["interaction_profile"]["incognito"] is True
        assert "expected_verdict" not in assignment["app_prompt"]
        assert "case:" not in assignment["app_prompt"]
        assert "held-out" not in assignment["app_prompt"].casefold()
        assert "detector output" not in assignment["app_prompt"].casefold()
    assert protocol["execution_state"] == "frozen_not_started"
    assert protocol["qualification_authority"] == "none_reviewer_calibration_only"
    assert "scientific_label" not in protocol
    assert "detector_outcome" not in protocol
    assert "finding" not in protocol


def test_app_protocol_preserves_lane_and_failure_history(project_root: Path) -> None:
    protocol = build_first_direct_app_reviewer_calibration(project_root)[
        "CALIBRATION_PROTOCOL.json"
    ]

    assert protocol["lane_freeze_digest"] == (
        "sha256:c58ee57c01d5f7c46855eb9f554d0a476f664e44edbdd7e15679bd53d72fa12b"
    )
    assert protocol["supersedes_protocol_digest"] == (
        "sha256:dc359b6884308ecc02b391d499f22c784bed5e71f258c8420eab95dae8dc4cc7"
    )
    assert protocol["retained_v3_failure_ledger_digest"] == (
        "sha256:375265c9dc05186c74c58c4658c20a2877011db476bcebc0a7281658a54f2893"
    )
    assert protocol["retained_v3_aggregate_ledger_digest"] == (
        "sha256:3da48f5fead855cd4685448f2f550b71b77ec1e366737381429c3874e00b9fa5"
    )


def test_app_capture_requires_exact_unfenced_json_and_ui_evidence(project_root: Path) -> None:
    protocol = build_first_direct_app_reviewer_calibration(project_root)[
        "CALIBRATION_PROTOCOL.json"
    ]
    assignment = protocol["assignments"][0]
    config = load_effective_execution_configuration(project_root)
    expected = {
        str(item["calibration_case_id"]): str(item["expected_verdict"])
        for item in config["reviewer_calibration_suite"]["vignettes"]
    }
    response = {
        "reviewer_participant_id": assignment["participant_id"],
        "calibration_results": [
            {
                "calibration_case_id": case_id,
                "verdict": verdict,
                "invented_material_premise": False,
                "evidence_basis": "stated_evidence_only",
                "rationale": "This uses only the stated evidence.",
            }
            for case_id, verdict in expected.items()
        ],
    }
    raw_response = json.dumps(response, sort_keys=True)
    assert parse_app_calibration_response(raw_response) == response
    capture = {
        "participant_id": assignment["participant_id"],
        "call_identity_id": assignment["call_identity_id"],
        "conversation_url": "claude.ai/chat/opaque-app-calibration-context",
        "started_at": "2026-08-05T00:27:00Z",
        "completed_at": "2026-08-05T00:28:00Z",
        "raw_response": raw_response,
        "ui_evidence": EXPECTED_UI_EVIDENCE,
    }

    evaluated = validate_app_capture_input(capture, assignment, expected)
    assert evaluated["pass"] is True
    assert evaluated["reason_codes"] == []

    fenced = dict(capture)
    fenced["raw_response"] = f"```json\n{raw_response}\n```"
    evaluated = validate_app_capture_input(fenced, assignment, expected)
    assert evaluated["pass"] is False
    assert "response_parse_failed" in evaluated["reason_codes"]

    wrong_ui = json.loads(json.dumps(capture))
    wrong_ui["ui_evidence"]["incognito"] = False
    evaluated = validate_app_capture_input(wrong_ui, assignment, expected)
    assert evaluated["pass"] is False
    assert "ui_evidence_mismatch" in evaluated["reason_codes"]
