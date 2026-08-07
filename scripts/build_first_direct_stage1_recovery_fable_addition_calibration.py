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
from scripts.build_first_direct_stage1_recovery_calibration import (
    CALIBRATION_SUITE_DIGEST,
    EXPECTED_CALIBRATION_VERDICTS,
)
from scripts.build_first_direct_stage1_recovery_claude_cli_replacement_calibration import (
    REPLACEMENT_RELATIVE as V8_CALIBRATION_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_protocol import LANE_RELATIVE

ADDITION_RELATIVE = (
    LANE_RELATIVE / "reviewer-calibration-v9-stage1-semantic-recovery-fable-addition"
)
FABLE_ADDITION_RELATIVE = ADDITION_RELATIVE
V8_ENROLLMENT_DIGEST = "sha256:a749696b6c72280bbd9f49e3e4372f86055551756d6d82cfb7a6cff158e4ce7a"
V8_PROTOCOL_DIGEST = "sha256:5f14cfc3b876281567cfcd6baa855ae3d83896b72ddf6af761a99b124f501400"
V8_LEDGER_DIGEST = "sha256:98d97c269781773700dad45ab460f09f0766b98bb3b5e2472d698eee9e0ecee9"
FROZEN_AT = "2026-08-07T18:22:00Z"
PROMPT_BOUNDARY = "Return only one JSON object"
ADR_REFERENCE = "ADR-0066-CROSS-MODEL-SINGLE-PROVIDER-REVIEW-PANEL.md"

# Each fresh Fable participant copies one calibrated v8 Claude CLI configuration
# template exactly, changing only the model identity, participant identity, and
# execution context. Nothing is superseded by this enrollment: the two calibrated
# Codex configurations remain enrolled and calibrated for future use.
TEMPLATE_BY_ADDITION = {
    "actor:stage1-recovery-fable-01": "actor:stage1-recovery-claude-04",
    "actor:stage1-recovery-fable-02": "actor:stage1-recovery-claude-05",
}
ADDITION_CONTEXTS = {
    "actor:stage1-recovery-fable-01": "context:stage1-recovery-fable-01-v1",
    "actor:stage1-recovery-fable-02": "context:stage1-recovery-fable-02-v1",
}
FABLE_MODEL_ID = "claude-fable-5"
FABLE_MODEL_NAME = "Claude Fable 5"
FABLE_CLI_MODEL_ALIAS = "fable"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def _v8_sources(
    project_root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    root = project_root / V8_CALIBRATION_RELATIVE
    enrollment = _load(root / "PARTICIPANT_ENROLLMENT.json")
    _replay(enrollment, "enrollment_digest", V8_ENROLLMENT_DIGEST, "The v8 enrollment")
    protocol = _load(root / "CALIBRATION_PROTOCOL.json")
    _replay(protocol, "protocol_digest", V8_PROTOCOL_DIGEST, "The v8 calibration protocol")
    ledger = _load(root / "CALIBRATION_LEDGER.json")
    _replay(ledger, "ledger_digest", V8_LEDGER_DIGEST, "The v8 calibration ledger")
    if ledger["summary"]["all_reviewer_configurations_passed"] is not True:
        raise ValueError("The v8 template configurations are not all calibrated.")
    participants = {str(item["participant_id"]): item for item in enrollment["participants"]}
    assignments = {str(item["participant_id"]): item for item in protocol["assignments"]}
    for template_id in TEMPLATE_BY_ADDITION.values():
        if template_id not in participants or template_id not in assignments:
            raise ValueError(f"The v8 template {template_id} is unavailable.")
    return participants, assignments


def _participant(template: dict[str, Any], participant_id: str) -> dict[str, Any]:
    participant = deepcopy(template)
    participant["participant_id"] = participant_id
    participant["execution_context_id"] = ADDITION_CONTEXTS[participant_id]
    participant["model_id"] = FABLE_MODEL_ID
    participant["model_name"] = FABLE_MODEL_NAME
    participant["calibration_status"] = "required_before_participation"
    participant["calibration_suite_digest"] = CALIBRATION_SUITE_DIGEST
    participant.pop("configuration_digest", None)
    participant["configuration_digest"] = semantic_digest(participant)
    return participant


def _prompt(
    source_prompt: str,
    source_participant_id: str,
    participant_id: str,
    output_schema: dict[str, Any],
) -> str:
    body = source_prompt.split(PROMPT_BOUNDARY, 1)[0]
    if source_participant_id not in body:
        raise ValueError("A v8 calibration prompt lacks its participant binding.")
    body = body.replace(source_participant_id, participant_id)
    return (
        body.rstrip()
        + "\n\nReturn only one JSON object, with no prose or Markdown fence, matching this exact schema:\n"
        + json.dumps(output_schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    )


def build_first_direct_stage1_recovery_fable_addition_calibration(
    project_root: Path,
) -> dict[str, Any]:
    output_root = project_root / ADDITION_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError("The Fable addition calibration is already frozen.")
    template_participants, template_assignments = _v8_sources(project_root)

    participants = []
    assignments = []
    addition_rows = []
    for participant_id in sorted(TEMPLATE_BY_ADDITION):
        template_id = TEMPLATE_BY_ADDITION[participant_id]
        participant = _participant(template_participants[template_id], participant_id)
        source_assignment = template_assignments[template_id]
        schema = deepcopy(source_assignment["output_schema"])
        schema["properties"]["reviewer_participant_id"]["const"] = participant_id
        prompt = _prompt(
            str(source_assignment["prompt"]),
            template_id,
            participant_id,
            schema,
        )
        command_profile = deepcopy(source_assignment["command_profile"])
        command_profile["model_alias_argument"] = FABLE_CLI_MODEL_ALIAS
        command_profile["model_usage_post_verification_required"] = True
        assignment = {
            **{
                key: participant[key]
                for key in (
                    "participant_id",
                    "role",
                    "provider",
                    "agent_surface",
                    "model_name",
                    "model_id",
                    "agent_version",
                    "reasoning_configuration",
                    "execution_context_id",
                    "configuration_digest",
                    "system_prompt_digest",
                    "tool_policy_digest",
                    "environment_digest",
                    "calibration_suite_digest",
                )
            },
            "template_participant_id": template_id,
            "template_configuration_digest": template_participants[template_id][
                "configuration_digest"
            ],
            "template_assignment_digest": semantic_digest(source_assignment),
            "call_identity_id": str(
                uuid5(
                    NAMESPACE_URL,
                    "sc-referee-stage1-semantic-recovery-fable-addition-calibration-v1:"
                    + participant_id,
                )
            ),
            "prompt": prompt,
            "prompt_digest": sha256_digest(prompt),
            "output_schema": schema,
            "output_schema_digest": semantic_digest(schema),
            "command_profile": command_profile,
        }
        participants.append(participant)
        assignments.append(assignment)
        addition_rows.append(
            {
                "addition_participant_id": participant_id,
                "addition_configuration_digest": participant["configuration_digest"],
                "addition_execution_context_id": participant["execution_context_id"],
                "template_participant_id": template_id,
                "template_configuration_digest": template_participants[template_id][
                    "configuration_digest"
                ],
            }
        )

    output_root.mkdir(parents=True)
    try:
        enrollment: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_recovery_fable_addition_enrollment",
            "enrollment_version": "1.0.0",
            "source_v8_enrollment_digest": V8_ENROLLMENT_DIGEST,
            "calibration_suite_digest": CALIBRATION_SUITE_DIGEST,
            "participants": participants,
            "participant_count": 2,
            "provider_participation": {"Anthropic": 2},
            "model_family_participation": {"Claude Fable 5": 2},
            "superseded_participant_ids": [],
            "fresh_participant_identities": True,
            "fresh_execution_contexts": True,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_participant_enrollment_only",
        }
        enrollment["enrollment_digest"] = semantic_digest(enrollment)
        write_normalized_json_once(output_root / "PARTICIPANT_ENROLLMENT.json", enrollment)

        protocol: dict[str, Any] = {
            "artifact_kind": (
                "direct_qualification_stage1_recovery_fable_addition_calibration_protocol"
            ),
            "protocol_version": "1.0.0",
            "protocol_id": "calibration:stage1-semantic-recovery-fable-addition-v1",
            "source_v8_calibration_protocol_digest": V8_PROTOCOL_DIGEST,
            "participant_enrollment_digest": enrollment["enrollment_digest"],
            "calibration_suite_digest": CALIBRATION_SUITE_DIGEST,
            "expected_verdicts": EXPECTED_CALIBRATION_VERDICTS,
            "assignments": assignments,
            "source_vignette_count": 6,
            "scientific_vignettes_unchanged": True,
            "expected_verdicts_unchanged": True,
            "output_schema_unchanged_except_participant_const": True,
            "prompt_unchanged_except_participant_identity": True,
            "execution_state": "frozen_not_started",
            "attempt_count": 0,
            "pass_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_calibration_only",
        }
        protocol["protocol_digest"] = semantic_digest(protocol)
        write_normalized_json_once(output_root / "CALIBRATION_PROTOCOL.json", protocol)

        amendment: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_recovery_fable_addition_amendment",
            "amendment_version": "1.0.0",
            "adr_reference": ADR_REFERENCE,
            "maintainer_directed": True,
            "maintainer_direction_summary": (
                "The maintainer directed completion of the active pilot review panel without "
                "the rate-limited OpenAI provider before a fixed deadline, using Claude Fable 5 "
                "as a second distinct Anthropic model family alongside Claude Opus 5. This "
                "enrollment only adds and calibrates the two fresh Fable configurations; panel "
                "composition changes require the referenced ADR to be accepted and a separate "
                "prospective protocol amendment."
            ),
            "codex_configurations_superseded": False,
            "codex_configurations_remain_enrolled_and_calibrated": True,
            "addition_rows": addition_rows,
            "addition_count": 2,
            "model_family_delta_only": True,
            "scientific_vignettes_unchanged": True,
            "expected_verdicts_unchanged": True,
            "output_schema_unchanged_except_participant_const": True,
            "prompt_unchanged_except_participant_identity": True,
            "reviewer_system_prompt_unchanged": True,
            "fresh_participant_identities": True,
            "fresh_execution_contexts": True,
            "calibration_required_before_scientific_participation": True,
            "frozen_at": FROZEN_AT,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "qualification_authority": "none_calibration_addition_only",
        }
        amendment["amendment_digest"] = semantic_digest(amendment)
        write_normalized_json_once(output_root / "ADDITION_AMENDMENT.json", amendment)
        return amendment
    except BaseException:
        shutil.rmtree(output_root, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    amendment = build_first_direct_stage1_recovery_fable_addition_calibration(
        arguments.project_root.resolve()
    )
    print(amendment["amendment_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
