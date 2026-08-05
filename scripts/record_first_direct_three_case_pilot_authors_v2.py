from __future__ import annotations

import argparse
import json
import tempfile
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator
from sc_referee_evaluation.prospective_qualification_v2 import (
    freeze_case_evidence_contract,
)
from sc_referee_evaluation.prospective_selected_result_verifier import (
    PYTHON_STATIC_MARKED_REPORT_PROFILE,
    freeze_independent_selected_result_derivation,
    freeze_selected_result_validation,
    validate_selected_result_validation,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_app_reviewer_calibration import APP_CALIBRATION_RELATIVE
from scripts.build_first_direct_reviewer_calibration_protocol import LANE_RELATIVE
from scripts.build_first_direct_three_case_pilot_authoring import (
    ACTIVE_ENROLLMENT_DIGEST,
    LANE_FREEZE_DIGEST,
    _author_output_schema,
)
from scripts.build_first_direct_three_case_pilot_authoring_v2 import (
    PILOT_AUTHORING_V2_RELATIVE,
)
from scripts.record_first_direct_three_case_pilot_authors import (
    CLAUDE_INCOGNITO_ROUTE,
    EXPECTED_CLAUDE_UI_EVIDENCE,
    PilotAuthorRecordError,
    _freeze_case,
    _iso,
    parse_author_response,
    validate_author_response,
)

PROTOCOL_DIGEST = "sha256:a925a0f05b7ab16f61da02c65b2f47506b0dfad14b0f0f3f630aaded29ef49cb"
RESTART_AMENDMENT_DIGEST = "sha256:41a274b59e79712216d3b2602758b757ca0c86767837e0e385d7344fd53039bc"
SANDBOX_FAILURE_CAPTURE_DIGEST = (
    "sha256:d1db3810b3dfa8517719175b512b3f0359d3255ecc1d25946bf85d03a0e00d9d"
)
CANONICAL_ISSUE_CLASS = "issue-class:retained-subset-for-complete-domain"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], digest_field: str, expected: str, label: str) -> None:
    supplied = record.pop(digest_field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise PilotAuthorRecordError(f"{label} does not replay.")
    record[digest_field] = supplied


def _iso_text(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def normalize_line_author_response(
    response: dict[str, Any], assignment: dict[str, Any]
) -> list[dict[str, Any]]:
    errors = sorted(
        Draft202012Validator(assignment["output_schema"]).iter_errors(response), key=str
    )
    if errors:
        raise PilotAuthorRecordError(f"V2 author response schema failed: {errors[0].message}")
    normalized_response = deepcopy(response)
    cases = cast(list[dict[str, Any]], normalized_response["authored_cases"])
    for case in cases:
        for role in ("input_file", "producer_file", "report_file"):
            file_record = case[role]
            lines = file_record.pop("content_lines")
            if not isinstance(lines, list) or not lines:
                raise PilotAuthorRecordError("V2 author file has no content lines.")
            if any(not isinstance(line, str) or "\n" in line or "\r" in line for line in lines):
                raise PilotAuthorRecordError(
                    "V2 author content_lines must contain physical lines without terminators."
                )
            file_record["content"] = "\n".join(lines) + "\n"
    normalized_assignment = deepcopy(assignment)
    participant_id = str(assignment["participant"]["participant_id"])
    normalized_assignment["output_schema"] = _author_output_schema(
        participant_id, [str(item) for item in assignment["case_ids"]]
    )
    return validate_author_response(normalized_response, normalized_assignment)


def validate_v2_author_attempt(
    attempt: dict[str, Any], assignment: dict[str, Any]
) -> list[dict[str, Any]]:
    participant = assignment["participant"]
    expected = {
        "participant_id": participant["participant_id"],
        "call_identity_id": assignment["call_identity_id"],
        "protocol_digest": PROTOCOL_DIGEST,
        "configuration_digest": participant["configuration_digest"],
        "prompt_digest": assignment["prompt_digest"],
        "output_schema_digest": assignment["output_schema_digest"],
        "replacement_count": 0,
    }
    for key, value in expected.items():
        if attempt.get(key) != value:
            raise PilotAuthorRecordError(f"V2 author attempt {key} does not match its freeze.")
    started = _iso(str(attempt.get("started_at")), "started_at")
    completed = _iso(str(attempt.get("completed_at")), "completed_at")
    if completed < started:
        raise PilotAuthorRecordError("V2 author attempt chronology is reversed.")
    if participant["provider"] == "OpenAI":
        if attempt.get("exit_code") != 0 or attempt.get("attempt_status") != "response_retained":
            raise PilotAuthorRecordError("V2 Codex author did not retain one response.")
    elif (
        attempt.get("conversation_url") != CLAUDE_INCOGNITO_ROUTE
        or attempt.get("ui_evidence") != EXPECTED_CLAUDE_UI_EVIDENCE
        or attempt.get("attempt_status") != "response_retained"
    ):
        raise PilotAuthorRecordError("V2 Claude app author capture evidence does not match.")
    raw_response = attempt.get("raw_response")
    if not isinstance(raw_response, str):
        raise PilotAuthorRecordError("V2 author attempt lacks a textual response.")
    return normalize_line_author_response(parse_author_response(raw_response), assignment)


def _validation_schedule(frozen_at: str) -> dict[str, str]:
    base = _iso(frozen_at, "frozen_at")
    return {
        "author_frozen_at": _iso_text(base),
        "coordinated_at": _iso_text(base + timedelta(seconds=1)),
        "contract_frozen_at": _iso_text(base + timedelta(seconds=2)),
        "derived_at": _iso_text(base + timedelta(seconds=3)),
        "derivation_frozen_at": _iso_text(base + timedelta(seconds=4)),
        "declaration_revealed_at": _iso_text(base + timedelta(seconds=5)),
        "compared_at": _iso_text(base + timedelta(seconds=6)),
    }


def _validate_static_case(
    case: dict[str, Any],
    *,
    participant: dict[str, Any],
    authored_at: str,
    schedule: dict[str, str],
    validator_identity: dict[str, Any],
    envelope: dict[str, Any],
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="sc-referee-v2-intake-") as directory:
        temporary = Path(directory)
        frozen = _freeze_case(
            case,
            participant=participant,
            authored_at=authored_at,
            frozen_at=schedule["author_frozen_at"],
            cases_root=temporary / "cases",
            declarations_root=temporary / "author-declarations",
            manifests_root=temporary / "case-manifests",
        )
        case_id = str(case["case_id"])
        case_root = temporary / "cases" / case_id.removeprefix("case:")
        contract = freeze_case_evidence_contract(
            {
                "case_id": case_id,
                "envelope": envelope,
                "canonical_issue_class": CANONICAL_ISSUE_CLASS,
                "author_declaration": frozen["declaration"],
                "coordinated_at": schedule["coordinated_at"],
            },
            frozen_at=schedule["contract_frozen_at"],
        )
        selected = frozen["declaration"]["selected_result_binding"]
        if selected is None:
            raise PilotAuthorRecordError("V2 pilot causal triad requires one selected result.")
        derivation = freeze_independent_selected_result_derivation(
            case_root,
            {
                "case_id": case_id,
                "validator_identity": validator_identity,
                "profile_id": PYTHON_STATIC_MARKED_REPORT_PROFILE,
                "selected_report_path": selected["report_locator"]["path"],
                "derived_at": schedule["derived_at"],
            },
            frozen_at=schedule["derivation_frozen_at"],
        )
        validation = freeze_selected_result_validation(
            case_root,
            contract,
            derivation,
            declaration_revealed_at=schedule["declaration_revealed_at"],
            compared_at=schedule["compared_at"],
        )
        if validation["status"] != "verified_complete":
            raise PilotAuthorRecordError(
                "V2 author case failed frozen selected-result intake: "
                f"{validation['status']} {validation['reason_codes']}"
            )
        return {
            "declaration": frozen["declaration"],
            "manifest": frozen["manifest"],
            "contract": contract,
            "derivation": derivation,
            "validation": validation,
        }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def record_first_direct_three_case_pilot_authors_v2(
    project_root: Path, *, frozen_at: str
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
    schedule = _validation_schedule(frozen_at)

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
    _replay(lane, "lane_freeze_digest", LANE_FREEZE_DIGEST, "Direct lane freeze")
    envelopes = lane["prospective_protocol"]["envelopes"]
    if len(envelopes) != 1:
        raise PilotAuthorRecordError("Direct lane does not contain one envelope.")
    envelope = envelopes[0]

    incoming = root / "incoming"
    assignments = protocol["author_assignments"]
    expected_paths = {
        str(item["participant"]["participant_id"]): incoming
        / f"{str(item['participant']['participant_id']).removeprefix('actor:')}.json"
        for item in assignments
    }
    missing = [str(path) for path in expected_paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing retained v2 author attempts: {missing}")
    sandbox_failure_path = incoming / "pilot-author-codex-02.sandbox-failed.json"
    allowed = {*expected_paths.values(), sandbox_failure_path}
    extras = sorted(path.name for path in incoming.glob("*.json") if path not in allowed)
    if extras:
        raise PilotAuthorRecordError(f"Unexpected retained v2 author attempts: {extras}")
    sandbox_bytes = sandbox_failure_path.read_bytes()
    sandbox_failure = cast(dict[str, Any], json.loads(sandbox_bytes))
    if (
        sha256_digest(sandbox_bytes) != SANDBOX_FAILURE_CAPTURE_DIGEST
        or sandbox_failure.get("attempt_status") != "failed_before_response"
        or sandbox_failure.get("raw_response") is not None
        or sandbox_failure.get("stdout_jsonl") != ""
        or sandbox_failure.get("exit_code") != 1
        or "readonly database" not in str(sandbox_failure.get("stderr"))
    ):
        raise PilotAuthorRecordError("Retained v2 Codex sandbox launch failure has drifted.")

    retained: list[dict[str, Any]] = []
    all_cases: list[dict[str, Any]] = []
    static_by_case: dict[str, dict[str, Any]] = {}
    for assignment in assignments:
        participant = assignment["participant"]
        participant_id = str(participant["participant_id"])
        input_path = expected_paths[participant_id]
        input_bytes = input_path.read_bytes()
        attempt = cast(dict[str, Any], json.loads(input_bytes))
        cases = validate_v2_author_attempt(attempt, assignment)
        for case in cases:
            case_id = str(case["case_id"])
            static_by_case[case_id] = _validate_static_case(
                case,
                participant=participant,
                authored_at=str(attempt["completed_at"]),
                schedule=schedule,
                validator_identity=validator_identity,
                envelope=envelope,
            )
            all_cases.append(case)
        response = parse_author_response(str(attempt["raw_response"]))
        retained.append(
            {
                "participant": participant,
                "attempt": attempt,
                "input_capture_digest": sha256_digest(input_bytes),
                "response_digest": semantic_digest(response),
                "case_ids": sorted(str(case["case_id"]) for case in cases),
            }
        )
    if len(retained) != 2 or len(all_cases) != 3 or len(static_by_case) != 3:
        raise PilotAuthorRecordError("V2 authoring is not the exact 2-call/3-case set.")

    output_paths = (
        root / "AUTHORING_LEDGER.json",
        root / "cases",
        root / "author-declarations",
        root / "case-manifests",
        root / "case-contracts",
        root / "selected-result-derivations",
        root / "selected-result-validations",
    )
    if any(path.exists() for path in output_paths):
        raise FileExistsError("Refusing to replace retained v2 authoring evidence.")

    assignment_by_participant = {
        str(item["participant"]["participant_id"]): item for item in assignments
    }
    entries = []
    for retained_attempt in retained:
        participant = retained_attempt["participant"]
        participant_id = str(participant["participant_id"])
        attempt = retained_attempt["attempt"]
        case_records = []
        for case in sorted(
            (item for item in all_cases if str(item["case_id"]) in retained_attempt["case_ids"]),
            key=lambda item: str(item["case_id"]),
        ):
            frozen = _freeze_case(
                case,
                participant=participant,
                authored_at=str(attempt["completed_at"]),
                frozen_at=schedule["author_frozen_at"],
                cases_root=root / "cases",
                declarations_root=root / "author-declarations",
                manifests_root=root / "case-manifests",
            )
            static = static_by_case[str(case["case_id"])]
            if frozen["declaration"] != static["declaration"]:
                raise PilotAuthorRecordError("V2 final author declaration differs from intake.")
            suffix = str(case["case_id"]).removeprefix("case:")
            replayed_validation = validate_selected_result_validation(
                static["validation"],
                case_root=root / "cases" / suffix,
                case_contract=static["contract"],
            )
            if replayed_validation != static["validation"]:
                raise PilotAuthorRecordError("V2 final selected-result validation did not replay.")
            _write_json(root / "case-contracts" / f"{suffix}.json", static["contract"])
            _write_json(
                root / "selected-result-derivations" / f"{suffix}.json",
                static["derivation"],
            )
            _write_json(
                root / "selected-result-validations" / f"{suffix}.json",
                static["validation"],
            )
            case_records.append(
                {
                    "case_id": case["case_id"],
                    "case_manifest_digest": frozen["manifest"]["manifest_digest"],
                    "author_declaration_digest": frozen["declaration"]["declaration_digest"],
                    "case_contract_digest": static["contract"]["contract_digest"],
                    "derivation_digest": static["derivation"]["derivation_digest"],
                    "validation_digest": static["validation"]["validation_digest"],
                    "validation_status": static["validation"]["status"],
                }
            )
        assignment = assignment_by_participant[participant_id]
        entries.append(
            {
                "participant_id": participant_id,
                "provider": participant["provider"],
                "configuration_digest": participant["configuration_digest"],
                "call_identity_id": assignment["call_identity_id"],
                "input_capture_digest": retained_attempt["input_capture_digest"],
                "response_digest": retained_attempt["response_digest"],
                "case_records": case_records,
                "started_at": attempt["started_at"],
                "completed_at": attempt["completed_at"],
                "attempt_status": "admitted_after_frozen_static_intake",
                "replacement_count": 0,
            }
        )
    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_three_case_pilot_authoring_ledger",
        "ledger_version": "2.0.0",
        "protocol_digest": PROTOCOL_DIGEST,
        "authoring_restart_amendment_digest": RESTART_AMENDMENT_DIGEST,
        "failed_iteration_selected_result_intake_ledger_digest": restart[
            "failed_selected_result_intake_ledger_digest"
        ],
        "pre_inference_launch_failures": [
            {
                "participant_id": sandbox_failure["participant_id"],
                "call_identity_id": sandbox_failure["call_identity_id"],
                "input_capture_digest": SANDBOX_FAILURE_CAPTURE_DIGEST,
                "attempt_status": "failed_before_response",
                "model_response_count": 0,
                "qualification_authority": "none_launch_failure_only",
            }
        ],
        "entries": sorted(entries, key=lambda item: str(item["participant_id"])),
        "validator_identity": validator_identity,
        "summary": {
            "assigned_author_context_count": 2,
            "model_attempt_count": 2,
            "pre_inference_launch_failure_count": 1,
            "admitted_attempt_count": 2,
            "authored_case_count": 3,
            "author_declaration_count": 3,
            "verified_selected_result_count": 3,
            "metric_eligible_case_count": 3,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
        },
        "schedule": schedule,
        "qualification_authority": "none_authoring_ledger_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    _write_json(root / "AUTHORING_LEDGER.json", ledger)
    return ledger


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--frozen-at", required=True)
    args = parser.parse_args()
    ledger = record_first_direct_three_case_pilot_authors_v2(
        args.project_root.resolve(), frozen_at=args.frozen_at
    )
    print(json.dumps(ledger["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
