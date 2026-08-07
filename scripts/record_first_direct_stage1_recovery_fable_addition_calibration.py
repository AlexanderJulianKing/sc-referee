from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage1_recovery_calibration import (
    EXPECTED_CALIBRATION_VERDICTS,
)
from scripts.build_first_direct_stage1_recovery_fable_addition_calibration import (
    FABLE_ADDITION_RELATIVE,
)
from scripts.run_first_direct_reviewer_calibration import validate_calibration_response

PARTICIPANT_IDS = (
    "actor:stage1-recovery-fable-01",
    "actor:stage1-recovery-fable-02",
)

# Set only after the prospective protocol builder reports the exact replayed self-digest.
PROTOCOL_DIGEST: str | None = (
    "sha256:ac0ca6426804afcf3a1c10a1685ec12ea47b63ddfeea2d29cddebced10a48d0a"
)


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected one JSON object at {path}.")
    return cast(dict[str, Any], value)


def _expected_protocol_digest() -> str:
    if PROTOCOL_DIGEST is None:
        raise ValueError(
            "The Fable addition calibration protocol digest has not been frozen in the recorder."
        )
    return PROTOCOL_DIGEST


def _protocol(project_root: Path) -> dict[str, Any]:
    protocol = _load(project_root / FABLE_ADDITION_RELATIVE / "CALIBRATION_PROTOCOL.json")
    supplied = protocol.pop("protocol_digest", None)
    if supplied != _expected_protocol_digest() or supplied != semantic_digest(protocol):
        raise ValueError("The Fable addition calibration protocol does not replay.")
    protocol["protocol_digest"] = supplied
    assignments = protocol.get("assignments")
    if not isinstance(assignments, list):
        raise ValueError("The Fable addition calibration assignments are unavailable.")
    by_participant = {str(item.get("participant_id")): item for item in assignments}
    if (
        protocol.get("execution_state") != "frozen_not_started"
        or tuple(sorted(by_participant)) != PARTICIPANT_IDS
        or len(assignments) != 2
        or any(item.get("provider") != "Anthropic" for item in assignments)
        or protocol.get("expected_verdicts") != EXPECTED_CALIBRATION_VERDICTS
        or protocol.get("scientific_label_count", 0) != 0
        or protocol.get("detector_outcome_count", 0) != 0
    ):
        raise ValueError("The Fable addition calibration protocol state is invalid.")
    for participant_id, assignment in by_participant.items():
        if assignment.get("participant_id") != participant_id:
            raise ValueError("A Fable addition assignment participant binding is invalid.")
        schema = assignment.get("output_schema")
        if not isinstance(schema, dict):
            raise ValueError("A Fable addition assignment lacks its strict output schema.")
        Draft202012Validator.check_schema(schema)
        if assignment.get("output_schema_digest") != semantic_digest(schema):
            raise ValueError("A Fable addition assignment output schema does not replay.")
        prompt = assignment.get("prompt")
        if not isinstance(prompt, str) or assignment.get("prompt_digest") != sha256_digest(prompt):
            raise ValueError("A Fable addition assignment prompt does not replay.")
    return protocol


def build_fable_addition_calibration_capture(
    project_root: Path,
    participant_id: str,
    raw_response: str,
    *,
    started_at: str,
    completed_at: str,
    captured_at: str | None = None,
    transport: dict[str, Any],
) -> dict[str, Any]:
    protocol = _protocol(project_root)
    assignments = {str(item["participant_id"]): item for item in protocol["assignments"]}
    assignment = assignments.get(participant_id)
    if assignment is None:
        raise ValueError(f"Unknown Fable addition participant: {participant_id}")
    capture: dict[str, Any] = {
        "artifact_kind": (
            "direct_qualification_stage1_recovery_fable_addition_calibration_capture"
        ),
        "capture_version": "1.0.0",
        "protocol_digest": protocol["protocol_digest"],
        "participant_id": participant_id,
        "call_identity_id": assignment["call_identity_id"],
        "configuration_digest": assignment["configuration_digest"],
        "execution_context_id": assignment["execution_context_id"],
        "prompt_digest": assignment["prompt_digest"],
        "raw_response": raw_response,
        "raw_response_digest": sha256_digest(raw_response),
        "started_at": started_at,
        "completed_at": completed_at,
        "captured_at": captured_at or _now(),
        "transport": transport,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "qualification_authority": "none_calibration_capture_only",
    }
    capture["capture_digest"] = semantic_digest(capture)
    return capture


def _evaluate_capture(assignment: dict[str, Any], capture_path: Path) -> dict[str, Any]:
    capture_bytes = capture_path.read_bytes()
    capture = _load(capture_path)
    supplied = capture.pop("capture_digest", None)
    if supplied != semantic_digest(capture):
        raise ValueError(f"Calibration capture drifted for {assignment['participant_id']}.")
    capture["capture_digest"] = supplied
    participant_id = str(assignment["participant_id"])
    for field in (
        "participant_id",
        "call_identity_id",
        "configuration_digest",
        "execution_context_id",
        "prompt_digest",
    ):
        if capture.get(field) != assignment.get(field):
            raise ValueError(f"Calibration capture binding drift: {participant_id} {field}.")

    raw_response = capture.get("raw_response")
    parse_error = None
    response: Any = None
    if not isinstance(raw_response, str):
        parse_error = "raw_response_not_text"
    elif capture.get("raw_response_digest") != sha256_digest(raw_response):
        parse_error = "raw_response_digest_mismatch"
    else:
        try:
            if raw_response.strip().startswith("```"):
                raise ValueError("response_is_fenced")
            response = json.loads(raw_response)
        except (ValueError, json.JSONDecodeError) as error:
            parse_error = f"{type(error).__name__}:{error}"
    evaluation = (
        validate_calibration_response(response, assignment, EXPECTED_CALIBRATION_VERDICTS)
        if parse_error is None and response is not None
        else {
            "structured_output_schema_valid": False,
            "calibration_case_set_complete": False,
            "exact_expected_verdict_count": 0,
            "invented_material_premise_count": 0,
            "pass": False,
            "reason_codes": [parse_error or "response_unavailable"],
        }
    )
    return {
        "participant_id": participant_id,
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
        "response_digest": semantic_digest(response) if isinstance(response, dict) else None,
        "transcript_digest": capture["raw_response_digest"],
        "parse_error": parse_error,
        "calibration_evaluation": evaluation,
        "calibration_status": "passed" if evaluation["pass"] else "failed",
        "started_at": capture["started_at"],
        "completed_at": capture["completed_at"],
        "captured_at": capture["captured_at"],
    }


def record_first_direct_stage1_recovery_fable_addition_calibration(
    project_root: Path,
) -> dict[str, Any]:
    protocol = _protocol(project_root)
    root = project_root / FABLE_ADDITION_RELATIVE
    incoming_root = root / "incoming"
    assignments = {str(item["participant_id"]): item for item in protocol["assignments"]}
    expected_paths = {
        participant_id: incoming_root / f"{participant_id.removeprefix('actor:')}.json"
        for participant_id in assignments
    }
    missing = [str(path) for path in expected_paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Fable addition calibration captures: {missing}")
    extra = sorted(
        path.name for path in incoming_root.glob("*.json") if path not in expected_paths.values()
    )
    if extra:
        raise ValueError(f"Unexpected Fable addition calibration captures: {extra}")
    ledger_path = root / "CALIBRATION_LEDGER.json"
    if ledger_path.exists() or ledger_path.is_symlink():
        raise FileExistsError("The Fable addition calibration ledger already exists.")

    entries = [
        _evaluate_capture(assignments[participant_id], expected_paths[participant_id])
        for participant_id in sorted(assignments)
    ]
    ledger: dict[str, Any] = {
        "artifact_kind": ("direct_qualification_stage1_recovery_fable_addition_calibration_ledger"),
        "ledger_version": "1.0.0",
        "protocol_digest": protocol["protocol_digest"],
        "participant_enrollment_digest": protocol["participant_enrollment_digest"],
        "entries": entries,
        "summary": {
            "assigned_reviewer_count": 2,
            "retained_attempt_count": 2,
            "passed_count": sum(item["calibration_status"] == "passed" for item in entries),
            "failed_count": sum(item["calibration_status"] != "passed" for item in entries),
            "all_assigned_attempts_retained": True,
            "replacement_count": 0,
            "all_reviewer_configurations_passed": all(
                item["calibration_status"] == "passed" for item in entries
            ),
        },
        "sealed_at": max(str(item["captured_at"]) for item in entries),
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "qualification_authority": "none_reviewer_calibration_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(ledger_path, ledger)
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    ledger = record_first_direct_stage1_recovery_fable_addition_calibration(
        arguments.project_root.resolve()
    )
    print(ledger["ledger_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
