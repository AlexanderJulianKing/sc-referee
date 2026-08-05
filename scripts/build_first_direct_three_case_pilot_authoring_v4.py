from __future__ import annotations

import argparse
import json
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from sc_referee_evaluation.authoring_render_grammar import (
    RENDER_ONLY_PROFILE_ID,
    REQUIRED_FINAL_WRITER,
    REQUIRED_PREFIX,
)

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from scripts.build_first_direct_reviewer_calibration_protocol import LANE_RELATIVE
from scripts.build_first_direct_three_case_pilot_authoring import (
    ACTIVE_REVIEWER_LEDGER_DIGEST,
    BRIEF_MANIFEST_DIGEST,
    LANE_FREEZE_DIGEST,
)
from scripts.build_first_direct_three_case_pilot_authoring_v2 import _load, _replay
from scripts.build_first_direct_three_case_pilot_authoring_v3 import (
    PILOT_AUTHORING_V3_RELATIVE,
    _output_schema,
)
from scripts.record_first_direct_three_case_pilot_authors_v3 import (
    PROTOCOL_DIGEST as V3_PROTOCOL_DIGEST,
)
from scripts.record_first_direct_three_case_pilot_authors_v3 import (
    RESTART_AMENDMENT_DIGEST as V3_RESTART_AMENDMENT_DIGEST,
)

PILOT_AUTHORING_V4_RELATIVE = LANE_RELATIVE / "pilot-authoring-v4-three-case"
V3_FAILURE_LEDGER_DIGEST = "sha256:622610d8632696edb70a9b112f20877601fcd45d44b73b753a77e1b75863c136"
SOURCE_COMMIT = "938d85804035a4654ee8397b01c9e210bbbda2d7"
FROZEN_AT = "2026-08-05T05:30:30Z"
AUTHOR_REPLACEMENTS = {
    "Anthropic": "actor:pilot-author-claude-04",
    "OpenAI": "actor:pilot-author-codex-04",
}


def _visible_briefs(prompt: str) -> list[dict[str, Any]]:
    marker = "Author-visible briefs:\n"
    end_marker = "\n\nReturn only one unfenced JSON object"
    start = prompt.index(marker) + len(marker)
    end = prompt.index(end_marker, start)
    value = json.loads(prompt[start:end])
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("V3 author prompt does not contain a visible-brief list.")
    return value


def _fresh_participant(original: dict[str, Any]) -> dict[str, Any]:
    participant = deepcopy(original)
    provider = str(participant["provider"])
    participant_id = AUTHOR_REPLACEMENTS[provider]
    participant["participant_id"] = participant_id
    participant["execution_context_id"] = (
        f"context:{participant_id.removeprefix('actor:')}-app-v4"
        if provider == "Anthropic"
        else f"context:{participant_id.removeprefix('actor:')}-v4"
    )
    participant.pop("configuration_digest", None)
    participant["configuration_digest"] = semantic_digest(participant)
    return participant


def _v4_brief(v3_brief: dict[str, Any], new_case_id: str) -> dict[str, Any]:
    brief = deepcopy(v3_brief)
    brief["case_id"] = new_case_id
    brief["brief_version"] = "4.0.0"
    return brief


def _prompt(
    participant: dict[str, Any], visible_briefs: list[dict[str, Any]], schema: dict[str, Any]
) -> str:
    prefix = "\n".join(REQUIRED_PREFIX)
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
        "string for a blank line. The controller joins entries with one LF after every entry. Every "
        "decoded entry must contain no LF or CR. Every producer entry must also contain no U+005C "
        "reverse-solidus character. Use these exact paths for every case: inputs/data.csv, "
        "workflow/analysis.py, and results/report.md.\n\n"
        "The Python producer must use exactly this frozen render-only grammar:\n"
        "1. Its first five statements are exactly these five physical lines:\n"
        f"{prefix}\n"
        "2. The ASCII CSV has a nonempty header and at least one data row. After line 5, do not "
        "read, parse, split, strip, convert, index, slice, call, or access an attribute on the CSV "
        "or any other value. Do not use a negative number or unary operator.\n"
        "3. Put scientific facts explicitly supplied by the brief into literal scalar assignments. "
        "After line 5 and before the final writer, use only one new NAME = EXPRESSION assignment "
        "per physical line. Assign each name once.\n"
        "4. An EXPRESSION may contain only ASCII string, integer, or decimal literals; earlier "
        "render names; +; or an f-string. Every f-string replacement field must be one plain "
        "earlier name with no conversion or format specification. SOURCE_LINE_COUNT and LF are the "
        "only prefix names available to these expressions.\n"
        "5. Build report lines with LF, use LF itself for blank lines, and assign REPORT_TEXT exactly "
        "once as the last render assignment. REPORT_TEXT must transitively depend on "
        "SOURCE_LINE_COUNT and LF and must end in LF.\n"
        f"6. The last and only writer is exactly: {REQUIRED_FINAL_WRITER}\n"
        "7. The materialized report lines must exactly equal REPORT_TEXT and contain exactly one "
        "line whose stripped text starts with [selected-result].\n"
        "8. The declaration uses one-based inclusive lines. For one_selected_result, its projection "
        "is non-null, candidate and unsupported arrays are empty, result_span is the one marked "
        "report line, and producer_span is exactly the single final writer line.\n\n"
        "Generic structure example; replace its prose and value with the brief's truthful content:\n"
        f"{prefix}\n"
        "VALUE = 3\n"
        "TITLE_LINE = '# Report' + LF\n"
        "INPUT_LINE = f'Input lines including header: {SOURCE_LINE_COUNT}' + LF\n"
        "RESULT_LINE = f'[selected-result] Reported value: {VALUE}.' + LF\n"
        "REPORT_TEXT = TITLE_LINE + INPUT_LINE + RESULT_LINE\n"
        f"{REQUIRED_FINAL_WRITER}\n\n"
        "Author-visible briefs:\n"
        + json.dumps(visible_briefs, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n\nReturn only one unfenced JSON object matching this exact schema:\n"
        + json.dumps(schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    )


def build_first_direct_three_case_pilot_authoring_v4(
    project_root: Path,
) -> dict[str, dict[str, Any]]:
    v3_root = project_root / PILOT_AUTHORING_V3_RELATIVE
    v3_restart = _load(v3_root / "PILOT_AUTHORING_RESTART_AMENDMENT.json")
    _replay(v3_restart, "amendment_digest", V3_RESTART_AMENDMENT_DIGEST, "V3 restart")
    v3_protocol = _load(v3_root / "PILOT_AUTHORING_PROTOCOL.json")
    _replay(v3_protocol, "protocol_digest", V3_PROTOCOL_DIGEST, "V3 protocol")
    v3_failure = _load(v3_root / "AUTHORING_INTAKE_FAILURE_LEDGER.json")
    _replay(
        v3_failure,
        "ledger_digest",
        V3_FAILURE_LEDGER_DIGEST,
        "V3 authoring intake failure ledger",
    )
    if v3_failure["summary"] != {
        "admitted_case_count": 0,
        "assigned_author_context_count": 2,
        "detector_outcome_count": 0,
        "metric_eligible_case_count": 0,
        "model_attempt_count": 2,
        "project_code_executed_count": 0,
        "response_case_count": 3,
        "scientific_label_count": 0,
        "unsupported_selected_result_count": 1,
        "verified_selected_result_count": 2,
    }:
        raise ValueError("V3 failure does not replay as the exact zero-admission state.")

    lane = _load(project_root / LANE_RELATIVE / "LANE_FREEZE.json")
    _replay(lane, "lane_freeze_digest", LANE_FREEZE_DIGEST, "Direct lane freeze")
    briefs = _load(project_root / LANE_RELATIVE / "AUTHORING_BRIEF_MANIFEST.json")
    _replay(briefs, "manifest_digest", BRIEF_MANIFEST_DIGEST, "Authoring brief manifest")

    v3_briefs = {
        str(brief["case_id"]): brief
        for assignment in v3_protocol["author_assignments"]
        for brief in _visible_briefs(str(assignment["prompt"]))
    }
    v3_assignment_by_case = {
        str(item["case_id"]): item for item in v3_restart["restart_assignments"]
    }
    v3_participant_by_case = {
        str(case_id): assignment["participant"]
        for assignment in v3_protocol["author_assignments"]
        for case_id in assignment["case_ids"]
    }
    new_by_old = {
        case_id: stable_id(
            "case",
            case_id,
            "first-envelope-authoring-restart-v4",
            V3_FAILURE_LEDGER_DIGEST,
        )
        for case_id in v3_assignment_by_case
    }

    restart_briefs: dict[str, dict[str, Any]] = {}
    restart_assignments: list[dict[str, Any]] = []
    for old_case_id in sorted(v3_assignment_by_case):
        prior = v3_assignment_by_case[old_case_id]
        new_case_id = new_by_old[old_case_id]
        v4_brief = _v4_brief(v3_briefs[old_case_id], new_case_id)
        restart_briefs[new_case_id] = v4_brief
        provider = str(v3_participant_by_case[old_case_id]["provider"])
        restart_assignments.append(
            {
                "case_id": new_case_id,
                "superseded_failed_case_id": old_case_id,
                "cell_type": prior["cell_type"],
                "author_id": AUTHOR_REPLACEMENTS[provider],
                "author_visible_brief_digest": semantic_digest(v4_brief),
                "reference_case_id": (
                    None
                    if prior["reference_case_id"] is None
                    else new_by_old[str(prior["reference_case_id"])]
                ),
            }
        )

    restart: dict[str, Any] = {
        "artifact_kind": "direct_qualification_three_case_authoring_restart_amendment",
        "amendment_version": "3.0.0",
        "source_commit": SOURCE_COMMIT,
        "lane_freeze_digest": LANE_FREEZE_DIGEST,
        "failed_v3_protocol_digest": V3_PROTOCOL_DIGEST,
        "failed_v3_authoring_intake_ledger_digest": V3_FAILURE_LEDGER_DIGEST,
        "failed_v3_input_capture_digests": [
            item["input_capture_digest"] for item in v3_failure["input_captures"]
        ],
        "restart_assignments": restart_assignments,
        "restart_reason": (
            "The complete v3 cohort failed atomic admission because its permissive indexing "
            "wording exceeded the unchanged static evaluator. Restart with fresh opaque identities "
            "and the generic render-only AST subgrammar frozen at the bound source commit."
        ),
        "failed_iterations_retained": True,
        "failed_case_bytes_repaired_or_reused": False,
        "scientific_briefs_changed": False,
        "detector_or_selected_result_verifier_changed": False,
        "authoring_transport_grammar_changed": True,
        "render_grammar_profile_id": RENDER_ONLY_PROFILE_ID,
        "render_grammar_source_commit": SOURCE_COMMIT,
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
    author_assignments: list[dict[str, Any]] = []
    replacements: list[dict[str, Any]] = []
    for author_id, assigned in sorted(grouped.items()):
        provider = next(
            name for name, replacement in AUTHOR_REPLACEMENTS.items() if replacement == author_id
        )
        original = next(
            item["participant"]
            for item in v3_protocol["author_assignments"]
            if item["participant"]["provider"] == provider
        )
        participant = _fresh_participant(original)
        replacements.append(
            {
                "participant_id": author_id,
                "superseded_participant_id": original["participant_id"],
                "superseded_configuration_digest": original["configuration_digest"],
                "replacement_configuration_digest": participant["configuration_digest"],
                "replacement_reason": "Fresh isolated v4 context after retained v3 failure.",
            }
        )
        case_ids = sorted(str(item["case_id"]) for item in assigned)
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
                        f"sc-referee:first-three-case-pilot-v4:{author_id}:"
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
        "protocol_version": "4.0.0",
        "source_commit": SOURCE_COMMIT,
        "lane_freeze_digest": LANE_FREEZE_DIGEST,
        "authoring_restart_amendment_digest": restart["amendment_digest"],
        "active_reviewer_calibration_ledger_digest": ACTIVE_REVIEWER_LEDGER_DIGEST,
        "render_grammar_profile_id": RENDER_ONLY_PROFILE_ID,
        "render_grammar_source_commit": SOURCE_COMMIT,
        "author_configuration_replacements": replacements,
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
            "pre_admission_render_grammar_validation_required": True,
            "unchanged_static_selected_result_validation_required": True,
            "atomic_complete_causal_triad_admission_required": True,
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
    artifacts = build_first_direct_three_case_pilot_authoring_v4(project_root)
    root = project_root / PILOT_AUTHORING_V4_RELATIVE
    if root.exists():
        raise FileExistsError(f"Refusing to replace frozen v4 authoring root: {root}")
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
