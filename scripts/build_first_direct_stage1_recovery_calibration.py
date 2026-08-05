from __future__ import annotations

import argparse
import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_three_case_stage1_protocol import (
    CASE_IDS,
    LANE_RELATIVE,
)

SOURCE_REVIEW_RELATIVE = LANE_RELATIVE / "pilot-scientific-review-v1-three-case"
CALIBRATION_RELATIVE = LANE_RELATIVE / "reviewer-calibration-v5-stage1-semantic-recovery"
SOURCE_PANEL_LEDGER_DIGEST = (
    "sha256:cde80f4a0faf9f2d96699122127177252afcaac275b35d2ba9be72b812433851"
)
SOURCE_ENROLLMENT_DIGEST = "sha256:95ef5badd874db346279de725a35679da80d00bf8d40c323041b414ce750a5bc"
CALIBRATION_SUITE_DIGEST = "sha256:15f3f1636429f624a6fbb649ce6ec9fc8d0bdfd30b6ab673ad47c9ef11cfe671"
FROZEN_AT = "2026-08-05T07:19:45Z"

SOURCE_PARTICIPANTS = {
    "actor:stage1-recovery-claude-01": "actor:stage1-claude-01",
    "actor:stage1-recovery-claude-02": "actor:stage1-claude-02",
    "actor:stage1-recovery-codex-01": "actor:stage1-codex-01",
    "actor:stage1-recovery-codex-02": "actor:stage1-codex-02",
}
RECOVERY_CONTEXTS = {
    participant_id: f"context:{participant_id.removeprefix('actor:')}-v1"
    for participant_id in SOURCE_PARTICIPANTS
}
EXPECTED_CALIBRATION_VERDICTS = {
    "calibration:complete-frame-mismatch": "demonstrated_issue",
    "calibration:conditional-subset-scope": "no_demonstrated_issue_within_scope",
    "calibration:full-frame-accounting": "no_demonstrated_issue_within_scope",
    "calibration:unrelated-quality-endpoint": "no_demonstrated_issue_within_scope",
    "calibration:conflicting-scope-records": "conditional_or_unknown",
    "calibration:no-selected-result": "insufficient_evidence",
}


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def _source_reviews(project_root: Path) -> list[dict[str, Any]]:
    root = project_root / SOURCE_REVIEW_RELATIVE / "stage1-captures"
    paths = sorted(root.glob("*/*/review.json"))
    reviews = [_load(path) for path in paths]
    if len(reviews) != 12:
        raise ValueError("The source Stage-1 panel does not contain exactly twelve reviews.")
    return reviews


def _output_schema(participant_id: str, template: dict[str, Any]) -> dict[str, Any]:
    schema = deepcopy(template)
    schema["properties"]["reviewer_participant_id"]["const"] = participant_id
    return schema


def _prompt(
    source_prompt: str,
    source_participant_id: str,
    participant_id: str,
    output_schema: dict[str, Any],
) -> str:
    body = source_prompt.split("Return only one JSON object", 1)[0]
    body = body.replace(source_participant_id, participant_id)
    return (
        body.rstrip()
        + "\n\nReturn only one JSON object, with no prose or Markdown fence, matching this exact schema:\n"
        + json.dumps(output_schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    )


def _participant(source: dict[str, Any], participant_id: str) -> dict[str, Any]:
    participant = deepcopy(source)
    participant["participant_id"] = participant_id
    participant["execution_context_id"] = RECOVERY_CONTEXTS[participant_id]
    participant["calibration_status"] = "required_before_participation"
    participant["calibration_suite_digest"] = CALIBRATION_SUITE_DIGEST
    participant.pop("configuration_digest", None)
    participant["configuration_digest"] = semantic_digest(participant)
    return participant


def build_first_direct_stage1_recovery_calibration(project_root: Path) -> dict[str, Any]:
    output_root = project_root / CALIBRATION_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise ValueError(f"Recovery calibration output already exists: {output_root}")

    source_panel = _load(project_root / SOURCE_REVIEW_RELATIVE / "STAGE1_PANEL_LEDGER.json")
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
        raise ValueError("The source Stage-1 panel is not in the expected pre-label state.")

    reviews = _source_reviews(project_root)
    blocking_reviews = []
    for review in reviews:
        questions = list(review.get("unresolved_material_questions", []))
        if questions:
            blocking_reviews.append(
                {
                    "case_id": review["case_id"],
                    "review_id": review["review_id"],
                    "review_digest": semantic_digest(review),
                    "provider": review["reviewer_agent"]["provider"],
                    "question_count": len(questions),
                    "questions_digest": semantic_digest(questions),
                }
            )
    if (
        len(blocking_reviews) != 4
        or sum(int(item["question_count"]) for item in blocking_reviews) != 5
    ):
        raise ValueError("The source panel no longer has the diagnosed label blocker.")

    source_calibration_root = project_root / (LANE_RELATIVE / "reviewer-calibration-v4-app")
    source_enrollment = _load(source_calibration_root / "PARTICIPANT_ENROLLMENT.json")
    _replay(
        source_enrollment,
        "enrollment_digest",
        SOURCE_ENROLLMENT_DIGEST,
        "The source participant enrollment",
    )
    source_by_id = {str(item["participant_id"]): item for item in source_enrollment["participants"]}
    participants = [
        _participant(source_by_id[source_id], participant_id)
        for participant_id, source_id in SOURCE_PARTICIPANTS.items()
    ]

    claude_protocol = _load(source_calibration_root / "CALIBRATION_PROTOCOL.json")
    codex_protocol = _load(
        project_root / LANE_RELATIVE / "reviewer-calibration-v2" / "CALIBRATION_PROTOCOL.json"
    )
    templates = {
        str(item["participant_id"]): item
        for item in [*codex_protocol["assignments"], *claude_protocol["assignments"]]
    }

    output_root.mkdir(parents=True)
    try:
        ineligibility: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_label_ineligibility_ledger",
            "ledger_version": "1.0.0",
            "source_stage1_panel_ledger_digest": SOURCE_PANEL_LEDGER_DIGEST,
            "case_ids": CASE_IDS,
            "review_count": 12,
            "blocking_review_count": len(blocking_reviews),
            "unresolved_material_question_count": sum(
                int(item["question_count"]) for item in blocking_reviews
            ),
            "blocking_reviews": sorted(blocking_reviews, key=lambda item: str(item["review_id"])),
            "label_eligibility": "blocked",
            "reason_code": "unresolved_material_review_questions",
            "stage2_can_reverse_stage1_blocker": False,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "recorded_at": FROZEN_AT,
            "qualification_authority": "none_failure_evidence_only",
        }
        ineligibility["ledger_digest"] = semantic_digest(ineligibility)
        write_normalized_json_once(
            output_root / "STAGE1_LABEL_INELIGIBILITY_LEDGER.json", ineligibility
        )

        enrollment: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_recovery_participant_enrollment",
            "enrollment_version": "1.0.0",
            "source_participant_enrollment_digest": SOURCE_ENROLLMENT_DIGEST,
            "calibration_suite_digest": CALIBRATION_SUITE_DIGEST,
            "participants": participants,
            "participant_count": 4,
            "provider_participation": {"Anthropic": 2, "OpenAI": 2},
            "fresh_execution_contexts": True,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_participant_enrollment_only",
        }
        enrollment["enrollment_digest"] = semantic_digest(enrollment)
        write_normalized_json_once(output_root / "PARTICIPANT_ENROLLMENT.json", enrollment)

        assignments = []
        for participant in participants:
            participant_id = str(participant["participant_id"])
            source_id = SOURCE_PARTICIPANTS[participant_id]
            template = templates[source_id]
            schema = _output_schema(participant_id, template["output_schema"])
            source_prompt_field = (
                "app_prompt" if participant["provider"] == "Anthropic" else "user_prompt"
            )
            prompt = _prompt(
                str(template[source_prompt_field]),
                source_id,
                participant_id,
                schema,
            )
            assignments.append(
                {
                    "participant_id": participant_id,
                    "role": "stage1_reviewer",
                    "provider": participant["provider"],
                    "agent_surface": participant["agent_surface"],
                    "model_name": participant["model_name"],
                    "model_id": participant["model_id"],
                    "agent_version": participant["agent_version"],
                    "reasoning_configuration": participant["reasoning_configuration"],
                    "execution_context_id": participant["execution_context_id"],
                    "configuration_digest": participant["configuration_digest"],
                    "system_prompt_digest": participant["system_prompt_digest"],
                    "tool_policy_digest": participant["tool_policy_digest"],
                    "environment_digest": participant["environment_digest"],
                    "calibration_suite_digest": CALIBRATION_SUITE_DIGEST,
                    "call_identity_id": str(
                        uuid5(
                            NAMESPACE_URL,
                            f"sc-referee-stage1-semantic-recovery-calibration-v1:{participant_id}",
                        )
                    ),
                    "prompt": prompt,
                    "prompt_digest": sha256_digest(prompt),
                    "output_schema": schema,
                    "output_schema_digest": semantic_digest(schema),
                    "interaction_profile": deepcopy(template["interaction_profile"])
                    if participant["provider"] == "Anthropic"
                    else deepcopy(template["command_profile"]),
                }
            )

        calibration: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_recovery_calibration_protocol",
            "protocol_version": "1.0.0",
            "protocol_id": "calibration:stage1-semantic-consistency-recovery-v1",
            "participant_enrollment_digest": enrollment["enrollment_digest"],
            "calibration_suite_digest": CALIBRATION_SUITE_DIGEST,
            "expected_verdicts": EXPECTED_CALIBRATION_VERDICTS,
            "assignments": assignments,
            "execution_state": "frozen_not_started",
            "attempt_count": 0,
            "pass_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_calibration_only",
        }
        calibration["protocol_digest"] = semantic_digest(calibration)
        write_normalized_json_once(output_root / "CALIBRATION_PROTOCOL.json", calibration)

        amendment: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_semantic_consistency_recovery_amendment",
            "amendment_version": "1.0.0",
            "source_stage1_panel_ledger_digest": SOURCE_PANEL_LEDGER_DIGEST,
            "source_label_ineligibility_ledger_digest": ineligibility["ledger_digest"],
            "recovery_participant_enrollment_digest": enrollment["enrollment_digest"],
            "recovery_calibration_protocol_digest": calibration["protocol_digest"],
            "decision": "rerun_complete_stage1_panel_after_fresh_configuration_calibration",
            "semantic_contract": {
                "unresolved_material_questions_meaning": "unanswered_questions_capable_of_reversing_the_in_scope_verdict_only",
                "eligible_verdict_requires_empty_array": True,
                "material_reversing_question_requires_noneligible_verdict": True,
                "out_of_scope_nonreversing_caveats_are_not_material_questions": True,
            },
            "unchanged": [
                "three_case_workflow_bytes",
                "blind_workspace_manifests",
                "canonical_issue_class_scope",
                "four_review_two_provider_panel_shape",
                "detector_and_selected_result_verifier_bytes",
                "scientific_label_eligibility_rule",
            ],
            "fresh": [
                "four_participant_identities",
                "four_execution_contexts",
                "four_calibration_calls",
                "four_stage1_calls_after_calibration",
            ],
            "prohibitions": [
                "mutating_or_reclassifying_any_source_review",
                "reusing_any_source_execution_context",
                "exposing_answer_side_or_detector_evidence",
                "controller_repair_of_semantic_content",
                "counting_the_source_panel_toward_an_eligible_label",
            ],
            "frozen_at": FROZEN_AT,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "qualification_authority": "none_prospective_recovery_only",
        }
        amendment["amendment_digest"] = semantic_digest(amendment)
        write_normalized_json_once(output_root / "RECOVERY_AMENDMENT.json", amendment)
        return amendment
    except BaseException:
        shutil.rmtree(output_root, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    amendment = build_first_direct_stage1_recovery_calibration(arguments.project_root.resolve())
    print(amendment["amendment_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
