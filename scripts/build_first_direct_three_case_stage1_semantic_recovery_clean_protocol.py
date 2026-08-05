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
from scripts.build_first_direct_three_case_stage1_protocol import (
    CANONICAL_ISSUE_CLASS,
    CASE_IDS,
    LANE_RELATIVE,
    VISIBLE_FILES,
)
from scripts.build_first_direct_three_case_stage1_semantic_recovery_protocol import (
    REVIEW_RELATIVE as SOURCE_REVIEW_RELATIVE,
)

__all__ = [
    "ACTIVE_REVIEWERS",
    "CANONICAL_ISSUE_CLASS",
    "CASE_IDS",
    "REVIEW_RELATIVE",
    "SOURCE_REVIEW_RELATIVE",
    "VISIBLE_FILES",
    "build_first_direct_three_case_stage1_semantic_recovery_clean_protocol",
]

REVIEW_RELATIVE = LANE_RELATIVE / "pilot-scientific-review-v3-semantic-recovery-clean-three-case"
CALIBRATION_RELATIVE = (
    LANE_RELATIVE / "reviewer-calibration-v7-stage1-semantic-recovery-codex-replacement"
)

SOURCE_V2_PROTOCOL_DIGEST = (
    "sha256:c7645bc5b5921f90505ce9f757cfbcff211f7386c14a1b778a8aeef595b93da6"
)
DUPLICATE_FAILURE_LEDGER_DIGEST = (
    "sha256:e47fcf73d71ade4c657ffc796f689457e2b956eafa333ee7583cd05219323267"
)
DUPLICATE_RECOVERY_AMENDMENT_DIGEST = (
    "sha256:d5638aa1fee086cf91def672fb5857ac874c0109172c4fea00903c65de21f24e"
)
V7_ENROLLMENT_DIGEST = "sha256:e14292917539270b13d345bc8a719a90d493627cdb618361db35b6de975cd772"
V7_PROTOCOL_DIGEST = "sha256:fb948e7b602e69ac8d7db4492c4805aa611fbceb72ccf009cbb7e0605f1f2d8d"
V7_AMENDMENT_DIGEST = "sha256:3329a5868dab425b32069acca9851ba5d3cc0e0f1c8971ea031b6100b28cb7c3"
V7_LEDGER_DIGEST = "sha256:a4b68cbe07aaba3237a805d5ce0df2aa4554b859f9efee371e382960fcc4de90"

PACKET_AT = "2026-08-05T08:24:18Z"
FROZEN_AT = "2026-08-05T08:24:19Z"
ACTIVE_REVIEWERS = [
    "actor:stage1-recovery-claude-01",
    "actor:stage1-recovery-claude-03",
    "actor:stage1-recovery-codex-03",
    "actor:stage1-recovery-codex-04",
]
SOURCE_REVIEWERS = {
    "actor:stage1-recovery-claude-01": "actor:stage1-recovery-claude-01",
    "actor:stage1-recovery-claude-03": "actor:stage1-recovery-claude-03",
    "actor:stage1-recovery-codex-03": "actor:stage1-recovery-codex-01",
    "actor:stage1-recovery-codex-04": "actor:stage1-recovery-codex-02",
}
CLAUDE_REVIEWERS = {
    "actor:stage1-recovery-claude-01",
    "actor:stage1-recovery-claude-03",
}
CODEX_REVIEWERS = {
    "actor:stage1-recovery-codex-03",
    "actor:stage1-recovery-codex-04",
}
PROMPT_SCHEMA_MARKER = "\n\nReturn only one unfenced JSON object matching this exact schema:\n"


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
        raise ValueError("Clean Stage-1 protocol timestamps require an offset.")
    return parsed


def _participant_agent(participant: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": participant["provider"],
        "agent_surface": participant["agent_surface"],
        "model_name": participant["model_name"],
        "model_id": participant["model_id"],
        "agent_version": participant["agent_version"],
        "model_snapshot": None,
        "reasoning_configuration": participant["reasoning_configuration"],
        "execution_context_id": participant["execution_context_id"],
        "independent_context": True,
        "system_prompt_digest": participant["system_prompt_digest"],
        "tool_policy_digest": participant["tool_policy_digest"],
        "environment_digest": participant["environment_digest"],
    }


def _source_v2_and_recovery(
    project_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = project_root / SOURCE_REVIEW_RELATIVE
    protocol = _load(root / "STAGE1_REVIEW_PROTOCOL.json")
    _replay(protocol, "protocol_digest", SOURCE_V2_PROTOCOL_DIGEST, "The v2 Stage-1 protocol")
    failure = _load(root / "CODEX_DUPLICATE_LAUNCH_FAILURE_LEDGER.json")
    _replay(
        failure,
        "ledger_digest",
        DUPLICATE_FAILURE_LEDGER_DIGEST,
        "The Codex duplicate-launch failure ledger",
    )
    amendment = _load(root / "CODEX_DUPLICATE_LAUNCH_RECOVERY_AMENDMENT.json")
    _replay(
        amendment,
        "amendment_digest",
        DUPLICATE_RECOVERY_AMENDMENT_DIGEST,
        "The Codex duplicate-launch recovery amendment",
    )
    if (
        protocol["artifact_kind"]
        != "direct_qualification_three_case_stage1_semantic_recovery_protocol"
        or protocol["protocol_version"] != "2.0.0"
        or protocol["execution_state"] != "frozen_not_started"
        or protocol["case_ids"] != CASE_IDS
        or protocol["stage1_freeze_count"] != 0
        or protocol["scientific_label_count"] != 0
        or protocol["detector_outcome_count"] != 0
    ):
        raise ValueError("The v2 Stage-1 protocol state drifted.")
    if (
        failure["protocol_digest"] != SOURCE_V2_PROTOCOL_DIGEST
        or failure["retained_artifact_admission"] != "ineligible_duplicate_attempt_identity"
        or failure["retained_review_count"] != 6
        or failure["stage1_freeze_count"] != 0
        or failure["scientific_label_count"] != 0
        or failure["detector_outcome_count"] != 0
    ):
        raise ValueError("The duplicate-launch failure state drifted.")
    if (
        amendment["protocol_digest"] != SOURCE_V2_PROTOCOL_DIGEST
        or amendment["source_failure_ledger_digest"] != DUPLICATE_FAILURE_LEDGER_DIGEST
        or amendment["decision"]
        != "abandon_both_affected_codex_configurations_and_recalibrate_fresh_replacements"
        or amendment["replacement_calibration_state"] != "not_started"
        or amendment["stage1_freeze_count"] != 0
        or amendment["scientific_label_count"] != 0
        or amendment["detector_outcome_count"] != 0
    ):
        raise ValueError("The duplicate-launch recovery authority drifted.")
    return protocol, failure, amendment


def _v7_calibration_evidence(
    project_root: Path,
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    root = project_root / CALIBRATION_RELATIVE
    enrollment = _load(root / "PARTICIPANT_ENROLLMENT.json")
    _replay(enrollment, "enrollment_digest", V7_ENROLLMENT_DIGEST, "The v7 enrollment")
    protocol = _load(root / "CALIBRATION_PROTOCOL.json")
    _replay(protocol, "protocol_digest", V7_PROTOCOL_DIGEST, "The v7 calibration protocol")
    amendment = _load(root / "REPLACEMENT_AMENDMENT.json")
    _replay(amendment, "amendment_digest", V7_AMENDMENT_DIGEST, "The v7 amendment")
    ledger = _load(root / "CALIBRATION_LEDGER.json")
    _replay(ledger, "ledger_digest", V7_LEDGER_DIGEST, "The v7 calibration ledger")

    participants = {str(item["participant_id"]): item for item in enrollment["participants"]}
    assignments = {str(item["participant_id"]): item for item in protocol["assignments"]}
    entries = {str(item["participant_id"]): item for item in ledger["entries"]}
    if set(participants) != CODEX_REVIEWERS or set(assignments) != CODEX_REVIEWERS:
        raise ValueError("The v7 calibration does not contain the exact clean Codex pair.")
    if set(entries) != CODEX_REVIEWERS:
        raise ValueError("The v7 calibration ledger does not cover the exact clean Codex pair.")
    for participant_id, participant in participants.items():
        supplied = participant.pop("configuration_digest", None)
        if supplied != semantic_digest(participant):
            raise ValueError(f"The v7 configuration does not replay for {participant_id}.")
        participant["configuration_digest"] = supplied
        assignment = assignments[participant_id]
        entry = entries[participant_id]
        if (
            assignment["configuration_digest"] != supplied
            or assignment["execution_context_id"] != participant["execution_context_id"]
            or entry["configuration_digest"] != supplied
            or entry["execution_context_id"] != participant["execution_context_id"]
            or entry["calibration_status"] != "passed"
            or entry["calibration_evaluation"]["pass"] is not True
        ):
            raise ValueError(f"The v7 reviewer {participant_id} is not exactly calibrated.")
    replacements = {
        str(item["replacement_participant_id"]): str(item["source_participant_id"])
        for item in amendment["replacements"]
    }
    if replacements != {item: SOURCE_REVIEWERS[item] for item in CODEX_REVIEWERS}:
        raise ValueError("The v7 amendment replacement mapping drifted.")
    if (
        protocol["participant_enrollment_digest"] != V7_ENROLLMENT_DIGEST
        or amendment["replacement_enrollment_digest"] != V7_ENROLLMENT_DIGEST
        or amendment["replacement_calibration_protocol_digest"] != V7_PROTOCOL_DIGEST
        or ledger["participant_enrollment_digest"] != V7_ENROLLMENT_DIGEST
        or ledger["protocol_digest"] != V7_PROTOCOL_DIGEST
        or protocol["source_duplicate_launch_failure_ledger_digest"]
        != DUPLICATE_FAILURE_LEDGER_DIGEST
        or protocol["source_duplicate_launch_recovery_amendment_digest"]
        != DUPLICATE_RECOVERY_AMENDMENT_DIGEST
        or amendment["source_duplicate_launch_failure_ledger_digest"]
        != DUPLICATE_FAILURE_LEDGER_DIGEST
        or amendment["source_duplicate_launch_recovery_amendment_digest"]
        != DUPLICATE_RECOVERY_AMENDMENT_DIGEST
        or ledger["summary"]["all_reviewer_configurations_passed"] is not True
        or ledger["summary"]["passed_count"] != 2
        or ledger["summary"]["failed_count"] != 0
        or ledger["scientific_label_count"] != 0
        or ledger["detector_outcome_count"] != 0
        or _timestamp(str(ledger["sealed_at"])) >= _timestamp(FROZEN_AT)
    ):
        raise ValueError("The v7 calibration chain or chronology drifted.")
    return participants, assignments, entries


def _assert_claude_unexposed(
    project_root: Path,
    protocol: dict[str, Any],
    amendment: dict[str, Any],
) -> None:
    root = project_root / SOURCE_REVIEW_RELATIVE
    calls = {str(item["participant_id"]): item for item in protocol["calls"]}
    preserved = {
        str(item["participant_id"]): item
        for item in amendment["preserved_unexposed_claude_configurations"]
    }
    if set(preserved) != CLAUDE_REVIEWERS:
        raise ValueError("The exact unexposed Claude pair is no longer preserved.")
    for participant_id in CLAUDE_REVIEWERS:
        call = calls[participant_id]
        item = preserved[participant_id]
        if (
            item["preservation_status"] != "authorized_unattempted_unchanged"
            or item["participant_configuration_digest"] != call["participant_configuration_digest"]
            or item["execution_context_id"] != call["participant"]["execution_context_id"]
            or item["call_identity_id"] != call["call_identity_id"]
            or item["prompt_digest"] != call["prompt_digest"]
            or item["output_schema_digest"] != call["output_schema_digest"]
            or item["case_order"] != call["case_order"]
        ):
            raise ValueError(f"The preserved Claude binding drifted for {participant_id}.")
        slug = participant_id.removeprefix("actor:")
        exposed = [
            root / "incoming" / f"{slug}.json",
            root / "stage1-call-ledgers" / f"{slug}.json",
            root / "codex-process-captures" / slug,
            root / "claude-process-captures" / slug,
            *list((root / "stage1-captures").glob(f"*/{slug}")),
        ]
        if any(path.exists() or path.is_symlink() for path in exposed):
            raise ValueError(f"The Claude configuration {participant_id} is no longer unexposed.")


def _source_case_bindings(
    project_root: Path, protocol: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    expected_paths = sorted(str(item["path"]) for item in VISIBLE_FILES)
    bindings = {str(item["case_id"]): item for item in protocol["source_case_bindings"]}
    if set(bindings) != set(CASE_IDS):
        raise ValueError("The v2 protocol no longer binds the exact three v1 cases.")
    manifests: dict[str, dict[str, Any]] = {}
    copied: list[dict[str, Any]] = []
    for case_id in CASE_IDS:
        binding = bindings[case_id]
        preparation_path = project_root / str(binding["source_preparation_relative_path"])
        manifest_path = project_root / str(binding["source_workspace_manifest_relative_path"])
        workspace_root = project_root / str(binding["source_workspace_relative_path"])
        if "pilot-scientific-review-v1-three-case" not in manifest_path.parts:
            raise ValueError("A clean Stage-1 workspace does not originate in the v1 blind freeze.")
        preparation = _load(preparation_path)
        _replay(
            preparation,
            "preparation_digest",
            str(binding["source_preparation_digest"]),
            f"The v1 preparation for {case_id}",
        )
        manifest = _load(manifest_path)
        _replay(
            manifest,
            "manifest_digest",
            str(binding["source_workspace_manifest_digest"]),
            f"The v1 workspace manifest for {case_id}",
        )
        actual: dict[str, str] = {}
        for item in manifest["files"]:
            relative = str(item["path"])
            path = workspace_root / relative
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"A v1 blind workspace file is unavailable: {path}")
            actual[relative] = sha256_digest(path.read_bytes())
        if (
            sorted(actual) != expected_paths
            or actual != binding["visible_content_digests"]
            or actual != preparation["visible_content_digests"]
            or manifest["answer_side_content_copied"] is not False
            or manifest["project_code_executed"] is not False
            or binding["workspace_bytes_reused_without_copy"] is not True
        ):
            raise ValueError(f"The exact v1 blind workspace binding drifted for {case_id}.")
        manifests[case_id] = manifest
        copied.append(deepcopy(binding))
    return copied, manifests


def _replacement_prompt(
    source_prompt: str,
    source_participant_id: str,
    participant_id: str,
    output_schema: dict[str, Any],
) -> str:
    if PROMPT_SCHEMA_MARKER not in source_prompt:
        raise ValueError("The v2 scientific prompt schema boundary is unavailable.")
    body = source_prompt.split(PROMPT_SCHEMA_MARKER, 1)[0]
    if source_participant_id not in body:
        raise ValueError("The v2 scientific prompt participant binding is unavailable.")
    body = body.replace(source_participant_id, participant_id)
    return (
        body
        + PROMPT_SCHEMA_MARKER
        + json.dumps(output_schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    ).strip()


def build_first_direct_three_case_stage1_semantic_recovery_clean_protocol(
    project_root: Path,
) -> dict[str, Any]:
    output_root = project_root / REVIEW_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"Clean Stage-1 protocol output already exists: {output_root}")
    source_protocol, _failure, recovery = _source_v2_and_recovery(project_root)
    codex_participants, _codex_assignments, codex_entries = _v7_calibration_evidence(project_root)
    _assert_claude_unexposed(project_root, source_protocol, recovery)
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
                participant = deepcopy(source_call["participant"])
                participant_configuration_digest = source_call["participant_configuration_digest"]
                reviewer_agent = deepcopy(source_call["reviewer_agent_base"])
                output_schema = deepcopy(source_call["output_schema"])
                prompt = str(source_call["prompt"])
                calibration_ledger_digest = source_protocol[
                    "aggregate_recovery_calibration_ledger_digest"
                ]
                calibration_entry_digest = source_call["aggregate_calibration_entry_digest"]
                preservation_status = "unexposed_v2_configuration_prompt_and_schema_exact"
            else:
                enrolled = codex_participants[participant_id]
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
                calibration_ledger_digest = V7_LEDGER_DIGEST
                calibration_entry_digest = semantic_digest(codex_entries[participant_id])
                preservation_status = "v2_scientific_semantics_with_v7_calibrated_configuration"

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
                            f"sc-referee-first-envelope-stage1-semantic-recovery-clean-v3:{participant_id}",
                        )
                    ),
                    "participant_id": participant_id,
                    "participant_configuration_digest": participant_configuration_digest,
                    "calibration_ledger_digest": calibration_ledger_digest,
                    "calibration_entry_digest": calibration_entry_digest,
                    "source_v2_participant_id": source_participant_id,
                    "source_v2_call_identity_id": source_call["call_identity_id"],
                    "source_v2_prompt_digest": source_call["prompt_digest"],
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
                        f"stage1-captures/{case_id.removeprefix('case:')}/{participant_id.removeprefix('actor:')}"
                        for case_id in case_order
                    ],
                    "interaction_profile": deepcopy(source_call["interaction_profile"]),
                }
            )

        protocol: dict[str, Any] = {
            "artifact_kind": (
                "direct_qualification_three_case_stage1_semantic_recovery_clean_protocol"
            ),
            "protocol_version": "3.0.0",
            "protocol_id": (
                "scientific-review:complete-domain-exposure-denominator-pilot-stage1-"
                "semantic-recovery-clean-v3"
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
                    "scripts/build_first_direct_three_case_stage1_semantic_recovery_clean_protocol.py",
                    "reference/schemas-v0.18.0/schemas/v0.18.0/agent-review.schema.json",
                )
            ],
            "source_v2_stage1_protocol_digest": SOURCE_V2_PROTOCOL_DIGEST,
            "duplicate_launch_failure_ledger_digest": DUPLICATE_FAILURE_LEDGER_DIGEST,
            "duplicate_launch_recovery_amendment_digest": (DUPLICATE_RECOVERY_AMENDMENT_DIGEST),
            "v7_codex_replacement_enrollment_digest": V7_ENROLLMENT_DIGEST,
            "v7_codex_replacement_calibration_protocol_digest": V7_PROTOCOL_DIGEST,
            "v7_codex_replacement_amendment_digest": V7_AMENDMENT_DIGEST,
            "v7_codex_replacement_calibration_ledger_digest": V7_LEDGER_DIGEST,
            "participant_transition": {
                "preserved_unexposed_v2_participant_ids": sorted(CLAUDE_REVIEWERS),
                "abandoned_v2_participant_ids": sorted(
                    SOURCE_REVIEWERS[item] for item in CODEX_REVIEWERS
                ),
                "fresh_v7_participant_ids": sorted(CODEX_REVIEWERS),
                "v7_replacement_mapping": {
                    item: SOURCE_REVIEWERS[item] for item in sorted(CODEX_REVIEWERS)
                },
            },
            "semantic_recovery_contract": deepcopy(source_protocol["semantic_recovery_contract"]),
            "semantic_recovery_instruction": source_protocol["semantic_recovery_instruction"],
            "canonical_issue_class_scope": CANONICAL_ISSUE_CLASS,
            "case_ids": CASE_IDS,
            "source_case_bindings": case_bindings,
            "workspace_reuse": {
                "source_v1_workspace_bytes_copied": False,
                "source_v1_workspace_bytes_regenerated": False,
                "source_v1_workspace_manifests_reused_exactly": True,
                "source_v1_visible_bytes_reused_exactly": True,
            },
            "review_design": deepcopy(source_protocol["review_design"]),
            "calls": calls,
            "failure_policy": {
                **deepcopy(source_protocol["failure_policy"]),
                "duplicate_launch_codex_reviews_may_not_be_reused": True,
                "abandoned_codex_configurations_may_not_be_reenrolled": True,
                "replacement_codex_calibration_must_remain_passed": True,
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
    protocol = build_first_direct_three_case_stage1_semantic_recovery_clean_protocol(
        arguments.project_root.resolve()
    )
    print(protocol["protocol_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
