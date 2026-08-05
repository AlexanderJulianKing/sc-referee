from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_reviewer_calibration_protocol import (
    CALIBRATION_RELATIVE,
    load_effective_execution_configuration,
)

CLAUDE = Path("/Users/alexanderking/.local/bin/claude")
CODEX = Path("/Users/alexanderking/.local/bin/codex")


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_protocol(protocol: dict[str, Any]) -> None:
    supplied = protocol.pop("protocol_digest", None)
    if supplied != semantic_digest(protocol):
        raise ValueError("Calibration protocol digest does not replay.")
    protocol["protocol_digest"] = supplied
    if (
        protocol.get("artifact_kind") != "direct_qualification_reviewer_calibration_protocol"
        or protocol.get("execution_state") != "frozen_not_started"
        or protocol.get("expected_reviewer_count") != 6
        or len(protocol.get("assignments", [])) != 6
        or protocol.get("qualification_authority") != "none_calibration_protocol_only"
    ):
        raise ValueError("Unsupported reviewer calibration protocol.")


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
                "{}",
                "--permission-mode",
                "dontAsk",
                "--no-session-persistence",
                "--output-format",
                "json",
                "--json-schema",
                json.dumps(assignment["output_schema"], sort_keys=True),
                "--session-id",
                str(assignment["requested_session_id"]),
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
    _validate_protocol(protocol)
    captures_root = root / "captures"
    ledger_path = root / "CALIBRATION_LEDGER.json"
    if captures_root.exists() or captures_root.is_symlink() or ledger_path.exists():
        raise FileExistsError("Refusing to overwrite retained reviewer calibration evidence.")
    config = load_effective_execution_configuration(project_root)
    suite = config["reviewer_calibration_suite"]
    expected_verdicts = {
        str(item["calibration_case_id"]): str(item["expected_verdict"])
        for item in suite["vignettes"]
    }
    role_configs = config["role_configurations"]
    assignments = list(protocol["assignments"])
    with ThreadPoolExecutor(max_workers=6) as executor:
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
            "requested_session_id": assignment["requested_session_id"],
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
        evaluation = (
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
        if attempt["return_code"] != 0:
            evaluation["pass"] = False
            evaluation["reason_codes"] = [
                *evaluation["reason_codes"],
                f"provider_cli_exit_code:{attempt['return_code']}",
            ]
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
                "requested_session_id": assignment["requested_session_id"],
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
            "assigned_reviewer_count": 6,
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
    return ledger


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    ledger = run_first_direct_reviewer_calibration(args.project_root.resolve())
    print(json.dumps(ledger["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
