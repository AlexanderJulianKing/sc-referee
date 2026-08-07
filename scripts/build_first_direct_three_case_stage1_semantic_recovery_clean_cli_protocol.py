from __future__ import annotations

import argparse
import json
import shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee_evaluation.review_protocol import build_stage1_review_packet
from sc_referee_evaluation.review_semantic_payload_v2 import (
    build_stage1_batch_output_schema_v2,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage1_recovery_claude_cli_replacement_calibration import (
    CLAUDE_CLI_REPLACEMENT_RELATIVE,
)
from scripts.build_first_direct_stage1_recovery_claude_cli_replacement_calibration import (
    REPLACEMENT_RELATIVE as V8_CALIBRATION_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_protocol import (
    CANONICAL_ISSUE_CLASS,
    CASE_IDS,
    LANE_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_protocol import (
    REVIEW_RELATIVE as SOURCE_REVIEW_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_protocol import (
    _participant_agent,
    _replacement_prompt,
    _source_case_bindings,
)

__all__ = [
    "ACTIVE_REVIEWERS",
    "CANONICAL_ISSUE_CLASS",
    "CASE_IDS",
    "REVIEW_RELATIVE",
    "SOURCE_REVIEW_RELATIVE",
    "build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol",
]

REVIEW_RELATIVE = (
    LANE_RELATIVE / "pilot-scientific-review-v4-semantic-recovery-clean-cli-three-case"
)

SOURCE_V3_PROTOCOL_DIGEST = (
    "sha256:94529e86411cc0c81c4a75a203c5895656b99228321288654a35d0d13feeb378"
)
V8_AMENDMENT_DIGEST = "sha256:7b85c5e3cd5ce4ec7fcda7cbaed98630442a3d3af972c4e1faee34df2867a8c2"
V8_ENROLLMENT_DIGEST = "sha256:a749696b6c72280bbd9f49e3e4372f86055551756d6d82cfb7a6cff158e4ce7a"
V8_PROTOCOL_DIGEST = "sha256:5f14cfc3b876281567cfcd6baa855ae3d83896b72ddf6af761a99b124f501400"
V8_LEDGER_DIGEST = "sha256:98d97c269781773700dad45ab460f09f0766b98bb3b5e2472d698eee9e0ecee9"

PACKET_AT = "2026-08-07T17:24:00Z"
FROZEN_AT = "2026-08-07T17:24:01Z"
ACTIVE_REVIEWERS = [
    "actor:stage1-recovery-claude-04",
    "actor:stage1-recovery-claude-05",
    "actor:stage1-recovery-codex-03",
    "actor:stage1-recovery-codex-04",
]
SOURCE_REVIEWERS = {
    "actor:stage1-recovery-claude-04": "actor:stage1-recovery-claude-01",
    "actor:stage1-recovery-claude-05": "actor:stage1-recovery-claude-03",
    "actor:stage1-recovery-codex-03": "actor:stage1-recovery-codex-03",
    "actor:stage1-recovery-codex-04": "actor:stage1-recovery-codex-04",
}
CLAUDE_REVIEWERS = {
    "actor:stage1-recovery-claude-04",
    "actor:stage1-recovery-claude-05",
}
CODEX_REVIEWERS = {
    "actor:stage1-recovery-codex-03",
    "actor:stage1-recovery-codex-04",
}
CLAUDE_CLI_INTERACTION_PROFILE = {
    "surface": "Claude Code CLI print mode",
    "print_mode": True,
    "safe_mode": True,
    "tools": "disabled",
    "mcp": "empty_strict",
    "session_persistence": False,
    "model_id": "claude-opus-5",
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


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Clean CLI Stage-1 protocol timestamps require an offset.")
    return parsed


def _source_v3_protocol(project_root: Path) -> dict[str, Any]:
    protocol = _load(project_root / SOURCE_REVIEW_RELATIVE / "STAGE1_REVIEW_PROTOCOL.json")
    _replay(protocol, "protocol_digest", SOURCE_V3_PROTOCOL_DIGEST, "The clean v3 protocol")
    if (
        protocol["artifact_kind"]
        != "direct_qualification_three_case_stage1_semantic_recovery_clean_protocol"
        or protocol["protocol_version"] != "3.0.0"
        or protocol["execution_state"] != "frozen_not_started"
        or protocol["case_ids"] != CASE_IDS
        or protocol["stage1_review_count"] != 0
        or protocol["stage1_freeze_count"] != 0
        or protocol["scientific_label_count"] != 0
        or protocol["detector_outcome_count"] != 0
    ):
        raise ValueError("The clean v3 protocol state drifted.")
    root = project_root / SOURCE_REVIEW_RELATIVE
    for name in (
        "incoming",
        "stage1-call-ledgers",
        "stage1-captures",
        "stage1-freezes",
        "codex-process-captures",
        "claude-process-captures",
        "claude-cli-process-captures",
    ):
        path = root / name
        if path.exists() or path.is_symlink():
            raise ValueError(f"The clean v3 protocol is no longer unexecuted: {path}")
    return protocol


def _v8_calibration_evidence(
    project_root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    root = project_root / V8_CALIBRATION_RELATIVE
    if V8_CALIBRATION_RELATIVE != CLAUDE_CLI_REPLACEMENT_RELATIVE:
        raise ValueError("The v8 calibration path binding drifted.")
    enrollment = _load(root / "PARTICIPANT_ENROLLMENT.json")
    _replay(enrollment, "enrollment_digest", V8_ENROLLMENT_DIGEST, "The v8 enrollment")
    amendment = _load(root / "REPLACEMENT_AMENDMENT.json")
    _replay(amendment, "amendment_digest", V8_AMENDMENT_DIGEST, "The v8 amendment")
    protocol = _load(root / "CALIBRATION_PROTOCOL.json")
    _replay(protocol, "protocol_digest", V8_PROTOCOL_DIGEST, "The v8 calibration protocol")
    ledger = _load(root / "CALIBRATION_LEDGER.json")
    _replay(ledger, "ledger_digest", V8_LEDGER_DIGEST, "The v8 calibration ledger")

    participants = {str(item["participant_id"]): item for item in enrollment["participants"]}
    entries = {str(item["participant_id"]): item for item in ledger["entries"]}
    if set(participants) != CLAUDE_REVIEWERS or set(entries) != CLAUDE_REVIEWERS:
        raise ValueError("The v8 calibration does not cover the exact clean Claude CLI pair.")
    for participant_id, participant in participants.items():
        supplied = participant.pop("configuration_digest", None)
        if supplied != semantic_digest(participant):
            raise ValueError(f"The v8 configuration does not replay for {participant_id}.")
        participant["configuration_digest"] = supplied
        entry = entries[participant_id]
        if (
            entry["configuration_digest"] != supplied
            or entry["execution_context_id"] != participant["execution_context_id"]
            or entry["calibration_status"] != "passed"
            or entry["calibration_evaluation"]["pass"] is not True
        ):
            raise ValueError(f"The v8 reviewer {participant_id} is not exactly calibrated.")
    replacements = {
        str(item["replacement_participant_id"]): str(item["superseded_participant_id"])
        for item in amendment["replacements"]
    }
    if replacements != {item: SOURCE_REVIEWERS[item] for item in CLAUDE_REVIEWERS}:
        raise ValueError("The v8 amendment replacement mapping drifted.")
    if (
        amendment["source_clean_stage1_protocol_digest"] != SOURCE_V3_PROTOCOL_DIGEST
        or amendment["replacement_enrollment_digest"] != V8_ENROLLMENT_DIGEST
        or amendment["replacement_calibration_protocol_digest"] != V8_PROTOCOL_DIGEST
        or ledger["participant_enrollment_digest"] != V8_ENROLLMENT_DIGEST
        or ledger["protocol_digest"] != V8_PROTOCOL_DIGEST
        or ledger["summary"]["all_reviewer_configurations_passed"] is not True
        or ledger["summary"]["passed_count"] != 2
        or ledger["summary"]["failed_count"] != 0
        or ledger["scientific_label_count"] != 0
        or ledger["detector_outcome_count"] != 0
        or _timestamp(str(ledger["sealed_at"])) >= _timestamp(FROZEN_AT)
    ):
        raise ValueError("The v8 calibration chain or chronology drifted.")
    return participants, entries


def build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol(
    project_root: Path,
) -> dict[str, Any]:
    output_root = project_root / REVIEW_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"Clean CLI Stage-1 protocol output already exists: {output_root}")
    source_protocol = _source_v3_protocol(project_root)
    claude_participants, claude_entries = _v8_calibration_evidence(project_root)
    case_bindings, manifests = _source_case_bindings(project_root, source_protocol)
    source_calls = {str(item["participant_id"]): item for item in source_protocol["calls"]}

    output_root.mkdir(parents=True)
    try:
        calls: list[dict[str, Any]] = []
        for participant_id in ACTIVE_REVIEWERS:
            source_participant_id = SOURCE_REVIEWERS[participant_id]
            source_call = source_calls[source_participant_id]
            case_order = [str(value) for value in source_call["case_order"]]
            if participant_id in CLAUDE_REVIEWERS:
                enrolled = claude_participants[participant_id]
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
                participant_configuration_digest = enrolled["configuration_digest"]
                reviewer_agent = _participant_agent(enrolled)
                output_schema = build_stage1_batch_output_schema_v2(
                    participant_id,
                    case_order,
                    CANONICAL_ISSUE_CLASS,
                )
                prompt = _replacement_prompt(
                    str(source_call["prompt"]),
                    source_participant_id,
                    participant_id,
                    output_schema,
                )
                calibration_ledger_digest = V8_LEDGER_DIGEST
                calibration_entry_digest = semantic_digest(claude_entries[participant_id])
                preservation_status = "v3_scientific_semantics_with_v8_calibrated_cli_configuration"
                interaction_profile = deepcopy(CLAUDE_CLI_INTERACTION_PROFILE)
            else:
                participant = deepcopy(source_call["participant"])
                participant_configuration_digest = source_call["participant_configuration_digest"]
                reviewer_agent = deepcopy(source_call["reviewer_agent_base"])
                output_schema = deepcopy(source_call["output_schema"])
                prompt = str(source_call["prompt"])
                calibration_ledger_digest = source_call["calibration_ledger_digest"]
                calibration_entry_digest = source_call["calibration_entry_digest"]
                preservation_status = "unexecuted_v3_configuration_prompt_and_schema_exact"
                interaction_profile = deepcopy(source_call["interaction_profile"])

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
                    output_root
                    / "stage1-packets"
                    / case_id.removeprefix("case:")
                    / f"{participant_id.removeprefix('actor:')}.json"
                )
                write_normalized_json_once(packet_path, packet)
                packet_refs.append(
                    {
                        "case_id": case_id,
                        "relative_path": packet_path.relative_to(output_root).as_posix(),
                        "packet_digest": packet["packet_digest"],
                        "source_workspace_manifest_digest": manifests[case_id]["manifest_digest"],
                    }
                )
            calls.append(
                {
                    "call_identity_id": str(
                        uuid5(
                            NAMESPACE_URL,
                            "sc-referee-first-envelope-stage1-semantic-recovery-clean-cli-v4:"
                            + participant_id,
                        )
                    ),
                    "participant_id": participant_id,
                    "participant_configuration_digest": participant_configuration_digest,
                    "calibration_ledger_digest": calibration_ledger_digest,
                    "calibration_entry_digest": calibration_entry_digest,
                    "source_v3_participant_id": source_participant_id,
                    "source_v3_call_identity_id": source_call["call_identity_id"],
                    "source_v3_prompt_digest": source_call["prompt_digest"],
                    "scientific_semantics_preservation": preservation_status,
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
                        source_protocol["semantic_recovery_contract"]
                    ),
                    "packet_refs": packet_refs,
                    "capture_destinations": [
                        "stage1-captures/"
                        + case_id.removeprefix("case:")
                        + "/"
                        + participant_id.removeprefix("actor:")
                        for case_id in case_order
                    ],
                    "interaction_profile": interaction_profile,
                }
            )

        protocol: dict[str, Any] = {
            "artifact_kind": (
                "direct_qualification_three_case_stage1_semantic_recovery_clean_cli_protocol"
            ),
            "protocol_version": "4.0.0",
            "protocol_id": (
                "scientific-review:complete-domain-exposure-denominator-pilot-stage1-"
                "semantic-recovery-clean-cli-v4"
            ),
            "controller_implementation": [
                {
                    "path": path_value,
                    "content_digest": sha256_digest((project_root / path_value).read_bytes()),
                }
                for path_value in (
                    "evaluation/src/sc_referee_evaluation/review_semantic_payload.py",
                    "evaluation/src/sc_referee_evaluation/review_semantic_payload_v2.py",
                    "evaluation/src/sc_referee_evaluation/review_protocol.py",
                    "evaluation/src/sc_referee_evaluation/capture.py",
                    "scripts/build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol.py",
                    "reference/schemas-v0.18.0/schemas/v0.18.0/agent-review.schema.json",
                )
            ],
            "source_v3_stage1_protocol_digest": SOURCE_V3_PROTOCOL_DIGEST,
            "source_v2_stage1_protocol_digest": source_protocol["source_v2_stage1_protocol_digest"],
            "duplicate_launch_failure_ledger_digest": source_protocol[
                "duplicate_launch_failure_ledger_digest"
            ],
            "duplicate_launch_recovery_amendment_digest": source_protocol[
                "duplicate_launch_recovery_amendment_digest"
            ],
            "v7_codex_replacement_calibration_ledger_digest": source_protocol[
                "v7_codex_replacement_calibration_ledger_digest"
            ],
            "v8_claude_cli_replacement_amendment_digest": V8_AMENDMENT_DIGEST,
            "v8_claude_cli_replacement_enrollment_digest": V8_ENROLLMENT_DIGEST,
            "v8_claude_cli_replacement_calibration_protocol_digest": V8_PROTOCOL_DIGEST,
            "v8_claude_cli_replacement_calibration_ledger_digest": V8_LEDGER_DIGEST,
            "participant_transition": {
                "preserved_unexecuted_v3_codex_participant_ids": sorted(CODEX_REVIEWERS),
                "superseded_v3_claude_participant_ids": sorted(
                    SOURCE_REVIEWERS[item] for item in CLAUDE_REVIEWERS
                ),
                "fresh_v8_participant_ids": sorted(CLAUDE_REVIEWERS),
                "v8_replacement_mapping": {
                    item: SOURCE_REVIEWERS[item] for item in sorted(CLAUDE_REVIEWERS)
                },
            },
            "semantic_recovery_contract": deepcopy(source_protocol["semantic_recovery_contract"]),
            "semantic_recovery_instruction": source_protocol["semantic_recovery_instruction"],
            "canonical_issue_class_scope": CANONICAL_ISSUE_CLASS,
            "case_ids": CASE_IDS,
            "source_case_bindings": case_bindings,
            "workspace_reuse": deepcopy(source_protocol["workspace_reuse"]),
            "review_design": deepcopy(source_protocol["review_design"]),
            "calls": calls,
            "failure_policy": {
                **deepcopy(source_protocol["failure_policy"]),
                "superseded_claude_app_configurations_may_not_be_reused": True,
                "replacement_claude_cli_calibration_must_remain_passed": True,
            },
            "limitations": deepcopy(source_protocol["limitations"]),
            "execution_state": "frozen_not_started",
            "stage1_review_count": 0,
            "stage1_freeze_count": 0,
            "stage2_review_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_clean_stage1_protocol_only",
        }
        protocol["protocol_digest"] = semantic_digest(protocol)
        write_normalized_json_once(output_root / "STAGE1_REVIEW_PROTOCOL.json", protocol)
        return protocol
    except BaseException:
        shutil.rmtree(output_root, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    protocol = build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol(
        arguments.project_root.resolve()
    )
    print(protocol["protocol_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
