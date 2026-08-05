from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage1_recovery_calibration import CALIBRATION_RELATIVE
from scripts.build_first_direct_stage1_recovery_claude_replacement_calibration import (
    REPLACEMENT_PARTICIPANT_ID,
    REPLACEMENT_RELATIVE,
    SOURCE_LEDGER_DIGEST,
)
from scripts.record_first_direct_stage1_recovery_calibration import (
    EXPECTED_CLAUDE_UI,
)
from scripts.run_first_direct_reviewer_calibration import validate_calibration_response


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _protocol(project_root: Path) -> dict[str, Any]:
    protocol = _load(project_root / REPLACEMENT_RELATIVE / "CALIBRATION_PROTOCOL.json")
    supplied = protocol.pop("protocol_digest", None)
    if supplied != semantic_digest(protocol):
        raise ValueError("The replacement calibration protocol does not replay.")
    protocol["protocol_digest"] = supplied
    if (
        protocol["execution_state"] != "frozen_not_started"
        or len(protocol["assignments"]) != 1
        or protocol["assignments"][0]["participant_id"] != REPLACEMENT_PARTICIPANT_ID
    ):
        raise ValueError("The replacement calibration protocol state is invalid.")
    return protocol


def capture_first_direct_stage1_recovery_claude_replacement_calibration(
    project_root: Path,
    raw_response: str,
    *,
    started_at: str,
    completed_at: str,
    captured_at: str,
) -> dict[str, Any]:
    protocol = _protocol(project_root)
    assignment = protocol["assignments"][0]
    capture: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_recovery_replacement_calibration_capture",
        "capture_version": "1.0.0",
        "protocol_digest": protocol["protocol_digest"],
        "participant_id": REPLACEMENT_PARTICIPANT_ID,
        "call_identity_id": assignment["call_identity_id"],
        "configuration_digest": assignment["configuration_digest"],
        "execution_context_id": assignment["execution_context_id"],
        "prompt_digest": assignment["prompt_digest"],
        "raw_response": raw_response,
        "raw_response_digest": sha256_digest(raw_response),
        "started_at": started_at,
        "completed_at": completed_at,
        "captured_at": captured_at,
        "transport": {
            "surface": "Claude Desktop App Home Chat",
            "conversation_url": "claude.ai/new?incognito=",
            "ui_evidence": EXPECTED_CLAUDE_UI,
        },
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "qualification_authority": "none_calibration_capture_only",
    }
    capture["capture_digest"] = semantic_digest(capture)
    return capture


def record_first_direct_stage1_recovery_claude_replacement_calibration(
    project_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol = _protocol(project_root)
    root = project_root / REPLACEMENT_RELATIVE
    capture_path = root / "incoming" / "stage1-recovery-claude-03.json"
    if not capture_path.is_file():
        raise FileNotFoundError("The replacement Claude capture is unavailable.")
    if (root / "CALIBRATION_LEDGER.json").exists() or (
        root / "AGGREGATE_CALIBRATION_LEDGER.json"
    ).exists():
        raise FileExistsError("The replacement calibration was already recorded.")
    capture_bytes = capture_path.read_bytes()
    capture = cast(dict[str, Any], json.loads(capture_bytes))
    supplied = capture.pop("capture_digest", None)
    if supplied != semantic_digest(capture):
        raise ValueError("The replacement Claude capture does not replay.")
    capture["capture_digest"] = supplied
    assignment = protocol["assignments"][0]
    for field in (
        "participant_id",
        "call_identity_id",
        "configuration_digest",
        "execution_context_id",
        "prompt_digest",
    ):
        if capture.get(field) != assignment.get(field):
            raise ValueError(f"Replacement capture binding drift: {field}.")
    raw_response = str(capture["raw_response"])
    response = cast(dict[str, Any], json.loads(raw_response))
    evaluation = validate_calibration_response(response, assignment, protocol["expected_verdicts"])
    entry = {
        "participant_id": REPLACEMENT_PARTICIPANT_ID,
        "role": assignment["role"],
        "provider": assignment["provider"],
        "model_id": assignment["model_id"],
        "agent_surface": assignment["agent_surface"],
        "agent_version": assignment["agent_version"],
        "reasoning_configuration": assignment["reasoning_configuration"],
        "execution_context_id": assignment["execution_context_id"],
        "configuration_digest": assignment["configuration_digest"],
        "call_identity_id": assignment["call_identity_id"],
        "input_capture_digest": sha256_digest(capture_bytes),
        "capture_digest": capture["capture_digest"],
        "response_digest": semantic_digest(response),
        "transcript_digest": capture["raw_response_digest"],
        "parse_error": None,
        "calibration_evaluation": evaluation,
        "calibration_status": "passed" if evaluation["pass"] else "failed",
        "started_at": capture["started_at"],
        "completed_at": capture["completed_at"],
        "captured_at": capture["captured_at"],
    }
    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_recovery_replacement_calibration_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": protocol["protocol_digest"],
        "entries": [entry],
        "summary": {
            "assigned_reviewer_count": 1,
            "retained_attempt_count": 1,
            "passed_count": int(entry["calibration_status"] == "passed"),
            "failed_count": int(entry["calibration_status"] != "passed"),
            "all_assigned_attempts_retained": True,
            "replacement_count": 0,
            "all_reviewer_configurations_passed": entry["calibration_status"] == "passed",
        },
        "sealed_at": capture["captured_at"],
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "qualification_authority": "none_reviewer_calibration_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(root / "CALIBRATION_LEDGER.json", ledger)

    source_ledger = _load(project_root / CALIBRATION_RELATIVE / "CALIBRATION_LEDGER.json")
    source_supplied = source_ledger.pop("ledger_digest", None)
    if source_supplied != SOURCE_LEDGER_DIGEST or source_supplied != semantic_digest(source_ledger):
        raise ValueError("The source calibration ledger does not replay.")
    source_ledger["ledger_digest"] = source_supplied
    active = [item for item in source_ledger["entries"] if item["calibration_status"] == "passed"]
    if entry["calibration_status"] == "passed":
        active.append(entry)
    aggregate: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_recovery_active_calibration_ledger",
        "ledger_version": "1.0.0",
        "source_ledger_digests": [SOURCE_LEDGER_DIGEST, ledger["ledger_digest"]],
        "entries": sorted(active, key=lambda item: str(item["participant_id"])),
        "summary": {
            "active_reviewer_configuration_count": len(active),
            "active_passed_count": sum(item["calibration_status"] == "passed" for item in active),
            "active_failed_count": sum(item["calibration_status"] != "passed" for item in active),
            "historical_attempt_count": 5,
            "historical_failed_attempt_count": 1 + int(entry["calibration_status"] != "passed"),
            "all_active_reviewer_configurations_passed": len(active) == 4
            and all(item["calibration_status"] == "passed" for item in active),
        },
        "sealed_at": capture["captured_at"],
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "qualification_authority": "none_reviewer_calibration_only",
    }
    aggregate["ledger_digest"] = semantic_digest(aggregate)
    write_normalized_json_once(root / "AGGREGATE_CALIBRATION_LEDGER.json", aggregate)
    return ledger, aggregate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--raw-response-base64")
    parser.add_argument("--started-at")
    parser.add_argument("--completed-at")
    parser.add_argument("--captured-at")
    arguments = parser.parse_args()
    project_root = arguments.project_root.resolve()
    if arguments.capture:
        required = (
            arguments.raw_response_base64,
            arguments.started_at,
            arguments.completed_at,
            arguments.captured_at,
        )
        if not all(required):
            raise ValueError("Replacement capture requires response and exact timestamps.")
        raw_response = base64.b64decode(str(arguments.raw_response_base64), validate=True).decode(
            "utf-8"
        )
        capture = capture_first_direct_stage1_recovery_claude_replacement_calibration(
            project_root,
            raw_response,
            started_at=str(arguments.started_at),
            completed_at=str(arguments.completed_at),
            captured_at=str(arguments.captured_at),
        )
        output = project_root / REPLACEMENT_RELATIVE / "incoming/stage1-recovery-claude-03.json"
        write_normalized_json_once(output, capture)
        print(capture["capture_digest"])
    else:
        ledger, aggregate = record_first_direct_stage1_recovery_claude_replacement_calibration(
            project_root
        )
        print(ledger["ledger_digest"], aggregate["ledger_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
