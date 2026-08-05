from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee_evaluation.direct_qualification_lane import (
    freeze_participant_enrollment,
    validate_participant_enrollment,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_reviewer_calibration_protocol import (
    LANE_RELATIVE,
    PARTIAL_CALIBRATION_RELATIVE,
    _output_schema,
    _user_prompt,
    load_effective_execution_configuration,
)

APP_CALIBRATION_RELATIVE = LANE_RELATIVE / "reviewer-calibration-v4-app"
V3_CALIBRATION_RELATIVE = LANE_RELATIVE / "reviewer-calibration-v3"
FROZEN_AT = "2026-08-05T00:26:00Z"
SOURCE_COMMIT = "48ebd29597fac0f641cf66b3dcd068c7058c25e6"
ORIGINAL_ENROLLMENT_DIGEST = (
    "sha256:c29bdc3c277b840c2bf9b4369f69181190663530467926ccfdfb24407eff0016"
)
LANE_FREEZE_DIGEST = "sha256:c58ee57c01d5f7c46855eb9f554d0a476f664e44edbdd7e15679bd53d72fa12b"
V2_LEDGER_DIGEST = "sha256:253b3fa6283c91e66442a3c9fe42f9f100754bd9aeb4e88e53564c96288e2bf3"
V1_PROTOCOL_DIGEST = "sha256:c7b28df0840b278af5d80838842f5b42104d225eac4759a5a62df9e377b30bd0"
V1_LEDGER_DIGEST = "sha256:ea070181d537a6c939bf2328ae75d5be1c697cff38a0f3e31e074ac04651c795"
V2_PROTOCOL_DIGEST = "sha256:b2875a535a1cbf86dffb1fb696c3b05bbc28dd9b5d67a0d82cbb5ed881864aad"
V3_PROTOCOL_DIGEST = "sha256:dc359b6884308ecc02b391d499f22c784bed5e71f258c8420eab95dae8dc4cc7"
V3_LEDGER_DIGEST = "sha256:375265c9dc05186c74c58c4658c20a2877011db476bcebc0a7281658a54f2893"
V3_AGGREGATE_DIGEST = "sha256:3da48f5fead855cd4685448f2f550b71b77ec1e366737381429c3874e00b9fa5"

_PARTICIPANT_INPUT_KEYS = (
    "participant_id",
    "role",
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
    "calibration_suite_digest",
    "calibration_status",
)

APP_ENVIRONMENT = {
    "operating_system": "macOS 26.6 build 25G72",
    "architecture": "arm64",
    "application": "Claude Desktop App",
    "application_version": "1.25927.0",
    "interaction_driver": "Codex Computer Use accessibility interface",
}
APP_TOOL_POLICY = {
    "chat_mode": True,
    "incognito_mode": True,
    "saved_to_account_history": False,
    "added_to_memory": False,
    "fresh_chat_per_participant": True,
    "file_uploads_permitted": False,
    "connectors_permitted": False,
    "project_or_repository_context_permitted": False,
    "tool_calls_permitted": False,
    "external_information_permitted": False,
    "compliance_verified_from_retained_conversation": True,
}


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], digest_field: str, expected: str, label: str) -> None:
    supplied = record.pop(digest_field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[digest_field] = supplied


def _replacement_participant(original: dict[str, Any]) -> dict[str, Any]:
    participant_id = str(original["participant_id"])
    return {
        "participant_id": participant_id,
        "role": original["role"],
        "provider": "Anthropic",
        "agent_surface": "Claude Desktop App chat",
        "agent_version": "1.25927.0",
        "model_name": "Claude Opus 5",
        "model_id": "claude-opus-5",
        "reasoning_configuration": "extra",
        "execution_context_id": f"context:{participant_id.removeprefix('actor:')}-app-v4",
        "system_prompt_digest": original["system_prompt_digest"],
        "tool_policy_digest": semantic_digest(APP_TOOL_POLICY),
        "environment_digest": semantic_digest(APP_ENVIRONMENT),
        "calibration_suite_digest": original["calibration_suite_digest"],
        "calibration_status": "required_before_participation",
    }


def _app_prompt(participant: dict[str, Any], suite: dict[str, Any], system_prompt: str) -> str:
    schema = _output_schema(str(participant["participant_id"]))
    return (
        "System instructions for this isolated reviewer calibration:\n"
        + system_prompt.rstrip()
        + "\n\n"
        + _user_prompt(participant, suite).rstrip()
        + "\n\nReturn only one JSON object, with no prose or Markdown fence, matching this exact schema:\n"
        + json.dumps(schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    )


def build_first_direct_app_reviewer_calibration(
    project_root: Path,
) -> dict[str, dict[str, Any]]:
    lane = _load(project_root / LANE_RELATIVE / "LANE_FREEZE.json")
    _replay(lane, "lane_freeze_digest", LANE_FREEZE_DIGEST, "The direct lane freeze")
    original_enrollment = validate_participant_enrollment(
        _load(project_root / LANE_RELATIVE / "PARTICIPANT_ENROLLMENT.json")
    )
    if original_enrollment["enrollment_digest"] != ORIGINAL_ENROLLMENT_DIGEST:
        raise ValueError("The original participant enrollment has drifted.")

    v3_protocol = _load(project_root / V3_CALIBRATION_RELATIVE / "CALIBRATION_PROTOCOL.json")
    _replay(v3_protocol, "protocol_digest", V3_PROTOCOL_DIGEST, "Protocol v3")
    v3_ledger = _load(project_root / V3_CALIBRATION_RELATIVE / "CALIBRATION_LEDGER.json")
    _replay(v3_ledger, "ledger_digest", V3_LEDGER_DIGEST, "Protocol-v3 ledger")
    v3_aggregate = _load(
        project_root / V3_CALIBRATION_RELATIVE / "AGGREGATE_CALIBRATION_LEDGER.json"
    )
    _replay(
        v3_aggregate,
        "ledger_digest",
        V3_AGGREGATE_DIGEST,
        "Protocol-v3 aggregate ledger",
    )
    if (
        v3_ledger["protocol_digest"] != V3_PROTOCOL_DIGEST
        or v3_aggregate["protocol_digest"] != V3_PROTOCOL_DIGEST
        or v3_ledger["summary"]["passed_count"] != 0
        or v3_ledger["summary"]["failed_count"] != 3
    ):
        raise ValueError("Protocol-v3 failure evidence has drifted.")

    replacement_ids = {
        "actor:stage1-claude-01",
        "actor:stage1-claude-02",
        "actor:stage2-claude-01",
    }
    original_by_id = {
        str(item["participant_id"]): item for item in original_enrollment["participants"]
    }
    replacement_inputs = []
    for participant in original_enrollment["participants"]:
        participant_id = str(participant["participant_id"])
        if participant_id in replacement_ids:
            replacement_inputs.append(_replacement_participant(participant))
        else:
            replacement_inputs.append({key: participant[key] for key in _PARTICIPANT_INPUT_KEYS})
    replacement_enrollment = freeze_participant_enrollment(
        {
            "enrollment_id": "enrollment:complete-domain-exposure-denominator-v3-app",
            "precase_freeze_digest": original_enrollment["precase_freeze_digest"],
            "participants": replacement_inputs,
        },
        frozen_at=FROZEN_AT,
    )
    replacement_by_id = {
        str(item["participant_id"]): item for item in replacement_enrollment["participants"]
    }
    supersession: dict[str, Any] = {
        "artifact_kind": "versioned_agent_adjudication_protocol_amendment",
        "protocol_amendment_version": "1.0.0",
        "protocol_amendment_id": "adjudication-protocol:desktop-app-opus-5-v1",
        "source_commit": SOURCE_COMMIT,
        "lane_freeze_digest": LANE_FREEZE_DIGEST,
        "superseded_enrollment_digest": ORIGINAL_ENROLLMENT_DIGEST,
        "replacement_enrollment_digest": replacement_enrollment["enrollment_digest"],
        "replaced_participant_ids": sorted(replacement_ids),
        "configuration_replacements": [
            {
                "participant_id": participant_id,
                "superseded_configuration_digest": original_by_id[participant_id][
                    "configuration_digest"
                ],
                "replacement_configuration_digest": replacement_by_id[participant_id][
                    "configuration_digest"
                ],
                "replacement_reason": "The frozen Claude Code CLI configuration was unauthenticated before inference; use one isolated authenticated Claude Desktop App chat before any scientific case exposure.",
            }
            for participant_id in sorted(replacement_ids)
        ],
        "historical_calibration_chain": [
            {"protocol_digest": V1_PROTOCOL_DIGEST, "ledger_digest": V1_LEDGER_DIGEST},
            {"protocol_digest": V2_PROTOCOL_DIGEST, "ledger_digest": V2_LEDGER_DIGEST},
            {
                "protocol_digest": V3_PROTOCOL_DIGEST,
                "ledger_digest": V3_LEDGER_DIGEST,
                "aggregate_ledger_digest": V3_AGGREGATE_DIGEST,
            },
        ],
        "precase_state": {
            "author_brief_exposure_count": 0,
            "authored_case_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
        },
        "frozen_at": FROZEN_AT,
        "qualification_authority": "none_adjudication_protocol_amendment_only",
    }
    supersession["amendment_digest"] = semantic_digest(supersession)

    config = load_effective_execution_configuration(project_root)
    suite = config["reviewer_calibration_suite"]
    v2_ledger = _load(project_root / PARTIAL_CALIBRATION_RELATIVE / "CALIBRATION_LEDGER.json")
    _replay(v2_ledger, "ledger_digest", V2_LEDGER_DIGEST, "Protocol-v2 partial ledger")
    retained_passes = sorted(
        (
            item
            for item in v2_ledger["entries"]
            if item["provider"] == "OpenAI" and item["calibration_status"] == "passed"
        ),
        key=lambda item: str(item["participant_id"]),
    )
    if len(retained_passes) != 3:
        raise ValueError("The exact three Codex calibration passes are not available.")

    assignments = []
    for participant_id in sorted(replacement_ids):
        participant = replacement_by_id[participant_id]
        role = str(participant["role"])
        prompt = _app_prompt(
            participant,
            suite,
            str(config["role_configurations"][role]["system_prompt"]),
        )
        schema = _output_schema(participant_id)
        assignments.append(
            {
                **{
                    key: participant[key]
                    for key in (
                        "participant_id",
                        "role",
                        "provider",
                        "agent_surface",
                        "agent_version",
                        "model_name",
                        "model_id",
                        "reasoning_configuration",
                        "execution_context_id",
                        "configuration_digest",
                        "system_prompt_digest",
                        "tool_policy_digest",
                        "environment_digest",
                        "calibration_suite_digest",
                    )
                },
                "call_identity_id": str(
                    uuid5(NAMESPACE_URL, f"sc-referee-app-calibration-v4:{participant_id}")
                ),
                "app_prompt": prompt,
                "app_prompt_digest": sha256_digest(prompt),
                "output_schema": schema,
                "output_schema_digest": semantic_digest(schema),
                "interaction_profile": {
                    "application": "Claude Desktop App",
                    "application_version": "1.25927.0",
                    "mode": "Chat",
                    "incognito": True,
                    "model_menu_label": "Opus 5",
                    "effort_menu_label": "Extra",
                    "fresh_chat_required": True,
                    "computer_use_required": True,
                    "file_uploads": "none",
                    "tools_or_connectors": "none",
                },
            }
        )

    protocol: dict[str, Any] = {
        "artifact_kind": "direct_qualification_app_reviewer_calibration_protocol",
        "protocol_version": "4.0.0",
        "protocol_id": "reviewer-calibration:complete-domain-exposure-denominator-v4-app",
        "source_commit": SOURCE_COMMIT,
        "lane_freeze_digest": LANE_FREEZE_DIGEST,
        "original_participant_enrollment_digest": ORIGINAL_ENROLLMENT_DIGEST,
        "replacement_enrollment_digest": replacement_enrollment["enrollment_digest"],
        "adjudication_protocol_amendment_digest": supersession["amendment_digest"],
        "supersedes_protocol_digest": V3_PROTOCOL_DIGEST,
        "retained_v3_failure_ledger_digest": V3_LEDGER_DIGEST,
        "retained_v3_aggregate_ledger_digest": V3_AGGREGATE_DIGEST,
        "retained_v2_pass_ledger_digest": V2_LEDGER_DIGEST,
        "calibration_suite_digest": semantic_digest(suite),
        "expected_vignette_count": 6,
        "expected_app_reviewer_count": 3,
        "aggregate_reviewer_count": 6,
        "retained_pass_refs": [
            {
                "participant_id": item["participant_id"],
                "configuration_digest": item["configuration_digest"],
                "reported_session_id": item["reported_session_id"],
                "response_digest": item["response_digest"],
                "transcript_digest": item["transcript_digest"],
                "calibration_status": item["calibration_status"],
            }
            for item in retained_passes
        ],
        "assignments": assignments,
        "execution_policy": {
            "one_fresh_chat_per_assignment": True,
            "incognito_chat_required": True,
            "one_attempt_per_assignment": True,
            "replacement_permitted": False,
            "all_attempts_retained": True,
            "parallel_execution_required": False,
            "repository_or_project_context_permitted": False,
            "tools_or_connectors_permitted": False,
            "external_information_permitted": False,
            "response_capture": "full_visible_assistant_response_and_conversation_url",
        },
        "pass_rule": {
            "all_six_expected_verdicts_required": True,
            "invented_material_premise_count": 0,
            "valid_exact_json_required": True,
            "visible_tool_call_count": 0,
            "fresh_conversation_url_required": True,
            "exact_model_and_effort_ui_selection_required": True,
        },
        "frozen_at": FROZEN_AT,
        "execution_state": "frozen_not_started",
        "qualification_authority": "none_reviewer_calibration_only",
    }
    protocol["protocol_digest"] = semantic_digest(protocol)
    return {
        "PARTICIPANT_ENROLLMENT.json": replacement_enrollment,
        "ADJUDICATION_PROTOCOL_AMENDMENT.json": supersession,
        "CALIBRATION_PROTOCOL.json": protocol,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    output_root = project_root / APP_CALIBRATION_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"Refusing to overwrite frozen app calibration: {output_root}")
    artifacts = build_first_direct_app_reviewer_calibration(project_root)
    output_root.mkdir(parents=True, exist_ok=False)
    for name, artifact in artifacts.items():
        (output_root / name).write_text(
            json.dumps(artifact, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
