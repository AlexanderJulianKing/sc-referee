"""Two-block dependence threshold-rehearsal and held-out driver.

The driver replays the complete frozen lane before selecting either the
author-accessible threshold-pilot block or the separately sealed held-out
block.  Only the held-out selection writes the ADR-0072 opening record.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

from sc_referee_evaluation.lean_pipeline import (
    EnvelopeConfig,
    ModelParticipant,
    pipeline_step_order,
    run_pipeline,
    write_heldout_opening,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_dependence_qualification_lane import (
    HELDOUT_AUTHOR_1,
    HELDOUT_AUTHOR_2,
    HELDOUT_BLOCK_ID,
    PILOT_AUTHOR_1,
    PILOT_AUTHOR_2,
    PILOT_BLOCK_ID,
)
from scripts.lean_pipeline import default_dependence_config

LANE_RELATIVE = Path(
    "evaluation/qualification/"
    "authorized-independent-unit-entry-into-row-independent-procedure-"
    "v1.1.0-direct-lane"
)
THRESHOLD_PIPELINE_RELATIVE = LANE_RELATIVE / "threshold-rehearsal"
HELDOUT_PIPELINE_RELATIVE = LANE_RELATIVE / "heldout-seven-case"
# Backward-compatible name for callers that previously had only the held-out path.
PIPELINE_RELATIVE = HELDOUT_PIPELINE_RELATIVE
OPENING_RELATIVE = "opening/DEPENDENCE_HELDOUT_OPENING.json"
ADR_RELATIVE = Path("docs/implementation/ADR-0072-HELDOUT-THRESHOLD-DEPENDENCE-ENVELOPE.md")
ADR_NAME = ADR_RELATIVE.name
SEALED_ENVELOPE_ID = (
    "relation-envelope:authorized-independent-unit-entry-into-row-independent-procedure"
)
EXPECTED_ROLES = frozenset(
    {
        "error_bearing",
        "corrected_twin",
        "valid_alternative",
        "hard_negative",
        "ambiguous",
        "unsupported",
        "renamed_implementation",
    }
)
STEP_CHOICES = ("authoring", "intake", "authority", "review", "labels", "detector")
BLOCK_CHOICES = ("threshold", "heldout")
BlockSelection = Literal["threshold", "heldout"]

THRESHOLD_AUTHOR_OPUS_21 = "actor:dependence-threshold-author-opus-21"
THRESHOLD_AUTHOR_OPUS_22 = "actor:dependence-threshold-author-opus-22"
HELDOUT_AUTHOR_OPUS_23 = "actor:dependence-heldout-author-opus-23"
HELDOUT_AUTHOR_OPUS_24 = "actor:dependence-heldout-author-opus-24"
THRESHOLD_AUTHOR_ROLES = {
    THRESHOLD_AUTHOR_OPUS_21: ["corrected_twin", "error_bearing"],
    THRESHOLD_AUTHOR_OPUS_22: [
        "ambiguous",
        "hard_negative",
        "renamed_implementation",
        "unsupported",
        "valid_alternative",
    ],
}
HELDOUT_AUTHOR_ROLES = {
    HELDOUT_AUTHOR_OPUS_23: ["corrected_twin", "error_bearing"],
    HELDOUT_AUTHOR_OPUS_24: [
        "ambiguous",
        "hard_negative",
        "renamed_implementation",
        "unsupported",
        "valid_alternative",
    ],
}
THRESHOLD_SEALED_AUTHOR_ROLES = {
    PILOT_AUTHOR_1: ["corrected_twin", "error_bearing"],
    PILOT_AUTHOR_2: [
        "ambiguous",
        "hard_negative",
        "renamed_implementation",
        "unsupported",
        "valid_alternative",
    ],
}
HELDOUT_SEALED_AUTHOR_ROLES = {
    HELDOUT_AUTHOR_1: ["corrected_twin", "error_bearing"],
    HELDOUT_AUTHOR_2: [
        "ambiguous",
        "hard_negative",
        "renamed_implementation",
        "unsupported",
        "valid_alternative",
    ],
}
THRESHOLD_HONORING_PARTICIPANT_BY_SEALED_AUTHOR = {
    PILOT_AUTHOR_1: THRESHOLD_AUTHOR_OPUS_21,
    PILOT_AUTHOR_2: THRESHOLD_AUTHOR_OPUS_22,
}
HELDOUT_HONORING_PARTICIPANT_BY_SEALED_AUTHOR = {
    HELDOUT_AUTHOR_1: HELDOUT_AUTHOR_OPUS_23,
    HELDOUT_AUTHOR_2: HELDOUT_AUTHOR_OPUS_24,
}


class DependenceHeldoutConfigurationError(ValueError):
    """The frozen dependence lane is absent, open, or inconsistent."""


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DependenceHeldoutConfigurationError(f"Expected one JSON object at {path}.")
    return value


def _replayed(record: dict[str, Any], digest_field: str, label: str) -> dict[str, Any]:
    candidate = dict(record)
    supplied = candidate.pop(digest_field, None)
    if supplied != semantic_digest(candidate):
        raise DependenceHeldoutConfigurationError(
            f"The sealed dependence {label} does not replay its digest."
        )
    return record


def load_sealed_block(project_root: Path, block: BlockSelection = "heldout") -> dict[str, Any]:
    """Replay the complete lane, preserve its held-out seal, and select one block."""

    if block not in BLOCK_CHOICES:
        raise DependenceHeldoutConfigurationError(
            f"Unsupported dependence block selection: {block!r}."
        )
    lane_root = project_root / LANE_RELATIVE
    precase = _replayed(
        _load(lane_root / "FREEZE_MANIFEST.json"), "freeze_digest", "precase freeze"
    )
    enrollment = _replayed(
        _load(lane_root / "PARTICIPANT_ENROLLMENT.json"),
        "enrollment_digest",
        "participant enrollment",
    )
    manifest = _replayed(
        _load(lane_root / "AUTHORING_BRIEF_MANIFEST.json"),
        "manifest_digest",
        "brief manifest",
    )
    lane = _replayed(_load(lane_root / "LANE_FREEZE.json"), "lane_freeze_digest", "lane freeze")
    if lane.get("precase_freeze_digest") != precase.get("freeze_digest"):
        raise DependenceHeldoutConfigurationError(
            "The dependence lane freeze does not bind this precase freeze."
        )
    if lane.get("participant_enrollment_digest") != enrollment.get("enrollment_digest"):
        raise DependenceHeldoutConfigurationError(
            "The dependence lane freeze does not bind this participant enrollment."
        )
    if lane.get("authoring_brief_manifest_digest") != manifest.get("manifest_digest"):
        raise DependenceHeldoutConfigurationError(
            "The dependence lane freeze does not bind this brief manifest."
        )
    raw_protocol = lane.get("prospective_protocol")
    if not isinstance(raw_protocol, dict):
        raise DependenceHeldoutConfigurationError("The dependence lane has no protocol.")
    protocol = _replayed(raw_protocol, "protocol_digest", "prospective protocol")
    block_rows = protocol.get("blocks")
    if not isinstance(block_rows, list) or any(not isinstance(item, dict) for item in block_rows):
        raise DependenceHeldoutConfigurationError(
            "The dependence protocol has no closed block table."
        )
    roles_by_block = {
        str(item.get("block_id")): str(item.get("evidence_role")) for item in block_rows
    }
    if len(block_rows) != 2 or roles_by_block != {
        PILOT_BLOCK_ID: "threshold_pilot",
        HELDOUT_BLOCK_ID: "qualification_heldout",
    }:
        raise DependenceHeldoutConfigurationError(
            "The dependence protocol does not contain the exact threshold and held-out blocks."
        )

    # This seal validation is deliberately unconditional: threshold selection
    # cannot become a route around any held-out refusal.
    seal = lane.get("heldout_seal")
    if not isinstance(seal, dict):
        raise DependenceHeldoutConfigurationError("The dependence lane has no held-out seal.")
    heldout_case_ids = [str(value) for value in seal.get("case_ids", [])]
    if len(heldout_case_ids) != 7 or len(set(heldout_case_ids)) != 7:
        raise DependenceHeldoutConfigurationError(
            "The sealed dependence block is not exactly seven distinct cases."
        )
    if seal.get("author_access_state") != "withheld_until_approved_threshold":
        raise DependenceHeldoutConfigurationError(
            "The sealed dependence block is not withheld pending threshold approval."
        )
    if seal.get("block_ids") != [HELDOUT_BLOCK_ID]:
        raise DependenceHeldoutConfigurationError(
            "The dependence held-out seal does not name the frozen held-out block."
        )
    if (
        seal.get("scientific_labels_present") is not False
        or seal.get("detector_outcomes_present") is not False
    ):
        raise DependenceHeldoutConfigurationError(
            "The dependence held-out seal already exposes labels or detector outcomes."
        )
    raw_assignments = protocol.get("assignments")
    if not isinstance(raw_assignments, list) or any(
        not isinstance(item, dict) for item in raw_assignments
    ):
        raise DependenceHeldoutConfigurationError(
            "The dependence protocol has no closed assignment table."
        )
    assignment_case_ids = [str(item.get("case_id")) for item in raw_assignments]
    raw_briefs = manifest.get("briefs")
    if not isinstance(raw_briefs, list) or any(not isinstance(item, dict) for item in raw_briefs):
        raise DependenceHeldoutConfigurationError(
            "The dependence brief manifest has no closed brief table."
        )
    brief_case_ids = [str(item.get("case_id")) for item in raw_briefs]
    if (
        len(assignment_case_ids) != 14
        or len(set(assignment_case_ids)) != 14
        or len(brief_case_ids) != 14
        or len(set(brief_case_ids)) != 14
        or set(assignment_case_ids) != set(brief_case_ids)
    ):
        raise DependenceHeldoutConfigurationError(
            "The dependence protocol and brief manifest do not bind 14 unique cases."
        )
    heldout_assignment_rows = [
        item for item in raw_assignments if item.get("block_id") == HELDOUT_BLOCK_ID
    ]
    heldout_assignment_ids = {str(item.get("case_id")) for item in heldout_assignment_rows}
    if len(heldout_assignment_rows) != 7 or heldout_assignment_ids != set(heldout_case_ids):
        raise DependenceHeldoutConfigurationError(
            "The held-out assignments do not equal the seven-case seal."
        )

    selected_block_id = PILOT_BLOCK_ID if block == "threshold" else HELDOUT_BLOCK_ID
    case_ids = sorted(
        str(item.get("case_id"))
        for item in raw_assignments
        if item.get("block_id") == selected_block_id
    )
    if len(case_ids) != 7 or len(set(case_ids)) != 7:
        raise DependenceHeldoutConfigurationError(
            f"The selected dependence {block} block is not exactly seven distinct cases."
        )
    if block == "threshold" and set(case_ids) & set(heldout_case_ids):
        raise DependenceHeldoutConfigurationError(
            "The threshold rehearsal overlaps the held-out seal."
        )
    selected_case_ids = set(case_ids)
    selected_assignment_rows = [
        item
        for item in raw_assignments
        if item.get("block_id") == selected_block_id
        and str(item.get("case_id")) in selected_case_ids
    ]
    assignments = {str(item["case_id"]): item for item in selected_assignment_rows}
    briefs = {
        str(item["case_id"]): item
        for item in raw_briefs
        if str(item.get("case_id")) in selected_case_ids
    }
    if (
        len(selected_assignment_rows) != 7
        or set(assignments) != selected_case_ids
        or set(briefs) != selected_case_ids
    ):
        raise DependenceHeldoutConfigurationError(
            "The selected dependence assignments and briefs do not equal its seven-case block."
        )
    rows: list[dict[str, Any]] = []
    for case_id in sorted(case_ids):
        assignment = assignments[case_id]
        entry = briefs[case_id]
        visible = entry.get("author_visible_brief")
        if not isinstance(visible, dict) or semantic_digest(visible) != entry.get("brief_digest"):
            raise DependenceHeldoutConfigurationError(
                f"The dependence brief for {case_id} does not replay."
            )
        if assignment.get("authoring_brief_digest") != entry.get("brief_digest"):
            raise DependenceHeldoutConfigurationError(
                f"The dependence assignment for {case_id} binds a different brief."
            )
        if assignment.get("envelope_id") != SEALED_ENVELOPE_ID:
            raise DependenceHeldoutConfigurationError(
                f"The dependence assignment for {case_id} is off-envelope."
            )
        rows.append(
            {
                "case_id": case_id,
                "role": str(assignment["cell_type"]),
                "sealed_author_id": str(assignment["author_id"]),
                "brief_digest": str(entry["brief_digest"]),
                "brief": dict(visible),
            }
        )
    if {row["role"] for row in rows} != EXPECTED_ROLES:
        raise DependenceHeldoutConfigurationError(
            "The sealed dependence block does not contain the exact seven-role matrix."
        )
    roles_by_author: dict[str, list[str]] = {}
    for row in rows:
        roles_by_author.setdefault(str(row["sealed_author_id"]), []).append(str(row["role"]))
    normalized = {key: sorted(value) for key, value in roles_by_author.items()}
    expected_sealed_roles = (
        THRESHOLD_SEALED_AUTHOR_ROLES if block == "threshold" else HELDOUT_SEALED_AUTHOR_ROLES
    )
    if normalized != expected_sealed_roles:
        raise DependenceHeldoutConfigurationError(
            "The sealed dependence author-role table differs from the sealed slot allocation."
        )
    return {
        "selection": block,
        "evidence_role": roles_by_block[selected_block_id],
        "author_access_state": (
            "permitted_threshold_rehearsal"
            if block == "threshold"
            else "withheld_until_approved_threshold"
        ),
        "precase_freeze_digest": str(precase["freeze_digest"]),
        "participant_enrollment_digest": str(enrollment["enrollment_digest"]),
        "lane_freeze_digest": str(lane["lane_freeze_digest"]),
        "protocol_digest": str(protocol["protocol_digest"]),
        "brief_manifest_digest": str(manifest["manifest_digest"]),
        "block_ids": [selected_block_id],
        "case_ids": case_ids,
        "assignments": rows,
    }


def block_config(
    project_root: Path, block_selection: BlockSelection
) -> tuple[EnvelopeConfig, dict[str, Any] | None]:
    """Carry one selected frozen block into its identity-isolated runtime lane."""

    block = load_sealed_block(project_root, block_selection)
    base = default_dependence_config()
    case_assignments = {row["case_id"]: row["role"] for row in block["assignments"]}
    case_briefs = {row["case_id"]: row["brief"] for row in block["assignments"]}
    renamed_candidate = base.candidate_by_role["error_bearing"]
    candidate_by_role = dict(base.candidate_by_role)
    candidate_by_role["renamed_implementation"] = renamed_candidate
    task_by_role = dict(base.task_by_role)
    task_by_role["renamed_implementation"] = base.task_by_role["error_bearing"]
    procedures = dict(base.frozen_workflow_procedure_by_role)
    procedures["renamed_implementation"] = "mannwhitneyu"
    expected = dict(base.expected_verdict_by_role or {})
    expected["renamed_implementation"] = "demonstrated_issue"
    labels = dict(base.label_status_by_role or {})
    labels["renamed_implementation"] = "positive_demonstrated"
    if block_selection == "threshold":
        author_roles = THRESHOLD_AUTHOR_ROLES
        honoring = THRESHOLD_HONORING_PARTICIPANT_BY_SEALED_AUTHOR
        pipeline_relative = THRESHOLD_PIPELINE_RELATIVE
        envelope_suffix = "threshold-rehearsal"
        reviewer_id = "actor:dependence-threshold-reviewer-fable-13"
        escalation_id = "actor:dependence-threshold-reviewer-opus-10"
        opening_relative = None
    else:
        # No rehearsal participant identity is admitted to the held-out exam.
        author_roles = HELDOUT_AUTHOR_ROLES
        honoring = HELDOUT_HONORING_PARTICIPANT_BY_SEALED_AUTHOR
        pipeline_relative = HELDOUT_PIPELINE_RELATIVE
        envelope_suffix = "heldout"
        reviewer_id = "actor:dependence-heldout-reviewer-fable-14"
        escalation_id = "actor:dependence-heldout-reviewer-opus-11"
        opening_relative = OPENING_RELATIVE
    authors = {
        participant_id: ModelParticipant(
            participant_id=participant_id,
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        )
        for participant_id in author_roles
    }
    config = EnvelopeConfig(
        envelope_id=(
            "authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-"
            + envelope_suffix
        ),
        pipeline_relative=pipeline_relative,
        check_id=base.check_id,
        canonical_issue_class=base.canonical_issue_class,
        candidate_by_role=candidate_by_role,
        task_by_role=task_by_role,
        role_constraints={},
        common_task=base.common_task,
        authors=authors,
        author_roles={key: list(value) for key, value in author_roles.items()},
        reviewer=ModelParticipant(
            participant_id=reviewer_id,
            model_id="claude-fable-5",
            model_name="Claude Fable 5",
            model_alias="fable",
        ),
        escalation_reviewer=ModelParticipant(
            participant_id=escalation_id,
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        ),
        review_instructions=base.review_instructions,
        cli_binary=base.cli_binary,
        cli_binary_version=base.cli_binary_version,
        calibration_suite=base.calibration_suite,
        adr_references=[*base.adr_references, ADR_NAME],
        sealed_case_assignments=case_assignments,
        case_briefs=case_briefs,
        expected_verdict_by_role=expected,
        label_status_by_role=labels,
        author_case_requirements=base.author_case_requirements,
        mq_tolerant_roles=set(base.mq_tolerant_roles),
        contract_free_roles=set(base.contract_free_roles),
        opening_record_relative=opening_relative,
        allowed_import_roots=frozenset(base.allowed_import_roots),
        detector_id=base.detector_id,
        sandbox_python=base.sandbox_python,
        required_sandbox_distributions=dict(base.required_sandbox_distributions),
        controller_material_files=dict(base.controller_material_files),
        material_input_paths=tuple(base.material_input_paths),
        input_csv_row_bounds=base.input_csv_row_bounds,
        frozen_workflow_template=base.frozen_workflow_template,
        frozen_workflow_procedure_by_role=procedures,
    )
    if pipeline_step_order(config) != STEP_CHOICES:
        raise DependenceHeldoutConfigurationError(
            "The selected dependence block order does not include the authority step."
        )
    if block_selection == "threshold":
        return config, None
    adr_path = Path(__file__).resolve().parents[1] / ADR_RELATIVE
    payload = {
        "artifact_kind": "dependence_heldout_opening",
        "opening_version": "1.0.0",
        "adr_reference": {
            "document": ADR_RELATIVE.as_posix(),
            "status": "accepted",
            "accepted_on": "2026-08-10",
            "content_digest": sha256_digest(adr_path.read_bytes()),
            "sensitivity_bar": "two_of_two_positives",
            "false_accusation_bar": "zero_of_five_controls",
        },
        "lane": {
            "lane_relative_path": LANE_RELATIVE.as_posix(),
            "precase_freeze_digest": block["precase_freeze_digest"],
            "participant_enrollment_digest": block["participant_enrollment_digest"],
            "lane_freeze_digest": block["lane_freeze_digest"],
            "prospective_protocol_digest": block["protocol_digest"],
            "authoring_brief_manifest_digest": block["brief_manifest_digest"],
            "heldout_seal_block_ids": block["block_ids"],
            "heldout_seal_case_ids": block["case_ids"],
        },
        "sealed_assignment_table": [
            {
                "case_id": row["case_id"],
                "case_role": row["role"],
                "sealed_author_id": row["sealed_author_id"],
                "honoring_participant_id": honoring[str(row["sealed_author_id"])],
                "brief_digest": row["brief_digest"],
            }
            for row in block["assignments"]
        ],
        "threshold_authority": "accepted_adr_0072",
        "detector_output_observed": False,
        "qualification_authority": "none_opening_record_only",
    }
    return config, payload


def threshold_config(project_root: Path) -> EnvelopeConfig:
    """Return the author-accessible threshold rehearsal configuration."""

    config, payload = block_config(project_root, "threshold")
    if payload is not None:
        raise DependenceHeldoutConfigurationError(
            "The threshold rehearsal unexpectedly produced a held-out opening payload."
        )
    return config


def heldout_config(project_root: Path) -> tuple[EnvelopeConfig, dict[str, Any]]:
    """Return the sealed held-out configuration and accepted ADR-0072 opening payload."""

    config, payload = block_config(project_root, "heldout")
    if payload is None:
        raise DependenceHeldoutConfigurationError(
            "The held-out selection produced no opening payload."
        )
    return config, payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--block", choices=BLOCK_CHOICES, default="heldout")
    parser.add_argument("--step", action="append", choices=STEP_CHOICES)
    arguments = parser.parse_args()
    project_root = arguments.project_root.resolve()
    config, payload = block_config(project_root, arguments.block)
    if payload is not None:
        opening_path = project_root / config.pipeline_relative / OPENING_RELATIVE
        if not opening_path.exists():
            opening = write_heldout_opening(project_root, config, payload)
            print(f"opening: {opening['semantic_digest']}")
    results = run_pipeline(project_root, config, arguments.step)
    for step, artifact in results.items():
        digest = artifact.get("ledger_digest") or artifact.get("protocol_digest")
        print(f"{step}: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
