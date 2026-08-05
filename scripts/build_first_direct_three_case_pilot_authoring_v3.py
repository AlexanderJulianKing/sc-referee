from __future__ import annotations

import argparse
import json
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from scripts.build_first_direct_reviewer_calibration_protocol import LANE_RELATIVE
from scripts.build_first_direct_three_case_pilot_authoring import (
    ACTIVE_REVIEWER_LEDGER_DIGEST,
    BRIEF_MANIFEST_DIGEST,
    LANE_FREEZE_DIGEST,
)
from scripts.build_first_direct_three_case_pilot_authoring_v2 import (
    PILOT_AUTHORING_V2_RELATIVE,
    _load,
    _replay,
    _restart_brief,
)
from scripts.record_first_direct_three_case_pilot_authors_v2 import (
    PROTOCOL_DIGEST as V2_PROTOCOL_DIGEST,
)
from scripts.record_first_direct_three_case_pilot_authors_v2 import (
    RESTART_AMENDMENT_DIGEST as V2_RESTART_AMENDMENT_DIGEST,
)

PILOT_AUTHORING_V3_RELATIVE = LANE_RELATIVE / "pilot-authoring-v3-three-case"
V2_FAILURE_LEDGER_DIGEST = "sha256:20dab1bcdd87463601a7f84425a032fb026f70ea4737dc3cb2e8c7e3e7449143"
SOURCE_COMMIT = "5361c03dd4d482d7cbe4acc80b730d475ad4e0aa"
FROZEN_AT = "2026-08-05T04:43:00Z"
AUTHOR_REPLACEMENTS = {
    "Anthropic": "actor:pilot-author-claude-03",
    "OpenAI": "actor:pilot-author-codex-03",
}


def _file_schema(path: str, *, producer: bool = False) -> dict[str, Any]:
    pattern = r"^[^\r\n\\]*$" if producer else r"^[^\r\n]*$"
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["relative_path", "content_lines"],
        "properties": {
            "relative_path": {"type": "string", "const": path},
            "content_lines": {
                "type": "array",
                "minItems": 1,
                "maxItems": 400,
                "items": {"type": "string", "pattern": pattern},
            },
        },
    }


def _output_schema(participant_id: str, case_ids: list[str]) -> dict[str, Any]:
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
            "input_file": _file_schema("inputs/data.csv"),
            "producer_file": _file_schema("workflow/analysis.py", producer=True),
            "report_file": _file_schema("results/report.md"),
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


def _fresh_participant(original: dict[str, Any]) -> dict[str, Any]:
    participant = deepcopy(original)
    provider = str(participant["provider"])
    participant_id = AUTHOR_REPLACEMENTS[provider]
    participant["participant_id"] = participant_id
    participant["execution_context_id"] = (
        f"context:{participant_id.removeprefix('actor:')}-app-v3"
        if provider == "Anthropic"
        else f"context:{participant_id.removeprefix('actor:')}-v3"
    )
    participant.pop("configuration_digest", None)
    participant["configuration_digest"] = semantic_digest(participant)
    return participant


def _v3_brief(v2_brief: dict[str, Any], new_case_id: str) -> dict[str, Any]:
    brief = deepcopy(v2_brief)
    brief["case_id"] = new_case_id
    brief["brief_version"] = "3.0.0"
    return brief


def _prompt(
    participant: dict[str, Any], visible_briefs: list[dict[str, Any]], schema: dict[str, Any]
) -> str:
    return (
        "System instructions for this isolated prospective author:\n"
        "Act as an independent scientific-workflow author. Follow only the supplied author-visible "
        "brief. Build a small auditable case tree whose input data, Python producer, and selected "
        "report agree. Preserve identifiers and planned-unit accounting. Do not search for or "
        "infer any hidden evaluation objective.\n\n"
        f"Author participant identity: {participant['participant_id']}\n"
        "This is one no-replacement attempt in a fresh authoring iteration. Use no repository "
        "context, detector output, answer key, prior case, hidden metadata, file, tool, connector, "
        "or external information.\n\n"
        "Return each file as content_lines: one JSON string per physical file line, with an empty "
        "string for a blank line. The controller joins the entries with one LF after every entry. "
        "Every decoded entry must contain no LF or CR. Every producer entry must additionally "
        "contain no U+005C reverse-solidus character.\n\n"
        "Use these exact relative paths for every case: inputs/data.csv, workflow/analysis.py, "
        "and results/report.md.\n\n"
        "The Python producer must use exactly this already-frozen finite grammar:\n"
        "1. Its first five statements are exactly these five physical lines:\n"
        "from pathlib import Path\n"
        "SOURCE_TEXT = Path('inputs/data.csv').read_text()\n"
        "SOURCE_LINES = SOURCE_TEXT.splitlines()\n"
        "SOURCE_LINE_COUNT = len(SOURCE_LINES)\n"
        "LF = SOURCE_TEXT[len(SOURCE_LINES[0])]\n"
        "2. The input is ASCII CSV, has a nonempty header and at least one data row, and is joined "
        "by the controller with LF, so that the fifth statement obtains the separator without a "
        "source escape.\n"
        "3. The producer has no docstring, other import, function, class, loop, branch, context "
        "manager, exception handler, or statement after its final writer.\n"
        "4. After the first five statements and before the final writer, use only simple "
        "module-level NAME = EXPRESSION assignments. Expressions may use literal strings or "
        "numbers, earlier names, +, f-strings, splitlines(), strip(), lstrip(), rstrip(), len(), "
        "str(), int(), float(), and indexing. Use no other call or method.\n"
        "5. Build every report line by adding LF, use LF itself for blank lines, and assemble "
        "REPORT_TEXT by concatenation. REPORT_TEXT must visibly depend on SOURCE_LINE_COUNT and "
        "must end in LF. Do not use a reverse-solidus escape anywhere in the producer.\n"
        "6. The last and only writer is exactly: "
        "Path('results/report.md').write_text(REPORT_TEXT)\n"
        "7. The materialized report lines exactly equal REPORT_TEXT, use ASCII LF text, and "
        "contain exactly one line whose stripped text starts with [selected-result].\n"
        "8. The author declaration uses one-based inclusive lines. For one_selected_result, the "
        "selected_result_projection is non-null, both candidate and unsupported span arrays are "
        "empty, result_span is the one [selected-result] report line, and producer_span is exactly "
        "the single final writer line—not a calculation, variable, or REPORT_TEXT line.\n\n"
        "Escape-free structure example; replace all scientific prose and values with the brief's "
        "truthful content while retaining the structure:\n"
        "from pathlib import Path\n"
        "SOURCE_TEXT = Path('inputs/data.csv').read_text()\n"
        "SOURCE_LINES = SOURCE_TEXT.splitlines()\n"
        "SOURCE_LINE_COUNT = len(SOURCE_LINES)\n"
        "LF = SOURCE_TEXT[len(SOURCE_LINES[0])]\n"
        "TITLE_LINE = '# Report' + LF\n"
        "INPUT_LINE = f'Input lines including header: {SOURCE_LINE_COUNT}' + LF\n"
        "RESULT_LINE = '[selected-result] Replace with the truthful selected result.' + LF\n"
        "REPORT_TEXT = TITLE_LINE + INPUT_LINE + RESULT_LINE\n"
        "Path('results/report.md').write_text(REPORT_TEXT)\n\n"
        "Author-visible briefs:\n"
        + json.dumps(visible_briefs, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n\nReturn only one unfenced JSON object matching this exact schema:\n"
        + json.dumps(schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    )


def build_first_direct_three_case_pilot_authoring_v3(
    project_root: Path,
) -> dict[str, dict[str, Any]]:
    v2_root = project_root / PILOT_AUTHORING_V2_RELATIVE
    v2_failure = _load(v2_root / "AUTHORING_INTAKE_FAILURE_LEDGER.json")
    _replay(
        v2_failure,
        "ledger_digest",
        V2_FAILURE_LEDGER_DIGEST,
        "V2 authoring intake failure ledger",
    )
    if (
        v2_failure["summary"]["response_case_count"] != 3
        or v2_failure["summary"]["admitted_case_count"] != 0
        or v2_failure["summary"]["metric_eligible_case_count"] != 0
        or v2_failure["summary"]["scientific_label_count"] != 0
        or v2_failure["summary"]["detector_outcome_count"] != 0
    ):
        raise ValueError("V2 failure is not the exact pre-review zero-admission state.")
    v2_restart = _load(v2_root / "PILOT_AUTHORING_RESTART_AMENDMENT.json")
    _replay(
        v2_restart,
        "amendment_digest",
        V2_RESTART_AMENDMENT_DIGEST,
        "V2 authoring restart amendment",
    )
    v2_protocol = _load(v2_root / "PILOT_AUTHORING_PROTOCOL.json")
    _replay(v2_protocol, "protocol_digest", V2_PROTOCOL_DIGEST, "V2 authoring protocol")

    lane = _load(project_root / LANE_RELATIVE / "LANE_FREEZE.json")
    _replay(lane, "lane_freeze_digest", LANE_FREEZE_DIGEST, "Direct lane freeze")
    briefs = _load(project_root / LANE_RELATIVE / "AUTHORING_BRIEF_MANIFEST.json")
    _replay(briefs, "manifest_digest", BRIEF_MANIFEST_DIGEST, "Authoring brief manifest")
    original_brief_by_case = {str(item["case_id"]): item for item in briefs["briefs"]}

    v2_assignment_by_case = {
        str(item["case_id"]): item for item in v2_restart["restart_assignments"]
    }
    v2_participant_by_case = {
        str(case_id): assignment["participant"]
        for assignment in v2_protocol["author_assignments"]
        for case_id in assignment["case_ids"]
    }
    new_by_old = {
        case_id: stable_id(
            "case",
            case_id,
            "first-envelope-authoring-restart-v3",
            V2_FAILURE_LEDGER_DIGEST,
        )
        for case_id in v2_assignment_by_case
    }

    restart_briefs: dict[str, dict[str, Any]] = {}
    restart_assignments: list[dict[str, Any]] = []
    for old_case_id in sorted(v2_assignment_by_case):
        prior = v2_assignment_by_case[old_case_id]
        original_case_id = str(prior["superseded_failed_case_id"])
        v2_brief = _restart_brief(
            original_brief_by_case[original_case_id]["author_visible_brief"], old_case_id
        )
        if semantic_digest(v2_brief) != prior["author_visible_brief_digest"]:
            raise ValueError("V2 scientific brief does not replay from the sealed source.")
        new_case_id = new_by_old[old_case_id]
        v3_brief = _v3_brief(v2_brief, new_case_id)
        restart_briefs[new_case_id] = v3_brief
        provider = str(v2_participant_by_case[old_case_id]["provider"])
        restart_assignments.append(
            {
                "case_id": new_case_id,
                "superseded_failed_case_id": old_case_id,
                "cell_type": prior["cell_type"],
                "author_id": AUTHOR_REPLACEMENTS[provider],
                "author_visible_brief_digest": semantic_digest(v3_brief),
                "reference_case_id": (
                    None
                    if prior["reference_case_id"] is None
                    else new_by_old[str(prior["reference_case_id"])]
                ),
            }
        )

    restart: dict[str, Any] = {
        "artifact_kind": "direct_qualification_three_case_authoring_restart_amendment",
        "amendment_version": "2.0.0",
        "source_commit": SOURCE_COMMIT,
        "lane_freeze_digest": LANE_FREEZE_DIGEST,
        "failed_v2_protocol_digest": V2_PROTOCOL_DIGEST,
        "failed_v2_authoring_intake_ledger_digest": V2_FAILURE_LEDGER_DIGEST,
        "failed_v2_input_capture_digests": [
            item["input_capture_digest"] for item in v2_failure["input_captures"]
        ],
        "restart_assignments": restart_assignments,
        "restart_reason": (
            "The complete v2 cohort failed generic transport and producer-role admission before "
            "materialization or review; restart with fresh opaque identities, exact role paths, "
            "escape-free LF construction, and final-writer declaration spans."
        ),
        "failed_iterations_retained": True,
        "failed_case_bytes_repaired_or_reused": False,
        "scientific_briefs_changed": False,
        "detector_or_verifier_changed": False,
        "evaluation_transport_constraints_changed": True,
        "scientific_label_count_at_freeze": 0,
        "detector_outcome_count_at_freeze": 0,
        "heldout_brief_access_permitted": False,
        "excluded_pilot_brief_access_permitted": False,
        "other_envelopes_authorized": False,
        "frozen_at": FROZEN_AT,
        "qualification_authority": "none_authoring_restart_amendment_only",
    }
    restart["amendment_digest"] = semantic_digest(restart)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for assignment in restart_assignments:
        grouped[str(assignment["author_id"])].append(assignment)
    author_assignments = []
    configuration_replacements = []
    for author_id, grouped_assignments in sorted(grouped.items()):
        provider = next(
            provider
            for provider, replacement in AUTHOR_REPLACEMENTS.items()
            if replacement == author_id
        )
        original = next(
            item["participant"]
            for item in v2_protocol["author_assignments"]
            if item["participant"]["provider"] == provider
        )
        participant = _fresh_participant(original)
        configuration_replacements.append(
            {
                "participant_id": author_id,
                "superseded_participant_id": original["participant_id"],
                "superseded_configuration_digest": original["configuration_digest"],
                "replacement_configuration_digest": participant["configuration_digest"],
                "replacement_reason": "Fresh isolated v3 author context after retained v2 failure.",
            }
        )
        case_ids = sorted(str(item["case_id"]) for item in grouped_assignments)
        visible = [restart_briefs[case_id] for case_id in case_ids]
        schema = _output_schema(author_id, case_ids)
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
                        f"sc-referee:first-three-case-pilot-v3:{author_id}:"
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
                    if provider == "Anthropic"
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
        "protocol_version": "3.0.0",
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
    artifacts = build_first_direct_three_case_pilot_authoring_v3(project_root)
    root = project_root / PILOT_AUTHORING_V3_RELATIVE
    if root.exists():
        raise FileExistsError(f"Refusing to replace frozen v3 authoring root: {root}")
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
