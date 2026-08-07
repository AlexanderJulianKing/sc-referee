from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee_evaluation.review_protocol import build_stage1_review_packet

from sc_referee.core.ids import semantic_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage1_fable_chronology_recovery import (
    RECOVERY_NAME,
)
from scripts.build_first_direct_stage1_fable_completion_amendment import (
    AMENDMENT_NAME as V1_AMENDMENT_NAME,
)
from scripts.build_first_direct_stage1_fable_completion_amendment import (
    SLOT_BY_FABLE,
)
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol import (
    REVIEW_RELATIVE,
)

V2_AMENDMENT_NAME = "FABLE_COMPLETION_AMENDMENT_V2.json"
FAILURE_LEDGER_NAME = "FABLE_COMPLETION_V1_FAILURE_LEDGER.json"
V1_AMENDMENT_DIGEST = "sha256:111d469bf279913d164e055cf3bb187cf8ffb89550a2680abaf1fc878942e50c"
V1_RECOVERY_DIGEST = "sha256:04e37618847f7e5459d2d1a3125059427060106cbf3130bf1fce59201095e6f7"
V1_INCOMING_CAPTURE_DIGESTS = {
    "actor:stage1-recovery-fable-01": (
        "sha256:2bc76c9ff08f69e015f92afd5e0239b6a7d31cb15805170310348fc365e64c08"
    ),
    "actor:stage1-recovery-fable-02": (
        "sha256:fe94a17e507f04247bc494a636ef0a5482e833f25cbcf70232f6fe816087fa2d"
    ),
}
V1_FAILURE_REASONS = {
    "actor:stage1-recovery-fable-01": "response_not_valid_json_at_character_6520",
    "actor:stage1-recovery-fable-02": (
        "review_completion_predates_forward_dated_packet_created_at"
    ),
}
# Both set just behind real wall-clock time at build; the v2 calls run afterward.
PACKET_AT = "2026-08-07T18:40:04Z"
FROZEN_AT = "2026-08-07T18:40:05Z"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def build_first_direct_stage1_fable_completion_v2(project_root: Path) -> dict[str, Any]:
    root = project_root / REVIEW_RELATIVE
    amendment_path = root / V2_AMENDMENT_NAME
    ledger_path = root / FAILURE_LEDGER_NAME
    if any(p.exists() or p.is_symlink() for p in (amendment_path, ledger_path)):
        raise FileExistsError("The v2 Fable completion iteration is already frozen.")

    v1 = _load(root / V1_AMENDMENT_NAME)
    _replay(v1, "amendment_digest", V1_AMENDMENT_DIGEST, "The v1 completion amendment")
    recovery = _load(root / RECOVERY_NAME)
    supplied_recovery = recovery.pop("recovery_digest", None)
    if supplied_recovery != V1_RECOVERY_DIGEST or supplied_recovery != semantic_digest(recovery):
        raise ValueError("The v1 chronology recovery does not replay.")
    recovery["recovery_digest"] = supplied_recovery

    failure_rows: list[dict[str, Any]] = []
    for participant_id in sorted(SLOT_BY_FABLE):
        slug = participant_id.removeprefix("actor:")
        process = _load(root / "fable-cli-process-captures" / slug / "capture.json")
        supplied_process = process.pop("capture_digest", None)
        if supplied_process != semantic_digest(process):
            raise ValueError(f"The v1 process capture drifted for {participant_id}.")
        process["capture_digest"] = supplied_process
        incoming = _load(root / "incoming" / f"{slug}.json")
        supplied_incoming = incoming.pop("capture_digest", None)
        if supplied_incoming != V1_INCOMING_CAPTURE_DIGESTS[
            participant_id
        ] or supplied_incoming != semantic_digest(incoming):
            raise ValueError(f"The v1 incoming capture drifted for {participant_id}.")
        incoming["capture_digest"] = supplied_incoming
        if (root / "stage1-call-ledgers" / f"{slug}.json").exists():
            raise ValueError(f"A v1 review was admitted for {participant_id}; cannot retire it.")
        failure_rows.append(
            {
                "participant_id": participant_id,
                "process_capture_digest": supplied_process,
                "incoming_capture_digest": supplied_incoming,
                "raw_response_digest": incoming["raw_response_digest"],
                "failure_reason": V1_FAILURE_REASONS[participant_id],
                "admitted_review_count": 0,
            }
        )

    failure_ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_fable_completion_failure_ledger",
        "ledger_version": "1.0.0",
        "v1_amendment_digest": V1_AMENDMENT_DIGEST,
        "v1_chronology_recovery_digest": V1_RECOVERY_DIGEST,
        "root_cause": (
            "The controller forward-dated the v1 amendment frozen_at, packet created_at, and "
            "recovery frozen_at constants relative to real wall-clock time. One retained "
            "response also failed JSON parsing before any semantic assessment. No review was "
            "admitted from the v1 iteration; its responses may not be reused, repaired, or "
            "reclassified."
        ),
        "entries": failure_rows,
        "attempt_count": 2,
        "admitted_review_count": 0,
        "responses_retained_without_repair": True,
        "v1_responses_permanently_ineligible": True,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "recorded_at": FROZEN_AT,
        "qualification_authority": "none_failure_evidence_only",
    }
    failure_ledger["ledger_digest"] = semantic_digest(failure_ledger)
    write_normalized_json_once(ledger_path, failure_ledger)

    calls: list[dict[str, Any]] = []
    v1_calls = {str(item["participant_id"]): item for item in v1["calls"]}
    for participant_id in sorted(SLOT_BY_FABLE):
        source_call = v1_calls[participant_id]
        slug = participant_id.removeprefix("actor:")
        packet_refs: list[dict[str, Any]] = []
        for ref in source_call["packet_refs"]:
            case_id = str(ref["case_id"])
            source_packet = _load(root / str(ref["relative_path"]))
            manifest = _manifest_stub(project_root, case_id)
            if manifest["manifest_digest"] != ref["source_workspace_manifest_digest"]:
                raise ValueError(f"The v1 workspace manifest drifted for {case_id}.")
            packet = build_stage1_review_packet(
                case_id,
                manifest,
                deepcopy(source_call["reviewer_agent_base"]),
                str(source_call["prompt"]),
                created_at=PACKET_AT,
            )
            if packet["packet_digest"] == source_packet.get("packet_digest"):
                raise ValueError("A v2 packet unexpectedly equals its forward-dated v1 packet.")
            packet_path = (
                root / "stage1-packets" / case_id.removeprefix("case:") / f"{slug}-v2.json"
            )
            write_normalized_json_once(packet_path, packet)
            packet_refs.append(
                {
                    "case_id": case_id,
                    "relative_path": packet_path.relative_to(root).as_posix(),
                    "packet_digest": packet["packet_digest"],
                    "source_workspace_manifest_digest": ref["source_workspace_manifest_digest"],
                }
            )
        call = deepcopy(source_call)
        call["call_identity_id"] = str(
            uuid5(
                NAMESPACE_URL,
                "sc-referee-first-envelope-stage1-fable-completion-v2:" + participant_id,
            )
        )
        call["packet_refs"] = packet_refs
        call["v1_call_identity_id"] = source_call["call_identity_id"]
        calls.append(call)

    amendment: dict[str, Any] = {
        **{
            key: deepcopy(value)
            for key, value in v1.items()
            if key not in {"calls", "frozen_at", "amendment_digest"}
        },
        "amendment_version": "2.0.0",
        "v1_amendment_digest": V1_AMENDMENT_DIGEST,
        "v1_failure_ledger_digest": failure_ledger["ledger_digest"],
        "calls": calls,
        "execution_state": "frozen_not_started",
        "frozen_at": FROZEN_AT,
    }
    amendment["amendment_digest"] = semantic_digest(amendment)
    write_normalized_json_once(amendment_path, amendment)
    return amendment


def _manifest_stub(project_root: Path, case_id: str) -> dict[str, Any]:
    """Load the exact v1 blind workspace manifest bound by the protocol."""

    from scripts.record_first_direct_three_case_stage1_semantic_recovery_clean_cli import (
        _protocol,
    )

    protocol = _protocol(project_root)
    binding = next(item for item in protocol["source_case_bindings"] if item["case_id"] == case_id)
    manifest = _load(project_root / str(binding["source_workspace_manifest_relative_path"]))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    amendment = build_first_direct_stage1_fable_completion_v2(arguments.project_root.resolve())
    print(amendment["amendment_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
