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
from scripts.build_first_direct_stage1_recovery_calibration import CALIBRATION_RELATIVE
from scripts.record_first_direct_stage1_recovery_calibration import (
    _now,
    _protocol,
    build_recovery_calibration_capture,
)
from scripts.run_first_direct_reviewer_calibration import _run_assignment


def run_first_direct_stage1_recovery_calibration_codex(
    project_root: Path,
) -> list[dict[str, Any]]:
    protocol = _protocol(project_root)
    root = project_root / CALIBRATION_RELATIVE
    config = load_effective_execution_configuration(project_root)
    system_prompt = str(config["role_configurations"]["stage1_reviewer"]["system_prompt"])
    assignments = [item for item in protocol["assignments"] if item["provider"] == "OpenAI"]
    if len(assignments) != 2:
        raise ValueError("The recovery protocol does not contain exactly two Codex calibrations.")
    for assignment in assignments:
        if sha256_digest(system_prompt) != assignment["system_prompt_digest"]:
            raise ValueError("The recovery calibration system prompt binding has drifted.")
        slug = str(assignment["participant_id"]).removeprefix("actor:")
        if (root / "process-captures" / slug).exists() or (
            root / "incoming" / f"{slug}.json"
        ).exists():
            raise FileExistsError(f"Recovery calibration already attempted: {slug}")

    def execute(assignment: dict[str, Any]) -> dict[str, Any]:
        runnable = {**assignment, "user_prompt": assignment["prompt"]}
        return _run_assignment(runnable, system_prompt)

    with ThreadPoolExecutor(max_workers=2) as executor:
        attempts = list(executor.map(execute, assignments))

    captures = []
    for attempt in attempts:
        assignment = attempt["assignment"]
        participant_id = str(assignment["participant_id"])
        slug = participant_id.removeprefix("actor:")
        process_root = root / "process-captures" / slug
        process_root.mkdir(parents=True)
        atomic_write_bytes(process_root / "stdout.bin", attempt["stdout"])
        atomic_write_bytes(process_root / "stderr.bin", attempt["stderr"])
        atomic_write_bytes(process_root / "final-response.bin", attempt["final"])
        process_capture: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_recovery_calibration_process_capture",
            "capture_version": "1.0.0",
            "protocol_digest": protocol["protocol_digest"],
            "participant_id": participant_id,
            "call_identity_id": assignment["call_identity_id"],
            "argv_digest": semantic_digest(attempt["argv"]),
            "return_code": attempt["return_code"],
            "process_error": attempt["process_error"],
            "stdout_digest": sha256_digest(attempt["stdout"]),
            "stderr_digest": sha256_digest(attempt["stderr"]),
            "final_response_digest": sha256_digest(attempt["final"]),
            "started_at": attempt["started_at"],
            "completed_at": attempt["completed_at"],
            "model_invoked": True,
            "project_code_executed": False,
            "qualification_authority": "none_process_capture_only",
        }
        process_capture["capture_digest"] = semantic_digest(process_capture)
        write_normalized_json_once(process_root / "capture.json", process_capture)
        if attempt["return_code"] != 0 or not attempt["final"]:
            raise ValueError(
                f"Codex recovery calibration failed; process evidence retained for {participant_id}."
            )
        raw_response = attempt["final"].decode("utf-8")
        capture = build_recovery_calibration_capture(
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
        incoming = root / "incoming" / f"{slug}.json"
        write_normalized_json_once(incoming, capture)
        captures.append(capture)
    return sorted(captures, key=lambda item: str(item["participant_id"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    captures = run_first_direct_stage1_recovery_calibration_codex(arguments.project_root.resolve())
    for capture in captures:
        print(capture["participant_id"], capture["capture_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
