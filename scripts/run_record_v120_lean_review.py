from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from sc_referee_evaluation.capture import capture_review_submission, load_review_capture
from sc_referee_evaluation.review_semantic_payload_v2 import (
    build_stage1_batch_output_schema_v2,
    project_stage1_semantic_batch_v2,
)

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.storage.atomic import atomic_write_bytes
from scripts.build_first_direct_three_case_stage1_protocol import (
    CANONICAL_ISSUE_CLASS,
    VISIBLE_FILES,
)
from scripts.build_v120_lean_review import PRIMARY_REVIEWER, V120_REVIEW_RELATIVE
from scripts.run_first_direct_stage1_recovery_claude_cli_replacement_calibration import (
    CLAUDE_PINNED,
    _verify_pinned_binary,
)

PROTOCOL_DIGEST: str | None = (
    "sha256:09510e4050cd54f3a1e8cd7823da6ab608b51bc7b55a8826175980e9558bcbe8"
)
SCHEMA_RELATIVE = Path("reference/schemas-v0.18.0")
TIMEOUT_SECONDS = 3600


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("V120 review timestamps must include an offset.")
    return parsed


def _protocol(project_root: Path) -> dict[str, Any]:
    if PROTOCOL_DIGEST is None:
        raise ValueError("The v120 review protocol digest has not been frozen.")
    protocol = _load(project_root / V120_REVIEW_RELATIVE / "REVIEW_PROTOCOL.json")
    supplied = protocol.pop("protocol_digest", None)
    if supplied != PROTOCOL_DIGEST or supplied != semantic_digest(protocol):
        raise ValueError("The v120 review protocol does not replay.")
    protocol["protocol_digest"] = supplied
    if (
        protocol.get("execution_state") != "frozen_not_started"
        or len(protocol.get("calls", [])) != 1
        or protocol.get("review_count") != 0
        or protocol.get("scientific_label_count") != 0
        or protocol.get("detector_outcome_count") != 0
    ):
        raise ValueError("The v120 review protocol state is invalid.")
    call = protocol["calls"][0]
    expected_schema = build_stage1_batch_output_schema_v2(
        str(call["participant_id"]),
        [str(value) for value in call["case_order"]],
        CANONICAL_ISSUE_CLASS,
    )
    if call.get("output_schema") != expected_schema:
        raise ValueError("The v120 review call does not bind the exact output schema.")
    if call.get("prompt_digest") != sha256_digest(str(call["prompt"])):
        raise ValueError("The v120 review call prompt does not replay.")
    return protocol


def run_v120_lean_review(project_root: Path) -> dict[str, Any]:
    protocol = _protocol(project_root)
    call = protocol["calls"][0]
    if str(call["participant_id"]) != PRIMARY_REVIEWER:
        raise ValueError("The v120 review call is not bound to the primary reviewer.")
    _verify_pinned_binary(str(call["participant"]["agent_version"]))
    root = project_root / V120_REVIEW_RELATIVE
    incoming = root / "incoming" / f"{PRIMARY_REVIEWER.removeprefix('actor:')}.json"
    process_root = root / "review-cli-process-captures" / PRIMARY_REVIEWER.removeprefix("actor:")
    if incoming.exists() or incoming.is_symlink():
        raise FileExistsError("The v120 review attempt already exists.")
    process_root.mkdir(parents=True)

    started_at = _now()
    environment = dict(os.environ)
    environment["NO_COLOR"] = "1"
    with tempfile.TemporaryDirectory(prefix="sc-referee-v120-review-") as temporary:
        argv = [
            str(CLAUDE_PINNED),
            "--safe-mode",
            "--print",
            "--model",
            str(call["command_profile"]["model_alias_argument"]),
            "--effort",
            str(call["participant"]["reasoning_configuration"]),
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
        completed = subprocess.run(
            argv,
            cwd=temporary,
            env=environment,
            capture_output=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
    completed_at = _now()
    atomic_write_bytes(process_root / "stdout.bin", completed.stdout)
    atomic_write_bytes(process_root / "stderr.bin", completed.stderr)
    transport_error = None
    raw_response = b""
    metadata: dict[str, Any] = {}
    if completed.returncode != 0:
        transport_error = f"provider_cli_exit_code:{completed.returncode}"
    else:
        envelope = json.loads(completed.stdout.decode("utf-8"))
        metadata = {
            "reported_session_id": envelope.get("session_id"),
            "served_model_ids": sorted(set(envelope.get("modelUsage", {}))),
        }
        if envelope.get("is_error") is not False:
            transport_error = "provider_reported_error"
        elif envelope.get("session_id") != str(call["call_identity_id"]):
            transport_error = "reported_session_id_mismatch"
        elif str(call["participant"]["model_id"]) not in set(envelope.get("modelUsage", {})):
            transport_error = "served_model_mismatch"
        else:
            text = envelope.get("result")
            if isinstance(text, str) and text.strip():
                raw_response = text.encode("utf-8")
            else:
                transport_error = "missing_result_text"

    process_record = {
        "artifact_kind": "direct_qualification_v120_review_cli_process_capture",
        "capture_version": "1.0.0",
        "protocol_digest": protocol["protocol_digest"],
        "participant_id": PRIMARY_REVIEWER,
        "call_identity_id": call["call_identity_id"],
        "argv_digest": semantic_digest(argv),
        "return_code": completed.returncode,
        "transport_error": transport_error,
        "reported_session_id": metadata.get("reported_session_id"),
        "served_model_ids": metadata.get("served_model_ids"),
        "stdout_digest": sha256_digest(completed.stdout),
        "stderr_digest": sha256_digest(completed.stderr),
        "final_response_digest": sha256_digest(raw_response),
        "started_at": started_at,
        "completed_at": completed_at,
        "model_invoked": completed.returncode == 0,
        "project_code_executed": False,
        "qualification_authority": "none_process_capture_only",
    }
    process_record["capture_digest"] = semantic_digest(process_record)
    write_normalized_json_once(process_root / "capture.json", process_record)
    if transport_error is not None:
        raise ValueError(f"The v120 review call failed and was retained: {transport_error}")

    capture: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_model_call_capture",
        "capture_version": "1.0.0",
        "capture_id": stable_id(
            "stage1-model-call-capture",
            str(protocol["protocol_digest"]),
            str(call["call_identity_id"]),
            sha256_digest(raw_response),
        ),
        "protocol_digest": protocol["protocol_digest"],
        "call_identity_id": call["call_identity_id"],
        "participant_id": PRIMARY_REVIEWER,
        "participant_configuration_digest": call["participant_configuration_digest"],
        "prompt_digest": call["prompt_digest"],
        "output_schema_digest": call["output_schema_digest"],
        "case_order": call["case_order"],
        "raw_response": raw_response.decode("utf-8"),
        "raw_response_digest": sha256_digest(raw_response),
        "raw_response_byte_size": len(raw_response),
        "started_at": started_at,
        "completed_at": completed_at,
        "captured_at": _now(),
        "transport": {
            "surface": "Claude Code CLI print mode",
            "binary_path": str(CLAUDE_PINNED),
            "safe_mode": True,
            "tools_disabled": True,
            "session_persistence": False,
            "reported_session_id": metadata["reported_session_id"],
            "served_model_verified": str(call["participant"]["model_id"]),
            "process_capture_digest": process_record["capture_digest"],
        },
        "model_invoked": True,
        "project_code_executed": False,
        "qualification_authority": "none_raw_call_capture_only",
    }
    frozen = _timestamp(str(protocol["frozen_at"]))
    if not (frozen < _timestamp(started_at) <= _timestamp(completed_at)):
        raise ValueError("V120 review call chronology is invalid.")
    capture["capture_digest"] = semantic_digest(capture)
    write_normalized_json_once(incoming, capture)
    return capture


def record_v120_lean_review(project_root: Path) -> dict[str, Any]:
    protocol = _protocol(project_root)
    call = protocol["calls"][0]
    root = project_root / V120_REVIEW_RELATIVE
    incoming = root / "incoming" / f"{PRIMARY_REVIEWER.removeprefix('actor:')}.json"
    capture = _load(incoming)
    supplied = capture.pop("capture_digest", None)
    if supplied != semantic_digest(capture):
        raise ValueError("The v120 review capture digest is invalid.")
    capture["capture_digest"] = supplied
    for field in (
        "call_identity_id",
        "participant_configuration_digest",
        "prompt_digest",
        "output_schema_digest",
        "case_order",
    ):
        if capture.get(field) != call[field]:
            raise ValueError(f"The v120 review capture drifted in {field}.")
    raw_response = str(capture["raw_response"]).encode("utf-8")
    if sha256_digest(raw_response) != capture["raw_response_digest"]:
        raise ValueError("The v120 review response bytes do not match their capture.")
    payload = json.loads(raw_response)
    packets = {
        str(item["case_id"]): _load(root / str(item["relative_path"]))
        for item in call["packet_refs"]
    }
    bindings = {str(item["case_id"]): item for item in protocol["source_case_bindings"]}
    payloads: dict[str, dict[str, bytes]] = {}
    for case_id, binding in bindings.items():
        workspace_root = project_root / str(binding["source_workspace_relative_path"])
        case_payloads: dict[str, bytes] = {}
        for item in VISIBLE_FILES:
            path_value = str(item["path"])
            content = (workspace_root / path_value).read_bytes()
            if sha256_digest(content) != binding["visible_content_digests"][path_value]:
                raise ValueError(f"Workspace bytes drifted for {case_id} {path_value}.")
            case_payloads[path_value] = content
        payloads[case_id] = case_payloads
    reviews = project_stage1_semantic_batch_v2(
        payload,
        output_schema=call["output_schema"],
        participant_id=PRIMARY_REVIEWER,
        participant_reviewer_agent=call["reviewer_agent_base"],
        packets_by_case=packets,
        workspace_payloads_by_case=payloads,
        canonical_issue_class=CANONICAL_ISSUE_CLASS,
        transcript=raw_response,
        completed_at=str(capture["completed_at"]),
        schema_root=project_root / SCHEMA_RELATIVE,
    )
    ledger_path = root / "review-call-ledger.json"
    destinations = {
        str(item["case_id"]): root / str(destination)
        for item, destination in zip(call["packet_refs"], call["capture_destinations"], strict=True)
    }
    if ledger_path.exists() or any(path.exists() for path in destinations.values()):
        raise ValueError("The v120 review was already recorded.")
    import os as _os

    with tempfile.TemporaryDirectory(prefix="sc-referee-v120-review-capture-") as temporary:
        temporary_root = Path(temporary)
        transcript_path = temporary_root / "transcript.bin"
        transcript_path.write_bytes(raw_response)
        staged: dict[str, Path] = {}
        manifests: dict[str, dict[str, Any]] = {}
        for review in reviews:
            case_id = str(review["case_id"])
            stage_path = temporary_root / case_id.removeprefix("case:")
            manifests[case_id] = capture_review_submission(
                review,
                packets[case_id],
                transcript_path,
                project_root / SCHEMA_RELATIVE,
                captured_at=str(capture["captured_at"]),
                destination=stage_path,
            )
            load_review_capture(stage_path, project_root / SCHEMA_RELATIVE)
            staged[case_id] = stage_path
        for case_id in sorted(staged):
            destination = destinations[case_id]
            destination.parent.mkdir(parents=True, exist_ok=True)
            _os.replace(staged[case_id], destination)

    entries = [
        {
            "case_id": str(review["case_id"]),
            "review_id": review["review_id"],
            "review_digest": semantic_digest(review),
            "packet_digest": packets[str(review["case_id"])]["packet_digest"],
            "capture_digest": manifests[str(review["case_id"])]["capture_digest"],
            "relative_capture_path": destinations[str(review["case_id"])]
            .relative_to(root)
            .as_posix(),
            "verdict": review["verdict"],
            "unresolved_material_question_count": len(
                review.get("unresolved_material_questions", [])
            ),
        }
        for review in reviews
    ]
    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_v120_lean_review_call_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": protocol["protocol_digest"],
        "participant_id": PRIMARY_REVIEWER,
        "call_identity_id": call["call_identity_id"],
        "incoming_capture_digest": capture["capture_digest"],
        "shared_transcript_digest": sha256_digest(raw_response),
        "entries": sorted(entries, key=lambda item: str(item["case_id"])),
        "review_count": len(entries),
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "recorded_at": capture["captured_at"],
        "qualification_authority": "none_lean_review_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(ledger_path, ledger)
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--record", action="store_true")
    arguments = parser.parse_args()
    project_root = arguments.project_root.resolve()
    if arguments.record:
        ledger = record_v120_lean_review(project_root)
        print(ledger["ledger_digest"])
    else:
        capture = run_v120_lean_review(project_root)
        print(capture["capture_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
