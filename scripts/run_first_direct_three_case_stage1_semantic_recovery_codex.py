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
from scripts.build_first_direct_three_case_stage1_semantic_recovery_protocol import (
    REVIEW_RELATIVE,
)
from scripts.record_first_direct_three_case_stage1_semantic_recovery import (
    _protocol,
    build_stage1_call_capture,
)
from scripts.run_first_direct_three_case_stage1_codex import _now, _run_one


def _system_prompt(project_root: Path, calls: list[dict[str, Any]]) -> str:
    config = load_effective_execution_configuration(project_root)
    prompt = str(config["role_configurations"]["stage1_reviewer"]["system_prompt"])
    digest = sha256_digest(prompt)
    if any(call["participant"].get("system_prompt_digest") != digest for call in calls):
        raise ValueError("A frozen Codex Stage-1 system prompt binding has drifted.")
    return prompt


def _attempt_paths(root: Path, participant_id: str) -> tuple[Path, Path]:
    slug = participant_id.removeprefix("actor:")
    return root / "codex-process-captures" / slug, root / "incoming" / f"{slug}.json"


def run_first_direct_three_case_stage1_semantic_recovery_codex(
    project_root: Path,
) -> list[dict[str, Any]]:
    """Run the two frozen Codex calls and retain both processes before assessing failure."""

    protocol = _protocol(project_root)
    calls = [item for item in protocol["calls"] if item["participant"]["provider"] == "OpenAI"]
    if len(calls) != 2:
        raise ValueError("The frozen recovery protocol does not contain two Codex Stage-1 calls.")

    root = project_root / REVIEW_RELATIVE
    for call in calls:
        process_root, incoming = _attempt_paths(root, str(call["participant_id"]))
        if (
            process_root.exists()
            or process_root.is_symlink()
            or incoming.exists()
            or incoming.is_symlink()
        ):
            raise ValueError(
                f"Codex Stage-1 semantic-recovery call {call['participant_id']} was already attempted."
            )

    system_prompt = _system_prompt(project_root, calls)

    def execute(call: dict[str, Any]) -> dict[str, Any]:
        try:
            return _run_one(
                project_root,
                call,
                system_prompt,
                enforce_output_schema=False,
            )
        except Exception as error:  # preserve both parallel attempt records before failing closed
            timestamp = _now()
            return {
                "participant_id": str(call["participant_id"]),
                "call": call,
                "started_at": timestamp,
                "completed_at": timestamp,
                "argv": [],
                "return_code": 125,
                "stdout": b"",
                "stderr": str(error).encode("utf-8", errors="backslashreplace"),
                "raw_response": b"",
                "process_error": f"transport_exception:{type(error).__name__}",
                "model_invoked": False,
            }

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(execute, calls))

    process_evidence: list[tuple[dict[str, Any], Path, dict[str, Any]]] = []
    for result in results:
        participant_id = str(result["participant_id"])
        process_root, _incoming = _attempt_paths(root, participant_id)
        process_root.mkdir(parents=True)
        atomic_write_bytes(process_root / "stdout.bin", result["stdout"])
        atomic_write_bytes(process_root / "stderr.bin", result["stderr"])
        atomic_write_bytes(process_root / "final-response.bin", result["raw_response"])
        process_record: dict[str, Any] = {
            "artifact_kind": (
                "direct_qualification_stage1_semantic_recovery_codex_process_capture"
            ),
            "capture_version": "1.0.0",
            "protocol_digest": protocol["protocol_digest"],
            "participant_id": participant_id,
            "call_identity_id": result["call"]["call_identity_id"],
            "argv_digest": semantic_digest(result["argv"]),
            "return_code": result["return_code"],
            "process_error": result["process_error"],
            "stdout_digest": sha256_digest(result["stdout"]),
            "stdout_byte_size": len(result["stdout"]),
            "stderr_digest": sha256_digest(result["stderr"]),
            "stderr_byte_size": len(result["stderr"]),
            "final_response_digest": sha256_digest(result["raw_response"]),
            "final_response_byte_size": len(result["raw_response"]),
            "started_at": result["started_at"],
            "completed_at": result["completed_at"],
            "api_output_schema_argument_present": False,
            "local_semantic_validation_profile": "stage1-semantic-payload-v2",
            "local_semantic_validation_required": True,
            "model_invoked": result.get("model_invoked", True),
            "project_code_executed": False,
            "qualification_authority": "none_process_capture_only",
        }
        process_record["capture_digest"] = semantic_digest(process_record)
        write_normalized_json_once(process_root / "capture.json", process_record)
        process_evidence.append((result, process_root, process_record))

    failures = [
        str(result["participant_id"])
        for result, _process_root, _process_record in process_evidence
        if result["return_code"] != 0 or not result["raw_response"]
    ]
    if failures:
        raise ValueError(
            "Codex Stage-1 semantic-recovery calls failed and exact process evidence was retained: "
            + ", ".join(sorted(failures))
        )

    captures: list[dict[str, Any]] = []
    for result, process_root, process_record in process_evidence:
        participant_id = str(result["participant_id"])
        _process_root, incoming = _attempt_paths(root, participant_id)
        capture = build_stage1_call_capture(
            project_root,
            participant_id,
            result["raw_response"],
            started_at=result["started_at"],
            completed_at=result["completed_at"],
            captured_at=_now(),
            transport={
                "surface": "Codex CLI exec",
                "ephemeral": True,
                "sandbox": "read-only",
                "external_network": False,
                "api_output_schema_argument_present": False,
                "local_semantic_validation_profile": "stage1-semantic-payload-v2",
                "local_semantic_validation_required": True,
                "process_capture_relative_path": process_root.relative_to(root).as_posix(),
                "process_capture_digest": process_record["capture_digest"],
            },
        )
        write_normalized_json_once(incoming, capture)
        captures.append(capture)
    return captures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    captures = run_first_direct_three_case_stage1_semantic_recovery_codex(
        arguments.project_root.resolve()
    )
    for capture in captures:
        print(capture["participant_id"], capture["capture_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
