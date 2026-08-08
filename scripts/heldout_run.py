"""ADR-0070 held-out driver for the sealed seven-case complete-domain block.

The sealed inputs are read at run time and never restated here: the case
identities, their roles, their sealed authors, and their author-visible briefs
all come from ``LANE_FREEZE.json`` and ``AUTHORING_BRIEF_MANIFEST.json`` in the
lane directory, and every digest in those files is replayed before the block
opens. What this driver does add is recorded in ``HELDOUT_OPENING.json`` before
the first author call: which live participant honors each sealed author, the
one superseded construction constraint, and the reviewer-panel supersession.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sc_referee_evaluation.lean_pipeline import (
    EnvelopeConfig,
    ModelParticipant,
    run_pipeline,
    write_heldout_opening,
)

from sc_referee.core.ids import semantic_digest
from scripts.lean_pipeline import (
    _REVIEW_INSTRUCTIONS,
    _TASK_BY_ROLE,
    CALIBRATION_SUITE,
    CLAUDE_PINNED,
    CLAUDE_PINNED_VERSION,
)

LANE_RELATIVE = Path(
    "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2"
)
PIPELINE_RELATIVE = LANE_RELATIVE / "heldout-v207-seven-case"
ENVELOPE_ID = "complete-domain-exposure-denominator-v2.0.7-heldout"
OPENING_RELATIVE = "HELDOUT_OPENING.json"
SEALED_ENVELOPE_ID = "relation-envelope:complete-domain-exposure-denominator"

UNSUPPORTED_ROLE = "unsupported"
UNSUPPORTED_ORIGINAL_MARKER = "runtime environment value"
UNSUPPORTED_REPLACEMENT = (
    "Compute the output path from a runtime data value carried in the input CSV rather than a "
    "source-code path literal; under the staged input the computed path must be exactly "
    "results/report.md so the workflow stays deterministic in the sandbox."
)
UNSUPPORTED_SUPERSESSION_REASON = (
    "ADR-0069 intake guard bans environment access; the cell's essence - statically "
    "unestablishable producer-to-report binding - is preserved via data-selected output"
)

_HELDOUT_COMMON_TASK = (
    "Each assigned case below supplies its own scientific subject area, its own planned-unit "
    "accounting, and its own construction constraints. Build exactly what that case brief "
    "asks for, using the counts the brief supplies, and return the three files described "
    "above for it."
)

_COMPLETE_SET_TASK = _TASK_BY_ROLE["error_bearing"]
_SUPPLIED_ACCOUNTING_TASK = (
    "Report one occurrence rate for this workflow's stated scientific target, using the "
    "planned-unit accounting supplied with this workflow."
)
TASK_BY_ROLE = {
    "error_bearing": _TASK_BY_ROLE["error_bearing"],
    "corrected_twin": _TASK_BY_ROLE["corrected_twin"],
    "valid_alternative": _TASK_BY_ROLE["valid_alternative"],
    "hard_negative": _COMPLETE_SET_TASK,
    "renamed_implementation": _COMPLETE_SET_TASK,
    "ambiguous": _SUPPLIED_ACCOUNTING_TASK,
    "unsupported": _SUPPLIED_ACCOUNTING_TASK,
}
CANDIDATE_BY_ROLE = {
    "error_bearing": "complete-declared-domain-exposure",
    "corrected_twin": "complete-declared-domain-exposure",
    "renamed_implementation": "complete-declared-domain-exposure",
    "hard_negative": "complete-declared-domain-exposure",
    "unsupported": "complete-declared-domain-exposure",
    "valid_alternative": "retained-observed-subset-exposure",
}
EXPECTED_VERDICT_BY_ROLE = {
    "error_bearing": "demonstrated_issue",
    "renamed_implementation": "demonstrated_issue",
    "corrected_twin": "no_demonstrated_issue_within_scope",
    "valid_alternative": "no_demonstrated_issue_within_scope",
    "hard_negative": "no_demonstrated_issue_within_scope",
    "ambiguous": "no_demonstrated_issue_within_scope",
    "unsupported": "no_demonstrated_issue_within_scope",
}
LABEL_STATUS_BY_ROLE = {
    "error_bearing": "positive_demonstrated",
    "renamed_implementation": "positive_demonstrated",
    "corrected_twin": "verified_good_eligible",
    "valid_alternative": "verified_good_eligible",
    "hard_negative": "verified_good_eligible",
    "ambiguous": "ambiguous_control",
    "unsupported": "unsupported_control",
}
MQ_TOLERANT_ROLES = {"ambiguous"}
CONTRACT_FREE_ROLES = {"ambiguous"}

# Each sealed author is honored by exactly one live participant of the same
# provider class. The Codex transport carries no reasoning-effort flag in the
# frozen ADR-0070 argv, so those participants record the effort actually sent.
HONORING_PARTICIPANTS = {
    "actor:sealed-author-codex-04": ModelParticipant(
        participant_id="actor:heldout-codex-04",
        model_id="gpt-5.6-sol",
        model_name="GPT-5.6 Sol",
        model_alias="gpt-5.6-sol",
        provider="OpenAI",
        reasoning_configuration="provider_default",
        transport="codex-cli",
    ),
    "actor:sealed-author-codex-05": ModelParticipant(
        participant_id="actor:heldout-codex-05",
        model_id="gpt-5.6-sol",
        model_name="GPT-5.6 Sol",
        model_alias="gpt-5.6-sol",
        provider="OpenAI",
        reasoning_configuration="provider_default",
        transport="codex-cli",
    ),
    "actor:sealed-author-codex-06": ModelParticipant(
        participant_id="actor:heldout-codex-06",
        model_id="gpt-5.6-sol",
        model_name="GPT-5.6 Sol",
        model_alias="gpt-5.6-sol",
        provider="OpenAI",
        reasoning_configuration="provider_default",
        transport="codex-cli",
    ),
    "actor:sealed-author-claude-04": ModelParticipant(
        participant_id="actor:heldout-claude-04",
        model_id="claude-opus-5",
        model_name="Claude Opus 5",
        model_alias="claude-opus-5",
        transport="claude-cli",
    ),
    "actor:sealed-author-claude-05": ModelParticipant(
        participant_id="actor:heldout-claude-05",
        model_id="claude-opus-5",
        model_name="Claude Opus 5",
        model_alias="claude-opus-5",
        transport="claude-cli",
    ),
    "actor:sealed-author-claude-06": ModelParticipant(
        participant_id="actor:heldout-claude-06",
        model_id="claude-fable-5",
        model_name="Claude Fable 5",
        model_alias="fable",
        transport="claude-cli",
    ),
}
EXPECTED_SEALED_ROLES = {
    "actor:sealed-author-codex-04": ["corrected_twin", "error_bearing"],
    "actor:sealed-author-codex-05": ["hard_negative"],
    "actor:sealed-author-codex-06": ["unsupported"],
    "actor:sealed-author-claude-04": ["valid_alternative"],
    "actor:sealed-author-claude-05": ["ambiguous"],
    "actor:sealed-author-claude-06": ["renamed_implementation"],
}
REVIEWER_SUPERSESSION_NOTE = (
    "The sealed prospective protocol names four stage-1 reviewers and two stage-2 reviewers "
    "per case. That panel design is superseded by accepted ADR-0067: one calibrated blind "
    "merged review with escalation to a second reviewer for non-clean cases only."
)
ONE_SHOT_SCOPE_NOTE = (
    "One shot per ADR-0070 rule 3. A transport failure before a case is admitted is a "
    "retained failure and is retried only under the pipeline's fresh-context rules, which "
    "give the replacement call a new context and retain the failed process capture. The "
    "detector run itself happens exactly once and is never repeated for this envelope's "
    "score."
)


class HeldoutConfigurationError(ValueError):
    """Fail-closed boundary for the sealed held-out inputs."""


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise HeldoutConfigurationError(f"Expected one JSON object at {path}.")
    return value


def _replayed(record: dict[str, Any], digest_field: str, label: str) -> dict[str, Any]:
    candidate = dict(record)
    supplied = candidate.pop(digest_field, None)
    if supplied != semantic_digest(candidate):
        raise HeldoutConfigurationError(f"The sealed {label} does not replay its digest.")
    return record


def load_sealed_block(project_root: Path) -> dict[str, Any]:
    """Read, replay, and cross-check the sealed lane freeze and brief manifest."""

    lane_root = project_root / LANE_RELATIVE
    lane = _replayed(_load(lane_root / "LANE_FREEZE.json"), "lane_freeze_digest", "lane freeze")
    manifest = _replayed(
        _load(lane_root / "AUTHORING_BRIEF_MANIFEST.json"), "manifest_digest", "brief manifest"
    )
    if lane["authoring_brief_manifest_digest"] != manifest["manifest_digest"]:
        raise HeldoutConfigurationError("The lane freeze does not bind this brief manifest.")
    protocol = _replayed(lane["prospective_protocol"], "protocol_digest", "prospective protocol")
    seal = lane["heldout_seal"]
    case_ids = [str(value) for value in seal["case_ids"]]
    if len(set(case_ids)) != 7:
        raise HeldoutConfigurationError("The sealed held-out block is not seven distinct cases.")
    rows = {
        str(row["case_id"]): row
        for row in protocol["assignments"]
        if str(row["case_id"]) in set(case_ids)
    }
    if sorted(rows) != sorted(case_ids):
        raise HeldoutConfigurationError("The prospective protocol misses a sealed case.")
    briefs = {str(item["case_id"]): item for item in manifest["briefs"]}
    assignments: list[dict[str, Any]] = []
    for case_id in sorted(case_ids):
        row = rows[case_id]
        entry = briefs.get(case_id)
        if entry is None:
            raise HeldoutConfigurationError(f"No sealed brief exists for {case_id}.")
        brief = dict(entry["author_visible_brief"])
        if semantic_digest(brief) != entry["brief_digest"]:
            raise HeldoutConfigurationError(f"The sealed brief for {case_id} does not replay.")
        if entry["brief_digest"] != row["authoring_brief_digest"]:
            raise HeldoutConfigurationError(
                f"The sealed assignment for {case_id} binds a different brief digest."
            )
        if str(row["envelope_id"]) != SEALED_ENVELOPE_ID:
            raise HeldoutConfigurationError(f"The sealed assignment for {case_id} is off-envelope.")
        assignments.append(
            {
                "case_id": case_id,
                "role": str(row["cell_type"]),
                "sealed_author_id": str(row["author_id"]),
                "brief_digest": str(entry["brief_digest"]),
                "brief": brief,
                "stage1_reviewer_ids": [str(value) for value in row["stage1_reviewer_ids"]],
                "stage2_reviewer_ids": [str(value) for value in row["stage2_reviewer_ids"]],
            }
        )
    return {
        "lane_freeze_digest": str(lane["lane_freeze_digest"]),
        "brief_manifest_digest": str(manifest["manifest_digest"]),
        "block_ids": [str(value) for value in seal["block_ids"]],
        "case_ids": case_ids,
        "assignments": assignments,
    }


def supersede_unsupported_constraint(block: dict[str, Any]) -> list[dict[str, Any]]:
    """Replace the one construction constraint the ADR-0069 intake guard forbids.

    The sealed unsupported cell asks the author to select the report path from a
    runtime environment value. Reading the environment is outside the import and
    builtin allowlist the intake sandbox enforces, so the constraint is rewritten
    to select the path from a value carried in the case's own input data. The
    property the cell exists to test - that static inspection cannot establish
    which producer wrote the selected report - is unchanged.
    """

    supersessions: list[dict[str, Any]] = []
    for assignment in block["assignments"]:
        if assignment["role"] != UNSUPPORTED_ROLE:
            continue
        constraints = list(assignment["brief"]["construction_constraints"])
        if not constraints or UNSUPPORTED_ORIGINAL_MARKER not in constraints[0]:
            raise HeldoutConfigurationError(
                "The sealed unsupported brief does not open with the environment-value "
                "constraint this supersession was written against."
            )
        original = constraints[0]
        constraints[0] = UNSUPPORTED_REPLACEMENT
        assignment["brief"]["construction_constraints"] = constraints
        original_task = str(assignment["brief"]["scientific_task"])
        if UNSUPPORTED_ORIGINAL_MARKER not in original_task:
            raise HeldoutConfigurationError(
                "The sealed unsupported brief's task line does not name the "
                "environment-value mechanism this supersession was written against."
            )
        replaced_task = original_task.replace(
            UNSUPPORTED_ORIGINAL_MARKER, "runtime data value carried in the input CSV"
        )
        assignment["brief"]["scientific_task"] = replaced_task
        supersessions.append(
            {
                "case_id": assignment["case_id"],
                "case_role": assignment["role"],
                "fields": ["construction_constraints[0]", "scientific_task"],
                "original_text": original,
                "replacement_text": UNSUPPORTED_REPLACEMENT,
                "original_task": original_task,
                "replacement_task": replaced_task,
                "reason": UNSUPPORTED_SUPERSESSION_REASON,
                "sealed_brief_digest": assignment["brief_digest"],
                "superseded_brief_digest": semantic_digest(assignment["brief"]),
                "residual_note": (
                    "The constraint and the task line were superseded consistently; "
                    "available_inputs are quoted unchanged. The author declaration "
                    "constraint is satisfied structurally: the selected-result "
                    "declaration lives in the author's response record outside the "
                    "three-file case tree."
                ),
            }
        )
    if len(supersessions) != 1:
        raise HeldoutConfigurationError(
            "The sealed block does not hold exactly one unsupported cell."
        )
    return supersessions


def heldout_config(project_root: Path) -> tuple[EnvelopeConfig, dict[str, Any]]:
    """Build the sealed held-out envelope config and its opening payload."""

    block = load_sealed_block(project_root)
    supersessions = supersede_unsupported_constraint(block)
    sealed_case_assignments = {item["case_id"]: item["role"] for item in block["assignments"]}
    case_briefs = {item["case_id"]: item["brief"] for item in block["assignments"]}
    roles_by_sealed_author: dict[str, list[str]] = {}
    for item in block["assignments"]:
        roles_by_sealed_author.setdefault(str(item["sealed_author_id"]), []).append(
            str(item["role"])
        )
    if {
        key: sorted(value) for key, value in roles_by_sealed_author.items()
    } != EXPECTED_SEALED_ROLES:
        raise HeldoutConfigurationError(
            "The sealed author-to-role table differs from the table ADR-0070 opened."
        )
    authors = {
        HONORING_PARTICIPANTS[sealed_author].participant_id: HONORING_PARTICIPANTS[sealed_author]
        for sealed_author in roles_by_sealed_author
    }
    author_roles = {
        HONORING_PARTICIPANTS[sealed_author].participant_id: sorted(roles)
        for sealed_author, roles in roles_by_sealed_author.items()
    }
    config = EnvelopeConfig(
        envelope_id=ENVELOPE_ID,
        pipeline_relative=PIPELINE_RELATIVE,
        check_id="check:complete-domain-exposure-denominator",
        canonical_issue_class="issue-class:retained-subset-for-complete-domain",
        candidate_by_role={
            role: CANDIDATE_BY_ROLE[role]
            for role in sealed_case_assignments.values()
            if role in CANDIDATE_BY_ROLE
        },
        task_by_role={role: TASK_BY_ROLE[role] for role in sealed_case_assignments.values()},
        role_constraints={},
        common_task=_HELDOUT_COMMON_TASK,
        authors=authors,
        author_roles=author_roles,
        reviewer=ModelParticipant(
            participant_id="actor:heldout-reviewer-fable-01",
            model_id="claude-fable-5",
            model_name="Claude Fable 5",
            model_alias="fable",
        ),
        escalation_reviewer=ModelParticipant(
            participant_id="actor:heldout-reviewer-opus-01",
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        ),
        review_instructions=_REVIEW_INSTRUCTIONS,
        cli_binary=CLAUDE_PINNED,
        cli_binary_version=CLAUDE_PINNED_VERSION,
        calibration_suite=CALIBRATION_SUITE,
        adr_references=[
            "ADR-0067-LEAN-SINGLE-REVIEW-QUALIFICATION-PROTOCOL.md",
            "ADR-0068-QUALIFICATION-PROCESS-CONSOLIDATION.md",
            "ADR-0069-OPERATIONS-BASED-DETECTION-AND-EXECUTABLE-CASES.md",
            "ADR-0070-HELDOUT-THRESHOLD-COMPLETE-DOMAIN-ENVELOPE.md",
        ],
        sealed_case_assignments=sealed_case_assignments,
        case_briefs=case_briefs,
        expected_verdict_by_role={
            role: EXPECTED_VERDICT_BY_ROLE[role] for role in sealed_case_assignments.values()
        },
        label_status_by_role={
            role: LABEL_STATUS_BY_ROLE[role] for role in sealed_case_assignments.values()
        },
        mq_tolerant_roles=set(MQ_TOLERANT_ROLES),
        contract_free_roles=set(CONTRACT_FREE_ROLES),
        opening_record_relative=OPENING_RELATIVE,
    )
    payload = build_opening_payload(block, supersessions)
    return config, payload


def build_opening_payload(
    block: dict[str, Any], supersessions: list[dict[str, Any]]
) -> dict[str, Any]:
    """The record of exactly what was opened and what was changed at opening."""

    sealed_table = []
    for item in block["assignments"]:
        participant = HONORING_PARTICIPANTS[str(item["sealed_author_id"])]
        sealed_table.append(
            {
                "case_id": item["case_id"],
                "case_role": item["role"],
                "sealed_author_id": item["sealed_author_id"],
                "honoring_participant_id": participant.participant_id,
                "honoring_provider": participant.provider,
                "honoring_model_id": participant.model_id,
                "transport": participant.transport,
                "sealed_brief_digest": item["brief_digest"],
            }
        )
    stage1 = sorted({name for item in block["assignments"] for name in item["stage1_reviewer_ids"]})
    stage2 = sorted({name for item in block["assignments"] for name in item["stage2_reviewer_ids"]})
    return {
        "artifact_kind": "heldout_opening",
        "opening_version": "1.0.0",
        "adr_reference": {
            "document": "ADR-0070-HELDOUT-THRESHOLD-COMPLETE-DOMAIN-ENVELOPE.md",
            "status": "accepted",
            "accepted_on": "2026-08-08",
            "sensitivity_bar": "at_least_one_of_two_positives",
            "false_accusation_bar": "zero_of_five_controls",
        },
        "lane": {
            "lane_relative_path": LANE_RELATIVE.as_posix(),
            "lane_freeze_digest": block["lane_freeze_digest"],
            "authoring_brief_manifest_digest": block["brief_manifest_digest"],
            "heldout_seal_block_ids": block["block_ids"],
            "heldout_seal_case_ids": block["case_ids"],
        },
        "sealed_assignment_table": sealed_table,
        "sealed_brief_digests": {
            item["case_id"]: item["brief_digest"] for item in block["assignments"]
        },
        "brief_supersessions": supersessions,
        "reviewer_supersession": {
            "sealed_stage1_reviewer_ids": stage1,
            "sealed_stage2_reviewer_ids": stage2,
            "superseding_adr": "ADR-0067-LEAN-SINGLE-REVIEW-QUALIFICATION-PROTOCOL.md",
            "note": REVIEWER_SUPERSESSION_NOTE,
        },
        "one_shot_scope_note": ONE_SHOT_SCOPE_NOTE,
        "detector_output_observed": False,
        "qualification_authority": "none_opening_record_only",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--step",
        action="append",
        choices=["authoring", "intake", "review", "labels", "detector"],
        help="Steps to run; omit to run every step not yet in the manifest.",
    )
    arguments = parser.parse_args()
    project_root = arguments.project_root.resolve()
    config, payload = heldout_config(project_root)
    opening_path = project_root / config.pipeline_relative / OPENING_RELATIVE
    if not opening_path.exists():
        opening = write_heldout_opening(project_root, config, payload)
        print(f"opening: {opening['semantic_digest']}")
    results = run_pipeline(project_root, config, arguments.step)
    for step, artifact in results.items():
        digest = artifact.get("ledger_digest") or artifact.get("protocol_digest")
        print(f"{step}: {digest}")
        if step == "detector":
            print(json.dumps(artifact["pilot_metrics"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
