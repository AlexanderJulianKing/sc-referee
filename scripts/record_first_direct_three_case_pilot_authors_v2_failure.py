from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_app_reviewer_calibration import APP_CALIBRATION_RELATIVE
from scripts.build_first_direct_reviewer_calibration_protocol import LANE_RELATIVE
from scripts.build_first_direct_three_case_pilot_authoring import ACTIVE_ENROLLMENT_DIGEST
from scripts.build_first_direct_three_case_pilot_authoring_v2 import (
    PILOT_AUTHORING_V2_RELATIVE,
)
from scripts.record_first_direct_three_case_pilot_authors import PilotAuthorRecordError
from scripts.record_first_direct_three_case_pilot_authors_v2 import (
    PROTOCOL_DIGEST,
    RESTART_AMENDMENT_DIGEST,
    _load,
    _replay,
    parse_author_response,
    validate_v2_author_attempt,
)

CLAUDE_CAPTURE_DIGEST = "sha256:2617a109e25ab871a14ae1236db8220a18a1ad59b512e00318f406b2cc17f973"
CODEX_CAPTURE_DIGEST = "sha256:5b9a17b658f2ea7485085bc27b5a48899ecc4ea55c5cff619c5ae8626df55e43"
COMPLETED_AT = "2026-08-05T04:35:00Z"


def _invalid_line_entries(response: dict[str, Any]) -> list[dict[str, Any]]:
    invalid: list[dict[str, Any]] = []
    for case in cast(list[dict[str, Any]], response["authored_cases"]):
        for file_role in ("input_file", "producer_file", "report_file"):
            lines = cast(list[str], case[file_role]["content_lines"])
            for index, line in enumerate(lines, start=1):
                if "\n" in line or "\r" in line:
                    invalid.append(
                        {
                            "case_id": case["case_id"],
                            "file_role": file_role,
                            "content_line_number": index,
                            "contains_lf": "\n" in line,
                            "contains_cr": "\r" in line,
                        }
                    )
    return invalid


def build_first_direct_three_case_pilot_authors_v2_failure(
    project_root: Path,
) -> dict[str, Any]:
    root = project_root / PILOT_AUTHORING_V2_RELATIVE
    restart = _load(root / "PILOT_AUTHORING_RESTART_AMENDMENT.json")
    _replay(
        restart,
        "amendment_digest",
        RESTART_AMENDMENT_DIGEST,
        "V2 authoring restart amendment",
    )
    protocol = _load(root / "PILOT_AUTHORING_PROTOCOL.json")
    _replay(protocol, "protocol_digest", PROTOCOL_DIGEST, "V2 authoring protocol")
    if protocol["authoring_restart_amendment_digest"] != RESTART_AMENDMENT_DIGEST:
        raise PilotAuthorRecordError("V2 protocol does not bind its restart amendment.")

    enrollment = _load(project_root / APP_CALIBRATION_RELATIVE / "PARTICIPANT_ENROLLMENT.json")
    _replay(
        enrollment,
        "enrollment_digest",
        ACTIVE_ENROLLMENT_DIGEST,
        "Active participant enrollment",
    )
    validators = [
        item for item in enrollment["participants"] if item["role"] == "evidence_validator"
    ]
    if len(validators) != 1:
        raise PilotAuthorRecordError("Active enrollment lacks one evidence validator.")
    validator = validators[0]
    validator_identity = {
        "validator_id": validator["participant_id"],
        "provider": validator["provider"],
        "execution_context_id": validator["execution_context_id"],
        "identity_evidence_digest": validator["configuration_digest"],
    }

    lane = _load(project_root / LANE_RELATIVE / "LANE_FREEZE.json")
    lane_digest = str(lane.get("lane_freeze_digest"))
    _replay(lane, "lane_freeze_digest", lane_digest, "Direct lane freeze")
    envelopes = lane["prospective_protocol"]["envelopes"]
    if len(envelopes) != 1:
        raise PilotAuthorRecordError("Direct lane does not contain one envelope.")

    assignments = protocol["author_assignments"]
    assignment_by_provider = {str(item["participant"]["provider"]): item for item in assignments}
    expected = {
        "Anthropic": (
            root / "incoming" / "pilot-author-claude-02.json",
            CLAUDE_CAPTURE_DIGEST,
        ),
        "OpenAI": (
            root / "incoming" / "pilot-author-codex-02.json",
            CODEX_CAPTURE_DIGEST,
        ),
    }
    if set(assignment_by_provider) != set(expected):
        raise PilotAuthorRecordError("V2 failure recorder expected one author per provider.")

    entries: list[dict[str, Any]] = []
    input_captures: list[dict[str, Any]] = []
    for provider in ("Anthropic", "OpenAI"):
        assignment = assignment_by_provider[provider]
        path, expected_digest = expected[provider]
        capture_bytes = path.read_bytes()
        capture_digest = sha256_digest(capture_bytes)
        if capture_digest != expected_digest:
            raise PilotAuthorRecordError(f"Retained v2 {provider} capture has drifted.")
        attempt = cast(dict[str, Any], json.loads(capture_bytes))
        response = parse_author_response(str(attempt["raw_response"]))
        response_digest = semantic_digest(response)
        raw_response_digest = sha256_digest(str(attempt["raw_response"]).encode("utf-8"))
        schema_errors = sorted(
            Draft202012Validator(assignment["output_schema"]).iter_errors(response), key=str
        )
        if schema_errors:
            raise PilotAuthorRecordError(
                f"Retained v2 {provider} response no longer passes its frozen schema."
            )
        input_captures.append(
            {
                "participant_id": attempt["participant_id"],
                "provider": provider,
                "input_capture_digest": capture_digest,
                "raw_response_digest": raw_response_digest,
                "response_digest": response_digest,
                "attempt_status": attempt["attempt_status"],
                "replacement_count": attempt["replacement_count"],
            }
        )

        if provider == "Anthropic":
            invalid = _invalid_line_entries(response)
            if not invalid:
                raise PilotAuthorRecordError(
                    "Retained v2 Claude response no longer demonstrates the intake failure."
                )
            invalid_by_case = {
                str(case["case_id"]): [
                    item for item in invalid if item["case_id"] == case["case_id"]
                ]
                for case in response["authored_cases"]
            }
            if any(not values for values in invalid_by_case.values()):
                raise PilotAuthorRecordError(
                    "Retained v2 Claude failure is not localized to both assigned cases."
                )
            try:
                validate_v2_author_attempt(attempt, assignment)
            except PilotAuthorRecordError as error:
                if "without terminators" not in str(error):
                    raise
            else:
                raise PilotAuthorRecordError("Retained v2 Claude attempt unexpectedly passed.")
            for case_id in sorted(invalid_by_case):
                entries.append(
                    {
                        "case_id": case_id,
                        "participant_id": attempt["participant_id"],
                        "provider": provider,
                        "transport_status": "invalid_content_lines",
                        "transport_reason_codes": ["embedded_line_terminator"],
                        "invalid_line_entries": invalid_by_case[case_id],
                        "role_path_status": "not_evaluated_due_prior_transport_failure",
                        "selected_result_intake_status": "not_run_transport_invalid",
                        "selected_result_validation_digest": None,
                        "admitted": False,
                        "metric_eligible": False,
                    }
                )
            continue

        invalid = _invalid_line_entries(response)
        if invalid:
            raise PilotAuthorRecordError("Retained v2 Codex transport unexpectedly changed.")
        try:
            validate_v2_author_attempt(attempt, assignment)
        except PilotAuthorRecordError as error:
            if "outside the frozen workflow/ role" not in str(error):
                raise
        else:
            raise PilotAuthorRecordError("Retained v2 Codex attempt unexpectedly passed.")
        authored_cases = cast(list[dict[str, Any]], response["authored_cases"])
        if len(authored_cases) != 1:
            raise PilotAuthorRecordError("Retained v2 Codex response is not exactly one case.")
        case = authored_cases[0]
        entries.append(
            {
                "case_id": case["case_id"],
                "participant_id": attempt["participant_id"],
                "provider": provider,
                "transport_status": "valid_content_lines",
                "transport_reason_codes": [],
                "invalid_line_entries": [],
                "role_path_status": "invalid_producer_path",
                "role_path_reason_codes": ["producer_path_outside_workflow_role"],
                "producer_relative_path": case["producer_file"]["relative_path"],
                "selected_result_intake_status": "not_run_role_path_invalid",
                "selected_result_validation_digest": None,
                "admitted": False,
                "metric_eligible": False,
            }
        )

    if len(entries) != 3:
        raise PilotAuthorRecordError("V2 failure ledger did not enumerate the exact triad.")
    transport_invalid_count = sum(
        item["transport_status"] == "invalid_content_lines" for item in entries
    )
    role_invalid_count = sum(
        item.get("role_path_status") == "invalid_producer_path" for item in entries
    )
    if transport_invalid_count != 2 or role_invalid_count != 1:
        raise PilotAuthorRecordError("V2 failure state no longer matches the retained evidence.")

    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_three_case_authoring_intake_failure_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": PROTOCOL_DIGEST,
        "authoring_restart_amendment_digest": RESTART_AMENDMENT_DIGEST,
        "lane_freeze_digest": lane_digest,
        "active_enrollment_digest": ACTIVE_ENROLLMENT_DIGEST,
        "input_captures": input_captures,
        "entries": sorted(entries, key=lambda item: str(item["case_id"])),
        "validator_identity": validator_identity,
        "summary": {
            "assigned_author_context_count": 2,
            "model_attempt_count": 2,
            "response_case_count": 3,
            "transport_invalid_case_count": transport_invalid_count,
            "role_path_invalid_case_count": role_invalid_count,
            "verified_selected_result_count": 0,
            "admitted_case_count": 0,
            "metric_eligible_case_count": 0,
            "project_code_executed_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
        },
        "cohort_status": "rejected_before_authoring_admission",
        "cohort_reason_codes": ["incomplete_admission_valid_causal_triad"],
        "completed_at": COMPLETED_AT,
        "qualification_authority": "none_failed_authoring_intake_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    return ledger


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    root = project_root / PILOT_AUTHORING_V2_RELATIVE
    output = root / "AUTHORING_INTAKE_FAILURE_LEDGER.json"
    if output.exists():
        raise FileExistsError("Refusing to replace retained v2 authoring intake failure.")
    ledger = build_first_direct_three_case_pilot_authors_v2_failure(project_root)
    _write_json(output, ledger)
    print(json.dumps(ledger["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
