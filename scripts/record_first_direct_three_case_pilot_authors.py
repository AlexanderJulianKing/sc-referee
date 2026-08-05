from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, cast

from jsonschema import Draft202012Validator
from sc_referee_evaluation.prospective_qualification_v2 import (
    freeze_author_selected_result_declaration,
)

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from scripts.build_first_direct_three_case_pilot_authoring import PILOT_AUTHORING_RELATIVE
from scripts.build_first_direct_three_case_pilot_intake_recovery import (
    CODEX_CAPTURE_DIGEST,
    FAILED_CLAUDE_CAPTURE_DIGEST,
    FAILED_CLAUDE_RAW_DIGEST,
    RECOVERY_AMENDMENT_DIGEST,
)

PROTOCOL_DIGEST = "sha256:51808c104df89a701f1b6dd612894207760c02da7c969dcb68df86ae589593af"
SCOPE_AMENDMENT_DIGEST = "sha256:35e1d193113b807257baab48bf2bd2d9b6482ed620bae09a1f36aa5541b91861"
CLAUDE_INCOGNITO_ROUTE = "claude.ai/new?incognito="
EXPECTED_CLAUDE_UI_EVIDENCE = {
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


class PilotAuthorRecordError(ValueError):
    """Raised when a retained author attempt cannot be admitted unchanged."""


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _iso(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise PilotAuthorRecordError(f"{label} is not an ISO-8601 timestamp.") from error
    if parsed.tzinfo is None:
        raise PilotAuthorRecordError(f"{label} lacks a timezone.")
    return parsed.astimezone(UTC)


def _relative_path(value: Any, *, prefix: str, suffixes: tuple[str, ...]) -> str:
    if not isinstance(value, str) or not value:
        raise PilotAuthorRecordError("Author file path is not text.")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or ".." in path.parts
        or not path.parts
        or path.parts[0] != prefix
        or path.suffix not in suffixes
    ):
        raise PilotAuthorRecordError(f"Author file path is outside the frozen {prefix}/ role.")
    return value


def parse_author_response(raw_response: str) -> dict[str, Any]:
    stripped = raw_response.strip()
    if not stripped.startswith("{") or stripped.startswith("```"):
        raise PilotAuthorRecordError("Author response is not one unfenced JSON object.")
    parsed = json.loads(stripped)
    if not isinstance(parsed, dict):
        raise PilotAuthorRecordError("Author response is not one JSON object.")
    return cast(dict[str, Any], parsed)


def validate_author_response(
    response: dict[str, Any],
    assignment: dict[str, Any],
    *,
    permit_redundant_selected_candidate: bool = False,
) -> list[dict[str, Any]]:
    errors = sorted(
        Draft202012Validator(assignment["output_schema"]).iter_errors(response), key=str
    )
    if errors:
        raise PilotAuthorRecordError(f"Author response schema failed: {errors[0].message}")
    cases = cast(list[dict[str, Any]], response["authored_cases"])
    expected_ids = sorted(str(item) for item in assignment["case_ids"])
    if sorted(str(item["case_id"]) for item in cases) != expected_ids:
        raise PilotAuthorRecordError(
            "Author response does not contain the exact assigned case set."
        )
    if len({str(item["case_id"]) for item in cases}) != len(cases):
        raise PilotAuthorRecordError("Author response repeats a case identity.")
    for case in cases:
        paths = {
            "input": _relative_path(
                case["input_file"]["relative_path"],
                prefix="inputs",
                suffixes=(".csv", ".tsv"),
            ),
            "producer": _relative_path(
                case["producer_file"]["relative_path"],
                prefix="workflow",
                suffixes=(".py",),
            ),
            "report": _relative_path(
                case["report_file"]["relative_path"],
                prefix="results",
                suffixes=(".md", ".txt"),
            ),
        }
        if len(set(paths.values())) != 3:
            raise PilotAuthorRecordError("Author response file roles are not distinct.")
        for role in ("input_file", "producer_file", "report_file"):
            content = case[role]["content"]
            if "\r" in content or not content.endswith("\n"):
                raise PilotAuthorRecordError(
                    "Author file content must use LF and end in a newline."
                )
            if role != "producer_file":
                try:
                    content.encode("ascii")
                except UnicodeEncodeError as error:
                    raise PilotAuthorRecordError(
                        "Input and report content must be ASCII."
                    ) from error
        report_lines = case["report_file"]["content"].splitlines()
        if sum("[selected-result]" in line for line in report_lines) != 1:
            raise PilotAuthorRecordError(
                "Every retained report must contain exactly one [selected-result] line."
            )
        declaration = case["author_declaration"]
        state = declaration["declaration_state"]
        selected = declaration["selected_result_projection"]
        candidates = declaration["candidate_result_spans"]
        unsupported = declaration["unsupported_producer_spans"]
        if state == "one_selected_result":
            if selected is None or unsupported:
                raise PilotAuthorRecordError("One-result author declaration is inconsistent.")
            if candidates and not permit_redundant_selected_candidate:
                raise PilotAuthorRecordError("One-result author declaration is inconsistent.")
            if candidates and any(span != selected["result_span"] for span in candidates):
                raise PilotAuthorRecordError(
                    "One-result candidate inventory conflicts with the selected result span."
                )
        if state == "multiple_candidate_results" and (
            selected is not None or len(candidates) < 2 or unsupported
        ):
            raise PilotAuthorRecordError("Multiple-result author declaration is inconsistent.")
        if state == "unsupported_producer_surface" and (
            selected is not None or candidates or not unsupported
        ):
            raise PilotAuthorRecordError("Unsupported-producer declaration is inconsistent.")
        _validate_spans(case)
    return cases


def _validate_spans(case: dict[str, Any]) -> None:
    declaration = case["author_declaration"]
    report_count = len(case["report_file"]["content"].splitlines())
    producer_count = len(case["producer_file"]["content"].splitlines())
    span_groups: list[tuple[dict[str, Any], int]] = []
    selected = declaration["selected_result_projection"]
    if selected is not None:
        span_groups.extend(
            [
                (selected["result_span"], report_count),
                (selected["producer_span"], producer_count),
            ]
        )
    span_groups.extend((span, report_count) for span in declaration["candidate_result_spans"])
    span_groups.extend((span, producer_count) for span in declaration["unsupported_producer_spans"])
    for span, ceiling in span_groups:
        if span["end_line"] < span["start_line"] or span["end_line"] > ceiling:
            raise PilotAuthorRecordError("Author declaration line span is outside retained bytes.")


def validate_author_attempt(
    attempt: dict[str, Any],
    assignment: dict[str, Any],
    protocol_digest: str,
    *,
    expected_replacement_count: int = 0,
    permit_redundant_selected_candidate: bool = False,
) -> dict[str, Any]:
    participant = assignment["participant"]
    required_common = {
        "participant_id": participant["participant_id"],
        "call_identity_id": assignment["call_identity_id"],
        "protocol_digest": protocol_digest,
        "configuration_digest": participant["configuration_digest"],
        "prompt_digest": assignment["prompt_digest"],
        "output_schema_digest": assignment["output_schema_digest"],
    }
    for key, expected in required_common.items():
        if attempt.get(key) != expected:
            raise PilotAuthorRecordError(f"Author attempt {key} does not match its freeze.")
    if attempt.get("replacement_count") != expected_replacement_count:
        raise PilotAuthorRecordError("Author attempt replacement count does not match its freeze.")
    started = _iso(str(attempt.get("started_at")), "started_at")
    completed = _iso(str(attempt.get("completed_at")), "completed_at")
    if completed < started:
        raise PilotAuthorRecordError("Author attempt chronology is reversed.")
    if participant["provider"] == "OpenAI":
        if attempt.get("exit_code") != 0 or attempt.get("attempt_status") != "response_retained":
            raise PilotAuthorRecordError(
                "Codex author attempt did not retain a successful response."
            )
    else:
        if (
            attempt.get("conversation_url") != CLAUDE_INCOGNITO_ROUTE
            or attempt.get("ui_evidence") != EXPECTED_CLAUDE_UI_EVIDENCE
            or attempt.get("attempt_status") != "response_retained"
        ):
            raise PilotAuthorRecordError("Claude app author capture evidence does not match.")
    raw_response = attempt.get("raw_response")
    if not isinstance(raw_response, str):
        raise PilotAuthorRecordError("Author attempt lacks a textual response.")
    response = parse_author_response(raw_response)
    cases = validate_author_response(
        response,
        assignment,
        permit_redundant_selected_candidate=permit_redundant_selected_candidate,
    )
    return {"response": response, "cases": cases}


def _canonicalization_codes(case: dict[str, Any]) -> list[str]:
    declaration = case["author_declaration"]
    if (
        declaration["declaration_state"] == "one_selected_result"
        and declaration["candidate_result_spans"]
    ):
        return ["redundant_selected_span_removed_from_candidate_inventory"]
    return []


def _locator(path: str, content: str, start_line: int, end_line: int) -> dict[str, Any]:
    return {
        "path": path,
        "content_digest": sha256_digest(content.encode("utf-8")),
        "start_line": start_line,
        "end_line": end_line,
    }


def _freeze_case(
    case: dict[str, Any],
    *,
    participant: dict[str, Any],
    authored_at: str,
    frozen_at: str,
    cases_root: Path,
    declarations_root: Path,
    manifests_root: Path,
) -> dict[str, Any]:
    case_id = str(case["case_id"])
    suffix = case_id.removeprefix("case:")
    case_root = cases_root / suffix
    if case_root.exists():
        raise FileExistsError(f"Refusing to replace retained pilot case: {case_root}")
    file_entries = []
    for role in ("input_file", "producer_file", "report_file"):
        relative_path = str(case[role]["relative_path"])
        content = str(case[role]["content"])
        destination = case_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="")
        file_entries.append(
            {
                "role": role.removesuffix("_file"),
                "path": relative_path,
                "content_digest": sha256_digest(content.encode("utf-8")),
                "line_count": len(content.splitlines()),
            }
        )
    input_file = case["input_file"]
    producer_file = case["producer_file"]
    report_file = case["report_file"]
    declaration_projection = case["author_declaration"]
    state = declaration_projection["declaration_state"]
    selected_binding = None
    candidate_locators: list[dict[str, Any]] = []
    unsupported_locators: list[dict[str, Any]] = []
    if state == "one_selected_result":
        selected = declaration_projection["selected_result_projection"]
        assert selected is not None
        input_path = str(input_file["relative_path"])
        input_content = str(input_file["content"])
        input_digest = sha256_digest(input_content.encode("utf-8"))
        report_path = str(report_file["relative_path"])
        report_content = str(report_file["content"])
        producer_path = str(producer_file["relative_path"])
        producer_content = str(producer_file["content"])
        selected_binding = {
            "binding_profile": "exact_selected_report_result_static_producer_v1",
            "selection_status": "one_selected_result",
            "report_locator": _locator(
                report_path, report_content, 1, len(report_content.splitlines())
            ),
            "result_locator": _locator(
                report_path,
                report_content,
                selected["result_span"]["start_line"],
                selected["result_span"]["end_line"],
            ),
            "producer_locator": _locator(
                producer_path,
                producer_content,
                selected["producer_span"]["start_line"],
                selected["producer_span"]["end_line"],
            ),
            "source_operands": [
                {
                    "operand_id": stable_id("operand", input_path, input_digest),
                    "record_ref": {
                        "record_type": "file_record",
                        "record_id": stable_id("file", input_path, input_digest),
                    },
                    "source_locator": _locator(
                        input_path, input_content, 1, len(input_content.splitlines())
                    ),
                }
            ],
            "alternative_producer_locators": [],
            "declared_dynamic_selection": False,
        }
    elif state == "multiple_candidate_results":
        candidate_locators = [
            _locator(
                str(report_file["relative_path"]),
                str(report_file["content"]),
                span["start_line"],
                span["end_line"],
            )
            for span in declaration_projection["candidate_result_spans"]
        ]
    else:
        unsupported_locators = [
            _locator(
                str(producer_file["relative_path"]),
                str(producer_file["content"]),
                span["start_line"],
                span["end_line"],
            )
            for span in declaration_projection["unsupported_producer_spans"]
        ]
    declaration = freeze_author_selected_result_declaration(
        {
            "case_id": case_id,
            "declaration_state": state,
            "selected_result_binding": selected_binding,
            "candidate_result_locators": candidate_locators,
            "unsupported_producer_locators": unsupported_locators,
            "authorship": {
                "author_id": participant["participant_id"],
                "provider": participant["provider"],
                "execution_context_id": participant["execution_context_id"],
                "identity_evidence_digest": participant["configuration_digest"],
            },
            "authored_at": authored_at,
        },
        frozen_at=frozen_at,
    )
    declarations_root.mkdir(parents=True, exist_ok=True)
    declaration_path = declarations_root / f"{suffix}.json"
    declaration_path.write_text(
        json.dumps(declaration, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    manifest: dict[str, Any] = {
        "artifact_kind": "direct_qualification_retained_author_case_manifest",
        "manifest_version": "1.0.0",
        "case_id": case_id,
        "author_id": participant["participant_id"],
        "author_configuration_digest": participant["configuration_digest"],
        "files": sorted(file_entries, key=lambda item: str(item["path"])),
        "author_declaration_digest": declaration["declaration_digest"],
        "qualification_authority": "none_retained_author_case_only",
    }
    manifest["manifest_digest"] = semantic_digest(manifest)
    manifests_root.mkdir(parents=True, exist_ok=True)
    (manifests_root / f"{suffix}.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {"manifest": manifest, "declaration": declaration}


def record_first_direct_three_case_pilot_authors(
    project_root: Path, *, frozen_at: str
) -> dict[str, Any]:
    root = project_root / PILOT_AUTHORING_RELATIVE
    protocol = _load(root / "PILOT_AUTHORING_PROTOCOL.json")
    protocol_digest = protocol.pop("protocol_digest", None)
    if protocol_digest != PROTOCOL_DIGEST or protocol_digest != semantic_digest(protocol):
        raise PilotAuthorRecordError("Pilot authoring protocol does not replay.")
    protocol["protocol_digest"] = protocol_digest
    scope = _load(root / "PILOT_SCOPE_AMENDMENT.json")
    scope_digest = scope.pop("amendment_digest", None)
    if scope_digest != SCOPE_AMENDMENT_DIGEST or scope_digest != semantic_digest(scope):
        raise PilotAuthorRecordError("Pilot scope amendment does not replay.")
    if protocol["pilot_scope_amendment_digest"] != scope_digest:
        raise PilotAuthorRecordError("Authoring protocol and scope amendment differ.")
    recovery = _load(root / "AUTHORING_INTAKE_RECOVERY_AMENDMENT.json")
    recovery_digest = recovery.pop("amendment_digest", None)
    if recovery_digest != RECOVERY_AMENDMENT_DIGEST or recovery_digest != semantic_digest(recovery):
        raise PilotAuthorRecordError("Author intake recovery amendment does not replay.")
    recovery["amendment_digest"] = recovery_digest
    if (
        recovery["parent_protocol_digest"] != protocol_digest
        or recovery["freeze_state"]["admitted_case_count"] != 0
        or recovery["freeze_state"]["scientific_review_count"] != 0
        or recovery["freeze_state"]["detector_outcome_count"] != 0
        or recovery["execution_policy"]["further_repair_retry_or_replacement_permitted"]
        is not False
    ):
        raise PilotAuthorRecordError("Author intake recovery authority is not narrow.")
    _iso(frozen_at, "frozen_at")
    incoming = root / "incoming"
    assignments = protocol["author_assignments"]
    recovery_assignment = recovery["transport_recovery_assignment"]
    expected_paths = {
        str(item["participant"]["participant_id"]): (
            incoming / "pilot-author-claude-01.transport-recovery.json"
            if item["participant"]["provider"] == "Anthropic"
            else incoming
            / f"{str(item['participant']['participant_id']).removeprefix('actor:')}.json"
        )
        for item in assignments
    }
    missing = [str(path) for path in expected_paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing retained author attempts: {missing}")
    failed_claude_path = incoming / "pilot-author-claude-01.failed.json"
    allowed_paths = {*expected_paths.values(), failed_claude_path}
    extras = sorted(path.name for path in incoming.glob("*.json") if path not in allowed_paths)
    if extras:
        raise PilotAuthorRecordError(f"Unexpected retained author attempts: {extras}")
    if not failed_claude_path.is_file():
        raise FileNotFoundError("Missing retained first Claude transport failure.")
    failed_bytes = failed_claude_path.read_bytes()
    failed_attempt = cast(dict[str, Any], json.loads(failed_bytes))
    original_claude_assignment = next(
        item for item in assignments if item["participant"]["provider"] == "Anthropic"
    )
    if (
        sha256_digest(failed_bytes) != FAILED_CLAUDE_CAPTURE_DIGEST
        or failed_attempt.get("call_identity_id") != original_claude_assignment["call_identity_id"]
        or failed_attempt.get("attempt_status") != "invalid_json_retained"
        or failed_attempt.get("replacement_count") != 0
        or sha256_digest(str(failed_attempt.get("raw_response")).encode("utf-8"))
        != FAILED_CLAUDE_RAW_DIGEST
    ):
        raise PilotAuthorRecordError("Retained first Claude failure has drifted.")
    _iso(str(failed_attempt.get("started_at")), "failed_started_at")
    _iso(str(failed_attempt.get("completed_at")), "failed_completed_at")
    try:
        parse_author_response(str(failed_attempt["raw_response"]))
    except json.JSONDecodeError as error:
        if (error.pos, error.lineno, error.colno) != (3688, 1, 3689):
            raise PilotAuthorRecordError("Retained Claude JSON failure has drifted.") from error
    else:
        raise PilotAuthorRecordError("Retained Claude failure unexpectedly parses.")
    ledger_path = root / "AUTHORING_LEDGER.json"
    cases_root = root / "cases"
    declarations_root = root / "author-declarations"
    manifests_root = root / "case-manifests"
    if (
        ledger_path.exists()
        or cases_root.exists()
        or declarations_root.exists()
        or manifests_root.exists()
    ):
        raise FileExistsError("Refusing to overwrite retained pilot authoring evidence.")

    entries = []
    for assignment in assignments:
        participant = assignment["participant"]
        participant_id = str(participant["participant_id"])
        input_path = expected_paths[participant_id]
        input_bytes = input_path.read_bytes()
        attempt = cast(dict[str, Any], json.loads(input_bytes))
        is_claude_recovery = participant["provider"] == "Anthropic"
        effective_assignment = recovery_assignment if is_claude_recovery else assignment
        effective_protocol_digest = recovery_digest if is_claude_recovery else protocol_digest
        permit_canonicalization = participant["provider"] == "OpenAI"
        if permit_canonicalization and sha256_digest(input_bytes) != CODEX_CAPTURE_DIGEST:
            raise PilotAuthorRecordError("Codex canonicalization input capture has drifted.")
        validated = validate_author_attempt(
            attempt,
            effective_assignment,
            str(effective_protocol_digest),
            expected_replacement_count=1 if is_claude_recovery else 0,
            permit_redundant_selected_candidate=permit_canonicalization,
        )
        case_records = []
        for case in validated["cases"]:
            frozen = _freeze_case(
                case,
                participant=participant,
                authored_at=str(attempt["completed_at"]),
                frozen_at=frozen_at,
                cases_root=cases_root,
                declarations_root=declarations_root,
                manifests_root=manifests_root,
            )
            case_records.append(
                {
                    "case_id": case["case_id"],
                    "case_manifest_digest": frozen["manifest"]["manifest_digest"],
                    "author_declaration_digest": frozen["declaration"]["declaration_digest"],
                    "canonicalization_codes": _canonicalization_codes(case),
                }
            )
        response = validated["response"]
        canonicalization_count = sum(len(item["canonicalization_codes"]) for item in case_records)
        entries.append(
            {
                "participant_id": participant_id,
                "provider": participant["provider"],
                "configuration_digest": participant["configuration_digest"],
                "call_identity_id": effective_assignment["call_identity_id"],
                "governing_protocol_digest": effective_protocol_digest,
                "input_capture_digest": sha256_digest(input_bytes),
                "response_digest": semantic_digest(response),
                "case_records": sorted(case_records, key=lambda item: str(item["case_id"])),
                "started_at": attempt["started_at"],
                "completed_at": attempt["completed_at"],
                "attempt_status": (
                    "admitted_with_frozen_metadata_canonicalization"
                    if canonicalization_count
                    else "admitted_without_repair"
                ),
                "replacement_count": 1 if is_claude_recovery else 0,
            }
        )
    all_cases = [item for entry in entries for item in entry["case_records"]]
    if len(entries) != 2 or len(all_cases) != 3:
        raise PilotAuthorRecordError(
            "Retained authoring evidence is not the exact 2-call/3-case set."
        )
    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_three_case_pilot_authoring_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": protocol_digest,
        "pilot_scope_amendment_digest": scope_digest,
        "author_intake_recovery_amendment_digest": recovery_digest,
        "entries": sorted(entries, key=lambda item: str(item["participant_id"])),
        "failed_attempts": [
            {
                "participant_id": failed_attempt["participant_id"],
                "call_identity_id": failed_attempt["call_identity_id"],
                "input_capture_digest": FAILED_CLAUDE_CAPTURE_DIGEST,
                "raw_response_digest": FAILED_CLAUDE_RAW_DIGEST,
                "attempt_status": "invalid_json_retained",
                "replacement_count": 0,
                "qualification_authority": "none_failed_author_attempt_only",
            }
        ],
        "summary": {
            "assigned_author_context_count": 2,
            "retained_attempt_count": 3,
            "admitted_attempt_count": 2,
            "failed_attempt_count": 1,
            "replacement_count": 1,
            "authored_case_count": 3,
            "author_declaration_count": 3,
            "metadata_canonicalization_count": 1,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
        },
        "frozen_at": frozen_at,
        "qualification_authority": "none_authoring_ledger_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    ledger_path.write_text(
        json.dumps(ledger, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return ledger


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--frozen-at", required=True)
    args = parser.parse_args()
    ledger = record_first_direct_three_case_pilot_authors(
        args.project_root.resolve(), frozen_at=args.frozen_at
    )
    print(json.dumps(ledger["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
