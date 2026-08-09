from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee_evaluation.review_protocol import build_stage1_review_packet
from sc_referee_evaluation.review_semantic_payload_v2 import (
    build_stage1_batch_output_schema_v2,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage1_recovery_fable_addition_calibration import (
    ADDITION_RELATIVE as V9_CALIBRATION_RELATIVE,
)
from scripts.build_first_direct_stage1_recovery_fable_addition_calibration import (
    FABLE_CLI_MODEL_ALIAS,
)
from scripts.build_first_direct_three_case_stage1_protocol import CANONICAL_ISSUE_CLASS
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol import (
    REVIEW_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_protocol import (
    _participant_agent,
    _replacement_prompt,
)
from scripts.record_first_direct_three_case_stage1_semantic_recovery_clean_cli import (
    _protocol,
)

AMENDMENT_NAME = "FABLE_COMPLETION_AMENDMENT.json"
ADR_REFERENCE = "ADR-0066-CROSS-MODEL-SINGLE-PROVIDER-REVIEW-PANEL.md"
ADR_STATUS = "accepted_by_maintainer_2026-08-07"
V9_ENROLLMENT_DIGEST = "sha256:3db930440af064ba2b774ab3d58d4c63cfb0edcf43fe8a6592d38379096bdb28"
V9_LEDGER_DIGEST = "sha256:6ae6507fa76c9444386f3c12dda0b141a496cfb57e0f3fefc3539d15a8dda542"
PACKET_AT = "2026-08-07T18:52:00Z"
FROZEN_AT = "2026-08-07T18:52:01Z"

# Each Fable call completes the panel slot of one obsolete, never-executed Codex
# call: it reuses that call's exact case order and scientific prompt body, with
# only the participant identity and output-schema constant changed.
SLOT_BY_FABLE = {
    "actor:stage1-recovery-fable-01": "actor:stage1-recovery-codex-03",
    "actor:stage1-recovery-fable-02": "actor:stage1-recovery-codex-04",
}
ADMITTED_OPUS_CALL_LEDGERS = {
    "actor:stage1-recovery-claude-04": (
        "sha256:da5c90dc9cf02ef3418601a3ac539dbfc81912ceabb4a89b54b9495daae65f83"
    ),
    "actor:stage1-recovery-claude-05": (
        "sha256:7cce51f846ccd077a78237c886f10068f16028a296f5769972304b4d231827e5"
    ),
}
FABLE_CLI_INTERACTION_PROFILE = {
    "surface": "Claude Code CLI print mode",
    "print_mode": True,
    "safe_mode": True,
    "tools": "disabled",
    "mcp": "empty_strict",
    "session_persistence": False,
    "model_id": "claude-fable-5",
    "model_alias_argument": FABLE_CLI_MODEL_ALIAS,
    "model_usage_post_verification_required": True,
    "reasoning_effort": "high",
    "session_id_binding": "call_identity_id",
    "structured_output": "prompt_embedded_schema_local_fail_closed_validation",
}


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def _v9_evidence(project_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    root = project_root / V9_CALIBRATION_RELATIVE
    enrollment = _load(root / "PARTICIPANT_ENROLLMENT.json")
    _replay(enrollment, "enrollment_digest", V9_ENROLLMENT_DIGEST, "The v9 enrollment")
    ledger = _load(root / "CALIBRATION_LEDGER.json")
    _replay(ledger, "ledger_digest", V9_LEDGER_DIGEST, "The v9 calibration ledger")
    participants = {str(item["participant_id"]): item for item in enrollment["participants"]}
    entries = {str(item["participant_id"]): item for item in ledger["entries"]}
    if set(participants) != set(SLOT_BY_FABLE) or set(entries) != set(SLOT_BY_FABLE):
        raise ValueError("The v9 calibration does not cover the exact Fable pair.")
    for participant_id, participant in participants.items():
        supplied = participant.pop("configuration_digest", None)
        if supplied != semantic_digest(participant):
            raise ValueError(f"The v9 configuration does not replay for {participant_id}.")
        participant["configuration_digest"] = supplied
        entry = entries[participant_id]
        if (
            entry["configuration_digest"] != supplied
            or entry["calibration_status"] != "passed"
            or entry["calibration_evaluation"]["pass"] is not True
        ):
            raise ValueError(f"The v9 reviewer {participant_id} is not exactly calibrated.")
    return participants, entries


def _adr_accepted(project_root: Path) -> str:
    adr_path = project_root / "docs" / "implementation" / ADR_REFERENCE
    text = adr_path.read_text(encoding="utf-8")
    if "**Status:** Accepted by the maintainer on 2026-08-07" not in text:
        raise ValueError("ADR-0066 is not recorded as accepted; the amendment may not freeze.")
    return sha256_digest(text)


def _admitted_opus_ledgers(project_root: Path, root: Path) -> dict[str, str]:
    admitted: dict[str, str] = {}
    for participant_id, expected in ADMITTED_OPUS_CALL_LEDGERS.items():
        ledger = _load(
            root / "stage1-call-ledgers" / f"{participant_id.removeprefix('actor:')}.json"
        )
        _replay(ledger, "ledger_digest", expected, f"The admitted call ledger {participant_id}")
        if ledger["review_count"] != 3 or ledger["scientific_label_count"] != 0:
            raise ValueError(f"The admitted call ledger {participant_id} is not in panel state.")
        admitted[participant_id] = expected
    return admitted


def build_first_direct_stage1_fable_completion_amendment(project_root: Path) -> dict[str, Any]:
    root = project_root / REVIEW_RELATIVE
    output_path = root / AMENDMENT_NAME
    if output_path.exists() or output_path.is_symlink():
        raise FileExistsError("The Fable completion amendment is already frozen.")
    adr_digest = _adr_accepted(project_root)
    protocol = _protocol(project_root)
    participants, entries = _v9_evidence(project_root)
    admitted = _admitted_opus_ledgers(project_root, root)
    protocol_calls = {str(item["participant_id"]): item for item in protocol["calls"]}
    for _fable_id, codex_id in SLOT_BY_FABLE.items():
        slug = codex_id.removeprefix("actor:")
        for stale in (
            root / "incoming" / f"{slug}.json",
            root / "stage1-call-ledgers" / f"{slug}.json",
        ):
            if stale.exists() or stale.is_symlink():
                raise ValueError(f"The obsolete Codex call {codex_id} was executed; cannot amend.")

    manifests = {
        str(binding["case_id"]): _load(
            project_root / str(binding["source_workspace_manifest_relative_path"])
        )
        for binding in protocol["source_case_bindings"]
    }

    calls: list[dict[str, Any]] = []
    for fable_id in sorted(SLOT_BY_FABLE):
        codex_id = SLOT_BY_FABLE[fable_id]
        source_call = protocol_calls[codex_id]
        case_order = [str(value) for value in source_call["case_order"]]
        enrolled = participants[fable_id]
        participant = {
            key: enrolled[key]
            for key in (
                "provider",
                "agent_surface",
                "agent_version",
                "model_name",
                "model_id",
                "reasoning_configuration",
                "execution_context_id",
                "system_prompt_digest",
                "tool_policy_digest",
                "environment_digest",
            )
        }
        reviewer_agent = _participant_agent(enrolled)
        output_schema = build_stage1_batch_output_schema_v2(
            fable_id,
            case_order,
            CANONICAL_ISSUE_CLASS,
        )
        prompt = _replacement_prompt(
            str(source_call["prompt"]),
            codex_id,
            fable_id,
            output_schema,
        )
        packet_refs: list[dict[str, Any]] = []
        for case_id in case_order:
            packet = build_stage1_review_packet(
                case_id,
                manifests[case_id],
                reviewer_agent,
                prompt,
                created_at=PACKET_AT,
            )
            packet_path = (
                root
                / "stage1-packets"
                / case_id.removeprefix("case:")
                / f"{fable_id.removeprefix('actor:')}.json"
            )
            write_normalized_json_once(packet_path, packet)
            packet_refs.append(
                {
                    "case_id": case_id,
                    "relative_path": packet_path.relative_to(root).as_posix(),
                    "packet_digest": packet["packet_digest"],
                    "source_workspace_manifest_digest": manifests[case_id]["manifest_digest"],
                }
            )
        calls.append(
            {
                "call_identity_id": str(
                    uuid5(
                        NAMESPACE_URL,
                        "sc-referee-first-envelope-stage1-fable-completion-v1:" + fable_id,
                    )
                ),
                "participant_id": fable_id,
                "participant_configuration_digest": enrolled["configuration_digest"],
                "calibration_ledger_digest": V9_LEDGER_DIGEST,
                "calibration_entry_digest": semantic_digest(entries[fable_id]),
                "completed_panel_slot_participant_id": codex_id,
                "obsolete_call_identity_id": source_call["call_identity_id"],
                "source_prompt_digest": source_call["prompt_digest"],
                "participant": participant,
                "reviewer_agent_base": reviewer_agent,
                "case_order": case_order,
                "shared_transcript_expected": True,
                "cross_case_comparison_permitted": False,
                "prompt": prompt,
                "prompt_digest": sha256_digest(prompt),
                "output_schema": output_schema,
                "output_schema_digest": semantic_digest(output_schema),
                "semantic_recovery_contract_digest": semantic_digest(
                    protocol["semantic_recovery_contract"]
                ),
                "packet_refs": packet_refs,
                "capture_destinations": [
                    "stage1-captures/"
                    + case_id.removeprefix("case:")
                    + "/"
                    + fable_id.removeprefix("actor:")
                    for case_id in case_order
                ],
                "interaction_profile": deepcopy(FABLE_CLI_INTERACTION_PROFILE),
            }
        )

    amendment: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_fable_panel_completion_amendment",
        "amendment_version": "1.0.0",
        "adr_reference": ADR_REFERENCE,
        "adr_status": ADR_STATUS,
        "adr_content_digest": adr_digest,
        "protocol_digest": protocol["protocol_digest"],
        "obsolete_codex_call_identity_ids": sorted(
            str(protocol_calls[codex_id]["call_identity_id"]) for codex_id in SLOT_BY_FABLE.values()
        ),
        "obsolete_codex_calls_executed": 0,
        "admitted_opus_call_ledger_digests": admitted,
        "v9_fable_enrollment_digest": V9_ENROLLMENT_DIGEST,
        "v9_fable_calibration_ledger_digest": V9_LEDGER_DIGEST,
        "panel_composition": {
            "provider_families": ["Anthropic"],
            "model_families": ["Claude Fable 5", "Claude Opus 5"],
            "reviews_per_case": 4,
            "reviews_per_model_family_per_case": 2,
            "single_provider_disclosure_required": True,
            "coordinator_model_family_overlap_disclosure_required": True,
        },
        "calls": calls,
        "execution_state": "frozen_not_started",
        "stage1_review_count": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "frozen_at": FROZEN_AT,
        "qualification_authority": "none_panel_completion_amendment_only",
    }
    amendment["amendment_digest"] = semantic_digest(amendment)
    write_normalized_json_once(output_path, amendment)
    return amendment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    amendment = build_first_direct_stage1_fable_completion_amendment(
        arguments.project_root.resolve()
    )
    print(amendment["amendment_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
