from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.storage.atomic import atomic_write_bytes
from scripts.build_first_direct_three_case_stage1_codex_recovery import (
    AMENDMENT_NAME,
    FAILURE_LEDGER_DIGEST,
)
from scripts.build_first_direct_three_case_stage1_protocol import (
    BASE_STAGE1_PROMPT_DIGEST,
    REVIEW_RELATIVE,
)
from scripts.record_first_direct_three_case_stage1_reviews import (
    PROTOCOL_DIGEST,
    build_stage1_call_capture,
)
from scripts.run_first_direct_three_case_stage1_codex import _load, _now, _run_one


def _replay(record: dict[str, Any], field: str, expected: str | None, label: str) -> str:
    supplied = record.pop(field, None)
    if not isinstance(supplied, str) or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    if expected is not None and supplied != expected:
        raise ValueError(f"{label} has an unexpected digest.")
    record[field] = supplied
    return supplied


def run_first_direct_three_case_stage1_codex_recovery(
    project_root: Path,
) -> list[dict[str, Any]]:
    root = project_root / REVIEW_RELATIVE
    protocol = _load(root / "STAGE1_REVIEW_PROTOCOL.json")
    _replay(protocol, "protocol_digest", PROTOCOL_DIGEST, "The Stage-1 protocol")
    failure = _load(root / "CODEX_TRANSPORT_FAILURE_LEDGER.json")
    _replay(failure, "ledger_digest", FAILURE_LEDGER_DIGEST, "The transport failure ledger")
    amendment = _load(root / AMENDMENT_NAME)
    amendment_digest = _replay(
        amendment, "amendment_digest", None, "The transport recovery amendment"
    )
    if (
        amendment["protocol_digest"] != PROTOCOL_DIGEST
        or amendment["retained_failure_ledger_digest"] != FAILURE_LEDGER_DIGEST
        or amendment["execution_state"] != "frozen_not_started"
        or amendment["transport_delta"]["api_output_schema_argument_present"] is not False
        or amendment["semantic_invariants"]["prompt_bytes_unchanged"] is not True
        or amendment["semantic_invariants"]["semantic_output_schema_unchanged"] is not True
        or amendment["semantic_invariants"]["local_semantic_validation_unchanged"] is not True
    ):
        raise ValueError("The transport recovery amendment is not eligible for execution.")
    for item in amendment["controller_implementation"]:
        path = project_root / str(item["path"])
        if sha256_digest(path.read_bytes()) != item["content_digest"]:
            raise ValueError(f"Recovery controller implementation drifted: {path}")

    base_prompt_path = (
        project_root
        / "evaluation/qualification/bounded-analysis-method-conflict-v0.2.0-precase/stage1-prompt.txt"
    )
    base_prompt = base_prompt_path.read_text(encoding="utf-8")
    if sha256_digest(base_prompt) != BASE_STAGE1_PROMPT_DIGEST:
        raise ValueError("The accepted Stage-1 system prompt has drifted.")

    calls_by_participant = {
        str(item["participant_id"]): item
        for item in protocol["calls"]
        if item["participant"]["provider"] == "OpenAI"
    }
    recovery_by_participant = {
        str(item["participant_id"]): item for item in amendment["recovery_calls"]
    }
    if set(calls_by_participant) != set(recovery_by_participant) or len(calls_by_participant) != 2:
        raise ValueError("Recovery does not bind the exact two Codex calls.")

    calls = []
    for participant_id in sorted(calls_by_participant):
        call = calls_by_participant[participant_id]
        recovery = recovery_by_participant[participant_id]
        if (
            recovery["semantic_call_identity_id"] != call["call_identity_id"]
            or recovery["prompt_digest"] != call["prompt_digest"]
            or recovery["semantic_output_schema_digest"] != call["output_schema_digest"]
            or recovery["case_order"] != call["case_order"]
        ):
            raise ValueError(f"Recovery semantic binding drifted for {participant_id}.")
        slug = participant_id.removeprefix("actor:")
        original_capture = root / "codex-process-captures" / slug / "capture.json"
        recovery_root = root / str(recovery["recovery_process_capture_relative_path"])
        incoming = root / str(recovery["incoming_capture_relative_path"])
        if not original_capture.is_file():
            raise ValueError(f"Original failed process evidence is missing for {participant_id}.")
        if recovery_root.exists() or recovery_root.is_symlink() or incoming.exists():
            raise ValueError(f"Codex recovery {participant_id} was already attempted.")
        calls.append((call, recovery))

    def execute(item: tuple[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
        call, recovery = item
        result = _run_one(
            project_root,
            call,
            base_prompt,
            enforce_output_schema=False,
        )
        result["recovery"] = recovery
        return result

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(execute, calls))

    process_evidence: list[tuple[dict[str, Any], Path, dict[str, Any]]] = []
    for result in results:
        participant_id = str(result["participant_id"])
        recovery = result["recovery"]
        process_root = root / str(recovery["recovery_process_capture_relative_path"])
        process_root.mkdir(parents=True)
        atomic_write_bytes(process_root / "stdout.bin", result["stdout"])
        atomic_write_bytes(process_root / "stderr.bin", result["stderr"])
        atomic_write_bytes(process_root / "final-response.bin", result["raw_response"])
        process_record: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_codex_recovery_process_capture",
            "capture_version": "1.0.0",
            "protocol_digest": PROTOCOL_DIGEST,
            "recovery_amendment_digest": amendment_digest,
            "participant_id": participant_id,
            "semantic_call_identity_id": recovery["semantic_call_identity_id"],
            "transport_attempt_identity_id": recovery["transport_attempt_identity_id"],
            "fresh_transport_context_id": recovery["fresh_transport_context_id"],
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
            "local_semantic_validation_required": True,
            "model_invoked": True,
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
            "Codex Stage-1 recovery calls failed and exact process evidence was retained: "
            + ", ".join(sorted(failures))
        )

    retained = []
    for result, process_root, process_record in process_evidence:
        participant_id = str(result["participant_id"])
        recovery = result["recovery"]
        participant_slug = participant_id.removeprefix("actor:")
        captured_at = _now()
        call_capture = build_stage1_call_capture(
            project_root,
            participant_id,
            result["raw_response"],
            started_at=result["started_at"],
            completed_at=result["completed_at"],
            captured_at=captured_at,
            transport={
                "surface": "Codex CLI exec",
                "ephemeral": True,
                "sandbox": "read-only",
                "external_network": False,
                "api_output_schema_argument_present": False,
                "local_semantic_validation_required": True,
                "recovery_amendment_digest": amendment_digest,
                "transport_attempt_identity_id": recovery["transport_attempt_identity_id"],
                "fresh_transport_context_id": recovery["fresh_transport_context_id"],
                "process_capture_relative_path": process_root.relative_to(root).as_posix(),
                "process_capture_digest": process_record["capture_digest"],
            },
        )
        write_normalized_json_once(root / "incoming" / f"{participant_slug}.json", call_capture)
        retained.append(call_capture)
    return retained


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    captures = run_first_direct_three_case_stage1_codex_recovery(arguments.project_root.resolve())
    for capture in captures:
        print(capture["participant_id"], capture["capture_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
