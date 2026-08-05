from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_reviewer_calibration_protocol import (
    CALIBRATION_RELATIVE,
    FAILED_CALIBRATION_RELATIVE,
    PARTIAL_CALIBRATION_RELATIVE,
    load_effective_execution_configuration,
)

CLAUDE = Path("/Users/alexanderking/.local/bin/claude")
CODEX = Path("/Users/alexanderking/.local/bin/codex")


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _append_reason(evaluation: dict[str, Any], reason: str) -> None:
    reasons = evaluation.get("reason_codes")
    if not isinstance(reasons, list):
        raise TypeError("Calibration evaluation reason_codes must be a list.")
    evaluation["reason_codes"] = [*reasons, reason]


def _validate_protocol(protocol: dict[str, Any], project_root: Path) -> None:
    supplied = protocol.pop("protocol_digest", None)
    if supplied != semantic_digest(protocol):
        raise ValueError("Calibration protocol digest does not replay.")
    protocol["protocol_digest"] = supplied
    if (
        protocol.get("artifact_kind") != "direct_qualification_reviewer_calibration_protocol"
        or protocol.get("protocol_version") != "3.0.0"
        or protocol.get("execution_state") != "frozen_not_started"
        or protocol.get("expected_reviewer_count") != 3
        or protocol.get("aggregate_reviewer_count") != 6
        or len(protocol.get("assignments", [])) != 3
        or len(protocol.get("retained_pass_refs", [])) != 3
        or protocol.get("qualification_authority") != "none_calibration_protocol_only"
    ):
        raise ValueError("Unsupported reviewer calibration protocol.")
    enrollment = _load(
        project_root
        / "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/"
        "PARTICIPANT_ENROLLMENT.json"
    )
    supplied_enrollment_digest = enrollment.pop("enrollment_digest", None)
    if supplied_enrollment_digest != semantic_digest(enrollment):
        raise ValueError("The frozen participant enrollment does not replay.")
    enrollment["enrollment_digest"] = supplied_enrollment_digest
    if supplied_enrollment_digest != protocol["participant_enrollment_digest"]:
        raise ValueError("The reviewer calibration enrollment binding has drifted.")
    by_id = {str(item["participant_id"]): item for item in enrollment["participants"]}
    expected_claude_ids = {
        participant_id
        for participant_id, item in by_id.items()
        if item["role"] in {"stage1_reviewer", "stage2_reviewer"}
        and item["provider"] == "Anthropic"
    }
    assignments = protocol["assignments"]
    actual_ids = [str(item["participant_id"]) for item in assignments]
    if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != expected_claude_ids:
        raise ValueError("Protocol v3 does not bind the exact frozen Claude reviewers.")
    if len({str(item["call_identity_id"]) for item in assignments}) != len(assignments):
        raise ValueError("Protocol v3 contains a reused call identity.")
    for assignment in assignments:
        participant = by_id[str(assignment["participant_id"])]
        for field in (
            "role",
            "provider",
            "agent_surface",
            "agent_version",
            "model_name",
            "model_id",
            "reasoning_configuration",
            "execution_context_id",
            "configuration_digest",
            "system_prompt_digest",
            "tool_policy_digest",
            "environment_digest",
            "calibration_suite_digest",
        ):
            if assignment.get(field) != participant.get(field):
                raise ValueError(
                    f"Protocol v3 participant binding drift: {assignment['participant_id']} {field}."
                )
        if assignment["calibration_suite_digest"] != protocol["calibration_suite_digest"]:
            raise ValueError("Protocol v3 calibration suite binding has drifted.")
        if assignment["user_prompt_digest"] != sha256_digest(assignment["user_prompt"]):
            raise ValueError("Protocol v3 user prompt digest has drifted.")
        if assignment["output_schema_digest"] != semantic_digest(assignment["output_schema"]):
            raise ValueError("Protocol v3 output schema digest has drifted.")
        if "$schema" in assignment["output_schema"]:
            raise ValueError("Protocol v3 contains the unsupported Claude schema identifier.")
        if assignment["requested_provider_session_id"] != assignment["call_identity_id"]:
            raise ValueError("Protocol v3 Claude session binding has drifted.")
    expected_codex_ids = {
        participant_id
        for participant_id, item in by_id.items()
        if item["role"] in {"stage1_reviewer", "stage2_reviewer"} and item["provider"] == "OpenAI"
    }
    retained_ids = [str(item["participant_id"]) for item in protocol["retained_pass_refs"]]
    if len(retained_ids) != len(set(retained_ids)) or set(retained_ids) != expected_codex_ids:
        raise ValueError("Protocol v3 does not bind the exact retained Codex reviewers.")


def _build_aggregate_ledger(
    project_root: Path,
    protocol: dict[str, Any],
    current_ledger: dict[str, Any],
) -> dict[str, Any]:
    supplied_current_digest = current_ledger.get("ledger_digest")
    current_without_digest = {
        key: value for key, value in current_ledger.items() if key != "ledger_digest"
    }
    if supplied_current_digest != semantic_digest(current_without_digest):
        raise ValueError("The current calibration ledger does not replay.")
    if current_ledger.get("protocol_digest") != protocol.get("protocol_digest"):
        raise ValueError("The current calibration ledger does not match protocol v3.")
    initial_ledger = _load(project_root / FAILED_CALIBRATION_RELATIVE / "CALIBRATION_LEDGER.json")
    supplied_initial_digest = initial_ledger.pop("ledger_digest", None)
    if supplied_initial_digest != semantic_digest(initial_ledger):
        raise ValueError("The initial calibration failure ledger does not replay.")
    initial_ledger["ledger_digest"] = supplied_initial_digest
    retained_ledger = _load(project_root / PARTIAL_CALIBRATION_RELATIVE / "CALIBRATION_LEDGER.json")
    supplied_retained_digest = retained_ledger.pop("ledger_digest", None)
    if supplied_retained_digest != semantic_digest(retained_ledger):
        raise ValueError("The retained partial calibration ledger does not replay.")
    retained_ledger["ledger_digest"] = supplied_retained_digest
    if supplied_retained_digest != protocol["retained_partial_ledger_digest"]:
        raise ValueError("The retained partial ledger does not match protocol v3.")
    if protocol["historical_failure_ledger_digests"] != [
        supplied_initial_digest,
        supplied_retained_digest,
    ]:
        raise ValueError("The calibration failure history binding has drifted.")

    retained_by_id = {
        str(item["participant_id"]): item
        for item in retained_ledger["entries"]
        if item["calibration_status"] == "passed"
    }
    retained_entries = []
    for reference in protocol["retained_pass_refs"]:
        participant_id = str(reference["participant_id"])
        entry = retained_by_id.get(participant_id)
        if entry is None:
            raise ValueError(f"Missing retained pass for {participant_id}.")
        for field in (
            "response_digest",
            "transcript_digest",
            "reported_session_id",
            "calibration_status",
        ):
            if entry.get(field) != reference.get(field):
                raise ValueError(f"Retained pass field drift for {participant_id}: {field}.")
        retained_entries.append(
            {
                **entry,
                "calibration_evidence_source": "retained_protocol_v2_pass",
                "source_ledger_digest": supplied_retained_digest,
                "source_protocol_digest": retained_ledger["protocol_digest"],
            }
        )

    current_entries = [
        {
            **item,
            "calibration_evidence_source": "protocol_v3_attempt",
            "source_ledger_digest": current_ledger["ledger_digest"],
            "source_protocol_digest": current_ledger["protocol_digest"],
        }
        for item in current_ledger["entries"]
    ]
    aggregate_entries = sorted(
        [*retained_entries, *current_entries],
        key=lambda item: str(item["participant_id"]),
    )
    enrollment = _load(
        project_root
        / "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/"
        "PARTICIPANT_ENROLLMENT.json"
    )
    expected_ids = {
        str(item["participant_id"])
        for item in enrollment["participants"]
        if item["role"] in {"stage1_reviewer", "stage2_reviewer"}
    }
    actual_ids = [str(item["participant_id"]) for item in aggregate_entries]
    if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != expected_ids:
        raise ValueError("Aggregate calibration entries do not match the frozen reviewers.")
    enrollment_by_id = {str(item["participant_id"]): item for item in enrollment["participants"]}
    for entry in aggregate_entries:
        participant = enrollment_by_id[str(entry["participant_id"])]
        for field in ("role", "provider", "configuration_digest", "execution_context_id"):
            if entry.get(field) != participant.get(field):
                raise ValueError(
                    f"Aggregate participant binding drift: {entry['participant_id']} {field}."
                )
        if entry.get("calibration_status") == "passed" and (
            entry.get("provider_cli_authenticated_success") is not True
            or not entry.get("reported_session_id")
            or entry.get("calibration_evaluation", {}).get("pass") is not True
        ):
            raise ValueError(f"Invalid calibration pass evidence: {entry['participant_id']}.")

    aggregate: dict[str, Any] = {
        "artifact_kind": "direct_qualification_reviewer_calibration_aggregate_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": protocol["protocol_digest"],
        "participant_enrollment_digest": protocol["participant_enrollment_digest"],
        "source_ledger_digests": [
            supplied_initial_digest,
            supplied_retained_digest,
            current_ledger["ledger_digest"],
        ],
        "entries": aggregate_entries,
        "summary": {
            "expected_reviewer_count": protocol["aggregate_reviewer_count"],
            "active_configuration_evidence_count": len(aggregate_entries),
            "retained_v2_pass_count": len(retained_entries),
            "new_v3_attempt_count": len(current_entries),
            "active_passed_count": sum(
                item["calibration_status"] == "passed" for item in aggregate_entries
            ),
            "active_failed_count": sum(
                item["calibration_status"] != "passed" for item in aggregate_entries
            ),
            "historical_attempt_count_across_protocols": (
                len(initial_ledger["entries"])
                + len(retained_ledger["entries"])
                + len(current_entries)
            ),
            "historical_failed_attempt_count": sum(
                item["calibration_status"] != "passed"
                for item in [
                    *initial_ledger["entries"],
                    *retained_ledger["entries"],
                    *current_entries,
                ]
            ),
            "current_protocol_replacement_count": 0,
            "all_active_reviewer_configurations_passed": all(
                item["calibration_status"] == "passed" for item in aggregate_entries
            ),
        },
        "sealed_at": current_ledger["sealed_at"],
        "qualification_authority": "none_reviewer_calibration_only",
    }
    aggregate["ledger_digest"] = semantic_digest(aggregate)
    return aggregate


def validate_calibration_response(
    response: Any,
    assignment: dict[str, Any],
    expected_verdicts: dict[str, str],
) -> dict[str, Any]:
    errors = sorted(
        Draft202012Validator(assignment["output_schema"]).iter_errors(response),
        key=lambda item: list(item.absolute_path),
    )
    reasons = [f"schema:{error.json_path}:{error.message}" for error in errors]
    results = response.get("calibration_results", []) if isinstance(response, dict) else []
    case_ids = [
        str(item.get("calibration_case_id", "")) for item in results if isinstance(item, dict)
    ]
    if len(case_ids) != len(set(case_ids)):
        reasons.append("duplicate_calibration_case_id")
    if set(case_ids) != set(expected_verdicts):
        reasons.append("calibration_case_set_mismatch")
    mismatches = sorted(
        case_id
        for case_id, expected in expected_verdicts.items()
        if next(
            (
                item.get("verdict")
                for item in results
                if isinstance(item, dict) and item.get("calibration_case_id") == case_id
            ),
            None,
        )
        != expected
    )
    if mismatches:
        reasons.append("verdict_mismatch:" + ",".join(mismatches))
    invented = sum(
        item.get("invented_material_premise") is not False
        for item in results
        if isinstance(item, dict)
    )
    if invented:
        reasons.append(f"invented_material_premise_count:{invented}")
    return {
        "structured_output_schema_valid": not errors,
        "calibration_case_set_complete": set(case_ids) == set(expected_verdicts),
        "exact_expected_verdict_count": len(expected_verdicts) - len(mismatches),
        "invented_material_premise_count": invented,
        "pass": not reasons,
        "reason_codes": reasons,
    }


def _parse_claude(stdout: bytes) -> tuple[Any, dict[str, Any]]:
    envelope = json.loads(stdout.decode("utf-8"))
    response = envelope.get("structured_output")
    if not isinstance(response, dict):
        result = envelope.get("result")
        response = result if isinstance(result, dict) else json.loads(str(result))
    return response, {
        "reported_session_id": envelope.get("session_id"),
        "provider_result_subtype": envelope.get("subtype"),
        "provider_is_error": envelope.get("is_error"),
        "provider_usage": envelope.get("usage"),
        "provider_model_usage": envelope.get("modelUsage"),
    }


def _parse_codex(stdout: bytes, final: bytes) -> tuple[Any, dict[str, Any]]:
    response = json.loads(final.decode("utf-8"))
    events = [json.loads(line) for line in stdout.decode("utf-8").splitlines() if line.strip()]
    thread_id = next(
        (
            event.get("thread_id")
            for event in events
            if event.get("type") in {"thread.started", "thread_started"}
        ),
        None,
    )
    usage = next(
        (
            event.get("usage")
            for event in reversed(events)
            if event.get("type") in {"turn.completed", "turn_completed"}
        ),
        None,
    )
    return response, {
        "reported_session_id": thread_id,
        "provider_result_subtype": "exec_completed",
        "provider_is_error": False,
        "provider_usage": usage,
        "provider_model_usage": None,
    }


def _run_assignment(assignment: dict[str, Any], system_prompt: str) -> dict[str, Any]:
    started_at = _now()
    environment = dict(os.environ)
    environment["NO_COLOR"] = "1"
    with tempfile.TemporaryDirectory(prefix="sc-referee-reviewer-calibration-") as temporary:
        working = Path(temporary)
        schema_path = working / "output-schema.json"
        schema_path.write_text(
            json.dumps(assignment["output_schema"], sort_keys=True), encoding="utf-8"
        )
        final_path = working / "final-response.json"
        if assignment["provider"] == "Anthropic":
            argv = [
                str(CLAUDE),
                "--safe-mode",
                "--print",
                "--model",
                str(assignment["model_id"]),
                "--effort",
                str(assignment["reasoning_configuration"]),
                "--system-prompt",
                system_prompt,
                "--tools",
                "",
                "--strict-mcp-config",
                "--mcp-config",
                '{"mcpServers":{}}',
                "--permission-mode",
                "dontAsk",
                "--no-session-persistence",
                "--output-format",
                "json",
                "--json-schema",
                json.dumps(assignment["output_schema"], sort_keys=True),
                "--session-id",
                str(assignment["requested_provider_session_id"]),
                str(assignment["user_prompt"]),
            ]
        else:
            argv = [
                str(CODEX),
                "--model",
                str(assignment["model_id"]),
                "--sandbox",
                "read-only",
                "--ask-for-approval",
                "never",
                "--config",
                f'model_reasoning_effort="{assignment["reasoning_configuration"]}"',
                "--config",
                f"developer_instructions={json.dumps(system_prompt)}",
                "exec",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--skip-git-repo-check",
                "--output-schema",
                str(schema_path),
                "--json",
                "--output-last-message",
                str(final_path),
                "--cd",
                str(working),
                str(assignment["user_prompt"]),
            ]
        try:
            completed = subprocess.run(
                argv,
                cwd=working,
                env=environment,
                capture_output=True,
                check=False,
                timeout=900,
            )
            return_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
            final = final_path.read_bytes() if final_path.exists() else b""
            process_error = None
        except subprocess.TimeoutExpired as error:
            return_code = 124
            stdout = error.stdout or b""
            stderr = error.stderr or b""
            final = b""
            process_error = "timeout_900_seconds"
        completed_at = _now()
    return {
        "assignment": assignment,
        "argv": argv,
        "started_at": started_at,
        "completed_at": completed_at,
        "return_code": return_code,
        "stdout": stdout,
        "stderr": stderr,
        "final": final,
        "process_error": process_error,
    }


def run_first_direct_reviewer_calibration(project_root: Path) -> dict[str, Any]:
    root = project_root / CALIBRATION_RELATIVE
    protocol = _load(root / "CALIBRATION_PROTOCOL.json")
    _validate_protocol(protocol, project_root)
    captures_root = root / "captures"
    ledger_path = root / "CALIBRATION_LEDGER.json"
    aggregate_path = root / "AGGREGATE_CALIBRATION_LEDGER.json"
    if (
        captures_root.exists()
        or captures_root.is_symlink()
        or ledger_path.exists()
        or aggregate_path.exists()
    ):
        raise FileExistsError("Refusing to overwrite retained reviewer calibration evidence.")
    config = load_effective_execution_configuration(project_root)
    suite = config["reviewer_calibration_suite"]
    expected_verdicts = {
        str(item["calibration_case_id"]): str(item["expected_verdict"])
        for item in suite["vignettes"]
    }
    role_configs = config["role_configurations"]
    assignments = list(protocol["assignments"])
    with ThreadPoolExecutor(max_workers=len(assignments)) as executor:
        futures = [
            executor.submit(
                _run_assignment,
                assignment,
                str(role_configs[str(assignment["role"])]["system_prompt"]),
            )
            for assignment in assignments
        ]
        attempts = [future.result() for future in futures]
    attempts.sort(key=lambda item: str(item["assignment"]["participant_id"]))

    captures_root.mkdir(parents=True, exist_ok=False)
    ledger_entries = []
    for attempt in attempts:
        assignment = attempt["assignment"]
        participant_id = str(assignment["participant_id"])
        directory = captures_root / participant_id.removeprefix("actor:")
        directory.mkdir()
        stdout_path = directory / "stdout.jsonl"
        stderr_path = directory / "stderr.txt"
        final_path = directory / "final-response.json"
        stdout_path.write_bytes(attempt["stdout"])
        stderr_path.write_bytes(attempt["stderr"])
        final_path.write_bytes(attempt["final"])
        invocation = {
            "participant_id": participant_id,
            "call_identity_id": assignment["call_identity_id"],
            "requested_provider_session_id": assignment["requested_provider_session_id"],
            "argv": attempt["argv"],
            "started_at": attempt["started_at"],
            "completed_at": attempt["completed_at"],
            "return_code": attempt["return_code"],
            "process_error": attempt["process_error"],
            "stdout_digest": sha256_digest(attempt["stdout"]),
            "stderr_digest": sha256_digest(attempt["stderr"]),
            "final_response_digest": sha256_digest(attempt["final"]),
        }
        invocation["invocation_digest"] = semantic_digest(invocation)
        (directory / "INVOCATION.json").write_text(
            json.dumps(invocation, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        response: Any = None
        provider_metadata: dict[str, Any] = {
            "reported_session_id": None,
            "provider_result_subtype": None,
            "provider_is_error": True,
            "provider_usage": None,
            "provider_model_usage": None,
        }
        parse_error = None
        if attempt["return_code"] == 0:
            try:
                if assignment["provider"] == "Anthropic":
                    response, provider_metadata = _parse_claude(attempt["stdout"])
                else:
                    response, provider_metadata = _parse_codex(attempt["stdout"], attempt["final"])
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                parse_error = f"{type(error).__name__}:{error}"
        evaluation: dict[str, Any] = (
            validate_calibration_response(response, assignment, expected_verdicts)
            if parse_error is None and response is not None
            else {
                "structured_output_schema_valid": False,
                "calibration_case_set_complete": False,
                "exact_expected_verdict_count": 0,
                "invented_material_premise_count": 0,
                "pass": False,
                "reason_codes": [parse_error or "provider_call_failed"],
            }
        )
        if provider_metadata["provider_is_error"] is not False:
            evaluation["pass"] = False
            _append_reason(evaluation, "provider_reported_error")
        if not provider_metadata["reported_session_id"]:
            evaluation["pass"] = False
            _append_reason(evaluation, "missing_reported_session_id")
        elif (
            assignment["provider"] == "Anthropic"
            and provider_metadata["reported_session_id"]
            != assignment["requested_provider_session_id"]
        ):
            evaluation["pass"] = False
            _append_reason(evaluation, "reported_session_id_mismatch")
        if attempt["return_code"] != 0:
            evaluation["pass"] = False
            _append_reason(evaluation, f"provider_cli_exit_code:{attempt['return_code']}")
        response_digest = semantic_digest(response) if isinstance(response, dict) else None
        transcript_digest = semantic_digest(
            {
                "stdout_digest": invocation["stdout_digest"],
                "stderr_digest": invocation["stderr_digest"],
                "final_response_digest": invocation["final_response_digest"],
                "response_digest": response_digest,
            }
        )
        ledger_entries.append(
            {
                "participant_id": participant_id,
                "role": assignment["role"],
                "provider": assignment["provider"],
                "model_id": assignment["model_id"],
                "execution_context_id": assignment["execution_context_id"],
                "configuration_digest": assignment["configuration_digest"],
                "call_identity_id": assignment["call_identity_id"],
                "requested_provider_session_id": assignment["requested_provider_session_id"],
                **provider_metadata,
                "provider_cli_exit_code": attempt["return_code"],
                "provider_cli_authenticated_success": attempt["return_code"] == 0,
                "response_digest": response_digest,
                "transcript_digest": transcript_digest,
                "invocation_digest": invocation["invocation_digest"],
                "parse_error": parse_error,
                "calibration_evaluation": evaluation,
                "calibration_status": "passed" if evaluation["pass"] else "failed",
                "completed_at": attempt["completed_at"],
            }
        )
    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_reviewer_calibration_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": protocol["protocol_digest"],
        "participant_enrollment_digest": protocol["participant_enrollment_digest"],
        "entries": ledger_entries,
        "summary": {
            "assigned_reviewer_count": protocol["expected_reviewer_count"],
            "retained_attempt_count": len(ledger_entries),
            "passed_count": sum(item["calibration_status"] == "passed" for item in ledger_entries),
            "failed_count": sum(item["calibration_status"] != "passed" for item in ledger_entries),
            "all_assigned_attempts_retained": True,
            "replacement_count": 0,
            "all_reviewer_configurations_passed": all(
                item["calibration_status"] == "passed" for item in ledger_entries
            ),
        },
        "sealed_at": _now(),
        "qualification_authority": "none_reviewer_calibration_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    ledger_path.write_text(
        json.dumps(ledger, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    aggregate = _build_aggregate_ledger(project_root, protocol, ledger)
    aggregate_path.write_text(
        json.dumps(aggregate, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return ledger


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    ledger = run_first_direct_reviewer_calibration(args.project_root.resolve())
    print(json.dumps(ledger["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
