from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from sc_referee.core.ids import semantic_digest, sha256_digest

LANE_RELATIVE = Path(
    "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2"
)
CALIBRATION_RELATIVE = LANE_RELATIVE / "reviewer-calibration"
FROZEN_AT = "2026-08-05T00:00:00Z"
SOURCE_COMMIT = "83a0a4807b16fe0a7441b0bbfb604e65b438c083"
ALLOWED_VERDICTS = (
    "demonstrated_issue",
    "no_demonstrated_issue_within_scope",
    "conditional_or_unknown",
    "insufficient_evidence",
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_effective_execution_configuration(project_root: Path) -> dict[str, Any]:
    base_path = (
        project_root
        / "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane/"
        "EXECUTION_CONFIGURATION.json"
    )
    amendment_path = project_root / LANE_RELATIVE / "EXECUTION_CONFIGURATION_AMENDMENT.json"
    config = _load(base_path)
    amendment = _load(amendment_path)
    if amendment["superseded_configuration_content_digest"] != sha256_digest(
        base_path.read_bytes()
    ):
        raise ValueError("The base execution configuration bytes have drifted.")
    config["role_configurations"]["author"]["system_prompt"] = amendment[
        "replacement_author_system_prompt"
    ]
    return config


def _output_schema(participant_id: str) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "reviewer_participant_id": {"const": participant_id},
            "calibration_results": {
                "type": "array",
                "minItems": 6,
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "calibration_case_id": {"type": "string", "minLength": 1},
                        "verdict": {"enum": list(ALLOWED_VERDICTS)},
                        "invented_material_premise": {"const": False},
                        "evidence_basis": {"const": "stated_evidence_only"},
                        "rationale": {"type": "string", "minLength": 1},
                    },
                    "required": [
                        "calibration_case_id",
                        "verdict",
                        "invented_material_premise",
                        "evidence_basis",
                        "rationale",
                    ],
                },
            },
        },
        "required": ["reviewer_participant_id", "calibration_results"],
    }


def _user_prompt(participant: dict[str, Any], suite: dict[str, Any]) -> str:
    lines = [
        "This is a reviewer calibration, not a scientific study case.",
        f"Reviewer participant identity: {participant['participant_id']}",
        "Use only the evidence stated in each vignette. Do not use tools, external sources, hidden answers, automated audit output, or unstated assumptions.",
        "Return exactly one structured result for every vignette. Use demonstrated_issue only when the stated evidence directly entails a narrow issue; otherwise preserve absence, uncertainty, or insufficiency.",
        "Allowed verdicts: " + ", ".join(ALLOWED_VERDICTS) + ".",
        "Set invented_material_premise to false and evidence_basis to stated_evidence_only for every result; if you cannot do that, the calibration does not pass.",
        "",
    ]
    for index, vignette in enumerate(suite["vignettes"], start=1):
        lines.extend(
            [
                f"Vignette {index}: {vignette['calibration_case_id']}",
                str(vignette["evidence"]),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_first_direct_reviewer_calibration_protocol(
    project_root: Path,
) -> dict[str, Any]:
    lane = _load(project_root / LANE_RELATIVE / "LANE_FREEZE.json")
    enrollment = _load(project_root / LANE_RELATIVE / "PARTICIPANT_ENROLLMENT.json")
    config = load_effective_execution_configuration(project_root)
    suite = config["reviewer_calibration_suite"]
    reviewers = [
        item
        for item in enrollment["participants"]
        if item["role"] in {"stage1_reviewer", "stage2_reviewer"}
    ]
    if len(reviewers) != 6:
        raise ValueError("The frozen enrollment does not contain the exact six-reviewer panel.")
    assignments = []
    for participant in reviewers:
        participant_id = str(participant["participant_id"])
        prompt = _user_prompt(participant, suite)
        schema = _output_schema(participant_id)
        provider = str(participant["provider"])
        assignments.append(
            {
                "participant_id": participant_id,
                "role": participant["role"],
                "provider": provider,
                "agent_surface": participant["agent_surface"],
                "agent_version": participant["agent_version"],
                "model_name": participant["model_name"],
                "model_id": participant["model_id"],
                "reasoning_configuration": participant["reasoning_configuration"],
                "execution_context_id": participant["execution_context_id"],
                "configuration_digest": participant["configuration_digest"],
                "system_prompt_digest": participant["system_prompt_digest"],
                "tool_policy_digest": participant["tool_policy_digest"],
                "environment_digest": participant["environment_digest"],
                "calibration_suite_digest": participant["calibration_suite_digest"],
                "requested_session_id": str(
                    uuid5(NAMESPACE_URL, f"sc-referee-calibration-v1:{participant_id}")
                ),
                "user_prompt": prompt,
                "user_prompt_digest": sha256_digest(prompt),
                "output_schema": schema,
                "output_schema_digest": semantic_digest(schema),
                "command_profile": (
                    {
                        "provider_cli": "claude",
                        "print_mode": True,
                        "safe_mode": True,
                        "tool_set": "empty",
                        "mcp_set": "empty_strict",
                        "permission_mode": "dontAsk",
                        "session_persistence": False,
                        "structured_output": "json_schema",
                    }
                    if provider == "Anthropic"
                    else {
                        "provider_cli": "codex",
                        "exec_mode": "ephemeral",
                        "user_config": "ignored",
                        "project_rules": "ignored",
                        "sandbox": "read-only",
                        "approval_policy": "never",
                        "web_search": False,
                        "developer_instruction_override": True,
                        "structured_output": "json_schema",
                    }
                ),
            }
        )
    assignments.sort(key=lambda item: str(item["participant_id"]))
    record: dict[str, Any] = {
        "artifact_kind": "direct_qualification_reviewer_calibration_protocol",
        "protocol_version": "1.0.0",
        "protocol_id": "reviewer-calibration:complete-domain-exposure-denominator-v1",
        "source_commit": SOURCE_COMMIT,
        "lane_freeze_digest": lane["lane_freeze_digest"],
        "participant_enrollment_digest": enrollment["enrollment_digest"],
        "calibration_suite_digest": semantic_digest(suite),
        "expected_vignette_count": 6,
        "expected_reviewer_count": 6,
        "assignments": assignments,
        "execution_policy": {
            "parallel_execution_permitted": True,
            "one_call_per_assignment": True,
            "replacement_permitted": False,
            "all_attempts_retained": True,
            "fresh_empty_working_directory_per_call": True,
            "tool_access_permitted": False,
            "external_information_access_permitted": False,
        },
        "pass_rule": {
            "all_six_expected_verdicts_required": True,
            "invented_material_premise_count": 0,
            "provider_cli_exit_code": 0,
            "structured_output_schema_valid": True,
        },
        "frozen_at": FROZEN_AT,
        "execution_state": "frozen_not_started",
        "qualification_authority": "none_calibration_protocol_only",
    }
    record["protocol_digest"] = semantic_digest(record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    output = (
        args.output.resolve()
        if args.output
        else project_root / CALIBRATION_RELATIVE / "CALIBRATION_PROTOCOL.json"
    )
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Refusing to overwrite frozen calibration protocol: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            build_first_direct_reviewer_calibration_protocol(project_root),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
