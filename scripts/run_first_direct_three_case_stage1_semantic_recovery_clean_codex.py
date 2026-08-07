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
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_protocol import (
    REVIEW_RELATIVE,
)
from scripts.record_first_direct_three_case_stage1_semantic_recovery_clean import (
    _protocol,
    build_stage1_call_capture,
)
from scripts.run_first_direct_three_case_stage1_codex import _now, _run_one

CODEX_PARTICIPANT_IDS = (
    "actor:stage1-recovery-codex-03",
    "actor:stage1-recovery-codex-04",
)


def _system_prompt(project_root: Path, calls: list[dict[str, Any]]) -> str:
    config = load_effective_execution_configuration(project_root)
    prompt = str(config["role_configurations"]["stage1_reviewer"]["system_prompt"])
    digest = sha256_digest(prompt)
    if any(call["participant"].get("system_prompt_digest") != digest for call in calls):
        raise ValueError("A frozen clean-panel Codex system-prompt binding has drifted.")
    return prompt


def _attempt_paths(root: Path, participant_id: str) -> tuple[Path, Path]:
    slug = participant_id.removeprefix("actor:")
    return root / "codex-process-captures" / slug, root / "incoming" / f"{slug}.json"


def _reserve_attempt_paths(root: Path, calls: list[dict[str, Any]]) -> dict[str, Path]:
    incoming_root = root / "incoming"
    process_parent = root / "codex-process-captures"
    incoming_root.mkdir(parents=True, exist_ok=True)
    process_parent.mkdir(parents=True, exist_ok=True)
    reserved: dict[str, Path] = {}
    for call in calls:
        participant_id = str(call["participant_id"])
        process_root, incoming = _attempt_paths(root, participant_id)
        if incoming.exists() or incoming.is_symlink():
            raise FileExistsError(f"Clean-panel Codex capture already exists: {participant_id}")
        try:
            process_root.mkdir()
        except FileExistsError as error:
            raise FileExistsError(
                f"Clean-panel Codex attempt already reserved: {participant_id}"
            ) from error
        reserved[participant_id] = process_root
    return reserved


def run_first_direct_three_case_stage1_semantic_recovery_clean_codex(
    project_root: Path,
) -> list[dict[str, Any]]:
    """Run both fresh clean-panel Codex calls and retain both processes before failure."""

    protocol = _protocol(project_root)
    calls = sorted(
        (item for item in protocol["calls"] if item["participant"]["provider"] == "OpenAI"),
        key=lambda item: str(item["participant_id"]),
    )
    if (
        len(calls) != 2
        or tuple(str(item["participant_id"]) for item in calls) != CODEX_PARTICIPANT_IDS
    ):
        raise ValueError("The frozen clean-panel protocol lacks the exact two Codex calls.")

    system_prompt = _system_prompt(project_root, calls)
    root = project_root / REVIEW_RELATIVE
    process_roots = _reserve_attempt_paths(root, calls)

    def execute(call: dict[str, Any]) -> dict[str, Any]:
        try:
            return _run_one(
                project_root,
                call,
                system_prompt,
                enforce_output_schema=False,
            )
        except Exception as error:  # retain both parallel attempts before failing closed
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
        process_root = process_roots[participant_id]
        atomic_write_bytes(process_root / "stdout.bin", result["stdout"])
        atomic_write_bytes(process_root / "stderr.bin", result["stderr"])
        atomic_write_bytes(process_root / "final-response.bin", result["raw_response"])
        process_record: dict[str, Any] = {
            "artifact_kind": (
                "direct_qualification_stage1_semantic_recovery_clean_codex_process_capture"
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
            "Clean-panel Codex calls failed; both exact process records were retained: "
            + ", ".join(sorted(failures))
        )

    captures: list[dict[str, Any]] = []
    for result, process_root, process_record in process_evidence:
        participant_id = str(result["participant_id"])
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
        _reserved_root, incoming = _attempt_paths(root, participant_id)
        write_normalized_json_once(incoming, capture)
        captures.append(capture)
    return sorted(captures, key=lambda item: str(item["participant_id"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    captures = run_first_direct_three_case_stage1_semantic_recovery_clean_codex(
        arguments.project_root.resolve()
    )
    for capture in captures:
        print(capture["participant_id"], capture["capture_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
