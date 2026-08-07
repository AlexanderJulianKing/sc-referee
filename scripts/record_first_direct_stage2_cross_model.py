from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from sc_referee_evaluation.capture import capture_review_submission, load_review_capture
from sc_referee_evaluation.review_semantic_payload_stage2 import (
    build_stage2_batch_output_schema,
    project_stage2_semantic_batch,
)

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage2_cross_model_protocol import (
    CANONICAL_ISSUE_CLASS,
    CASE_IDS,
    STAGE2_REVIEW_RELATIVE,
    STAGE2_REVIEWERS,
)
from scripts.record_first_direct_three_case_stage1_semantic_recovery_clean_cli import (
    _protocol as _stage1_protocol,
)

PROTOCOL_DIGEST: str | None = (
    "sha256:49ff4ccff416b1d2794b497953b22eded3bed69a81f0e2d3c2637db0e221639c"
)
SCHEMA_RELATIVE = Path("reference/schemas-v0.18.0")


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Stage-2 timestamps must include an offset.")
    return parsed


def _expected_protocol_digest() -> str:
    if PROTOCOL_DIGEST is None:
        raise ValueError("The Stage-2 protocol digest has not been frozen in the recorder.")
    return PROTOCOL_DIGEST


def _protocol(project_root: Path) -> dict[str, Any]:
    protocol = _load(project_root / STAGE2_REVIEW_RELATIVE / "STAGE2_REVIEW_PROTOCOL.json")
    supplied = protocol.pop("protocol_digest", None)
    if supplied != _expected_protocol_digest() or supplied != semantic_digest(protocol):
        raise ValueError("The frozen Stage-2 protocol does not replay.")
    protocol["protocol_digest"] = supplied
    if (
        protocol.get("artifact_kind")
        != "direct_qualification_three_case_stage2_cross_model_protocol"
        or protocol.get("execution_state") != "frozen_not_started"
        or protocol.get("case_ids") != CASE_IDS
        or sorted(str(item["participant_id"]) for item in protocol.get("calls", []))
        != sorted(STAGE2_REVIEWERS)
        or protocol.get("stage2_review_count") != 0
        or protocol.get("scientific_label_count") != 0
        or protocol.get("detector_outcome_count") != 0
    ):
        raise ValueError("The frozen Stage-2 protocol state is invalid.")
    for call in protocol["calls"]:
        participant_id = str(call["participant_id"])
        case_order = [str(value) for value in call["case_order"]]
        expected_schema = build_stage2_batch_output_schema(
            participant_id, case_order, CANONICAL_ISSUE_CLASS
        )
        if call.get("output_schema") != expected_schema or call.get(
            "output_schema_digest"
        ) != semantic_digest(expected_schema):
            raise ValueError("A Stage-2 call does not bind the exact output schema.")
        if call.get("prompt_digest") != sha256_digest(str(call["prompt"])):
            raise ValueError("A Stage-2 call prompt does not replay.")
    return protocol


def _call(project_root: Path, participant_id: str) -> dict[str, Any]:
    protocol = _protocol(project_root)
    call = next(
        (item for item in protocol["calls"] if item["participant_id"] == participant_id),
        None,
    )
    if call is None:
        raise ValueError(f"Unknown Stage-2 participant {participant_id!r}.")
    return cast(dict[str, Any], call)


def build_stage2_call_capture(
    project_root: Path,
    participant_id: str,
    raw_response: bytes,
    *,
    started_at: str,
    completed_at: str,
    captured_at: str,
    transport: dict[str, Any],
) -> dict[str, Any]:
    protocol_digest = _expected_protocol_digest()
    protocol = _protocol(project_root)
    call = _call(project_root, participant_id)
    if not raw_response:
        raise ValueError("A Stage-2 capture requires nonempty response bytes.")
    raw_response.decode("utf-8")
    frozen = _timestamp(str(protocol["frozen_at"]))
    start = _timestamp(started_at)
    completed = _timestamp(completed_at)
    captured = _timestamp(captured_at)
    if not (frozen < start <= completed <= captured):
        raise ValueError("Stage-2 call chronology is invalid.")
    record: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage2_model_call_capture",
        "capture_version": "1.0.0",
        "capture_id": stable_id(
            "stage2-model-call-capture",
            protocol_digest,
            str(call["call_identity_id"]),
            sha256_digest(raw_response),
        ),
        "protocol_digest": protocol_digest,
        "call_identity_id": call["call_identity_id"],
        "participant_id": participant_id,
        "participant_configuration_digest": call["participant_configuration_digest"],
        "prompt_digest": call["prompt_digest"],
        "output_schema_digest": call["output_schema_digest"],
        "case_order": call["case_order"],
        "raw_response": raw_response.decode("utf-8"),
        "raw_response_digest": sha256_digest(raw_response),
        "raw_response_byte_size": len(raw_response),
        "started_at": started_at,
        "completed_at": completed_at,
        "captured_at": captured_at,
        "transport": transport,
        "model_invoked": True,
        "project_code_executed": False,
        "qualification_authority": "none_raw_call_capture_only",
    }
    record["capture_digest"] = semantic_digest(record)
    return record


def _validate_call_capture(
    project_root: Path, capture: dict[str, Any]
) -> tuple[dict[str, Any], bytes]:
    protocol_digest = _expected_protocol_digest()
    supplied = capture.pop("capture_digest", None)
    if supplied != semantic_digest(capture):
        raise ValueError("The Stage-2 call-capture digest is invalid.")
    capture["capture_digest"] = supplied
    if (
        capture.get("artifact_kind") != "direct_qualification_stage2_model_call_capture"
        or capture.get("protocol_digest") != protocol_digest
        or capture.get("model_invoked") is not True
        or capture.get("project_code_executed") is not False
    ):
        raise ValueError("The Stage-2 call-capture metadata is invalid.")
    participant_id = str(capture["participant_id"])
    call = _call(project_root, participant_id)
    for field in (
        "call_identity_id",
        "participant_configuration_digest",
        "prompt_digest",
        "output_schema_digest",
        "case_order",
    ):
        if capture.get(field) != call[field]:
            raise ValueError(f"The Stage-2 capture drifted in {field}.")
    raw_response = str(capture["raw_response"]).encode("utf-8")
    if (
        sha256_digest(raw_response) != capture["raw_response_digest"]
        or len(raw_response) != capture["raw_response_byte_size"]
    ):
        raise ValueError("The Stage-2 response bytes do not match their capture.")
    return call, raw_response


def _workspace_payloads(project_root: Path) -> dict[str, dict[str, bytes]]:
    stage1_protocol = _stage1_protocol(project_root)
    payloads: dict[str, dict[str, bytes]] = {}
    for binding in stage1_protocol["source_case_bindings"]:
        case_id = str(binding["case_id"])
        workspace_root = project_root / str(binding["source_workspace_relative_path"])
        case_payloads: dict[str, bytes] = {}
        for path_value, digest in dict(binding["visible_content_digests"]).items():
            content = (workspace_root / path_value).read_bytes()
            if sha256_digest(content) != digest:
                raise ValueError(f"Workspace bytes drifted for {case_id} {path_value}.")
            case_payloads[path_value] = content
        payloads[case_id] = case_payloads
    return payloads


def record_stage2_call(project_root: Path, incoming_path: Path) -> dict[str, Any]:
    capture = _load(incoming_path)
    call, raw_response = _validate_call_capture(project_root, capture)
    payload = json.loads(raw_response)
    if not isinstance(payload, dict):
        raise ValueError("The Stage-2 response is not one JSON object.")
    root = project_root / STAGE2_REVIEW_RELATIVE
    participant_id = str(call["participant_id"])
    packets = {
        str(item["case_id"]): _load(root / str(item["relative_path"]))
        for item in call["packet_refs"]
    }
    reviews = project_stage2_semantic_batch(
        payload,
        output_schema=call["output_schema"],
        participant_id=participant_id,
        participant_reviewer_agent=call["reviewer_agent_base"],
        packets_by_case=packets,
        workspace_payloads_by_case=_workspace_payloads(project_root),
        canonical_issue_class=CANONICAL_ISSUE_CLASS,
        transcript=raw_response,
        completed_at=str(capture["completed_at"]),
        schema_root=project_root / SCHEMA_RELATIVE,
    )
    ledger_path = root / "stage2-call-ledgers" / f"{participant_id.removeprefix('actor:')}.json"
    destinations = {
        str(item["case_id"]): root / str(destination)
        for item, destination in zip(call["packet_refs"], call["capture_destinations"], strict=True)
    }
    if (
        ledger_path.exists()
        or ledger_path.is_symlink()
        or any(path.exists() or path.is_symlink() for path in destinations.values())
    ):
        raise ValueError(f"Stage-2 call {participant_id} was already recorded.")

    staged: dict[str, Path] = {}
    manifests: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="sc-referee-stage2-capture-") as temporary:
        temporary_root = Path(temporary)
        transcript_path = temporary_root / "transcript.bin"
        transcript_path.write_bytes(raw_response)
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
            os.replace(staged[case_id], destination)

    entries = []
    for review in reviews:
        case_id = str(review["case_id"])
        manifest = manifests[case_id]
        entries.append(
            {
                "case_id": case_id,
                "review_id": review["review_id"],
                "review_digest": semantic_digest(review),
                "packet_digest": packets[case_id]["packet_digest"],
                "capture_id": manifest["capture_id"],
                "capture_digest": manifest["capture_digest"],
                "relative_capture_path": destinations[case_id].relative_to(root).as_posix(),
                "verdict": review["verdict"],
            }
        )
    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage2_call_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": _expected_protocol_digest(),
        "participant_id": participant_id,
        "call_identity_id": call["call_identity_id"],
        "incoming_capture_digest": capture["capture_digest"],
        "shared_transcript_digest": sha256_digest(raw_response),
        "entries": sorted(entries, key=lambda item: str(item["case_id"])),
        "review_count": len(CASE_IDS),
        "case_count": len(CASE_IDS),
        "admission_status": "three_reviews_captured",
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "recorded_at": capture["captured_at"],
        "qualification_authority": "none_stage2_reviews_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(ledger_path, ledger)
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--incoming", type=Path, required=True)
    arguments = parser.parse_args()
    ledger = record_stage2_call(arguments.project_root.resolve(), arguments.incoming.resolve())
    print(ledger["ledger_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
