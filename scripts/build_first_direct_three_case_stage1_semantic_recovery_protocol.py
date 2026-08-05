from __future__ import annotations

import argparse
import json
import shutil
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
from scripts.build_first_direct_three_case_stage1_protocol import (
    CANONICAL_ISSUE_CLASS,
    CASE_IDS,
    LANE_RELATIVE,
    VISIBLE_FILES,
)
from scripts.build_first_direct_three_case_stage1_protocol import (
    REVIEW_RELATIVE as SOURCE_REVIEW_RELATIVE,
)

REVIEW_RELATIVE = LANE_RELATIVE / "pilot-scientific-review-v2-semantic-recovery-three-case"
RECOVERY_RELATIVE = LANE_RELATIVE / "reviewer-calibration-v5-stage1-semantic-recovery"
REPLACEMENT_RELATIVE = (
    LANE_RELATIVE / "reviewer-calibration-v6-stage1-semantic-recovery-claude-replacement"
)

SOURCE_PROTOCOL_DIGEST = "sha256:d9f3a84d205b2fa58d3abb38486f2068d4efd8a33526b4d1f35a2419a72d7d6b"
SOURCE_PANEL_LEDGER_DIGEST = (
    "sha256:cde80f4a0faf9f2d96699122127177252afcaac275b35d2ba9be72b812433851"
)
SOURCE_INELIGIBILITY_LEDGER_DIGEST = (
    "sha256:6f084c78e616769fee141d6256dd3423c70cdc81674bd9defb3b5177696be79e"
)
RECOVERY_AMENDMENT_DIGEST = (
    "sha256:225c037b5bbcfdcc16bd49bcb0f676fd3715ccf94528e4e6ad3e6fc403df38a4"
)
CODEX_RETRY_AMENDMENT_DIGEST = (
    "sha256:f817612f395f490760b108b314de2f2fda86977caa43ab27b966e4c25e68c44b"
)
REPLACEMENT_AMENDMENT_DIGEST = (
    "sha256:2e8880107d0e276dd93b1db85587db944f5dcfe79272beb30021e449c8f0208f"
)
RECOVERY_ENROLLMENT_DIGEST = (
    "sha256:5b1ecce6b493eadc5184dc359927f19519b0cd8ceeb4124e98220313752bb251"
)
REPLACEMENT_ENROLLMENT_DIGEST = (
    "sha256:832ffc15b3897dcbb2013d35b25e25d4484d985b8d2a402bfe070e3b55351f18"
)
AGGREGATE_CALIBRATION_LEDGER_DIGEST = (
    "sha256:3ad5715c1ae74d0e6c2e5f54f9507ee51cc77d6934fb0e2014d6aea64f4c2a1b"
)

PACKET_AT = "2026-08-05T07:50:00Z"
FROZEN_AT = "2026-08-05T07:51:00Z"
ACTIVE_REVIEWERS = [
    "actor:stage1-recovery-claude-01",
    "actor:stage1-recovery-claude-03",
    "actor:stage1-recovery-codex-01",
    "actor:stage1-recovery-codex-02",
]
SOURCE_REVIEWERS = {
    "actor:stage1-recovery-claude-01": "actor:stage1-claude-01",
    "actor:stage1-recovery-claude-03": "actor:stage1-claude-02",
    "actor:stage1-recovery-codex-01": "actor:stage1-codex-01",
    "actor:stage1-recovery-codex-02": "actor:stage1-codex-02",
}
SEMANTIC_RECOVERY_INSTRUCTION = (
    "unresolved_material_questions has one narrow operational meaning: include only unanswered "
    "questions whose resolution could reverse the verdict for the declared in-scope issue. If any "
    "such question remains, use conditional_or_unknown or insufficient_evidence. For "
    "demonstrated_issue or no_demonstrated_issue_within_scope, return an empty array. Do not place "
    "out-of-scope or explicitly non-reversing caveats in unresolved_material_questions."
)


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


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


def _active_participants(project_root: Path) -> dict[str, dict[str, Any]]:
    recovery_root = project_root / RECOVERY_RELATIVE
    replacement_root = project_root / REPLACEMENT_RELATIVE
    recovery_enrollment = _load(recovery_root / "PARTICIPANT_ENROLLMENT.json")
    _replay(
        recovery_enrollment,
        "enrollment_digest",
        RECOVERY_ENROLLMENT_DIGEST,
        "The recovery participant enrollment",
    )
    replacement_enrollment = _load(replacement_root / "PARTICIPANT_ENROLLMENT.json")
    _replay(
        replacement_enrollment,
        "enrollment_digest",
        REPLACEMENT_ENROLLMENT_DIGEST,
        "The replacement participant enrollment",
    )
    participants = {
        str(item["participant_id"]): item
        for item in [
            *recovery_enrollment["participants"],
            *replacement_enrollment["participants"],
        ]
    }
    selected = {participant_id: participants[participant_id] for participant_id in ACTIVE_REVIEWERS}
    if len(selected) != 4 or {str(item["provider"]) for item in selected.values()} != {
        "Anthropic",
        "OpenAI",
    }:
        raise ValueError("The recovery panel does not contain the exact active 2x2 provider set.")
    for participant in selected.values():
        supplied = participant.pop("configuration_digest", None)
        if supplied != semantic_digest(participant):
            raise ValueError("An active recovery participant configuration does not replay.")
        participant["configuration_digest"] = supplied

    aggregate = _load(replacement_root / "AGGREGATE_CALIBRATION_LEDGER.json")
    _replay(
        aggregate,
        "ledger_digest",
        AGGREGATE_CALIBRATION_LEDGER_DIGEST,
        "The aggregate recovery calibration ledger",
    )
    if aggregate["summary"] != {
        "active_failed_count": 0,
        "active_passed_count": 4,
        "active_reviewer_configuration_count": 4,
        "all_active_reviewer_configurations_passed": True,
        "historical_attempt_count": 5,
        "historical_failed_attempt_count": 1,
    }:
        raise ValueError("The aggregate recovery calibration status has drifted.")
    entries = {str(item["participant_id"]): item for item in aggregate["entries"]}
    if set(entries) != set(ACTIVE_REVIEWERS):
        raise ValueError("The aggregate calibration ledger does not equal the active panel.")
    for participant_id, participant in selected.items():
        entry = entries[participant_id]
        if (
            entry["calibration_status"] != "passed"
            or entry["calibration_evaluation"]["pass"] is not True
            or entry["configuration_digest"] != participant["configuration_digest"]
            or entry["execution_context_id"] != participant["execution_context_id"]
        ):
            raise ValueError(f"Active recovery reviewer {participant_id} is not calibrated.")
    return selected


def _source_evidence(project_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    source_root = project_root / SOURCE_REVIEW_RELATIVE
    recovery_root = project_root / RECOVERY_RELATIVE
    replacement_root = project_root / REPLACEMENT_RELATIVE
    source_protocol = _load(source_root / "STAGE1_REVIEW_PROTOCOL.json")
    _replay(
        source_protocol,
        "protocol_digest",
        SOURCE_PROTOCOL_DIGEST,
        "The source Stage-1 protocol",
    )
    source_panel = _load(source_root / "STAGE1_PANEL_LEDGER.json")
    _replay(
        source_panel,
        "ledger_digest",
        SOURCE_PANEL_LEDGER_DIGEST,
        "The source Stage-1 panel ledger",
    )
    if (
        source_panel["review_count"] != 12
        or source_panel["stage1_freeze_count"] != 3
        or source_panel["scientific_label_count"] != 0
        or source_panel["detector_outcome_count"] != 0
    ):
        raise ValueError("The source Stage-1 panel state has drifted.")

    evidence = [
        (
            recovery_root / "STAGE1_LABEL_INELIGIBILITY_LEDGER.json",
            "ledger_digest",
            SOURCE_INELIGIBILITY_LEDGER_DIGEST,
            "The source label-ineligibility ledger",
        ),
        (
            recovery_root / "RECOVERY_AMENDMENT.json",
            "amendment_digest",
            RECOVERY_AMENDMENT_DIGEST,
            "The semantic recovery amendment",
        ),
        (
            recovery_root / "CODEX_CALIBRATION_TRANSPORT_RETRY_AMENDMENT.json",
            "amendment_digest",
            CODEX_RETRY_AMENDMENT_DIGEST,
            "The Codex calibration retry amendment",
        ),
        (
            replacement_root / "REPLACEMENT_AMENDMENT.json",
            "amendment_digest",
            REPLACEMENT_AMENDMENT_DIGEST,
            "The Claude replacement amendment",
        ),
    ]
    replayed: dict[str, dict[str, Any]] = {}
    for path, field, digest, label in evidence:
        record = _load(path)
        _replay(record, field, digest, label)
        replayed[path.name] = record
    ineligibility = replayed["STAGE1_LABEL_INELIGIBILITY_LEDGER.json"]
    recovery = replayed["RECOVERY_AMENDMENT.json"]
    if (
        ineligibility["label_eligibility"] != "blocked"
        or ineligibility["stage2_can_reverse_stage1_blocker"] is not False
        or ineligibility["scientific_label_count"] != 0
        or ineligibility["detector_outcome_count"] != 0
        or recovery["decision"]
        != "rerun_complete_stage1_panel_after_fresh_configuration_calibration"
        or recovery["semantic_contract"]["eligible_verdict_requires_empty_array"] is not True
    ):
        raise ValueError("The semantic recovery authority has drifted.")
    return source_protocol, recovery


def _source_case_bindings(
    project_root: Path, source_protocol: dict[str, Any]
) -> list[dict[str, Any]]:
    source_root = project_root / SOURCE_REVIEW_RELATIVE
    expected_paths = sorted(str(item["path"]) for item in VISIBLE_FILES)
    protocol_preparations = {
        str(item["case_id"]): item for item in source_protocol["case_preparations"]
    }
    bindings: list[dict[str, Any]] = []
    for case_id in CASE_IDS:
        case_slug = case_id.removeprefix("case:")
        protocol_preparation = protocol_preparations[case_id]
        preparation_path = source_root / str(protocol_preparation["relative_path"])
        preparation = _load(preparation_path)
        _replay(
            preparation,
            "preparation_digest",
            str(protocol_preparation["preparation_digest"]),
            f"The source preparation for {case_id}",
        )
        manifest_path = source_root / "case-preparations" / case_slug / "workspace-manifest.json"
        manifest = _load(manifest_path)
        _replay(
            manifest,
            "manifest_digest",
            str(protocol_preparation["workspace_manifest_digest"]),
            f"The source workspace manifest for {case_id}",
        )
        workspace_root = source_root / "case-preparations" / case_slug / "workspace"
        file_digests: dict[str, str] = {}
        for item in manifest["files"]:
            path_value = str(item["path"])
            path = workspace_root / path_value
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"Source workspace file is unavailable: {path}")
            digest = sha256_digest(path.read_bytes())
            if digest != item["content_digest"]:
                raise ValueError(f"Source workspace bytes drifted for {case_id} {path_value}.")
            file_digests[path_value] = digest
        if (
            sorted(file_digests) != expected_paths
            or file_digests != preparation["visible_content_digests"]
            or manifest["answer_side_content_copied"] is not False
            or manifest["project_code_executed"] is not False
        ):
            raise ValueError(f"Source workspace scope drifted for {case_id}.")
        bindings.append(
            {
                "case_id": case_id,
                "source_preparation_relative_path": preparation_path.relative_to(
                    project_root
                ).as_posix(),
                "source_preparation_digest": preparation["preparation_digest"],
                "source_workspace_relative_path": workspace_root.relative_to(
                    project_root
                ).as_posix(),
                "source_workspace_manifest_relative_path": manifest_path.relative_to(
                    project_root
                ).as_posix(),
                "source_workspace_manifest_digest": manifest["manifest_digest"],
                "visible_content_digests": dict(sorted(file_digests.items())),
                "workspace_bytes_reused_without_copy": True,
            }
        )
    return bindings


def _recovered_prompt(
    source_prompt: str,
    source_participant_id: str,
    participant_id: str,
    output_schema: dict[str, Any],
) -> str:
    marker = "\n\nReturn only one unfenced JSON object matching this exact schema:\n"
    if marker not in source_prompt:
        raise ValueError("The source Stage-1 prompt schema boundary is unavailable.")
    body = source_prompt.split(marker, 1)[0]
    if source_participant_id not in body:
        raise ValueError("The source Stage-1 prompt participant binding is unavailable.")
    body = body.replace(source_participant_id, participant_id)
    case_marker = "\n\nOPAQUE CASE "
    if case_marker not in body:
        raise ValueError("The source Stage-1 prompt case boundary is unavailable.")
    prefix, cases = body.split(case_marker, 1)
    recovered = (
        prefix.rstrip()
        + "\n\nSemantic recovery contract:\n"
        + SEMANTIC_RECOVERY_INSTRUCTION
        + case_marker
        + cases
        + marker
        + json.dumps(output_schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    )
    return recovered.strip()


def build_first_direct_three_case_stage1_semantic_recovery_protocol(
    project_root: Path,
) -> dict[str, Any]:
    output_root = project_root / REVIEW_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise ValueError(f"Stage-1 semantic-recovery protocol output already exists: {output_root}")
    source_protocol, recovery = _source_evidence(project_root)
    participants = _active_participants(project_root)
    case_bindings = _source_case_bindings(project_root, source_protocol)
    source_calls = {str(item["participant_id"]): item for item in source_protocol["calls"]}
    source_manifests = {
        str(item["case_id"]): _load(
            project_root / str(item["source_workspace_manifest_relative_path"])
        )
        for item in case_bindings
    }

    output_root.mkdir(parents=True)
    try:
        calls: list[dict[str, Any]] = []
        for participant_id in ACTIVE_REVIEWERS:
            participant = participants[participant_id]
            source_participant_id = SOURCE_REVIEWERS[participant_id]
            source_call = source_calls[source_participant_id]
            case_order = [str(value) for value in source_call["case_order"]]
            output_schema = build_stage1_batch_output_schema_v2(
                participant_id,
                case_order,
                CANONICAL_ISSUE_CLASS,
            )
            prompt = _recovered_prompt(
                str(source_call["prompt"]),
                source_participant_id,
                participant_id,
                output_schema,
            )
            reviewer_agent = _participant_agent(participant)
            packet_refs: list[dict[str, Any]] = []
            for case_id in case_order:
                packet = build_stage1_review_packet(
                    case_id,
                    source_manifests[case_id],
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
                        "source_workspace_manifest_digest": source_manifests[case_id][
                            "manifest_digest"
                        ],
                    }
                )
            calls.append(
                {
                    "call_identity_id": str(
                        uuid5(
                            NAMESPACE_URL,
                            f"sc-referee-first-envelope-stage1-semantic-recovery-v2:{participant_id}",
                        )
                    ),
                    "participant_id": participant_id,
                    "participant_configuration_digest": participant["configuration_digest"],
                    "aggregate_calibration_entry_digest": semantic_digest(
                        next(
                            item
                            for item in _load(
                                project_root
                                / REPLACEMENT_RELATIVE
                                / "AGGREGATE_CALIBRATION_LEDGER.json"
                            )["entries"]
                            if item["participant_id"] == participant_id
                        )
                    ),
                    "source_v1_participant_id": source_participant_id,
                    "source_v1_prompt_digest": source_call["prompt_digest"],
                    "participant": {
                        key: participant[key]
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
                    },
                    "reviewer_agent_base": reviewer_agent,
                    "case_order": case_order,
                    "shared_transcript_expected": True,
                    "cross_case_comparison_permitted": False,
                    "prompt": prompt,
                    "prompt_digest": sha256_digest(prompt),
                    "output_schema": output_schema,
                    "output_schema_digest": semantic_digest(output_schema),
                    "semantic_recovery_contract_digest": semantic_digest(
                        recovery["semantic_contract"]
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
            "artifact_kind": "direct_qualification_three_case_stage1_semantic_recovery_protocol",
            "protocol_version": "2.0.0",
            "protocol_id": (
                "scientific-review:complete-domain-exposure-denominator-pilot-stage1-"
                "semantic-recovery-v2"
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
                    "scripts/build_first_direct_three_case_stage1_semantic_recovery_protocol.py",
                    "reference/schemas-v0.18.0/schemas/v0.18.0/agent-review.schema.json",
                )
            ],
            "source_v1_stage1_protocol_digest": SOURCE_PROTOCOL_DIGEST,
            "source_v1_stage1_panel_ledger_digest": SOURCE_PANEL_LEDGER_DIGEST,
            "source_v1_label_ineligibility_ledger_digest": SOURCE_INELIGIBILITY_LEDGER_DIGEST,
            "semantic_recovery_amendment_digest": RECOVERY_AMENDMENT_DIGEST,
            "codex_calibration_retry_amendment_digest": CODEX_RETRY_AMENDMENT_DIGEST,
            "claude_replacement_amendment_digest": REPLACEMENT_AMENDMENT_DIGEST,
            "aggregate_recovery_calibration_ledger_digest": (AGGREGATE_CALIBRATION_LEDGER_DIGEST),
            "active_participant_enrollment_digests": [
                RECOVERY_ENROLLMENT_DIGEST,
                REPLACEMENT_ENROLLMENT_DIGEST,
            ],
            "semantic_recovery_contract": deepcopy(recovery["semantic_contract"]),
            "semantic_recovery_instruction": SEMANTIC_RECOVERY_INSTRUCTION,
            "canonical_issue_class_scope": CANONICAL_ISSUE_CLASS,
            "case_ids": CASE_IDS,
            "source_case_bindings": case_bindings,
            "workspace_reuse": {
                "source_workspace_bytes_copied": False,
                "source_workspace_bytes_regenerated": False,
                "source_workspace_manifests_reused_exactly": True,
                "source_visible_bytes_reused_exactly": True,
            },
            "review_design": {
                "reviews_per_case": 4,
                "providers_per_case": 2,
                "reviews_per_provider_per_case": 2,
                "external_call_count": 4,
                "cases_per_call": 3,
                "batching_prospectively_declared": True,
                "case_order_preserved_from_ineligible_v1_panel": True,
                "one_agent_review_per_case_per_reviewer": True,
                "one_packet_and_capture_per_agent_review": True,
                "shared_transcript_within_reviewer_batch": True,
                "eligible_verdict_requires_empty_unresolved_material_questions": True,
                "detector_output_visible": False,
                "answer_side_evidence_visible": False,
                "other_reviews_visible": False,
                "project_code_execution_permitted": False,
            },
            "calls": calls,
            "failure_policy": {
                "attempts_retained_without_replacement": True,
                "invalid_or_incomplete_batch_admits_no_reviews_from_that_call": True,
                "retry_requires_prospective_protocol_amendment_and_fresh_context": True,
                "semantic_content_may_not_be_controller_repaired": True,
                "source_v1_reviews_may_not_be_reclassified_or_reused": True,
            },
            "limitations": [
                "The scientific workflow bytes and blind workspace manifests are exact references to the immutable v1 case preparations; they are not newly authored cases.",
                "Each reviewer sees all three opaque cases in one transport batch, so cross-case correlation remains possible even though comparison is forbidden.",
                "The semantic recovery contract prevents eligible verdicts from retaining typed material questions; it does not prove the reviewer identified every material premise.",
                "Capture establishes exact bytes and packet consistency, not cryptographic provider authentication.",
                "Agent-only scientific review is not human scientific adjudication.",
            ],
            "execution_state": "frozen_not_started",
            "stage1_review_count": 0,
            "stage1_freeze_count": 0,
            "stage2_review_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_stage1_recovery_protocol_only",
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
    protocol = build_first_direct_three_case_stage1_semantic_recovery_protocol(
        arguments.project_root.resolve()
    )
    print(protocol["protocol_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
