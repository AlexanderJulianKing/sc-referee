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

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.storage.atomic import atomic_write_bytes
from scripts.build_v120_lean_pilot_authoring import V120_AUTHORING_RELATIVE
from scripts.run_first_direct_stage1_recovery_claude_cli_replacement_calibration import (
    CLAUDE_PINNED,
    _verify_pinned_binary,
)

PROTOCOL_DIGEST: str | None = (
    "sha256:a4744397f1017b93c4b69bde937e381efd5b3692ca7d85bc41f4cf8ad2f5396b"
)
TIMEOUT_SECONDS = 3600


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _protocol(project_root: Path) -> dict[str, Any]:
    if PROTOCOL_DIGEST is None:
        raise ValueError("The v120 authoring protocol digest has not been frozen.")
    protocol = _load(project_root / V120_AUTHORING_RELATIVE / "PILOT_AUTHORING_PROTOCOL.json")
    supplied = protocol.pop("protocol_digest", None)
    if supplied != PROTOCOL_DIGEST or supplied != semantic_digest(protocol):
        raise ValueError("The v120 authoring protocol does not replay.")
    protocol["protocol_digest"] = supplied
    if (
        protocol.get("execution_state") != "frozen_not_started"
        or len(protocol.get("author_assignments", [])) != 2
        or protocol.get("scientific_label_count") != 0
        or protocol.get("detector_outcome_count") != 0
    ):
        raise ValueError("The v120 authoring protocol state is invalid.")
    for assignment in protocol["author_assignments"]:
        if assignment.get("prompt_digest") != sha256_digest(str(assignment["prompt"])):
            raise ValueError("A v120 author prompt does not replay.")
    return protocol


def _run_one(assignment: dict[str, Any]) -> dict[str, Any]:
    started_at = _now()
    environment = dict(os.environ)
    environment["NO_COLOR"] = "1"
    with tempfile.TemporaryDirectory(prefix="sc-referee-v120-author-") as temporary:
        argv = [
            str(CLAUDE_PINNED),
            "--safe-mode",
            "--print",
            "--model",
            str(assignment["command_profile"]["model_alias_argument"]),
            "--effort",
            str(assignment["participant"]["reasoning_configuration"]),
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
                cwd=temporary,
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


def run_v120_lean_pilot_authors(project_root: Path) -> list[str]:
    protocol = _protocol(project_root)
    assignments = sorted(
        protocol["author_assignments"],
        key=lambda item: str(item["participant"]["participant_id"]),
    )
    versions = {str(item["participant"]["agent_version"]) for item in assignments}
    if len(versions) != 1:
        raise ValueError("The v120 author assignments disagree on the agent version.")
    _verify_pinned_binary(next(iter(versions)))

    root = project_root / V120_AUTHORING_RELATIVE
    incoming_root = root / "incoming"
    process_parent = root / "author-cli-process-captures"
    incoming_root.mkdir(exist_ok=True)
    process_parent.mkdir(exist_ok=True)
    reserved: dict[str, Path] = {}
    for assignment in assignments:
        participant_id = str(assignment["participant"]["participant_id"])
        slug = participant_id.removeprefix("actor:")
        incoming = incoming_root / f"{slug}.json"
        process_root = process_parent / slug
        if incoming.exists() or incoming.is_symlink():
            raise FileExistsError(f"A v120 author attempt already exists: {participant_id}")
        process_root.mkdir()
        reserved[participant_id] = process_root

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(_run_one, assignments))

    written: list[str] = []
    failures: list[str] = []
    for result in results:
        assignment = result["assignment"]
        participant = assignment["participant"]
        participant_id = str(participant["participant_id"])
        process_root = reserved[participant_id]
        atomic_write_bytes(process_root / "stdout.bin", result["stdout"])
        atomic_write_bytes(process_root / "stderr.bin", result["stderr"])
        raw_response = None
        metadata: dict[str, Any] = {}
        transport_error = result["process_error"]
        if result["return_code"] == 0 and transport_error is None:
            try:
                envelope = json.loads(result["stdout"].decode("utf-8"))
                metadata = {
                    "reported_session_id": envelope.get("session_id"),
                    "provider_is_error": envelope.get("is_error"),
                    "served_model_ids": sorted(set(envelope.get("modelUsage", {}))),
                }
                if envelope.get("is_error") is not False:
                    transport_error = "provider_reported_error"
                elif envelope.get("session_id") != str(assignment["call_identity_id"]):
                    transport_error = "reported_session_id_mismatch"
                elif str(participant["model_id"]) not in set(envelope.get("modelUsage", {})):
                    transport_error = "served_model_mismatch"
                else:
                    text = envelope.get("result")
                    if isinstance(text, str) and text.strip():
                        raw_response = text
                    else:
                        transport_error = "missing_result_text"
            except (ValueError, json.JSONDecodeError) as error:
                transport_error = f"envelope_parse:{type(error).__name__}"
        else:
            transport_error = transport_error or f"provider_cli_exit_code:{result['return_code']}"

        process_capture = {
            "artifact_kind": "direct_qualification_v120_author_cli_process_capture",
            "capture_version": "1.0.0",
            "protocol_digest": protocol["protocol_digest"],
            "participant_id": participant_id,
            "call_identity_id": assignment["call_identity_id"],
            "argv_digest": semantic_digest(result["argv"]),
            "return_code": result["return_code"],
            "process_error": result["process_error"],
            "transport_error": transport_error,
            "stdout_digest": sha256_digest(result["stdout"]),
            "stderr_digest": sha256_digest(result["stderr"]),
            "started_at": result["started_at"],
            "completed_at": result["completed_at"],
            "served_model_ids": metadata.get("served_model_ids"),
            "model_invoked": result["return_code"] == 0,
            "project_code_executed": False,
            "qualification_authority": "none_process_capture_only",
        }
        process_capture["capture_digest"] = semantic_digest(process_capture)
        write_normalized_json_once(process_root / "capture.json", process_capture)

        if raw_response is None:
            failures.append(f"{participant_id}:{transport_error}")
            continue
        attempt = {
            "participant_id": participant_id,
            "call_identity_id": assignment["call_identity_id"],
            "protocol_digest": protocol["protocol_digest"],
            "configuration_digest": participant["configuration_digest"],
            "prompt_digest": assignment["prompt_digest"],
            "output_schema_digest": assignment["output_schema_digest"],
            "replacement_count": 0,
            "started_at": result["started_at"],
            "completed_at": result["completed_at"],
            "attempt_status": "response_retained",
            "exit_code": 0,
            "reported_session_id": metadata["reported_session_id"],
            "served_model_ids": metadata["served_model_ids"],
            "process_capture_digest": process_capture["capture_digest"],
            "raw_response": raw_response,
        }
        slug = participant_id.removeprefix("actor:")
        write_normalized_json_once(incoming_root / f"{slug}.json", attempt)
        written.append(participant_id)
    if failures:
        raise ValueError(
            "V120 author calls failed; all process evidence was retained: "
            + ", ".join(sorted(failures))
        )
    return written


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    for participant_id in run_v120_lean_pilot_authors(arguments.project_root.resolve()):
        print(participant_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
