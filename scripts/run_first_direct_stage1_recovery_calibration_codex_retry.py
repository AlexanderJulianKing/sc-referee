from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.storage.atomic import atomic_write_bytes
from scripts.build_first_direct_reviewer_calibration_protocol import (
    load_effective_execution_configuration,
)
from scripts.build_first_direct_stage1_recovery_calibration import CALIBRATION_RELATIVE
from scripts.build_first_direct_stage1_recovery_calibration_codex_retry import AMENDMENT_NAME
from scripts.record_first_direct_stage1_recovery_calibration import (
    _now,
    _protocol,
    build_recovery_calibration_capture,
)
from scripts.run_first_direct_reviewer_calibration import _run_assignment


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def run_first_direct_stage1_recovery_calibration_codex_retry(
    project_root: Path,
) -> list[dict[str, Any]]:
    protocol = _protocol(project_root)
    root = project_root / CALIBRATION_RELATIVE
    amendment = _load(root / AMENDMENT_NAME)
    amendment_digest = amendment.pop("amendment_digest", None)
    if amendment_digest != semantic_digest(amendment):
        raise ValueError("The Codex calibration retry amendment does not replay.")
    amendment["amendment_digest"] = amendment_digest
    if (
        amendment["calibration_protocol_digest"] != protocol["protocol_digest"]
        or amendment["execution_state"] != "frozen_not_started"
        or amendment["transport_delta"]["prompt_bytes_unchanged"] is not True
        or amendment["transport_delta"]["output_schema_unchanged"] is not True
    ):
        raise ValueError("The Codex calibration retry amendment is ineligible for execution.")
    for item in amendment["controller_implementation"]:
        path = project_root / str(item["path"])
        if sha256_digest(path.read_bytes()) != item["content_digest"]:
            raise ValueError(f"The Codex retry controller drifted: {path}")

    by_participant = {
        str(item["participant_id"]): item
        for item in protocol["assignments"]
        if item["provider"] == "OpenAI"
    }
    retries = {str(item["participant_id"]): item for item in amendment["retry_calls"]}
    if set(by_participant) != set(retries) or len(retries) != 2:
        raise ValueError("The retry does not bind the exact two Codex participants.")
    config = load_effective_execution_configuration(project_root)
    system_prompt = str(config["role_configurations"]["stage1_reviewer"]["system_prompt"])
    assignments = []
    for participant_id in sorted(retries):
        assignment = by_participant[participant_id]
        retry = retries[participant_id]
        if any(
            retry[field] != assignment[source]
            for field, source in (
                ("semantic_call_identity_id", "call_identity_id"),
                ("prompt_digest", "prompt_digest"),
                ("output_schema_digest", "output_schema_digest"),
                ("configuration_digest", "configuration_digest"),
            )
        ):
            raise ValueError(f"The retry semantic binding drifted for {participant_id}.")
        process_root = root / str(retry["process_capture_relative_path"])
        incoming = root / str(retry["incoming_capture_relative_path"])
        if process_root.exists() or process_root.is_symlink() or incoming.exists():
            raise FileExistsError(f"The Codex retry was already attempted: {participant_id}")
        assignments.append((assignment, retry))

    def execute(item: tuple[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
        assignment, retry = item
        runnable = {**assignment, "user_prompt": assignment["prompt"]}
        result = _run_assignment(runnable, system_prompt)
        result["retry"] = retry
        return result

    with ThreadPoolExecutor(max_workers=2) as executor:
        attempts = list(executor.map(execute, assignments))

    process_evidence: list[tuple[dict[str, Any], Path, dict[str, Any]]] = []
    for attempt in attempts:
        assignment = attempt["assignment"]
        retry = attempt["retry"]
        participant_id = str(assignment["participant_id"])
        process_root = root / str(retry["process_capture_relative_path"])
        process_root.mkdir(parents=True)
        atomic_write_bytes(process_root / "stdout.bin", attempt["stdout"])
        atomic_write_bytes(process_root / "stderr.bin", attempt["stderr"])
        atomic_write_bytes(process_root / "final-response.bin", attempt["final"])
        process_capture: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_recovery_calibration_codex_retry_process_capture",
            "capture_version": "1.0.0",
            "protocol_digest": protocol["protocol_digest"],
            "retry_amendment_digest": amendment_digest,
            "participant_id": participant_id,
            "semantic_call_identity_id": assignment["call_identity_id"],
            "transport_attempt_identity_id": retry["transport_attempt_identity_id"],
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
        process_evidence.append((attempt, process_root, process_capture))
    failures = [
        str(attempt["assignment"]["participant_id"])
        for attempt, _process_root, _process_capture in process_evidence
        if attempt["return_code"] != 0 or not attempt["final"]
    ]
    if failures:
        raise ValueError(
            "Codex calibration retries failed; all process evidence was retained: "
            + ", ".join(sorted(failures))
        )

    captures = []
    for attempt, process_root, process_capture in process_evidence:
        assignment = attempt["assignment"]
        retry = attempt["retry"]
        participant_id = str(assignment["participant_id"])
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
                "retry_amendment_digest": amendment_digest,
                "transport_attempt_identity_id": retry["transport_attempt_identity_id"],
                "process_capture_relative_path": process_root.relative_to(root).as_posix(),
                "process_capture_digest": process_capture["capture_digest"],
            },
        )
        incoming = root / str(retry["incoming_capture_relative_path"])
        write_normalized_json_once(incoming, capture)
        captures.append(capture)
    return sorted(captures, key=lambda item: str(item["participant_id"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    captures = run_first_direct_stage1_recovery_calibration_codex_retry(
        arguments.project_root.resolve()
    )
    for capture in captures:
        print(capture["participant_id"], capture["capture_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
