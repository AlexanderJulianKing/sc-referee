from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_app_reviewer_calibration import APP_CALIBRATION_RELATIVE
from scripts.build_first_direct_reviewer_calibration_protocol import (
    LANE_RELATIVE,
    load_effective_execution_configuration,
)

PILOT_AUTHORING_RELATIVE = LANE_RELATIVE / "pilot-authoring-v1-three-case"
LANE_FREEZE_DIGEST = "sha256:c58ee57c01d5f7c46855eb9f554d0a476f664e44edbdd7e15679bd53d72fa12b"
BRIEF_MANIFEST_DIGEST = "sha256:7133cb96256ab17a7eff58efa4d2b9a97dc9c2addac575a3ec03b830c869ec8e"
ACTIVE_ENROLLMENT_DIGEST = "sha256:95ef5badd874db346279de725a35679da80d00bf8d40c323041b414ce750a5bc"
ACTIVE_REVIEWER_LEDGER_DIGEST = (
    "sha256:3c64169c830ff1e963f81fe0e774e367021e3ad4f77892641002e4ff7f13e030"
)
SOURCE_COMMIT = "0325db3543a30edc54169e5c49926b7875c1cfbd"
FROZEN_AT = "2026-08-05T02:20:00Z"
ELIGIBLE_CELL_TYPES = ("error_bearing", "corrected_twin", "valid_alternative")

APP_AUTHOR_ENVIRONMENT = {
    "operating_system": "macOS 26.6 build 25G72",
    "architecture": "arm64",
    "application": "Claude Desktop App",
    "application_version": "1.25927.0",
    "interaction_driver": "Codex Computer Use accessibility interface",
}
APP_AUTHOR_TOOL_POLICY = {
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
    "response_materialization": "controller_writes_exact_retained_json_file_contents",
}


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], digest_field: str, expected: str, label: str) -> None:
    supplied = record.pop(digest_field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[digest_field] = supplied


def _author_output_schema(participant_id: str, case_ids: list[str]) -> dict[str, Any]:
    file_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["relative_path", "content"],
        "properties": {
            "relative_path": {"type": "string", "minLength": 1},
            "content": {"type": "string", "minLength": 1},
        },
    }
    line_span = {
        "type": "object",
        "additionalProperties": False,
        "required": ["start_line", "end_line"],
        "properties": {
            "start_line": {"type": "integer", "minimum": 1},
            "end_line": {"type": "integer", "minimum": 1},
        },
    }
    selected_projection = {
        "type": "object",
        "additionalProperties": False,
        "required": ["result_span", "producer_span"],
        "properties": {
            "result_span": line_span,
            "producer_span": line_span,
        },
    }
    declaration = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "declaration_state",
            "selected_result_projection",
            "candidate_result_spans",
            "unsupported_producer_spans",
        ],
        "properties": {
            "declaration_state": {
                "type": "string",
                "enum": [
                    "one_selected_result",
                    "multiple_candidate_results",
                    "unsupported_producer_surface",
                ],
            },
            "selected_result_projection": {"anyOf": [{"type": "null"}, selected_projection]},
            "candidate_result_spans": {"type": "array", "items": line_span},
            "unsupported_producer_spans": {"type": "array", "items": line_span},
        },
    }
    case_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "case_id",
            "input_file",
            "producer_file",
            "report_file",
            "author_declaration",
        ],
        "properties": {
            "case_id": {"type": "string", "enum": case_ids},
            "input_file": file_schema,
            "producer_file": file_schema,
            "report_file": file_schema,
            "author_declaration": declaration,
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["author_participant_id", "authored_cases"],
        "properties": {
            "author_participant_id": {"type": "string", "const": participant_id},
            "authored_cases": {
                "type": "array",
                "minItems": len(case_ids),
                "maxItems": len(case_ids),
                "items": case_schema,
            },
        },
    }


def _app_author(original: dict[str, Any]) -> dict[str, Any]:
    participant_id = str(original["participant_id"])
    participant = {
        "participant_id": participant_id,
        "role": "author",
        "provider": "Anthropic",
        "agent_surface": "Claude Desktop App chat",
        "agent_version": "1.25927.0",
        "model_name": "Claude Opus 5",
        "model_id": "claude-opus-5",
        "reasoning_configuration": "extra",
        "execution_context_id": f"context:{participant_id.removeprefix('actor:')}-app-v1",
        "system_prompt_digest": original["system_prompt_digest"],
        "tool_policy_digest": semantic_digest(APP_AUTHOR_TOOL_POLICY),
        "environment_digest": semantic_digest(APP_AUTHOR_ENVIRONMENT),
        "calibration_suite_digest": original["calibration_suite_digest"],
        "calibration_status": "not_applicable",
    }
    participant["configuration_digest"] = semantic_digest(participant)
    return participant


def _author_prompt(
    participant: dict[str, Any], visible_briefs: list[dict[str, Any]], schema: dict[str, Any]
) -> str:
    return (
        "System instructions for this isolated prospective author:\n"
        "Act as an independent scientific-workflow author. Follow only the supplied "
        "author-visible brief. Build a small, auditable case tree whose input data, analysis "
        "source, and selected report agree with the requested scientific task and exact artifact "
        "list. Preserve identifiers and missing-unit accounting. State truthfully whether there "
        "is one selected result, several candidate results, or a producer surface that cannot be "
        "resolved statically. Do not search for or infer any hidden evaluation objective.\n\n"
        f"Author participant identity: {participant['participant_id']}\n"
        "This is one no-replacement authoring attempt. Use no external information, repository "
        "context, detector output, answer key, prior case, or hidden metadata.\n"
        "For each supplied brief, return exactly three file contents: one input table under "
        "inputs/, one Python producer under workflow/, and one selected report under results/. "
        "Use normalized relative paths, LF line endings, no README or extra file, and end every "
        "file with a newline. The report must contain exactly one [selected-result] line. The "
        "author declaration is metadata outside the three-file case tree. Line spans are "
        "one-based and inclusive.\n\n"
        "Author-visible briefs:\n"
        + json.dumps(visible_briefs, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n\nReturn only one unfenced JSON object matching this exact schema:\n"
        + json.dumps(schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    )


def build_first_direct_three_case_pilot_authoring(
    project_root: Path,
) -> dict[str, dict[str, Any]]:
    root = project_root / LANE_RELATIVE
    lane = _load(root / "LANE_FREEZE.json")
    _replay(lane, "lane_freeze_digest", LANE_FREEZE_DIGEST, "Direct lane freeze")
    briefs = _load(root / "AUTHORING_BRIEF_MANIFEST.json")
    _replay(briefs, "manifest_digest", BRIEF_MANIFEST_DIGEST, "Authoring brief manifest")
    aggregate = _load(project_root / APP_CALIBRATION_RELATIVE / "AGGREGATE_CALIBRATION_LEDGER.json")
    _replay(
        aggregate,
        "ledger_digest",
        ACTIVE_REVIEWER_LEDGER_DIGEST,
        "Active reviewer calibration ledger",
    )
    if not aggregate["summary"]["all_active_reviewer_configurations_passed"]:
        raise ValueError("The exact active reviewer panel has not passed calibration.")

    blocks = {
        str(item["block_id"]): str(item["evidence_role"])
        for item in lane["prospective_protocol"]["blocks"]
    }
    pilot_assignments = [
        item
        for item in lane["prospective_protocol"]["assignments"]
        if blocks[str(item["block_id"])] == "threshold_pilot"
    ]
    eligible = [item for item in pilot_assignments if str(item["cell_type"]) in ELIGIBLE_CELL_TYPES]
    excluded = [
        item for item in pilot_assignments if str(item["cell_type"]) not in ELIGIBLE_CELL_TYPES
    ]
    if len(eligible) != 3 or len(excluded) != 4:
        raise ValueError("The frozen first pilot does not contain the expected 3+4 split.")
    if len({str(item["author_id"]) for item in eligible}) != 2:
        raise ValueError("The pilot causal triad does not map to two frozen author identities.")

    scope: dict[str, Any] = {
        "artifact_kind": "direct_qualification_three_case_pilot_scope_amendment",
        "amendment_version": "1.0.0",
        "source_commit": SOURCE_COMMIT,
        "lane_freeze_digest": LANE_FREEZE_DIGEST,
        "authoring_brief_manifest_digest": BRIEF_MANIFEST_DIGEST,
        "active_reviewer_calibration_ledger_digest": ACTIVE_REVIEWER_LEDGER_DIGEST,
        "eligible_cell_types": list(ELIGIBLE_CELL_TYPES),
        "eligible_assignments": [
            {
                "case_id": item["case_id"],
                "author_id": item["author_id"],
                "authoring_brief_digest": item["authoring_brief_digest"],
                "cell_type": item["cell_type"],
            }
            for item in sorted(eligible, key=lambda value: str(value["case_id"]))
        ],
        "excluded_unopened_assignments": [
            {
                "case_id": item["case_id"],
                "author_id": item["author_id"],
                "authoring_brief_digest": item["authoring_brief_digest"],
                "cell_type": item["cell_type"],
                "state": "unopened_metric_ineligible",
            }
            for item in sorted(excluded, key=lambda value: str(value["case_id"]))
        ],
        "heldout_seal_digest": semantic_digest(lane["heldout_seal"]),
        "preexposure_state": {
            "author_brief_exposure_count": 0,
            "authored_case_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
        },
        "reason": "Maintainer-directed minimal causal triad for the currently active first envelope.",
        "other_envelopes_authorized": False,
        "frozen_at": FROZEN_AT,
        "qualification_authority": "none_pilot_scope_amendment_only",
    }
    scope["amendment_digest"] = semantic_digest(scope)

    active_enrollment = _load(
        project_root / APP_CALIBRATION_RELATIVE / "PARTICIPANT_ENROLLMENT.json"
    )
    _replay(
        active_enrollment,
        "enrollment_digest",
        ACTIVE_ENROLLMENT_DIGEST,
        "Active participant enrollment",
    )
    participant_by_id = {
        str(item["participant_id"]): item for item in active_enrollment["participants"]
    }
    brief_by_case = {str(item["case_id"]): item for item in briefs["briefs"]}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for assignment in eligible:
        grouped[str(assignment["author_id"])].append(assignment)

    config = load_effective_execution_configuration(project_root)
    author_system_prompt = str(config["role_configurations"]["author"]["system_prompt"])
    author_system_digest = sha256_digest(author_system_prompt)
    author_assignments = []
    author_replacements = []
    for author_id, assignments in sorted(grouped.items()):
        original = participant_by_id[author_id]
        participant = _app_author(original) if original["provider"] == "Anthropic" else original
        if participant["system_prompt_digest"] != author_system_digest:
            raise ValueError("The author system-prompt binding has drifted.")
        if participant is not original:
            author_replacements.append(
                {
                    "participant_id": author_id,
                    "superseded_configuration_digest": original["configuration_digest"],
                    "replacement_configuration_digest": participant["configuration_digest"],
                    "replacement_reason": "Claude Code CLI reported loggedIn false before any author brief exposure; use one authenticated isolated Claude Desktop App chat.",
                }
            )
        case_ids = sorted(str(item["case_id"]) for item in assignments)
        visible = [brief_by_case[case_id]["author_visible_brief"] for case_id in case_ids]
        schema = _author_output_schema(author_id, case_ids)
        prompt = _author_prompt(participant, visible, schema)
        prompt_digest = sha256_digest(prompt)
        author_assignments.append(
            {
                "participant": participant,
                "case_ids": case_ids,
                "author_visible_brief_digests": [
                    brief_by_case[case_id]["brief_digest"] for case_id in case_ids
                ],
                "call_identity_id": str(
                    uuid5(
                        NAMESPACE_URL,
                        f"sc-referee:first-three-case-pilot:{author_id}:{scope['amendment_digest']}",
                    )
                ),
                "prompt": prompt,
                "prompt_digest": prompt_digest,
                "output_schema": schema,
                "output_schema_digest": semantic_digest(schema),
                "interaction_profile": (
                    {
                        "surface": "Claude Desktop App Home Chat",
                        "model_label": "Opus 5",
                        "effort_label": "Extra",
                        "incognito": True,
                        "fresh_chat": True,
                        "tools_or_connectors": "none",
                    }
                    if participant["provider"] == "Anthropic"
                    else {
                        "surface": "Codex CLI exec",
                        "model_id": "gpt-5.6-sol",
                        "reasoning_effort": "high",
                        "ephemeral": True,
                        "fresh_empty_workspace": True,
                        "sandbox": "workspace-write",
                        "external_network": False,
                    }
                ),
            }
        )

    protocol: dict[str, Any] = {
        "artifact_kind": "direct_qualification_three_case_pilot_authoring_protocol",
        "protocol_version": "1.0.0",
        "source_commit": SOURCE_COMMIT,
        "lane_freeze_digest": LANE_FREEZE_DIGEST,
        "pilot_scope_amendment_digest": scope["amendment_digest"],
        "active_reviewer_calibration_ledger_digest": ACTIVE_REVIEWER_LEDGER_DIGEST,
        "author_configuration_replacements": author_replacements,
        "author_assignments": author_assignments,
        "execution_policy": {
            "exact_author_context_count": 2,
            "exact_case_count": 3,
            "one_attempt_per_author_context": True,
            "repair_or_retry_permitted": False,
            "replacement_permitted": False,
            "all_attempts_retained": True,
            "excluded_pilot_brief_access_permitted": False,
            "heldout_brief_access_permitted": False,
            "controller_metadata_access_permitted": False,
        },
        "execution_state": "frozen_not_started",
        "frozen_at": FROZEN_AT,
        "qualification_authority": "none_authoring_protocol_only",
    }
    protocol["protocol_digest"] = semantic_digest(protocol)
    return {
        "PILOT_SCOPE_AMENDMENT.json": scope,
        "PILOT_AUTHORING_PROTOCOL.json": protocol,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    artifacts = build_first_direct_three_case_pilot_authoring(project_root)
    target = project_root / PILOT_AUTHORING_RELATIVE
    target.mkdir(parents=True, exist_ok=True)
    for name, artifact in artifacts.items():
        path = target / name
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite frozen pilot authoring artifact: {path}")
        path.write_text(
            json.dumps(artifact, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                name: artifact.get("protocol_digest") or artifact.get("amendment_digest")
                for name, artifact in artifacts.items()
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
