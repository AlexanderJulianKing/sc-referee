from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.storage.atomic import atomic_write_bytes
from scripts.build_first_direct_reviewer_calibration_protocol import (
    load_effective_execution_configuration,
)
from scripts.build_first_direct_stage1_recovery_codex_replacement_calibration import (
    CODEX_REPLACEMENT_RELATIVE,
)
from scripts.record_first_direct_stage1_recovery_codex_replacement_calibration import (
    _now,
    _protocol,
    build_codex_replacement_calibration_capture,
)
from scripts.run_first_direct_reviewer_calibration import _run_assignment


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
            raise FileExistsError(f"Codex replacement capture already exists: {participant_id}")
        try:
            process_root.mkdir()
        except FileExistsError as error:
            raise FileExistsError(
                f"Codex replacement attempt already reserved: {participant_id}"
            ) from error
        reserved[participant_id] = process_root
    return reserved


def run_first_direct_stage1_recovery_codex_replacement_calibration(
    project_root: Path,
) -> list[dict[str, Any]]:
    protocol = _protocol(project_root)
    assignments = sorted(protocol["assignments"], key=lambda item: str(item["participant_id"]))
    if len(assignments) != 2 or any(item["provider"] != "OpenAI" for item in assignments):
        raise ValueError("The replacement protocol does not contain exactly two Codex assignments.")

    config = load_effective_execution_configuration(project_root)
    system_prompt = str(config["role_configurations"]["stage1_reviewer"]["system_prompt"])
    system_prompt_digest = sha256_digest(system_prompt)
    if any(item["system_prompt_digest"] != system_prompt_digest for item in assignments):
        raise ValueError("A Codex replacement system prompt binding has drifted.")

    root = project_root / CODEX_REPLACEMENT_RELATIVE
    process_roots = _reserve_attempt_paths(root, assignments)

    def execute(assignment: dict[str, Any]) -> dict[str, Any]:
        runnable = {**assignment, "user_prompt": assignment["prompt"]}
        try:
            return _run_assignment(runnable, system_prompt)
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
                "final": b"",
                "process_error": f"transport_exception:{type(error).__name__}",
                "model_invoked": False,
            }

    with ThreadPoolExecutor(max_workers=2) as executor:
        attempts = list(executor.map(execute, assignments))

    process_evidence: list[tuple[dict[str, Any], Path, dict[str, Any]]] = []
    for attempt in attempts:
        assignment = attempt["assignment"]
        participant_id = str(assignment["participant_id"])
        process_root = process_roots[participant_id]
        atomic_write_bytes(process_root / "stdout.bin", attempt["stdout"])
        atomic_write_bytes(process_root / "stderr.bin", attempt["stderr"])
        atomic_write_bytes(process_root / "final-response.bin", attempt["final"])
        process_capture: dict[str, Any] = {
            "artifact_kind": (
                "direct_qualification_stage1_recovery_codex_replacement_calibration_process_capture"
            ),
            "capture_version": "1.0.0",
            "protocol_digest": protocol["protocol_digest"],
            "participant_id": participant_id,
            "call_identity_id": assignment["call_identity_id"],
            "argv_digest": semantic_digest(attempt["argv"]),
            "return_code": attempt["return_code"],
            "process_error": attempt["process_error"],
            "stdout_digest": sha256_digest(attempt["stdout"]),
            "stdout_byte_size": len(attempt["stdout"]),
            "stderr_digest": sha256_digest(attempt["stderr"]),
            "stderr_byte_size": len(attempt["stderr"]),
            "final_response_digest": sha256_digest(attempt["final"]),
            "final_response_byte_size": len(attempt["final"]),
            "started_at": attempt["started_at"],
            "completed_at": attempt["completed_at"],
            "model_invoked": attempt.get("model_invoked", True),
            "project_code_executed": False,
            "qualification_authority": "none_process_capture_only",
        }
        process_capture["capture_digest"] = semantic_digest(process_capture)
        write_normalized_json_once(process_root / "capture.json", process_capture)
        process_evidence.append((attempt, process_root, process_capture))

    failures = [
        str(attempt["assignment"]["participant_id"])
        for attempt, _process_root, _process_capture in process_evidence
        if attempt["return_code"] != 0 or not attempt["final"]
    ]
    if failures:
        raise ValueError(
            "Codex replacement calibrations failed; all process evidence was retained: "
            + ", ".join(sorted(failures))
        )

    captures: list[dict[str, Any]] = []
    for attempt, process_root, process_capture in process_evidence:
        assignment = attempt["assignment"]
        participant_id = str(assignment["participant_id"])
        raw_response = attempt["final"].decode("utf-8")
        capture = build_codex_replacement_calibration_capture(
            project_root,
            participant_id,
            raw_response,
            started_at=attempt["started_at"],
            completed_at=attempt["completed_at"],
            captured_at=_now(),
            transport={
                "surface": "Codex CLI exec",
                "ephemeral": True,
                "sandbox": "read-only",
                "external_network": False,
                "api_output_schema_argument_present": True,
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
    captures = run_first_direct_stage1_recovery_codex_replacement_calibration(
        arguments.project_root.resolve()
    )
    for capture in captures:
        print(capture["participant_id"], capture["capture_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
