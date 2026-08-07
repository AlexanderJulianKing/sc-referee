from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.storage.atomic import atomic_write_bytes
from scripts.build_first_direct_reviewer_calibration_protocol import (
    load_effective_execution_configuration,
)
from scripts.build_first_direct_stage1_recovery_fable_addition_calibration import (
    FABLE_ADDITION_RELATIVE,
)
from scripts.record_first_direct_stage1_recovery_fable_addition_calibration import (
    _now,
    _protocol,
    build_fable_addition_calibration_capture,
)

# The exact pinned entrypoint for the frozen agent version; the launcher symlink
# auto-updates and must not be used for a frozen configuration.
CLAUDE_PINNED = Path("/Users/alexanderking/.local/share/claude/versions/2.1.221")
TIMEOUT_SECONDS = 1800


def _attempt_paths(root: Path, participant_id: str) -> tuple[Path, Path]:
    slug = participant_id.removeprefix("actor:")
    return root / "process-captures" / slug, root / "incoming" / f"{slug}.json"


def _reserve_attempt_paths(root: Path, assignments: list[dict[str, Any]]) -> dict[str, Path]:
    incoming_root = root / "incoming"
    process_parent = root / "process-captures"
    incoming_root.mkdir(parents=True, exist_ok=True)
    process_parent.mkdir(parents=True, exist_ok=True)
    reserved: dict[str, Path] = {}
    for assignment in assignments:
        participant_id = str(assignment["participant_id"])
        process_root, incoming = _attempt_paths(root, participant_id)
        if incoming.exists() or incoming.is_symlink():
            raise FileExistsError(f"Fable addition capture already exists: {participant_id}")
        try:
            process_root.mkdir()
        except FileExistsError as error:
            raise FileExistsError(
                f"Fable addition attempt already reserved: {participant_id}"
            ) from error
        reserved[participant_id] = process_root
    return reserved


def _verify_pinned_binary(expected_version: str) -> None:
    if not CLAUDE_PINNED.exists():
        raise FileNotFoundError(f"The pinned Claude CLI binary is missing: {CLAUDE_PINNED}")
    completed = subprocess.run(
        [str(CLAUDE_PINNED), "--version"],
        capture_output=True,
        check=False,
        timeout=120,
        cwd=tempfile.gettempdir(),
    )
    reported = completed.stdout.decode("utf-8", errors="backslashreplace").strip()
    if completed.returncode != 0 or not reported.startswith(expected_version):
        raise ValueError(
            "The pinned Claude CLI binary does not report the frozen agent version "
            f"{expected_version!r}: {reported!r}"
        )


def _run_assignment(assignment: dict[str, Any], system_prompt: str) -> dict[str, Any]:
    started_at = _now()
    environment = dict(os.environ)
    environment["NO_COLOR"] = "1"
    with tempfile.TemporaryDirectory(prefix="sc-referee-claude-cli-calibration-") as temporary:
        working = Path(temporary)
        argv = [
            str(CLAUDE_PINNED),
            "--safe-mode",
            "--print",
            "--model",
            str(assignment["command_profile"]["model_alias_argument"]),
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
            "--session-id",
            str(assignment["call_identity_id"]),
            str(assignment["prompt"]),
        ]
        try:
            completed = subprocess.run(
                argv,
                cwd=working,
                env=environment,
                capture_output=True,
                check=False,
                timeout=TIMEOUT_SECONDS,
            )
            return_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
            process_error = None
        except subprocess.TimeoutExpired as error:
            return_code = 124
            stdout = error.stdout or b""
            stderr = error.stderr or b""
            process_error = f"timeout_{TIMEOUT_SECONDS}_seconds"
        completed_at = _now()
    return {
        "assignment": assignment,
        "argv": argv,
        "started_at": started_at,
        "completed_at": completed_at,
        "return_code": return_code,
        "stdout": stdout,
        "stderr": stderr,
        "process_error": process_error,
    }


def _parse_envelope(attempt: dict[str, Any]) -> tuple[str | None, dict[str, Any], str | None]:
    """Return (raw_response, envelope_metadata, transport_error)."""
    metadata: dict[str, Any] = {
        "reported_session_id": None,
        "provider_result_subtype": None,
        "provider_is_error": None,
        "provider_usage": None,
        "provider_model_usage_ids": None,
    }
    if attempt["return_code"] != 0:
        return None, metadata, f"provider_cli_exit_code:{attempt['return_code']}"
    try:
        envelope = json.loads(attempt["stdout"].decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as error:
        return None, metadata, f"envelope_parse:{type(error).__name__}"
    metadata = {
        "reported_session_id": envelope.get("session_id"),
        "provider_result_subtype": envelope.get("subtype"),
        "provider_is_error": envelope.get("is_error"),
        "provider_usage": envelope.get("usage"),
    }
    if envelope.get("is_error") is not False:
        return None, metadata, "provider_reported_error"
    requested = str(attempt["assignment"]["call_identity_id"])
    if envelope.get("session_id") != requested:
        return None, metadata, "reported_session_id_mismatch"
    served_models = set(envelope.get("modelUsage", {}))
    metadata["provider_model_usage_ids"] = sorted(served_models)
    if str(attempt["assignment"]["model_id"]) not in served_models:
        return None, metadata, "served_model_mismatch"
    result = envelope.get("result")
    if not isinstance(result, str) or not result.strip():
        return None, metadata, "missing_result_text"
    return result, metadata, None


def run_first_direct_stage1_recovery_fable_addition_calibration(
    project_root: Path,
) -> list[dict[str, Any]]:
    protocol = _protocol(project_root)
    assignments = sorted(protocol["assignments"], key=lambda item: str(item["participant_id"]))
    if len(assignments) != 2 or any(item["provider"] != "Anthropic" for item in assignments):
        raise ValueError(
            "The replacement protocol does not contain exactly two Claude assignments."
        )

    config = load_effective_execution_configuration(project_root)
    system_prompt = str(config["role_configurations"]["stage1_reviewer"]["system_prompt"])
    system_prompt_digest = sha256_digest(system_prompt)
    if any(item["system_prompt_digest"] != system_prompt_digest for item in assignments):
        raise ValueError("A Fable addition system prompt binding has drifted.")
    expected_versions = {str(item["agent_version"]) for item in assignments}
    if len(expected_versions) != 1:
        raise ValueError("The Fable addition assignments disagree on the agent version.")
    _verify_pinned_binary(next(iter(expected_versions)))

    root = project_root / FABLE_ADDITION_RELATIVE
    process_roots = _reserve_attempt_paths(root, assignments)

    def execute(assignment: dict[str, Any]) -> dict[str, Any]:
        try:
            return _run_assignment(assignment, system_prompt)
        except Exception as error:  # retain both parallel attempts before failing closed
            timestamp = _now()
            return {
                "assignment": assignment,
                "argv": [],
                "started_at": timestamp,
                "completed_at": timestamp,
                "return_code": 125,
                "stdout": b"",
                "stderr": str(error).encode("utf-8", errors="backslashreplace"),
                "process_error": f"transport_exception:{type(error).__name__}",
            }

    with ThreadPoolExecutor(max_workers=2) as executor:
        attempts = list(executor.map(execute, assignments))

    parsed: list[tuple[dict[str, Any], Path, dict[str, Any], str | None, dict[str, Any]]] = []
    for attempt in attempts:
        assignment = attempt["assignment"]
        participant_id = str(assignment["participant_id"])
        process_root = process_roots[participant_id]
        raw_response, envelope_metadata, transport_error = _parse_envelope(attempt)
        result_bytes = raw_response.encode("utf-8") if raw_response is not None else b""
        atomic_write_bytes(process_root / "stdout.bin", attempt["stdout"])
        atomic_write_bytes(process_root / "stderr.bin", attempt["stderr"])
        atomic_write_bytes(process_root / "final-response.bin", result_bytes)
        process_capture: dict[str, Any] = {
            "artifact_kind": (
                "direct_qualification_stage1_recovery_fable_addition_calibration_process_capture"
            ),
            "capture_version": "1.0.0",
            "protocol_digest": protocol["protocol_digest"],
            "participant_id": participant_id,
            "call_identity_id": assignment["call_identity_id"],
            "argv_digest": semantic_digest(attempt["argv"]),
            "return_code": attempt["return_code"],
            "process_error": attempt["process_error"],
            "transport_error": transport_error,
            "reported_session_id": envelope_metadata["reported_session_id"],
            "provider_result_subtype": envelope_metadata["provider_result_subtype"],
            "provider_is_error": envelope_metadata["provider_is_error"],
            "provider_usage": envelope_metadata["provider_usage"],
            "provider_model_usage_ids": envelope_metadata["provider_model_usage_ids"],
            "stdout_digest": sha256_digest(attempt["stdout"]),
            "stdout_byte_size": len(attempt["stdout"]),
            "stderr_digest": sha256_digest(attempt["stderr"]),
            "stderr_byte_size": len(attempt["stderr"]),
            "final_response_digest": sha256_digest(result_bytes),
            "final_response_byte_size": len(result_bytes),
            "started_at": attempt["started_at"],
            "completed_at": attempt["completed_at"],
            "model_invoked": attempt["return_code"] == 0,
            "project_code_executed": False,
            "qualification_authority": "none_process_capture_only",
        }
        process_capture["capture_digest"] = semantic_digest(process_capture)
        write_normalized_json_once(process_root / "capture.json", process_capture)
        parsed.append((attempt, process_root, process_capture, raw_response, envelope_metadata))

    failures = [
        f"{attempt['assignment']['participant_id']}:{process_capture['transport_error'] or process_capture['process_error']}"
        for attempt, _process_root, process_capture, raw_response, _metadata in parsed
        if raw_response is None
    ]
    if failures:
        raise ValueError(
            "Fable addition calibrations failed; all process evidence was retained: "
            + ", ".join(sorted(failures))
        )

    captures: list[dict[str, Any]] = []
    for attempt, process_root, process_capture, raw_response, envelope_metadata in parsed:
        assignment = attempt["assignment"]
        participant_id = str(assignment["participant_id"])
        assert raw_response is not None
        capture = build_fable_addition_calibration_capture(
            project_root,
            participant_id,
            raw_response,
            started_at=attempt["started_at"],
            completed_at=attempt["completed_at"],
            captured_at=_now(),
            transport={
                "surface": "Claude Code CLI print mode",
                "binary_path": str(CLAUDE_PINNED),
                "safe_mode": True,
                "tools_disabled": True,
                "mcp_servers": "empty_strict",
                "permission_mode": "dontAsk",
                "session_persistence": False,
                "output_format": "json",
                "json_schema_argument_present": False,
                "reported_session_id": envelope_metadata["reported_session_id"],
                "process_capture_relative_path": process_root.relative_to(root).as_posix(),
                "process_capture_digest": process_capture["capture_digest"],
            },
        )
        _process_root, incoming = _attempt_paths(root, participant_id)
        write_normalized_json_once(incoming, capture)
        captures.append(capture)
    return sorted(captures, key=lambda item: str(item["participant_id"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    captures = run_first_direct_stage1_recovery_fable_addition_calibration(
        arguments.project_root.resolve()
    )
    for capture in captures:
        print(capture["participant_id"], capture["capture_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
