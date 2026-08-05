from __future__ import annotations

import argparse
import json
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from scripts.build_first_direct_app_reviewer_calibration import APP_CALIBRATION_RELATIVE
from scripts.build_first_direct_reviewer_calibration_protocol import LANE_RELATIVE
from scripts.build_first_direct_three_case_pilot_authoring import (
    ACTIVE_ENROLLMENT_DIGEST,
    ACTIVE_REVIEWER_LEDGER_DIGEST,
    APP_AUTHOR_ENVIRONMENT,
    APP_AUTHOR_TOOL_POLICY,
    BRIEF_MANIFEST_DIGEST,
    LANE_FREEZE_DIGEST,
    PILOT_AUTHORING_RELATIVE,
)

PILOT_AUTHORING_V2_RELATIVE = LANE_RELATIVE / "pilot-authoring-v2-three-case"
FAILED_INTAKE_LEDGER_DIGEST = (
    "sha256:ee9ee169fe6b6970ea2a85565750f6e99a34273b4d0f3a0f9ab02bb6d34cffeb"
)
FAILED_AUTHORING_LEDGER_DIGEST = (
    "sha256:b1a0bcdaf9aa9a7fc2970bd94c510ac9b8ac5475e0e90d5ce7d4f39a540a58f6"
)
SOURCE_COMMIT = "d508a939adfb02f3d5c6e3ee59a369df93c19df6"
FROZEN_AT = "2026-08-05T02:24:00Z"
AUTHOR_REPLACEMENTS = {
    "Anthropic": "actor:pilot-author-claude-02",
    "OpenAI": "actor:pilot-author-codex-02",
}


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], digest_field: str, expected: str, label: str) -> None:
    supplied = record.pop(digest_field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[digest_field] = supplied


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
        "execution_context_id": f"context:{participant_id.removeprefix('actor:')}-app-v2",
        "system_prompt_digest": original["system_prompt_digest"],
        "tool_policy_digest": semantic_digest(APP_AUTHOR_TOOL_POLICY),
        "environment_digest": semantic_digest(APP_AUTHOR_ENVIRONMENT),
        "calibration_suite_digest": original["calibration_suite_digest"],
        "calibration_status": "not_applicable",
    }
    participant["configuration_digest"] = semantic_digest(participant)
    return participant


def _line_output_schema(participant_id: str, case_ids: list[str]) -> dict[str, Any]:
    file_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["relative_path", "content_lines"],
        "properties": {
            "relative_path": {"type": "string", "minLength": 1},
            "content_lines": {
                "type": "array",
                "minItems": 1,
                "maxItems": 400,
                "items": {"type": "string"},
            },
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
    projection = {
        "type": "object",
        "additionalProperties": False,
        "required": ["result_span", "producer_span"],
        "properties": {"result_span": line_span, "producer_span": line_span},
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
            "selected_result_projection": {"anyOf": [{"type": "null"}, projection]},
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


def _restart_brief(original: dict[str, Any], new_case_id: str) -> dict[str, Any]:
    brief = deepcopy(original)
    brief["case_id"] = new_case_id
    brief["brief_version"] = "2.0.0"
    brief["required_artifacts"] = [
        "One ASCII CSV or TSV input containing the complete planned-unit accounting.",
        "One Python producer in the exact frozen straight-line static grammar described by the author prompt.",
        "One ASCII-LF Markdown or text report whose lines exactly equal the producer output and contain exactly one [selected-result] line.",
        "A truthful author-only selected-result declaration stored outside the three-file case tree.",
    ]
    return brief


def _prompt(
    participant: dict[str, Any], visible_briefs: list[dict[str, Any]], schema: dict[str, Any]
) -> str:
    return (
        "System instructions for this isolated prospective author:\n"
        "Act as an independent scientific-workflow author. Follow only the supplied "
        "author-visible brief. Build a small auditable case tree whose input data, Python "
        "producer, and selected report agree. Preserve identifiers and planned-unit accounting. "
        "Do not search for or infer any hidden evaluation objective.\n\n"
        f"Author participant identity: {participant['participant_id']}\n"
        "This is one no-replacement attempt in a fresh authoring iteration. Use no repository "
        "context, detector output, answer key, prior case, hidden metadata, file, tool, connector, "
        "or external information.\n\n"
        "Return each file as content_lines: one JSON string per physical file line, with an empty "
        "string for a blank line. No content_lines entry may contain a newline or carriage return. "
        "The controller will join the entries with one LF after every entry.\n\n"
        "The Python producer must use exactly this already-frozen finite grammar:\n"
        "1. Its first statement is exactly: from pathlib import Path\n"
        "2. It has no docstring, other import, function, class, loop, branch, context manager, "
        "exception handler, or statement after its final writer.\n"
        "3. Before the final writer it uses only simple module-level NAME = EXPRESSION "
        "assignments.\n"
        "4. It reads the one input with a literal zero-argument call such as "
        "Path('inputs/stations.csv').read_text(). Do not pass encoding or any other argument.\n"
        "5. It may use literal strings/numbers, earlier names, +, f-strings, splitlines(), "
        "strip(), lstrip(), rstrip(), len(), str(), int(), float(), and indexing. Do not use "
        "any other call or method.\n"
        "6. The report text must depend visibly on the input read. A simple supported method is "
        "SOURCE_LINES = SOURCE_TEXT.splitlines(), SOURCE_LINE_COUNT = len(SOURCE_LINES), and an "
        "f-string report line that states the input line count including its header.\n"
        "7. Its last and only writer is exactly one positional argument with a literal path: "
        "Path('results/report.md').write_text(REPORT_TEXT). Do not pass encoding, newline, or any "
        "keyword argument.\n"
        "8. The materialized report lines must exactly equal REPORT_TEXT, use ASCII LF text, end "
        "with LF, and contain exactly one line whose stripped text starts with [selected-result].\n"
        "9. The author declaration uses one-based inclusive lines. For one_selected_result, "
        "selected_result_projection is non-null and both candidate and unsupported span arrays "
        "are empty.\n\n"
        "Author-visible briefs:\n"
        + json.dumps(visible_briefs, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n\nReturn only one unfenced JSON object matching this exact schema:\n"
        + json.dumps(schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    )


def build_first_direct_three_case_pilot_authoring_v2(
    project_root: Path,
) -> dict[str, dict[str, Any]]:
    failed_root = project_root / PILOT_AUTHORING_RELATIVE
    failed_intake = _load(failed_root / "SELECTED_RESULT_INTAKE_LEDGER.json")
    _replay(
        failed_intake,
        "ledger_digest",
        FAILED_INTAKE_LEDGER_DIGEST,
        "Failed selected-result intake ledger",
    )
    if (
        failed_intake["summary"]["case_count"] != 3
        or failed_intake["summary"]["metric_eligible_case_count"] != 0
        or failed_intake["summary"]["scientific_label_count"] != 0
        or failed_intake["summary"]["detector_outcome_count"] != 0
    ):
        raise ValueError("First authoring intake is not the exact pre-review failure state.")

    lane = _load(project_root / LANE_RELATIVE / "LANE_FREEZE.json")
    _replay(lane, "lane_freeze_digest", LANE_FREEZE_DIGEST, "Direct lane freeze")
    briefs = _load(project_root / LANE_RELATIVE / "AUTHORING_BRIEF_MANIFEST.json")
    _replay(briefs, "manifest_digest", BRIEF_MANIFEST_DIGEST, "Authoring brief manifest")
    brief_by_case = {str(item["case_id"]): item for item in briefs["briefs"]}
    failed_cases = {str(item["case_id"]): item for item in failed_intake["entries"]}
    assignments = [
        item
        for item in lane["prospective_protocol"]["assignments"]
        if str(item["case_id"]) in failed_cases
    ]
    if len(assignments) != 3:
        raise ValueError("Failed intake does not map to the exact frozen causal triad.")

    new_by_old = {
        str(item["case_id"]): stable_id(
            "case",
            str(item["case_id"]),
            "first-envelope-authoring-restart-v2",
            FAILED_INTAKE_LEDGER_DIGEST,
        )
        for item in assignments
    }
    restart_assignments = []
    restart_briefs: dict[str, dict[str, Any]] = {}
    for item in sorted(assignments, key=lambda value: str(value["case_id"])):
        old_case_id = str(item["case_id"])
        new_case_id = new_by_old[old_case_id]
        original_author = next(
            participant
            for participant in lane["prospective_protocol"]["participants"]
            if participant["participant_id"] == item["author_id"]
        )
        provider = str(original_author["provider"])
        brief = _restart_brief(brief_by_case[old_case_id]["author_visible_brief"], new_case_id)
        restart_briefs[new_case_id] = brief
        restart_assignments.append(
            {
                "case_id": new_case_id,
                "superseded_failed_case_id": old_case_id,
                "cell_type": item["cell_type"],
                "author_id": AUTHOR_REPLACEMENTS[provider],
                "author_visible_brief_digest": semantic_digest(brief),
                "reference_case_id": (
                    None
                    if item["reference_case_id"] is None
                    else new_by_old[str(item["reference_case_id"])]
                ),
            }
        )

    restart: dict[str, Any] = {
        "artifact_kind": "direct_qualification_three_case_authoring_restart_amendment",
        "amendment_version": "1.0.0",
        "source_commit": SOURCE_COMMIT,
        "lane_freeze_digest": LANE_FREEZE_DIGEST,
        "failed_authoring_ledger_digest": FAILED_AUTHORING_LEDGER_DIGEST,
        "failed_selected_result_intake_ledger_digest": FAILED_INTAKE_LEDGER_DIGEST,
        "restart_assignments": restart_assignments,
        "restart_reason": (
            "All first-iteration cases failed the frozen selected-result grammar before review; "
            "restart with new opaque identities and grammar-only author instructions."
        ),
        "failed_iteration_retained": True,
        "failed_case_bytes_repaired_or_reused": False,
        "scientific_briefs_changed": False,
        "producer_grammar_instructions_changed": True,
        "scientific_label_count_at_freeze": 0,
        "detector_outcome_count_at_freeze": 0,
        "heldout_brief_access_permitted": False,
        "excluded_pilot_brief_access_permitted": False,
        "other_envelopes_authorized": False,
        "frozen_at": FROZEN_AT,
        "qualification_authority": "none_authoring_restart_amendment_only",
    }
    restart["amendment_digest"] = semantic_digest(restart)

    enrollment = _load(project_root / APP_CALIBRATION_RELATIVE / "PARTICIPANT_ENROLLMENT.json")
    _replay(
        enrollment,
        "enrollment_digest",
        ACTIVE_ENROLLMENT_DIGEST,
        "Active participant enrollment",
    )
    participant_by_id = {str(item["participant_id"]): item for item in enrollment["participants"]}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for assignment in restart_assignments:
        grouped[str(assignment["author_id"])].append(assignment)
    author_assignments = []
    configuration_replacements = []
    for author_id, grouped_assignments in sorted(grouped.items()):
        original = participant_by_id[author_id]
        participant = _app_author(original) if original["provider"] == "Anthropic" else original
        if participant is not original:
            configuration_replacements.append(
                {
                    "participant_id": author_id,
                    "superseded_configuration_digest": original["configuration_digest"],
                    "replacement_configuration_digest": participant["configuration_digest"],
                    "replacement_reason": (
                        "Use the authenticated isolated Claude Desktop App author surface."
                    ),
                }
            )
        case_ids = sorted(str(item["case_id"]) for item in grouped_assignments)
        visible = [restart_briefs[case_id] for case_id in case_ids]
        schema = _line_output_schema(author_id, case_ids)
        prompt = _prompt(participant, visible, schema)
        author_assignments.append(
            {
                "participant": participant,
                "case_ids": case_ids,
                "author_visible_brief_digests": [
                    semantic_digest(restart_briefs[case_id]) for case_id in case_ids
                ],
                "call_identity_id": str(
                    uuid5(
                        NAMESPACE_URL,
                        f"sc-referee:first-three-case-pilot-v2:{author_id}:"
                        f"{restart['amendment_digest']}",
                    )
                ),
                "prompt": prompt,
                "prompt_digest": sha256_digest(prompt),
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
        "protocol_version": "2.0.0",
        "source_commit": SOURCE_COMMIT,
        "lane_freeze_digest": LANE_FREEZE_DIGEST,
        "authoring_restart_amendment_digest": restart["amendment_digest"],
        "active_reviewer_calibration_ledger_digest": ACTIVE_REVIEWER_LEDGER_DIGEST,
        "author_configuration_replacements": configuration_replacements,
        "author_assignments": author_assignments,
        "execution_policy": {
            "exact_author_context_count": 2,
            "exact_case_count": 3,
            "one_attempt_per_author_context": True,
            "repair_retry_or_replacement_permitted": False,
            "all_attempts_retained": True,
            "failed_iteration_access_permitted": False,
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
        "PILOT_AUTHORING_RESTART_AMENDMENT.json": restart,
        "PILOT_AUTHORING_PROTOCOL.json": protocol,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    artifacts = build_first_direct_three_case_pilot_authoring_v2(project_root)
    root = project_root / PILOT_AUTHORING_V2_RELATIVE
    if root.exists():
        raise FileExistsError(f"Refusing to replace frozen v2 authoring root: {root}")
    root.mkdir(parents=True)
    for name, value in artifacts.items():
        (root / name).write_text(
            json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                name: value.get("amendment_digest") or value.get("protocol_digest")
                for name, value in artifacts.items()
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
