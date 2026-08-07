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
from sc_referee_evaluation.review_semantic_payload_v2 import (
    build_stage1_batch_output_schema_v2,
    project_stage1_semantic_batch_v2,
)

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage1_fable_completion_amendment import (
    AMENDMENT_NAME,
    SLOT_BY_FABLE,
)
from scripts.build_first_direct_three_case_stage1_protocol import (
    CANONICAL_ISSUE_CLASS,
    CASE_IDS,
    VISIBLE_FILES,
)
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol import (
    REVIEW_RELATIVE,
)
from scripts.record_first_direct_three_case_stage1_semantic_recovery_clean_cli import (
    _protocol,
)

AMENDMENT_DIGEST: str | None = (
    "sha256:111d469bf279913d164e055cf3bb187cf8ffb89550a2680abaf1fc878942e50c"
)
SCHEMA_RELATIVE = Path("reference/schemas-v0.18.0")
OPUS_PARTICIPANT_IDS = (
    "actor:stage1-recovery-claude-04",
    "actor:stage1-recovery-claude-05",
)
PANEL_REVIEWERS = (*OPUS_PARTICIPANT_IDS, *sorted(SLOT_BY_FABLE))


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Fable completion timestamps must include an offset.")
    return parsed


def _expected_amendment_digest() -> str:
    if AMENDMENT_DIGEST is None:
        raise ValueError("The Fable completion amendment digest has not been frozen.")
    return AMENDMENT_DIGEST


def _amendment(project_root: Path) -> dict[str, Any]:
    amendment = _load(project_root / REVIEW_RELATIVE / AMENDMENT_NAME)
    supplied = amendment.pop("amendment_digest", None)
    if supplied != _expected_amendment_digest() or supplied != semantic_digest(amendment):
        raise ValueError("The Fable completion amendment does not replay.")
    amendment["amendment_digest"] = supplied
    protocol = _protocol(project_root)
    if (
        amendment.get("artifact_kind")
        != "direct_qualification_stage1_fable_panel_completion_amendment"
        or amendment.get("protocol_digest") != protocol["protocol_digest"]
        or amendment.get("execution_state") != "frozen_not_started"
        or amendment.get("scientific_label_count") != 0
        or amendment.get("detector_outcome_count") != 0
        or sorted(str(item["participant_id"]) for item in amendment.get("calls", []))
        != sorted(SLOT_BY_FABLE)
    ):
        raise ValueError("The Fable completion amendment state is invalid.")
    for call in amendment["calls"]:
        participant_id = str(call["participant_id"])
        case_order = [str(value) for value in call["case_order"]]
        if len(case_order) != len(CASE_IDS) or set(case_order) != set(CASE_IDS):
            raise ValueError("A Fable completion call does not cover every case exactly once.")
        expected_schema = build_stage1_batch_output_schema_v2(
            participant_id,
            case_order,
            CANONICAL_ISSUE_CLASS,
        )
        if call.get("output_schema") != expected_schema or call.get(
            "output_schema_digest"
        ) != semantic_digest(expected_schema):
            raise ValueError("A Fable completion call does not bind the exact v2 output schema.")
        if call.get("prompt_digest") != sha256_digest(str(call["prompt"])):
            raise ValueError("A Fable completion call prompt does not replay.")
    return amendment


def _amendment_call(project_root: Path, participant_id: str) -> dict[str, Any]:
    amendment = _amendment(project_root)
    call = next(
        (item for item in amendment["calls"] if item["participant_id"] == participant_id),
        None,
    )
    if call is None:
        raise ValueError(f"Unknown Fable completion participant {participant_id!r}.")
    return cast(dict[str, Any], call)


def build_fable_stage1_call_capture(
    project_root: Path,
    participant_id: str,
    raw_response: bytes,
    *,
    started_at: str,
    completed_at: str,
    captured_at: str,
    transport: dict[str, Any],
) -> dict[str, Any]:
    amendment_digest = _expected_amendment_digest()
    amendment = _amendment(project_root)
    call = _amendment_call(project_root, participant_id)
    if not raw_response:
        raise ValueError("A Fable completion capture requires nonempty response bytes.")
    raw_response.decode("utf-8")
    start = _timestamp(started_at)
    completed = _timestamp(completed_at)
    captured = _timestamp(captured_at)
    frozen = _timestamp(str(amendment["frozen_at"]))
    if not (frozen < start <= completed <= captured):
        raise ValueError("Fable completion call chronology is invalid.")
    record: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_model_call_capture",
        "capture_version": "1.0.0",
        "capture_id": stable_id(
            "stage1-model-call-capture",
            amendment_digest,
            str(call["call_identity_id"]),
            sha256_digest(raw_response),
        ),
        "protocol_digest": amendment_digest,
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
    amendment_digest = _expected_amendment_digest()
    supplied = capture.pop("capture_digest", None)
    if supplied != semantic_digest(capture):
        raise ValueError("The Fable completion call-capture digest is invalid.")
    capture["capture_digest"] = supplied
    if (
        capture.get("artifact_kind") != "direct_qualification_stage1_model_call_capture"
        or capture.get("protocol_digest") != amendment_digest
        or capture.get("model_invoked") is not True
        or capture.get("project_code_executed") is not False
    ):
        raise ValueError("The Fable completion call-capture metadata is invalid.")
    participant_id = str(capture["participant_id"])
    call = _amendment_call(project_root, participant_id)
    for field in (
        "call_identity_id",
        "participant_configuration_digest",
        "prompt_digest",
        "output_schema_digest",
        "case_order",
    ):
        if capture.get(field) != call[field]:
            raise ValueError(f"The Fable completion capture drifted in {field}.")
    raw_response = str(capture["raw_response"]).encode("utf-8")
    if (
        sha256_digest(raw_response) != capture["raw_response_digest"]
        or len(raw_response) != capture["raw_response_byte_size"]
        or capture["capture_id"]
        != stable_id(
            "stage1-model-call-capture",
            amendment_digest,
            str(call["call_identity_id"]),
            str(capture["raw_response_digest"]),
        )
    ):
        raise ValueError("The Fable completion response bytes do not match their capture.")
    return call, raw_response


def validate_fable_stage1_call_capture(
    project_root: Path, capture: dict[str, Any]
) -> list[dict[str, Any]]:
    call, raw_response = _validate_call_capture(project_root, capture)
    payload = json.loads(raw_response)
    if not isinstance(payload, dict):
        raise ValueError("The Fable completion response is not one JSON object.")
    protocol = _protocol(project_root)
    root = project_root / REVIEW_RELATIVE
    packets = {
        str(item["case_id"]): _load(root / str(item["relative_path"]))
        for item in call["packet_refs"]
    }
    source_bindings = {str(item["case_id"]): item for item in protocol["source_case_bindings"]}
    payloads: dict[str, dict[str, bytes]] = {}
    for case_id in CASE_IDS:
        binding = source_bindings[case_id]
        workspace_root = project_root / str(binding["source_workspace_relative_path"])
        expected_digests = dict(binding["visible_content_digests"])
        case_payloads: dict[str, bytes] = {}
        for file_item in VISIBLE_FILES:
            path_value = str(file_item["path"])
            path = workspace_root / path_value
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"A Fable completion source file is unavailable: {path}")
            content = path.read_bytes()
            if sha256_digest(content) != expected_digests.get(path_value):
                raise ValueError(f"Source bytes drifted for {case_id} {path_value}.")
            case_payloads[path_value] = content
        payloads[case_id] = case_payloads
    return project_stage1_semantic_batch_v2(
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


def record_fable_stage1_call(project_root: Path, incoming_path: Path) -> dict[str, Any]:
    capture = _load(incoming_path)
    call, raw_response = _validate_call_capture(project_root, capture)
    reviews = validate_fable_stage1_call_capture(project_root, capture)
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
        raise ValueError(f"Fable completion call {participant_id} was already recorded.")
    packets = {
        str(item["case_id"]): _load(root / str(item["relative_path"]))
        for item in call["packet_refs"]
    }

    staged: dict[str, Path] = {}
    manifests: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="sc-referee-stage1-fable-capture-") as temporary:
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
        "protocol_digest": _expected_amendment_digest(),
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
        "qualification_authority": "none_stage1_reviews_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(ledger_path, ledger)
    return ledger


def finalize_cross_model_stage1_panel(project_root: Path, *, frozen_at: str) -> dict[str, Any]:
    """Freeze three complete 2x2 cross-model panels from the Opus and Fable ledgers."""

    protocol = _protocol(project_root)
    amendment = _amendment(project_root)
    root = project_root / REVIEW_RELATIVE
    final_ledger_path = root / "STAGE1_PANEL_LEDGER.json"
    if final_ledger_path.exists() or final_ledger_path.is_symlink():
        raise ValueError("The cross-model Stage-1 panel was already finalized.")
    protocol_calls = {str(item["participant_id"]): item for item in protocol["calls"]}
    amendment_calls = {str(item["participant_id"]): item for item in amendment["calls"]}
    expected_ledger_source = {
        **{
            participant_id: (protocol_calls[participant_id], protocol["protocol_digest"])
            for participant_id in OPUS_PARTICIPANT_IDS
        },
        **{
            participant_id: (amendment_calls[participant_id], amendment["amendment_digest"])
            for participant_id in sorted(SLOT_BY_FABLE)
        },
    }

    call_ledgers = []
    reviews_by_case: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in CASE_IDS}
    packets_by_case: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in CASE_IDS}
    manifests_by_case: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in CASE_IDS}
    for participant_id in PANEL_REVIEWERS:
        call, source_digest = expected_ledger_source[participant_id]
        call_ledger = _load(
            root / "stage1-call-ledgers" / f"{participant_id.removeprefix('actor:')}.json"
        )
        supplied = call_ledger.pop("ledger_digest", None)
        if supplied != semantic_digest(call_ledger):
            raise ValueError(f"Cross-model ledger drifted for {participant_id}.")
        call_ledger["ledger_digest"] = supplied
        if (
            call_ledger.get("protocol_digest") != source_digest
            or call_ledger.get("participant_id") != participant_id
            or call_ledger.get("call_identity_id") != call["call_identity_id"]
            or call_ledger.get("review_count") != len(CASE_IDS)
            or call_ledger.get("scientific_label_count") != 0
            or call_ledger.get("detector_outcome_count") != 0
        ):
            raise ValueError(f"Cross-model ledger metadata drifted for {participant_id}.")
        call_ledgers.append(call_ledger)
        entries = {str(item["case_id"]): item for item in call_ledger["entries"]}
        if set(entries) != set(CASE_IDS):
            raise ValueError(f"Cross-model ledger is incomplete for {participant_id}.")
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
                raise ValueError("A cross-model captured review drifted from its call ledger.")
            reviews_by_case[case_id].append(review)
            packets_by_case[case_id].append(packet)
            manifests_by_case[case_id].append(manifest)

    frozen_time = _timestamp(frozen_at)
    if any(
        _timestamp(str(manifest["captured_at"])) > frozen_time
        for manifests in manifests_by_case.values()
        for manifest in manifests
    ):
        raise ValueError("The cross-model panel freeze predates a capture.")
    freeze_root = root / "stage1-freezes"
    if freeze_root.exists() or freeze_root.is_symlink():
        raise ValueError("The cross-model freeze destination already exists.")
    freeze_records: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="sc-referee-stage1-fable-freeze-") as temporary:
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
    model_families = Counter(
        str(review["reviewer_agent"]["model_name"])
        for reviews in reviews_by_case.values()
        for review in reviews
    )
    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_panel_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": protocol["protocol_digest"],
        "panel_completion_amendment_digest": amendment["amendment_digest"],
        "adr_reference": str(amendment["adr_reference"]),
        "single_provider_cross_model_panel": True,
        "provider_participation_disclosure": {"Anthropic": len(PANEL_REVIEWERS)},
        "model_family_participation": dict(sorted(model_families.items())),
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
        "model_call_count": len(PANEL_REVIEWERS),
        "review_count": len(PANEL_REVIEWERS) * len(CASE_IDS),
        "stage1_freeze_count": len(CASE_IDS),
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "shared_transcript_within_reviewer_batch": True,
        "semantic_contract": "stage1-semantic-payload-v2",
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
        result = finalize_cross_model_stage1_panel(project_root, frozen_at=arguments.frozen_at)
    else:
        if arguments.incoming is None or arguments.frozen_at is not None:
            parser.error("recording requires --incoming and no --frozen-at")
        result = record_fable_stage1_call(project_root, arguments.incoming.resolve())
    print(result["ledger_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
