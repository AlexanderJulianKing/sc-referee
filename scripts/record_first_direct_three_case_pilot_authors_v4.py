from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator
from sc_referee_evaluation.authoring_render_grammar import (
    RENDER_ONLY_PROFILE_ID,
    validate_render_only_producer,
)
from sc_referee_evaluation.prospective_selected_result_verifier import (
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
from scripts.build_first_direct_three_case_pilot_authoring_v4 import (
    PILOT_AUTHORING_V4_RELATIVE,
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
from scripts.record_first_direct_three_case_pilot_authors_v2 import (
    _load,
    _replay,
    _validate_static_case,
    _validation_schedule,
    _write_json,
)

PROTOCOL_DIGEST = "sha256:2a853080b2e2faace3f6bfdfe440843e1023c199f02b3cee27d32ee70eaf307f"
RESTART_AMENDMENT_DIGEST = "sha256:fd92ebaad0655d55efa29600f12a9db583486bef7c99f306b66e7596bb44272e"


def normalize_v4_author_response(
    response: dict[str, Any], assignment: dict[str, Any]
) -> list[dict[str, Any]]:
    errors = sorted(
        Draft202012Validator(assignment["output_schema"]).iter_errors(response), key=str
    )
    if errors:
        raise PilotAuthorRecordError(f"V4 author response schema failed: {errors[0].message}")
    normalized_response = deepcopy(response)
    cases = cast(list[dict[str, Any]], normalized_response["authored_cases"])
    for case in cases:
        producer_lines: list[str] | None = None
        for role in ("input_file", "producer_file", "report_file"):
            file_record = case[role]
            lines = file_record.pop("content_lines")
            if not isinstance(lines, list) or not lines:
                raise PilotAuthorRecordError("V4 author file has no content lines.")
            if any(
                not isinstance(line, str) or "\n" in line or "\r" in line or not line.isascii()
                for line in lines
            ):
                raise PilotAuthorRecordError(
                    "V4 author content_lines must contain ASCII physical lines without terminators."
                )
            if role == "producer_file":
                producer_lines = cast(list[str], lines)
                if any("\\" in line for line in producer_lines):
                    raise PilotAuthorRecordError(
                        "V4 producer content_lines must use the escape-free grammar."
                    )
            file_record["content"] = "\n".join(lines) + "\n"
        if producer_lines is None:
            raise PilotAuthorRecordError("V4 author case lacks producer lines.")
        try:
            validate_render_only_producer(producer_lines)
        except ValueError as error:
            raise PilotAuthorRecordError(f"V4 render grammar failed: {error}") from error
        projection = case["author_declaration"].get("selected_result_projection")
        if not isinstance(projection, dict):
            raise PilotAuthorRecordError("V4 pilot causal triad requires one selected result.")
        expected_writer_line = len(producer_lines)
        if projection.get("producer_span") != {
            "start_line": expected_writer_line,
            "end_line": expected_writer_line,
        }:
            raise PilotAuthorRecordError(
                "V4 selected producer span must be exactly the final writer line."
            )

    normalized_assignment = deepcopy(assignment)
    participant_id = str(assignment["participant"]["participant_id"])
    normalized_assignment["output_schema"] = _author_output_schema(
        participant_id, [str(item) for item in assignment["case_ids"]]
    )
    return validate_author_response(normalized_response, normalized_assignment)


def validate_v4_author_attempt(
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
            raise PilotAuthorRecordError(f"V4 author attempt {key} does not match its freeze.")
    started = _iso(str(attempt.get("started_at")), "started_at")
    completed = _iso(str(attempt.get("completed_at")), "completed_at")
    if completed < started:
        raise PilotAuthorRecordError("V4 author attempt chronology is reversed.")
    if participant["provider"] == "OpenAI":
        if attempt.get("exit_code") != 0 or attempt.get("attempt_status") != "response_retained":
            raise PilotAuthorRecordError("V4 Codex author did not retain one response.")
    elif (
        attempt.get("conversation_url") != CLAUDE_INCOGNITO_ROUTE
        or attempt.get("ui_evidence") != EXPECTED_CLAUDE_UI_EVIDENCE
        or attempt.get("attempt_status") != "response_retained"
    ):
        raise PilotAuthorRecordError("V4 Claude app author capture evidence does not match.")
    raw_response = attempt.get("raw_response")
    if not isinstance(raw_response, str):
        raise PilotAuthorRecordError("V4 author attempt lacks a textual response.")
    return normalize_v4_author_response(parse_author_response(raw_response), assignment)


def record_first_direct_three_case_pilot_authors_v4(
    project_root: Path, *, frozen_at: str
) -> dict[str, Any]:
    root = project_root / PILOT_AUTHORING_V4_RELATIVE
    restart = _load(root / "PILOT_AUTHORING_RESTART_AMENDMENT.json")
    _replay(
        restart,
        "amendment_digest",
        RESTART_AMENDMENT_DIGEST,
        "V4 authoring restart amendment",
    )
    protocol = _load(root / "PILOT_AUTHORING_PROTOCOL.json")
    _replay(protocol, "protocol_digest", PROTOCOL_DIGEST, "V4 authoring protocol")
    if protocol["authoring_restart_amendment_digest"] != RESTART_AMENDMENT_DIGEST:
        raise PilotAuthorRecordError("V4 protocol does not bind its restart amendment.")
    if protocol["render_grammar_profile_id"] != RENDER_ONLY_PROFILE_ID:
        raise PilotAuthorRecordError("V4 protocol does not bind the render-only grammar.")
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
        raise FileNotFoundError(f"Missing retained v4 author attempts: {missing}")
    extras = sorted(
        path.name for path in incoming.glob("*.json") if path not in set(expected_paths.values())
    )
    if extras:
        raise PilotAuthorRecordError(f"Unexpected retained v4 author attempts: {extras}")

    retained: list[dict[str, Any]] = []
    all_cases: list[dict[str, Any]] = []
    static_by_case: dict[str, dict[str, Any]] = {}
    grammar_by_case: dict[str, dict[str, Any]] = {}
    for assignment in assignments:
        participant = assignment["participant"]
        participant_id = str(participant["participant_id"])
        input_path = expected_paths[participant_id]
        input_bytes = input_path.read_bytes()
        attempt = cast(dict[str, Any], json.loads(input_bytes))
        cases = validate_v4_author_attempt(attempt, assignment)
        for case in cases:
            case_id = str(case["case_id"])
            producer_lines = str(case["producer_file"]["content"]).splitlines()
            grammar_by_case[case_id] = validate_render_only_producer(producer_lines)
            try:
                static_by_case[case_id] = _validate_static_case(
                    case,
                    participant=participant,
                    authored_at=str(attempt["completed_at"]),
                    schedule=schedule,
                    validator_identity=validator_identity,
                    envelope=envelope,
                )
            except PilotAuthorRecordError as error:
                raise PilotAuthorRecordError(
                    f"V4 author case {case_id} failed frozen static intake: {error}"
                ) from error
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
    if (
        len(retained) != 2
        or len(all_cases) != 3
        or len(static_by_case) != 3
        or len(grammar_by_case) != 3
    ):
        raise PilotAuthorRecordError("V4 authoring is not the exact 2-call/3-case set.")

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
        raise FileExistsError("Refusing to replace retained v4 authoring evidence.")

    entries: list[dict[str, Any]] = []
    for retained_attempt in retained:
        participant = retained_attempt["participant"]
        participant_id = str(participant["participant_id"])
        attempt = retained_attempt["attempt"]
        case_records: list[dict[str, Any]] = []
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
            case_id = str(case["case_id"])
            static = static_by_case[case_id]
            if frozen["declaration"] != static["declaration"]:
                raise PilotAuthorRecordError("V4 final author declaration differs from intake.")
            suffix = case_id.removeprefix("case:")
            replayed = validate_selected_result_validation(
                static["validation"],
                case_root=root / "cases" / suffix,
                case_contract=static["contract"],
            )
            if replayed != static["validation"]:
                raise PilotAuthorRecordError("V4 final selected-result validation did not replay.")
            _write_json(root / "case-contracts" / f"{suffix}.json", static["contract"])
            _write_json(
                root / "selected-result-derivations" / f"{suffix}.json", static["derivation"]
            )
            _write_json(
                root / "selected-result-validations" / f"{suffix}.json", static["validation"]
            )
            case_records.append(
                {
                    "case_id": case_id,
                    "case_manifest_digest": frozen["manifest"]["manifest_digest"],
                    "author_declaration_digest": frozen["declaration"]["declaration_digest"],
                    "case_contract_digest": static["contract"]["contract_digest"],
                    "render_grammar_profile_id": RENDER_ONLY_PROFILE_ID,
                    "render_grammar_validation_digest": grammar_by_case[case_id][
                        "validation_digest"
                    ],
                    "render_grammar_validation_status": grammar_by_case[case_id]["status"],
                    "derivation_digest": static["derivation"]["derivation_digest"],
                    "validation_digest": static["validation"]["validation_digest"],
                    "validation_status": static["validation"]["status"],
                    "metric_eligible": True,
                }
            )
        assignment = next(
            item for item in assignments if item["participant"]["participant_id"] == participant_id
        )
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
                "attempt_status": "admitted_after_frozen_render_and_static_intake",
                "replacement_count": 0,
            }
        )
    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_three_case_pilot_authoring_ledger",
        "ledger_version": "4.0.0",
        "protocol_digest": PROTOCOL_DIGEST,
        "authoring_restart_amendment_digest": RESTART_AMENDMENT_DIGEST,
        "render_grammar_profile_id": RENDER_ONLY_PROFILE_ID,
        "entries": sorted(entries, key=lambda item: str(item["participant_id"])),
        "validator_identity": validator_identity,
        "summary": {
            "assigned_author_context_count": 2,
            "model_attempt_count": 2,
            "admitted_attempt_count": 2,
            "authored_case_count": 3,
            "author_declaration_count": 3,
            "render_grammar_valid_case_count": 3,
            "verified_selected_result_count": 3,
            "metric_eligible_case_count": 3,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
        },
        "schedule": schedule,
        "completed_at": schedule["compared_at"],
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
    ledger = record_first_direct_three_case_pilot_authors_v4(
        args.project_root.resolve(), frozen_at=args.frozen_at
    )
    print(json.dumps(ledger["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
