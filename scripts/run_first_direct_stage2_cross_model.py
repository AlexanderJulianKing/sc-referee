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

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.storage.atomic import atomic_write_bytes
from scripts.build_first_direct_reviewer_calibration_protocol import (
    load_effective_execution_configuration,
)
from scripts.build_first_direct_stage2_cross_model_protocol import (
    STAGE2_REVIEW_RELATIVE,
    STAGE2_REVIEWERS,
)
from scripts.record_first_direct_stage2_cross_model import (
    _expected_protocol_digest,
    _protocol,
    build_stage2_call_capture,
)
from scripts.run_first_direct_stage1_recovery_claude_cli_replacement_calibration import (
    CLAUDE_PINNED,
    _verify_pinned_binary,
)

TIMEOUT_SECONDS = 3600


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _attempt_paths(root: Path, participant_id: str) -> tuple[Path, Path]:
    slug = participant_id.removeprefix("actor:")
    return (
        root / "stage2-cli-process-captures" / slug,
        root / "incoming" / f"{slug}.json",
    )


def _reserve_attempt_paths(root: Path, calls: list[dict[str, Any]]) -> dict[str, Path]:
    incoming_root = root / "incoming"
    process_parent = root / "stage2-cli-process-captures"
    incoming_root.mkdir(parents=True, exist_ok=True)
    process_parent.mkdir(parents=True, exist_ok=True)
    reserved: dict[str, Path] = {}
    for call in calls:
        participant_id = str(call["participant_id"])
        process_root, incoming = _attempt_paths(root, participant_id)
        if incoming.exists() or incoming.is_symlink():
            raise FileExistsError(f"Stage-2 cross-model capture already exists: {participant_id}")
        try:
            process_root.mkdir()
        except FileExistsError as error:
            raise FileExistsError(
                f"Stage-2 cross-model attempt already reserved: {participant_id}"
            ) from error
        reserved[participant_id] = process_root
    return reserved


def _system_prompt(project_root: Path, calls: list[dict[str, Any]]) -> str:
    config = load_effective_execution_configuration(project_root)
    prompt = str(config["role_configurations"]["stage1_reviewer"]["system_prompt"])
    digest = sha256_digest(prompt)
    if any(call["participant"].get("system_prompt_digest") != digest for call in calls):
        raise ValueError("A Stage-2 cross-model system-prompt binding has drifted.")
    return prompt


def _run_one(call: dict[str, Any], system_prompt: str) -> dict[str, Any]:
    started_at = _now()
    environment = dict(os.environ)
    environment["NO_COLOR"] = "1"
    with tempfile.TemporaryDirectory(prefix="sc-referee-stage2-cli-") as temporary:
        working = Path(temporary)
        argv = [
            str(CLAUDE_PINNED),
            "--safe-mode",
            "--print",
            "--model",
            str(call["command_profile"]["model_alias_argument"]),
            "--effort",
            str(call["participant"]["reasoning_configuration"]),
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
            str(call["call_identity_id"]),
            str(call["prompt"]),
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
        "participant_id": str(call["participant_id"]),
        "call": call,
        "argv": argv,
        "started_at": started_at,
        "completed_at": completed_at,
        "return_code": return_code,
        "stdout": stdout,
        "stderr": stderr,
        "process_error": process_error,
    }


def _parse_envelope(result: dict[str, Any]) -> tuple[bytes, dict[str, Any], str | None]:
    metadata: dict[str, Any] = {
        "reported_session_id": None,
        "provider_result_subtype": None,
        "provider_is_error": None,
        "provider_usage": None,
        "provider_model_usage_ids": None,
    }
    if result["return_code"] != 0:
        return b"", metadata, f"provider_cli_exit_code:{result['return_code']}"
    try:
        envelope = json.loads(result["stdout"].decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as error:
        return b"", metadata, f"envelope_parse:{type(error).__name__}"
    metadata = {
        "reported_session_id": envelope.get("session_id"),
        "provider_result_subtype": envelope.get("subtype"),
        "provider_is_error": envelope.get("is_error"),
        "provider_usage": envelope.get("usage"),
        "provider_model_usage_ids": sorted(set(envelope.get("modelUsage", {}))),
    }
    if envelope.get("is_error") is not False:
        return b"", metadata, "provider_reported_error"
    if envelope.get("session_id") != str(result["call"]["call_identity_id"]):
        return b"", metadata, "reported_session_id_mismatch"
    if str(result["call"]["participant"]["model_id"]) not in set(envelope.get("modelUsage", {})):
        return b"", metadata, "served_model_mismatch"
    text = envelope.get("result")
    if not isinstance(text, str) or not text.strip():
        return b"", metadata, "missing_result_text"
    return text.encode("utf-8"), metadata, None


def run_first_direct_stage2_cross_model_cli(project_root: Path) -> list[dict[str, Any]]:
    """Run both frozen Fable panel-completion calls and retain both processes before failure."""

    protocol = _protocol(project_root)
    calls = sorted(protocol["calls"], key=lambda item: str(item["participant_id"]))
    if len(calls) != 2 or tuple(str(item["participant_id"]) for item in calls) != tuple(
        sorted(STAGE2_REVIEWERS)
    ):
        raise ValueError("The frozen amendment lacks the exact two Stage-2 cross-model calls.")

    system_prompt = _system_prompt(project_root, calls)
    expected_versions = {str(item["participant"]["agent_version"]) for item in calls}
    if len(expected_versions) != 1:
        raise ValueError("The Stage-2 cross-model calls disagree on the agent version.")
    _verify_pinned_binary(next(iter(expected_versions)))

    root = project_root / STAGE2_REVIEW_RELATIVE
    process_roots = _reserve_attempt_paths(root, calls)

    def execute(call: dict[str, Any]) -> dict[str, Any]:
        try:
            return _run_one(call, system_prompt)
        except Exception as error:  # retain both parallel attempts before failing closed
            timestamp = _now()
            return {
                "participant_id": str(call["participant_id"]),
                "call": call,
                "argv": [],
                "started_at": timestamp,
                "completed_at": timestamp,
                "return_code": 125,
                "stdout": b"",
                "stderr": str(error).encode("utf-8", errors="backslashreplace"),
                "process_error": f"transport_exception:{type(error).__name__}",
            }

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(execute, calls))

    process_evidence: list[tuple[dict[str, Any], Path, dict[str, Any], bytes]] = []
    for result in results:
        participant_id = str(result["participant_id"])
        process_root = process_roots[participant_id]
        raw_response, envelope_metadata, transport_error = _parse_envelope(result)
        atomic_write_bytes(process_root / "stdout.bin", result["stdout"])
        atomic_write_bytes(process_root / "stderr.bin", result["stderr"])
        atomic_write_bytes(process_root / "final-response.bin", raw_response)
        process_record: dict[str, Any] = {
            "artifact_kind": ("direct_qualification_stage2_cross_model_cli_process_capture"),
            "capture_version": "1.0.0",
            "protocol_digest": _expected_protocol_digest(),
            "participant_id": participant_id,
            "call_identity_id": result["call"]["call_identity_id"],
            "argv_digest": semantic_digest(result["argv"]),
            "return_code": result["return_code"],
            "process_error": result["process_error"],
            "transport_error": transport_error,
            "reported_session_id": envelope_metadata["reported_session_id"],
            "provider_result_subtype": envelope_metadata["provider_result_subtype"],
            "provider_is_error": envelope_metadata["provider_is_error"],
            "provider_usage": envelope_metadata["provider_usage"],
            "provider_model_usage_ids": envelope_metadata["provider_model_usage_ids"],
            "stdout_digest": sha256_digest(result["stdout"]),
            "stdout_byte_size": len(result["stdout"]),
            "stderr_digest": sha256_digest(result["stderr"]),
            "stderr_byte_size": len(result["stderr"]),
            "final_response_digest": sha256_digest(raw_response),
            "final_response_byte_size": len(raw_response),
            "started_at": result["started_at"],
            "completed_at": result["completed_at"],
            "api_output_schema_argument_present": False,
            "local_semantic_validation_profile": "stage1-semantic-payload-v2",
            "local_semantic_validation_required": True,
            "model_invoked": result["return_code"] == 0,
            "project_code_executed": False,
            "qualification_authority": "none_process_capture_only",
        }
        process_record["capture_digest"] = semantic_digest(process_record)
        write_normalized_json_once(process_root / "capture.json", process_record)
        process_evidence.append((result, process_root, process_record, raw_response))

    failures = [
        f"{record['participant_id']}:{record['transport_error'] or record['process_error']}"
        for _result, _root, record, raw_response in process_evidence
        if not raw_response
    ]
    if failures:
        raise ValueError(
            "Stage-2 cross-model calls failed; both exact process records were retained: "
            + ", ".join(sorted(failures))
        )

    captures: list[dict[str, Any]] = []
    for result, process_root, process_record, raw_response in process_evidence:
        participant_id = str(result["participant_id"])
        capture = build_stage2_call_capture(
            project_root,
            participant_id,
            raw_response,
            started_at=result["started_at"],
            completed_at=result["completed_at"],
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
                "model_alias_argument": str(
                    result["call"]["command_profile"]["model_alias_argument"]
                ),
                "served_model_verified": str(result["call"]["participant"]["model_id"]),
                "api_output_schema_argument_present": False,
                "local_semantic_validation_profile": "stage1-semantic-payload-v2",
                "local_semantic_validation_required": True,
                "reported_session_id": process_record["reported_session_id"],
                "process_capture_relative_path": process_root.relative_to(root).as_posix(),
                "process_capture_digest": process_record["capture_digest"],
            },
        )
        _reserved_root, incoming = _attempt_paths(root, participant_id)
        write_normalized_json_once(incoming, capture)
        captures.append(capture)
    return sorted(captures, key=lambda item: str(item["participant_id"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    captures = run_first_direct_stage2_cross_model_cli(arguments.project_root.resolve())
    for capture in captures:
        print(capture["participant_id"], capture["capture_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
