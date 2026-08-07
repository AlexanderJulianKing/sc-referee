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
    CALIBRATION_RELATIVE as V5_CALIBRATION_RELATIVE,
)
from scripts.build_first_direct_stage1_recovery_calibration import (
    CALIBRATION_SUITE_DIGEST,
    EXPECTED_CALIBRATION_VERDICTS,
)
from scripts.build_first_direct_stage1_recovery_claude_replacement_calibration import (
    REPLACEMENT_RELATIVE as V6_CALIBRATION_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_protocol import LANE_RELATIVE
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_protocol import (
    REVIEW_RELATIVE as CLEAN_REVIEW_RELATIVE,
)

REPLACEMENT_RELATIVE = (
    LANE_RELATIVE / "reviewer-calibration-v8-stage1-semantic-recovery-claude-cli-replacement"
)
CLAUDE_CLI_REPLACEMENT_RELATIVE = REPLACEMENT_RELATIVE
LANE_ENROLLMENT_DIGEST = "sha256:c29bdc3c277b840c2bf9b4369f69181190663530467926ccfdfb24407eff0016"
V5_ENROLLMENT_DIGEST = "sha256:5b1ecce6b493eadc5184dc359927f19519b0cd8ceeb4124e98220313752bb251"
V5_PROTOCOL_DIGEST = "sha256:d8738800d8211cc1a6a4ead04721b09a1eb76e819516fc3dea00eace94538d76"
V5_LEDGER_DIGEST = "sha256:4892d3ee890c19bb98110b8f301bddf225213064ac0acc368c2ae197b67aafc6"
V6_ENROLLMENT_DIGEST = "sha256:832ffc15b3897dcbb2013d35b25e25d4484d985b8d2a402bfe070e3b55351f18"
V6_PROTOCOL_DIGEST = "sha256:6f8562f5fdc8def78663bb3160c8f9c10a07b896f6cb39d487ce48ada11293a1"
V6_LEDGER_DIGEST = "sha256:8257ac400f97cee37f236bd840e14442dbecbd43f4b17945d6bf508bf041a254"
CLEAN_STAGE1_PROTOCOL_DIGEST = (
    "sha256:94529e86411cc0c81c4a75a203c5895656b99228321288654a35d0d13feeb378"
)
FROZEN_AT = "2026-08-07T17:08:00Z"
PROMPT_BOUNDARY = "Return only one JSON object"

# Each fresh CLI participant supersedes one calibrated, never-case-exposed desktop-app
# configuration and copies its exact configuration template from one distinct frozen
# Claude Code CLI reviewer configuration in the immutable lane enrollment.
SUPERSEDED_BY_REPLACEMENT = {
    "actor:stage1-recovery-claude-04": "actor:stage1-recovery-claude-01",
    "actor:stage1-recovery-claude-05": "actor:stage1-recovery-claude-03",
}
TEMPLATE_BY_REPLACEMENT = {
    "actor:stage1-recovery-claude-04": "actor:stage1-claude-01",
    "actor:stage1-recovery-claude-05": "actor:stage1-claude-02",
}
REPLACEMENT_CONTEXTS = {
    "actor:stage1-recovery-claude-04": "context:stage1-recovery-claude-04-v1",
    "actor:stage1-recovery-claude-05": "context:stage1-recovery-claude-05-v1",
}
OBSOLETE_CLEAN_STAGE1_CLAUDE_CALL_IDS = (
    "82ee366c-f4c8-5c63-8f5d-5faf9fd6d420",
    "39f01523-cd7f-54e7-9202-e2ef54acacd9",
)
SUPERSESSION_REASON = (
    "The two calibrated Claude reviewer configurations are bound to the Claude Desktop App "
    "surface, which requires an approved Computer-Use operator to submit prompts. That operator "
    "approval is unavailable, and the maintainer directed a replacement on the authenticated "
    "Claude Code CLI surface before any Stage-1 case exposure. Both superseded configurations, "
    "their passing calibrations, and the unexecuted clean Stage-1 protocol remain retained and "
    "immutable; neither superseded configuration authored, saw, or reviewed any case packet."
)
COMMAND_PROFILE = {
    "provider_cli": "claude",
    "print_mode": True,
    "safe_mode": True,
    "tool_set": "empty",
    "mcp_set": "empty_mcpServers_record_strict",
    "permission_mode": "dontAsk",
    "session_persistence": False,
    "session_id_binding": "call_identity_id",
    "structured_output": "prompt_embedded_schema_local_fail_closed_validation",
    "json_schema_argument_present": False,
}


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def _passing_entry(ledger: dict[str, Any], participant_id: str, label: str) -> dict[str, Any]:
    entry = next(
        (
            item
            for item in ledger.get("entries", [])
            if item.get("participant_id") == participant_id
        ),
        None,
    )
    if entry is None or entry.get("calibration_status") != "passed":
        raise ValueError(f"{label} does not retain a passing calibration for {participant_id}.")
    return cast(dict[str, Any], entry)


def _superseded_sources(
    project_root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    v5_root = project_root / V5_CALIBRATION_RELATIVE
    v6_root = project_root / V6_CALIBRATION_RELATIVE
    v5_enrollment = _load(v5_root / "PARTICIPANT_ENROLLMENT.json")
    _replay(
        v5_enrollment,
        "enrollment_digest",
        V5_ENROLLMENT_DIGEST,
        "The v5 recovery-calibration enrollment",
    )
    v5_protocol = _load(v5_root / "CALIBRATION_PROTOCOL.json")
    _replay(v5_protocol, "protocol_digest", V5_PROTOCOL_DIGEST, "The v5 calibration protocol")
    v5_ledger = _load(v5_root / "CALIBRATION_LEDGER.json")
    _replay(v5_ledger, "ledger_digest", V5_LEDGER_DIGEST, "The v5 calibration ledger")
    v6_enrollment = _load(v6_root / "PARTICIPANT_ENROLLMENT.json")
    _replay(
        v6_enrollment,
        "enrollment_digest",
        V6_ENROLLMENT_DIGEST,
        "The v6 replacement enrollment",
    )
    v6_protocol = _load(v6_root / "CALIBRATION_PROTOCOL.json")
    _replay(v6_protocol, "protocol_digest", V6_PROTOCOL_DIGEST, "The v6 calibration protocol")
    v6_ledger = _load(v6_root / "CALIBRATION_LEDGER.json")
    _replay(v6_ledger, "ledger_digest", V6_LEDGER_DIGEST, "The v6 calibration ledger")

    participants: dict[str, dict[str, Any]] = {}
    assignments: dict[str, dict[str, Any]] = {}
    passes: dict[str, dict[str, Any]] = {}
    for enrollment, protocol, ledger, participant_id, label in (
        (v5_enrollment, v5_protocol, v5_ledger, "actor:stage1-recovery-claude-01", "v5"),
        (v6_enrollment, v6_protocol, v6_ledger, "actor:stage1-recovery-claude-03", "v6"),
    ):
        participant = next(
            (
                item
                for item in enrollment["participants"]
                if item.get("participant_id") == participant_id
            ),
            None,
        )
        assignment = next(
            (
                item
                for item in protocol["assignments"]
                if item.get("participant_id") == participant_id
            ),
            None,
        )
        if participant is None or assignment is None:
            raise ValueError(f"The {label} record set lacks {participant_id}.")
        if (
            participant.get("provider") != "Anthropic"
            or participant.get("model_id") != "claude-opus-5"
            or participant.get("agent_surface") != "Claude Desktop App chat"
            or assignment.get("prompt_digest") != sha256_digest(str(assignment["prompt"]))
            or assignment.get("output_schema_digest")
            != semantic_digest(assignment["output_schema"])
        ):
            raise ValueError(f"The {label} superseded configuration drifted.")
        participants[participant_id] = cast(dict[str, Any], participant)
        assignments[participant_id] = cast(dict[str, Any], assignment)
        passes[participant_id] = _passing_entry(
            ledger, participant_id, f"The {label} calibration ledger"
        )
    return participants, assignments, passes


def _cli_templates(project_root: Path) -> dict[str, dict[str, Any]]:
    enrollment = _load(project_root / LANE_RELATIVE / "PARTICIPANT_ENROLLMENT.json")
    _replay(
        enrollment,
        "enrollment_digest",
        LANE_ENROLLMENT_DIGEST,
        "The frozen lane participant enrollment",
    )
    templates: dict[str, dict[str, Any]] = {}
    for template_id in TEMPLATE_BY_REPLACEMENT.values():
        template = next(
            (
                item
                for item in enrollment["participants"]
                if item.get("participant_id") == template_id
            ),
            None,
        )
        if template is None:
            raise ValueError(f"The lane enrollment lacks CLI template {template_id}.")
        if (
            template.get("provider") != "Anthropic"
            or template.get("agent_surface") != "Claude Code CLI"
            or template.get("agent_version") != "2.1.221"
            or template.get("model_id") != "claude-opus-5"
            or template.get("reasoning_configuration") != "high"
            or template.get("role") != "stage1_reviewer"
        ):
            raise ValueError(f"CLI template {template_id} drifted from its frozen shape.")
        templates[template_id] = cast(dict[str, Any], template)
    return templates


def _clean_stage1_protocol(project_root: Path) -> dict[str, Any]:
    protocol = _load(project_root / CLEAN_REVIEW_RELATIVE / "STAGE1_REVIEW_PROTOCOL.json")
    _replay(
        protocol,
        "protocol_digest",
        CLEAN_STAGE1_PROTOCOL_DIGEST,
        "The clean Stage-1 recovery protocol",
    )
    if (
        protocol.get("execution_state") != "frozen_not_started"
        or protocol.get("stage1_review_count") != 0
        or protocol.get("stage1_freeze_count") != 0
        or protocol.get("scientific_label_count") != 0
        or protocol.get("detector_outcome_count") != 0
    ):
        raise ValueError("The clean Stage-1 protocol is not in the unexecuted frozen state.")
    claude_call_ids = sorted(
        str(call["call_identity_id"])
        for call in protocol.get("calls", [])
        if call.get("interaction_profile", {}).get("surface") == "Claude Desktop App Home Chat"
    )
    if claude_call_ids != sorted(OBSOLETE_CLEAN_STAGE1_CLAUDE_CALL_IDS):
        raise ValueError("The clean Stage-1 Claude call identities drifted.")
    return protocol


def _participant(
    template: dict[str, Any], superseded: dict[str, Any], participant_id: str
) -> dict[str, Any]:
    participant = deepcopy(template)
    participant["participant_id"] = participant_id
    participant["execution_context_id"] = REPLACEMENT_CONTEXTS[participant_id]
    participant["role"] = "stage1_reviewer"
    participant["calibration_status"] = "required_before_participation"
    participant["calibration_suite_digest"] = CALIBRATION_SUITE_DIGEST
    if participant.get("system_prompt_digest") != superseded.get("system_prompt_digest"):
        raise ValueError(
            "The CLI template and superseded configuration disagree on the reviewer system prompt."
        )
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
        raise ValueError("A superseded calibration prompt lacks its participant binding.")
    body = body.replace(source_participant_id, participant_id)
    return (
        body.rstrip()
        + "\n\nReturn only one JSON object, with no prose or Markdown fence, matching this exact schema:\n"
        + json.dumps(output_schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    )


def build_first_direct_stage1_recovery_claude_cli_replacement_calibration(
    project_root: Path,
) -> dict[str, Any]:
    output_root = project_root / REPLACEMENT_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError("The Claude CLI replacement calibration is already frozen.")
    superseded_participants, superseded_assignments, superseded_passes = _superseded_sources(
        project_root
    )
    templates = _cli_templates(project_root)
    _clean_stage1_protocol(project_root)

    participants = []
    assignments = []
    replacement_rows = []
    for participant_id in sorted(SUPERSEDED_BY_REPLACEMENT):
        superseded_id = SUPERSEDED_BY_REPLACEMENT[participant_id]
        template = templates[TEMPLATE_BY_REPLACEMENT[participant_id]]
        superseded = superseded_participants[superseded_id]
        participant = _participant(template, superseded, participant_id)
        source_assignment = superseded_assignments[superseded_id]
        schema = deepcopy(source_assignment["output_schema"])
        schema["properties"]["reviewer_participant_id"]["const"] = participant_id
        prompt = _prompt(
            str(source_assignment["prompt"]),
            superseded_id,
            participant_id,
            schema,
        )
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
            "superseded_participant_id": superseded_id,
            "superseded_configuration_digest": superseded["configuration_digest"],
            "superseded_assignment_digest": semantic_digest(source_assignment),
            "template_participant_id": TEMPLATE_BY_REPLACEMENT[participant_id],
            "call_identity_id": str(
                uuid5(
                    NAMESPACE_URL,
                    "sc-referee-stage1-semantic-recovery-claude-cli-replacement-calibration-v1:"
                    + participant_id,
                )
            ),
            "prompt": prompt,
            "prompt_digest": sha256_digest(prompt),
            "output_schema": schema,
            "output_schema_digest": semantic_digest(schema),
            "command_profile": deepcopy(COMMAND_PROFILE),
        }
        participants.append(participant)
        assignments.append(assignment)
        replacement_rows.append(
            {
                "superseded_participant_id": superseded_id,
                "superseded_configuration_digest": superseded["configuration_digest"],
                "superseded_calibration_status": "passed_retained",
                "superseded_pass_response_digest": superseded_passes[superseded_id][
                    "response_digest"
                ],
                "replacement_participant_id": participant_id,
                "replacement_configuration_digest": participant["configuration_digest"],
                "replacement_execution_context_id": participant["execution_context_id"],
                "template_participant_id": TEMPLATE_BY_REPLACEMENT[participant_id],
            }
        )

    output_root.mkdir(parents=True)
    try:
        enrollment: dict[str, Any] = {
            "artifact_kind": (
                "direct_qualification_stage1_recovery_claude_cli_replacement_enrollment"
            ),
            "enrollment_version": "1.0.0",
            "source_lane_enrollment_digest": LANE_ENROLLMENT_DIGEST,
            "source_v5_enrollment_digest": V5_ENROLLMENT_DIGEST,
            "source_v6_enrollment_digest": V6_ENROLLMENT_DIGEST,
            "calibration_suite_digest": CALIBRATION_SUITE_DIGEST,
            "superseded_participant_ids": sorted(SUPERSEDED_BY_REPLACEMENT.values()),
            "participants": participants,
            "participant_count": 2,
            "provider_participation": {"Anthropic": 2},
            "fresh_participant_identities": True,
            "fresh_execution_contexts": True,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_participant_enrollment_only",
        }
        enrollment["enrollment_digest"] = semantic_digest(enrollment)
        write_normalized_json_once(output_root / "PARTICIPANT_ENROLLMENT.json", enrollment)

        protocol: dict[str, Any] = {
            "artifact_kind": (
                "direct_qualification_stage1_recovery_claude_cli_replacement_calibration_protocol"
            ),
            "protocol_version": "1.0.0",
            "protocol_id": "calibration:stage1-semantic-recovery-claude-cli-replacement-v1",
            "source_v5_calibration_protocol_digest": V5_PROTOCOL_DIGEST,
            "source_v6_calibration_protocol_digest": V6_PROTOCOL_DIGEST,
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
            "artifact_kind": (
                "direct_qualification_stage1_recovery_claude_cli_replacement_amendment"
            ),
            "amendment_version": "1.0.0",
            "supersession_reason": SUPERSESSION_REASON,
            "superseded_surface": "Claude Desktop App chat",
            "replacement_surface": "Claude Code CLI",
            "source_clean_stage1_protocol_digest": CLEAN_STAGE1_PROTOCOL_DIGEST,
            "obsolete_clean_stage1_claude_call_identity_ids": sorted(
                OBSOLETE_CLEAN_STAGE1_CLAUDE_CALL_IDS
            ),
            "clean_stage1_calls_executed_before_amendment": 0,
            "case_exposure_before_amendment": False,
            "source_v5_calibration_ledger_digest": V5_LEDGER_DIGEST,
            "source_v6_calibration_ledger_digest": V6_LEDGER_DIGEST,
            "replacement_enrollment_digest": enrollment["enrollment_digest"],
            "replacement_calibration_protocol_digest": protocol["protocol_digest"],
            "replacements": replacement_rows,
            "replacement_count": 2,
            "superseded_configurations_retained_without_repair": True,
            "superseded_pass_evidence_not_reused": True,
            "scientific_vignettes_unchanged": True,
            "expected_verdicts_unchanged": True,
            "output_schema_unchanged_except_participant_const": True,
            "prompt_unchanged_except_participant_identity": True,
            "reviewer_system_prompt_unchanged": True,
            "provider_and_model_family_unchanged": True,
            "configuration_changes_disclosed": {
                "agent_surface": ["Claude Desktop App chat", "Claude Code CLI"],
                "agent_version": ["1.25927.0", "2.1.221"],
                "reasoning_configuration": ["extra", "high"],
                "tool_policy_digest_source": "frozen_lane_cli_reviewer_template",
                "environment_digest_source": "frozen_lane_cli_reviewer_template",
            },
            "maintainer_directed": True,
            "fresh_participant_identities": True,
            "fresh_execution_contexts": True,
            "calibration_required_before_scientific_participation": True,
            "replacement_stage1_protocol_required_before_review": True,
            "frozen_at": FROZEN_AT,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "qualification_authority": "none_calibration_replacement_only",
        }
        amendment["amendment_digest"] = semantic_digest(amendment)
        write_normalized_json_once(output_root / "REPLACEMENT_AMENDMENT.json", amendment)
        return amendment
    except BaseException:
        shutil.rmtree(output_root, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    amendment = build_first_direct_stage1_recovery_claude_cli_replacement_calibration(
        arguments.project_root.resolve()
    )
    print(amendment["amendment_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
