from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from sc_referee_evaluation.capture import capture_review_submission, load_review_capture
from sc_referee_evaluation.review_protocol import (
    freeze_stage1_panel,
    validate_stage1_freeze_evidence,
)
from sc_referee_evaluation.review_semantic_payload import project_stage1_semantic_batch

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_three_case_stage1_protocol import (
    CANONICAL_ISSUE_CLASS,
    CASE_IDS,
    REVIEW_RELATIVE,
    STAGE1_REVIEWERS,
    VISIBLE_FILES,
)

PROTOCOL_DIGEST = "sha256:d9f3a84d205b2fa58d3abb38486f2068d4efd8a33526b4d1f35a2419a72d7d6b"
SCHEMA_RELATIVE = Path("reference/schemas-v0.18.0")


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"Invalid Stage-1 timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise ValueError("Stage-1 timestamps must include an offset.")
    return parsed


def _protocol(project_root: Path) -> dict[str, Any]:
    protocol = _load(project_root / REVIEW_RELATIVE / "STAGE1_REVIEW_PROTOCOL.json")
    supplied = protocol.pop("protocol_digest", None)
    if supplied != PROTOCOL_DIGEST or supplied != semantic_digest(protocol):
        raise ValueError("The frozen Stage-1 protocol does not replay.")
    protocol["protocol_digest"] = supplied
    if (
        protocol.get("execution_state") != "frozen_not_started"
        or protocol.get("case_ids") != CASE_IDS
        or [item.get("participant_id") for item in protocol.get("calls", [])] != STAGE1_REVIEWERS
        or protocol.get("stage1_review_count") != 0
        or protocol.get("scientific_label_count") != 0
        or protocol.get("detector_outcome_count") != 0
    ):
        raise ValueError("The frozen Stage-1 protocol state is invalid.")
    for item in protocol["controller_implementation"]:
        path = project_root / str(item["path"])
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Bound controller file is unavailable: {path}")
        if sha256_digest(path.read_bytes()) != item["content_digest"]:
            raise ValueError(f"Bound controller file drifted: {path}")
    return protocol


def build_stage1_call_capture(
    project_root: Path,
    participant_id: str,
    raw_response: bytes,
    *,
    started_at: str,
    completed_at: str,
    captured_at: str,
    transport: dict[str, Any],
) -> dict[str, Any]:
    """Build one exact response capture against a frozen call without interpreting semantics."""

    protocol = _protocol(project_root)
    calls = {str(item["participant_id"]): item for item in protocol["calls"]}
    call = calls.get(participant_id)
    if call is None:
        raise ValueError(f"Unknown Stage-1 participant {participant_id!r}.")
    if not raw_response:
        raise ValueError("A Stage-1 call capture requires nonempty exact response bytes.")
    start = _timestamp(started_at)
    completed = _timestamp(completed_at)
    captured = _timestamp(captured_at)
    frozen = _timestamp(str(protocol["frozen_at"]))
    if not (frozen < start <= completed <= captured):
        raise ValueError("Stage-1 call chronology is invalid.")
    record: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_model_call_capture",
        "capture_version": "1.0.0",
        "capture_id": stable_id(
            "stage1-model-call-capture",
            PROTOCOL_DIGEST,
            str(call["call_identity_id"]),
            sha256_digest(raw_response),
        ),
        "protocol_digest": PROTOCOL_DIGEST,
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
) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    protocol = _protocol(project_root)
    supplied = capture.pop("capture_digest", None)
    if supplied != semantic_digest(capture):
        raise ValueError("The Stage-1 model-call capture digest is invalid.")
    capture["capture_digest"] = supplied
    expected_keys = {
        "artifact_kind",
        "capture_version",
        "capture_id",
        "protocol_digest",
        "call_identity_id",
        "participant_id",
        "participant_configuration_digest",
        "prompt_digest",
        "output_schema_digest",
        "case_order",
        "raw_response",
        "raw_response_digest",
        "raw_response_byte_size",
        "started_at",
        "completed_at",
        "captured_at",
        "transport",
        "model_invoked",
        "project_code_executed",
        "qualification_authority",
        "capture_digest",
    }
    if set(capture) != expected_keys:
        raise ValueError("The Stage-1 model-call capture has an unsupported shape.")
    if (
        capture["artifact_kind"] != "direct_qualification_stage1_model_call_capture"
        or capture["capture_version"] != "1.0.0"
        or capture["protocol_digest"] != PROTOCOL_DIGEST
        or capture["model_invoked"] is not True
        or capture["project_code_executed"] is not False
        or capture["qualification_authority"] != "none_raw_call_capture_only"
    ):
        raise ValueError("The Stage-1 model-call capture metadata is invalid.")
    participant_id = str(capture["participant_id"])
    call = next(
        (item for item in protocol["calls"] if item["participant_id"] == participant_id),
        None,
    )
    if call is None:
        raise ValueError("The Stage-1 call capture participant is not frozen.")
    for field in (
        "call_identity_id",
        "participant_configuration_digest",
        "prompt_digest",
        "output_schema_digest",
        "case_order",
    ):
        if capture[field] != call[field]:
            raise ValueError(f"The Stage-1 call capture drifted in {field}.")
    raw_response = str(capture["raw_response"]).encode("utf-8")
    if (
        sha256_digest(raw_response) != capture["raw_response_digest"]
        or len(raw_response) != capture["raw_response_byte_size"]
        or capture["capture_id"]
        != stable_id(
            "stage1-model-call-capture",
            PROTOCOL_DIGEST,
            str(call["call_identity_id"]),
            str(capture["raw_response_digest"]),
        )
    ):
        raise ValueError("The Stage-1 raw response bytes do not match their capture.")
    if not (
        _timestamp(str(protocol["frozen_at"]))
        < _timestamp(str(capture["started_at"]))
        <= _timestamp(str(capture["completed_at"]))
        <= _timestamp(str(capture["captured_at"]))
    ):
        raise ValueError("The Stage-1 call capture chronology is invalid.")
    return protocol, call, raw_response


def validate_stage1_call_capture(
    project_root: Path, capture: dict[str, Any]
) -> list[dict[str, Any]]:
    """Validate and project all three reviews without mutating the qualification tree."""

    _protocol_record, call, raw_response = _validate_call_capture(project_root, capture)
    try:
        payload = json.loads(raw_response)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("The Stage-1 response is not one UTF-8 JSON object.") from error
    if not isinstance(payload, dict):
        raise ValueError("The Stage-1 response is not one JSON object.")
    root = project_root / REVIEW_RELATIVE
    packets = {
        str(item["case_id"]): _load(root / str(item["relative_path"]))
        for item in call["packet_refs"]
    }
    payloads = {
        case_id: {
            str(file_item["path"]): (
                root
                / "case-preparations"
                / case_id.removeprefix("case:")
                / "workspace"
                / str(file_item["path"])
            ).read_bytes()
            for file_item in VISIBLE_FILES
        }
        for case_id in CASE_IDS
    }
    return project_stage1_semantic_batch(
        payload,
        output_schema=call["output_schema"],
        participant_id=str(call["participant_id"]),
        participant_reviewer_agent=call["reviewer_agent_base"],
        packets_by_case=packets,
        workspace_payloads_by_case=payloads,
        canonical_issue_class=CANONICAL_ISSUE_CLASS,
        transcript=raw_response,
        completed_at=str(capture["completed_at"]),
        schema_root=project_root / SCHEMA_RELATIVE,
    )


def record_stage1_call(project_root: Path, incoming_path: Path) -> dict[str, Any]:
    """Project and immutably capture all reviews from one valid frozen batch call."""

    capture = _load(incoming_path)
    _protocol_record, call, raw_response = _validate_call_capture(project_root, capture)
    reviews = validate_stage1_call_capture(project_root, capture)
    root = project_root / REVIEW_RELATIVE
    participant_id = str(call["participant_id"])
    ledger_path = root / "stage1-call-ledgers" / f"{participant_id.removeprefix('actor:')}.json"
    destinations = {
        str(item["case_id"]): root / str(destination)
        for item, destination in zip(call["packet_refs"], call["capture_destinations"], strict=True)
    }
    if (
        ledger_path.exists()
        or ledger_path.is_symlink()
        or any(path.exists() or path.is_symlink() for path in destinations.values())
    ):
        raise ValueError(f"Stage-1 call {participant_id} was already recorded.")
    packets = {
        str(item["case_id"]): _load(root / str(item["relative_path"]))
        for item in call["packet_refs"]
    }

    staged: dict[str, Path] = {}
    manifests: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="sc-referee-stage1-capture-") as temporary:
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
        "artifact_kind": "direct_qualification_stage1_call_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": PROTOCOL_DIGEST,
        "participant_id": participant_id,
        "call_identity_id": call["call_identity_id"],
        "incoming_capture_digest": capture["capture_digest"],
        "shared_transcript_digest": sha256_digest(raw_response),
        "entries": sorted(entries, key=lambda item: str(item["case_id"])),
        "review_count": 3,
        "case_count": 3,
        "admission_status": "three_reviews_captured",
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "recorded_at": capture["captured_at"],
        "qualification_authority": "none_stage1_reviews_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(ledger_path, ledger)
    return ledger


def finalize_stage1_panel(project_root: Path, *, frozen_at: str) -> dict[str, Any]:
    """Freeze all three complete 2x2 panels only after four valid batch calls exist."""

    protocol = _protocol(project_root)
    root = project_root / REVIEW_RELATIVE
    final_ledger_path = root / "STAGE1_PANEL_LEDGER.json"
    if final_ledger_path.exists() or final_ledger_path.is_symlink():
        raise ValueError("The Stage-1 panel was already finalized.")
    call_ledgers = []
    reviews_by_case: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in CASE_IDS}
    packets_by_case: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in CASE_IDS}
    manifests_by_case: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in CASE_IDS}
    for call in protocol["calls"]:
        participant_id = str(call["participant_id"])
        call_ledger = _load(
            root / "stage1-call-ledgers" / f"{participant_id.removeprefix('actor:')}.json"
        )
        supplied = call_ledger.pop("ledger_digest", None)
        if supplied != semantic_digest(call_ledger):
            raise ValueError(f"Stage-1 call ledger drifted for {participant_id}.")
        call_ledger["ledger_digest"] = supplied
        call_ledgers.append(call_ledger)
        entries = {str(item["case_id"]): item for item in call_ledger["entries"]}
        if set(entries) != set(CASE_IDS):
            raise ValueError(f"Stage-1 call ledger is incomplete for {participant_id}.")
        for packet_ref in call["packet_refs"]:
            case_id = str(packet_ref["case_id"])
            capture_path = root / str(entries[case_id]["relative_capture_path"])
            review, packet, manifest = load_review_capture(
                capture_path, project_root / SCHEMA_RELATIVE
            )
            if (
                review["review_id"] != entries[case_id]["review_id"]
                or semantic_digest(review) != entries[case_id]["review_digest"]
                or packet["packet_digest"] != packet_ref["packet_digest"]
                or manifest["capture_digest"] != entries[case_id]["capture_digest"]
            ):
                raise ValueError("A Stage-1 captured review drifted from its call ledger.")
            reviews_by_case[case_id].append(review)
            packets_by_case[case_id].append(packet)
            manifests_by_case[case_id].append(manifest)

    frozen_time = _timestamp(frozen_at)
    if any(
        _timestamp(str(manifest["captured_at"])) > frozen_time
        for manifests in manifests_by_case.values()
        for manifest in manifests
    ):
        raise ValueError("The Stage-1 panel freeze predates a capture.")
    freeze_root = root / "stage1-freezes"
    if freeze_root.exists() or freeze_root.is_symlink():
        raise ValueError("The Stage-1 freeze destination already exists.")
    freeze_records: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="sc-referee-stage1-freeze-") as temporary:
        temporary_root = Path(temporary)
        for case_id in CASE_IDS:
            output = temporary_root / f"{case_id.removeprefix('case:')}.json"
            frozen = freeze_stage1_panel(
                reviews_by_case[case_id],
                packets_by_case[case_id],
                manifests_by_case[case_id],
                project_root / SCHEMA_RELATIVE,
                frozen_at=frozen_at,
                output=output,
            )
            validate_stage1_freeze_evidence(
                frozen,
                reviews_by_case[case_id],
                packets_by_case[case_id],
                manifests_by_case[case_id],
                project_root / SCHEMA_RELATIVE,
            )
            freeze_records[case_id] = frozen
        freeze_root.mkdir(parents=True)
        for case_id in CASE_IDS:
            os.replace(
                temporary_root / f"{case_id.removeprefix('case:')}.json",
                freeze_root / f"{case_id.removeprefix('case:')}.json",
            )

    verdict_counts = Counter(
        str(review["verdict"]) for reviews in reviews_by_case.values() for review in reviews
    )
    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_panel_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": PROTOCOL_DIGEST,
        "call_ledgers": [
            {
                "participant_id": item["participant_id"],
                "ledger_digest": item["ledger_digest"],
            }
            for item in call_ledgers
        ],
        "case_panels": [
            {
                "case_id": case_id,
                "freeze_relative_path": f"stage1-freezes/{case_id.removeprefix('case:')}.json",
                "freeze_digest": freeze_records[case_id]["freeze_digest"],
                "review_count": len(reviews_by_case[case_id]),
                "provider_participation": freeze_records[case_id]["provider_participation"],
            }
            for case_id in CASE_IDS
        ],
        "model_call_count": 4,
        "review_count": 12,
        "stage1_freeze_count": 3,
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "shared_transcript_within_reviewer_batch": True,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "frozen_at": frozen_at,
        "qualification_authority": "none_stage1_panel_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(final_ledger_path, ledger)
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--incoming", type=Path)
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--frozen-at")
    arguments = parser.parse_args()
    project_root = arguments.project_root.resolve()
    if arguments.finalize:
        if arguments.incoming is not None or not arguments.frozen_at:
            parser.error("--finalize requires --frozen-at and no --incoming")
        result = finalize_stage1_panel(project_root, frozen_at=arguments.frozen_at)
    else:
        if arguments.incoming is None or arguments.frozen_at is not None:
            parser.error("recording requires --incoming and no --frozen-at")
        result = record_stage1_call(project_root, arguments.incoming.resolve())
    print(result["ledger_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
