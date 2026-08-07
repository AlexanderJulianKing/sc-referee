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
from scripts.build_first_direct_stage1_recovery_fable_addition_calibration import (
    ADDITION_RELATIVE as V9_CALIBRATION_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_protocol import LANE_RELATIVE

V120_REVIEWER_RELATIVE = LANE_RELATIVE / "reviewer-calibration-v12-v120-lean"
V8_ENROLLMENT_DIGEST = "sha256:a749696b6c72280bbd9f49e3e4372f86055551756d6d82cfb7a6cff158e4ce7a"
V8_PROTOCOL_DIGEST = "sha256:5f14cfc3b876281567cfcd6baa855ae3d83896b72ddf6af761a99b124f501400"
V9_ENROLLMENT_DIGEST = "sha256:3db930440af064ba2b774ab3d58d4c63cfb0edcf43fe8a6592d38379096bdb28"
V9_PROTOCOL_DIGEST = "sha256:ac0ca6426804afcf3a1c10a1685ec12ea47b63ddfeea2d29cddebced10a48d0a"
FROZEN_AT = "2026-08-07T18:57:00Z"
PROMPT_BOUNDARY = "Return only one JSON object"
ADR_REFERENCE = "ADR-0067-LEAN-SINGLE-REVIEW-QUALIFICATION-PROTOCOL.md"

# One fresh Stage-2 reviewer per model family, per ADR-0066. Each copies one
# calibrated Stage-1 CLI configuration template exactly, changing only the
# participant identity, execution context, and role. Identities are disjoint
# from every author and Stage-1 reviewer.
TEMPLATE_BY_ADDITION = {
    "actor:v120-reviewer-fable-01": ("v9", "actor:stage1-recovery-fable-01"),
    "actor:v120-reviewer-opus-01": ("v8", "actor:stage1-recovery-claude-04"),
}
ADDITION_CONTEXTS = {
    "actor:v120-reviewer-fable-01": "context:v120-reviewer-fable-01-v1",
    "actor:v120-reviewer-opus-01": "context:v120-reviewer-opus-01-v1",
}
MODEL_ALIAS_BY_MODEL_ID = {
    "claude-fable-5": "fable",
    "claude-opus-5": "claude-opus-5",
}


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def _sources(
    project_root: Path,
) -> dict[str, tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]]:
    sources: dict[str, tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]] = {}
    for key, relative, enrollment_digest, protocol_digest in (
        ("v8", V8_CALIBRATION_RELATIVE, V8_ENROLLMENT_DIGEST, V8_PROTOCOL_DIGEST),
        ("v9", V9_CALIBRATION_RELATIVE, V9_ENROLLMENT_DIGEST, V9_PROTOCOL_DIGEST),
    ):
        root = project_root / relative
        enrollment = _load(root / "PARTICIPANT_ENROLLMENT.json")
        _replay(enrollment, "enrollment_digest", enrollment_digest, f"The {key} enrollment")
        protocol = _load(root / "CALIBRATION_PROTOCOL.json")
        _replay(protocol, "protocol_digest", protocol_digest, f"The {key} calibration protocol")
        participants = {str(item["participant_id"]): item for item in enrollment["participants"]}
        assignments = {str(item["participant_id"]): item for item in protocol["assignments"]}
        sources[key] = (participants, assignments)
    return sources


def _participant(template: dict[str, Any], participant_id: str) -> dict[str, Any]:
    participant = deepcopy(template)
    participant["participant_id"] = participant_id
    participant["execution_context_id"] = ADDITION_CONTEXTS[participant_id]
    participant["role"] = "stage1_reviewer"
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
        raise ValueError("A template calibration prompt lacks its participant binding.")
    body = body.replace(source_participant_id, participant_id)
    return (
        body.rstrip()
        + "\n\nReturn only one JSON object, with no prose or Markdown fence, matching this exact schema:\n"
        + json.dumps(output_schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    )


def build_first_direct_v120_lean_reviewer_calibration(project_root: Path) -> dict[str, Any]:
    output_root = project_root / V120_REVIEWER_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError("The Stage-2 cross-model calibration is already frozen.")
    sources = _sources(project_root)

    participants = []
    assignments = []
    addition_rows = []
    for participant_id in sorted(TEMPLATE_BY_ADDITION):
        source_key, template_id = TEMPLATE_BY_ADDITION[participant_id]
        template_participants, template_assignments = sources[source_key]
        template = template_participants[template_id]
        source_assignment = template_assignments[template_id]
        participant = _participant(template, participant_id)
        schema = deepcopy(source_assignment["output_schema"])
        schema["properties"]["reviewer_participant_id"]["const"] = participant_id
        prompt = _prompt(
            str(source_assignment["prompt"]),
            template_id,
            participant_id,
            schema,
        )
        command_profile = deepcopy(source_assignment["command_profile"])
        command_profile["model_alias_argument"] = MODEL_ALIAS_BY_MODEL_ID[
            str(participant["model_id"])
        ]
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
            "template_configuration_digest": template["configuration_digest"],
            "template_assignment_digest": semantic_digest(source_assignment),
            "call_identity_id": str(
                uuid5(
                    NAMESPACE_URL,
                    "sc-referee-v120-lean-reviewer-calibration-v1:" + participant_id,
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
                "template_configuration_digest": template["configuration_digest"],
            }
        )

    output_root.mkdir(parents=True)
    try:
        enrollment: dict[str, Any] = {
            "artifact_kind": "direct_qualification_v120_lean_reviewer_enrollment",
            "enrollment_version": "1.0.0",
            "source_v8_enrollment_digest": V8_ENROLLMENT_DIGEST,
            "source_v9_enrollment_digest": V9_ENROLLMENT_DIGEST,
            "calibration_suite_digest": CALIBRATION_SUITE_DIGEST,
            "participants": participants,
            "participant_count": 2,
            "provider_participation": {"Anthropic": 2},
            "model_family_participation": {"Claude Fable 5": 1, "Claude Opus 5": 1},
            "superseded_participant_ids": [],
            "identities_disjoint_from_authors_and_stage1_reviewers": True,
            "fresh_participant_identities": True,
            "fresh_execution_contexts": True,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_participant_enrollment_only",
        }
        enrollment["enrollment_digest"] = semantic_digest(enrollment)
        write_normalized_json_once(output_root / "PARTICIPANT_ENROLLMENT.json", enrollment)

        protocol: dict[str, Any] = {
            "artifact_kind": "direct_qualification_v120_lean_reviewer_calibration_protocol",
            "protocol_version": "1.0.0",
            "protocol_id": "calibration:v120-lean-reviewer-v1",
            "adr_reference": ADR_REFERENCE,
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
            "artifact_kind": "direct_qualification_v120_lean_reviewer_addition_amendment",
            "amendment_version": "1.0.0",
            "adr_reference": ADR_REFERENCE,
            "maintainer_directed": True,
            "addition_rows": addition_rows,
            "addition_count": 2,
            "role": "stage1_reviewer",
            "identities_disjoint_from_authors_and_stage1_reviewers": True,
            "scientific_vignettes_unchanged": True,
            "expected_verdicts_unchanged": True,
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
    amendment = build_first_direct_v120_lean_reviewer_calibration(arguments.project_root.resolve())
    print(amendment["amendment_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
