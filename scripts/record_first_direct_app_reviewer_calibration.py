from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_app_reviewer_calibration import (
    APP_CALIBRATION_RELATIVE,
    V1_LEDGER_DIGEST,
    V2_LEDGER_DIGEST,
    V3_LEDGER_DIGEST,
)
from scripts.build_first_direct_reviewer_calibration_protocol import (
    FAILED_CALIBRATION_RELATIVE,
    PARTIAL_CALIBRATION_RELATIVE,
    load_effective_execution_configuration,
)
from scripts.run_first_direct_reviewer_calibration import validate_calibration_response

EXPECTED_UI_EVIDENCE = {
    "application": "Claude Desktop App",
    "application_version": "1.25927.0",
    "surface": "Home Chat",
    "model_label": "Opus 5",
    "effort_label": "Extra",
    "incognito": True,
    "account_history_saved": False,
    "memory_enabled": False,
    "file_upload_count": 0,
    "visible_tool_or_connector_call_count": 0,
    "capture_method": "Codex Computer Use accessibility state",
}

EXPECTED_INCOGNITO_CONVERSATION_ROUTE = "claude.ai/new?incognito="
CAPTURE_TRANSPORT_AMENDMENT_FILENAME = "CAPTURE_TRANSPORT_AMENDMENT.json"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], digest_field: str, expected: str, label: str) -> None:
    supplied = record.pop(digest_field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[digest_field] = supplied


def parse_app_calibration_response(raw_response: str) -> dict[str, Any]:
    stripped = raw_response.strip()
    if not stripped or stripped.startswith("```") or not stripped.startswith("{"):
        raise ValueError("The app response is not one unfenced JSON object.")
    parsed = json.loads(stripped)
    if not isinstance(parsed, dict):
        raise ValueError("The app response is not one JSON object.")
    return cast(dict[str, Any], parsed)


def validate_app_capture_input(
    capture: dict[str, Any], assignment: dict[str, Any], expected_verdicts: dict[str, str]
) -> dict[str, Any]:
    required = {
        "participant_id",
        "call_identity_id",
        "conversation_url",
        "started_at",
        "completed_at",
        "raw_response",
        "ui_evidence",
    }
    reasons = []
    if set(capture) != required:
        reasons.append("capture_field_set_mismatch")
    if capture.get("participant_id") != assignment["participant_id"]:
        reasons.append("participant_id_mismatch")
    if capture.get("call_identity_id") != assignment["call_identity_id"]:
        reasons.append("call_identity_id_mismatch")
    conversation_url = capture.get("conversation_url")
    if conversation_url != EXPECTED_INCOGNITO_CONVERSATION_ROUTE:
        reasons.append("conversation_url_invalid")
    if capture.get("ui_evidence") != EXPECTED_UI_EVIDENCE:
        reasons.append("ui_evidence_mismatch")
    response = None
    parse_error = None
    raw_response = capture.get("raw_response")
    if isinstance(raw_response, str):
        try:
            response = parse_app_calibration_response(raw_response)
        except (ValueError, json.JSONDecodeError) as error:
            parse_error = f"{type(error).__name__}:{error}"
            reasons.append("response_parse_failed")
    else:
        reasons.append("raw_response_not_text")
    response_evaluation: dict[str, Any] = (
        validate_calibration_response(response, assignment, expected_verdicts)
        if response is not None
        else {
            "structured_output_schema_valid": False,
            "calibration_case_set_complete": False,
            "exact_expected_verdict_count": 0,
            "invented_material_premise_count": 0,
            "pass": False,
            "reason_codes": [parse_error or "response_unavailable"],
        }
    )
    response_reasons = response_evaluation.get("reason_codes")
    if not isinstance(response_reasons, list):
        raise TypeError("Calibration response reason_codes must be a list.")
    reasons.extend(str(item) for item in response_reasons)
    return {
        "response": response,
        "response_evaluation": response_evaluation,
        "parse_error": parse_error,
        "pass": not reasons and response_evaluation["pass"] is True,
        "reason_codes": reasons,
    }


def record_first_direct_app_reviewer_calibration(project_root: Path) -> dict[str, Any]:
    root = project_root / APP_CALIBRATION_RELATIVE
    protocol = _load(root / "CALIBRATION_PROTOCOL.json")
    protocol_digest = protocol.pop("protocol_digest", None)
    if protocol_digest != semantic_digest(protocol):
        raise ValueError("The app calibration protocol does not replay.")
    protocol["protocol_digest"] = protocol_digest
    if (
        protocol["protocol_version"] != "4.0.0"
        or protocol["execution_state"] != "frozen_not_started"
        or protocol["qualification_authority"] != "none_reviewer_calibration_only"
    ):
        raise ValueError("Unsupported app calibration protocol.")
    transport_amendment = _load(root / CAPTURE_TRANSPORT_AMENDMENT_FILENAME)
    transport_amendment_digest = transport_amendment.pop("amendment_digest", None)
    if transport_amendment_digest != semantic_digest(transport_amendment):
        raise ValueError("The capture transport amendment does not replay.")
    transport_amendment["amendment_digest"] = transport_amendment_digest
    if (
        transport_amendment["calibration_protocol_digest"] != protocol_digest
        or transport_amendment["observed_incognito_route"] != EXPECTED_INCOGNITO_CONVERSATION_ROUTE
        or transport_amendment["scientific_rubric_changed"] is not False
        or transport_amendment["qualification_authority"] != "none_capture_transport_amendment_only"
    ):
        raise ValueError("The capture transport amendment binding has drifted.")
    enrollment = _load(root / "PARTICIPANT_ENROLLMENT.json")
    enrollment_digest = enrollment.pop("enrollment_digest", None)
    if enrollment_digest != semantic_digest(enrollment):
        raise ValueError("The replacement enrollment does not replay.")
    enrollment["enrollment_digest"] = enrollment_digest
    if enrollment_digest != protocol["replacement_enrollment_digest"]:
        raise ValueError("The app calibration enrollment binding has drifted.")

    assignments = {str(item["participant_id"]): item for item in protocol["assignments"]}
    incoming_root = root / "incoming"
    expected_paths = {
        participant_id: incoming_root / f"{participant_id.removeprefix('actor:')}.json"
        for participant_id in assignments
    }
    missing = [str(path) for path in expected_paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing retained app calibration inputs: {missing}")
    extra = sorted(
        path.name for path in incoming_root.glob("*.json") if path not in expected_paths.values()
    )
    if extra:
        raise ValueError(f"Unexpected app calibration inputs: {extra}")
    ledger_path = root / "CALIBRATION_LEDGER.json"
    aggregate_path = root / "AGGREGATE_CALIBRATION_LEDGER.json"
    if ledger_path.exists() or aggregate_path.exists():
        raise FileExistsError("Refusing to overwrite retained app calibration evidence.")

    config = load_effective_execution_configuration(project_root)
    expected_verdicts = {
        str(item["calibration_case_id"]): str(item["expected_verdict"])
        for item in config["reviewer_calibration_suite"]["vignettes"]
    }
    entries = []
    for participant_id, assignment in sorted(assignments.items()):
        path = expected_paths[participant_id]
        raw_bytes = path.read_bytes()
        capture = cast(dict[str, Any], json.loads(raw_bytes))
        validation = validate_app_capture_input(capture, assignment, expected_verdicts)
        response = validation.pop("response")
        response_evaluation = validation.pop("response_evaluation")
        raw_response = capture.get("raw_response")
        response_digest = semantic_digest(response) if isinstance(response, dict) else None
        transcript_digest = semantic_digest(
            {
                "app_prompt_digest": assignment["app_prompt_digest"],
                "raw_response_digest": sha256_digest(
                    raw_response if isinstance(raw_response, str) else b""
                ),
                "response_digest": response_digest,
                "conversation_url": capture.get("conversation_url"),
                "ui_evidence": capture.get("ui_evidence"),
            }
        )
        entries.append(
            {
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
                "conversation_url": capture.get("conversation_url"),
                "provider_app_authenticated_success": bool(
                    validation["pass"] or capture.get("conversation_url")
                ),
                "input_capture_digest": sha256_digest(raw_bytes),
                "response_digest": response_digest,
                "transcript_digest": transcript_digest,
                "calibration_evaluation": response_evaluation,
                "capture_evaluation": validation,
                "calibration_status": "passed" if validation["pass"] else "failed",
                "started_at": capture.get("started_at"),
                "completed_at": capture.get("completed_at"),
            }
        )
    call_identity_ids = [str(item["call_identity_id"]) for item in entries]
    if len(call_identity_ids) != len(set(call_identity_ids)):
        raise ValueError("App calibration call identities are not distinct.")

    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_app_reviewer_calibration_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": protocol_digest,
        "capture_transport_amendment_digest": transport_amendment_digest,
        "replacement_enrollment_digest": enrollment_digest,
        "entries": entries,
        "summary": {
            "assigned_reviewer_count": 3,
            "retained_attempt_count": 3,
            "passed_count": sum(item["calibration_status"] == "passed" for item in entries),
            "failed_count": sum(item["calibration_status"] != "passed" for item in entries),
            "all_assigned_attempts_retained": True,
            "replacement_count": 0,
            "all_app_reviewer_configurations_passed": all(
                item["calibration_status"] == "passed" for item in entries
            ),
        },
        "sealed_at": max(str(item["completed_at"]) for item in entries),
        "qualification_authority": "none_reviewer_calibration_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)

    initial_ledger = _load(project_root / FAILED_CALIBRATION_RELATIVE / "CALIBRATION_LEDGER.json")
    _replay(initial_ledger, "ledger_digest", V1_LEDGER_DIGEST, "Protocol-v1 ledger")
    partial_ledger = _load(project_root / PARTIAL_CALIBRATION_RELATIVE / "CALIBRATION_LEDGER.json")
    _replay(partial_ledger, "ledger_digest", V2_LEDGER_DIGEST, "Protocol-v2 ledger")
    v3_ledger = _load(
        project_root
        / "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/"
        "reviewer-calibration-v3/CALIBRATION_LEDGER.json"
    )
    _replay(v3_ledger, "ledger_digest", V3_LEDGER_DIGEST, "Protocol-v3 ledger")
    retained_codex = [
        {
            **item,
            "calibration_evidence_source": "retained_protocol_v2_pass",
            "source_ledger_digest": V2_LEDGER_DIGEST,
        }
        for item in partial_ledger["entries"]
        if item["provider"] == "OpenAI" and item["calibration_status"] == "passed"
    ]
    current_app = [
        {
            **item,
            "calibration_evidence_source": "protocol_v4_app_attempt",
            "source_ledger_digest": ledger["ledger_digest"],
        }
        for item in entries
    ]
    active_entries = sorted(
        [*retained_codex, *current_app], key=lambda item: str(item["participant_id"])
    )
    active_ids = [str(item["participant_id"]) for item in active_entries]
    if len(active_ids) != 6 or len(active_ids) != len(set(active_ids)):
        raise ValueError("The active reviewer calibration set is not an exact six-member panel.")
    if Counter(str(item["role"]) for item in active_entries) != {
        "stage1_reviewer": 4,
        "stage2_reviewer": 2,
    } or Counter(str(item["provider"]) for item in active_entries) != {
        "Anthropic": 3,
        "OpenAI": 3,
    }:
        raise ValueError("The active reviewer calibration panel shape has drifted.")

    historical_entries = [
        *initial_ledger["entries"],
        *partial_ledger["entries"],
        *v3_ledger["entries"],
        *entries,
    ]
    aggregate: dict[str, Any] = {
        "artifact_kind": "direct_qualification_active_reviewer_calibration_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": protocol_digest,
        "capture_transport_amendment_digest": transport_amendment_digest,
        "replacement_enrollment_digest": enrollment_digest,
        "source_ledger_digests": [
            V1_LEDGER_DIGEST,
            V2_LEDGER_DIGEST,
            V3_LEDGER_DIGEST,
            ledger["ledger_digest"],
        ],
        "entries": active_entries,
        "summary": {
            "expected_reviewer_count": 6,
            "active_configuration_evidence_count": 6,
            "retained_v2_pass_count": len(retained_codex),
            "new_v4_app_attempt_count": len(current_app),
            "active_passed_count": sum(
                item["calibration_status"] == "passed" for item in active_entries
            ),
            "active_failed_count": sum(
                item["calibration_status"] != "passed" for item in active_entries
            ),
            "historical_attempt_count_across_protocols": len(historical_entries),
            "historical_failed_attempt_count": sum(
                item["calibration_status"] != "passed" for item in historical_entries
            ),
            "current_protocol_replacement_count": 0,
            "all_active_reviewer_configurations_passed": all(
                item["calibration_status"] == "passed" for item in active_entries
            ),
        },
        "sealed_at": ledger["sealed_at"],
        "qualification_authority": "none_reviewer_calibration_only",
    }
    aggregate["ledger_digest"] = semantic_digest(aggregate)
    ledger_path.write_text(
        json.dumps(ledger, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    aggregate_path.write_text(
        json.dumps(aggregate, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return aggregate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    aggregate = record_first_direct_app_reviewer_calibration(args.project_root.resolve())
    print(json.dumps(aggregate["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
