"""Sealed seven-case dependence held-out driver scaffold.

The threshold ADR and maintainer opening decision are intentionally outside
this module.  This driver reads only a future one-shot lane freeze, replays all
sealed digests, records an opening before authoring, and carries the complete
dependence envelope configuration into the generic lean pipeline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sc_referee_evaluation.lean_pipeline import (
    EnvelopeConfig,
    ModelParticipant,
    pipeline_step_order,
    run_pipeline,
    write_heldout_opening,
)

from sc_referee.core.ids import semantic_digest
from scripts.build_dependence_qualification_lane import (
    HELDOUT_AUTHOR_1,
    HELDOUT_AUTHOR_2,
    HELDOUT_BLOCK_ID,
)
from scripts.lean_pipeline import default_dependence_config

LANE_RELATIVE = Path(
    "evaluation/qualification/"
    "authorized-independent-unit-entry-into-row-independent-procedure-"
    "v1.1.0-direct-lane"
)
PIPELINE_RELATIVE = LANE_RELATIVE / "heldout-seven-case"
OPENING_RELATIVE = "opening/DEPENDENCE_HELDOUT_OPENING.json"
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

AUTHOR_OPUS_21 = "actor:dependence-heldout-author-opus-21"
AUTHOR_OPUS_22 = "actor:dependence-heldout-author-opus-22"
EXPECTED_AUTHOR_ROLES = {
    AUTHOR_OPUS_21: ["corrected_twin", "error_bearing"],
    AUTHOR_OPUS_22: [
        "ambiguous",
        "hard_negative",
        "renamed_implementation",
        "unsupported",
        "valid_alternative",
    ],
}
EXPECTED_SEALED_AUTHOR_ROLES = {
    HELDOUT_AUTHOR_1: ["corrected_twin", "error_bearing"],
    HELDOUT_AUTHOR_2: [
        "ambiguous",
        "hard_negative",
        "renamed_implementation",
        "unsupported",
        "valid_alternative",
    ],
}
HONORING_PARTICIPANT_BY_SEALED_AUTHOR = {
    HELDOUT_AUTHOR_1: AUTHOR_OPUS_21,
    HELDOUT_AUTHOR_2: AUTHOR_OPUS_22,
}


class DependenceHeldoutConfigurationError(ValueError):
    """A future dependence held-out lane is absent, open, or inconsistent."""


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


def load_sealed_block(project_root: Path) -> dict[str, Any]:
    """Replay one exact seven-case held-out block without opening it."""

    lane_root = project_root / LANE_RELATIVE
    lane = _replayed(_load(lane_root / "LANE_FREEZE.json"), "lane_freeze_digest", "lane freeze")
    manifest = _replayed(
        _load(lane_root / "AUTHORING_BRIEF_MANIFEST.json"),
        "manifest_digest",
        "brief manifest",
    )
    if lane.get("authoring_brief_manifest_digest") != manifest.get("manifest_digest"):
        raise DependenceHeldoutConfigurationError(
            "The dependence lane freeze does not bind this brief manifest."
        )
    seal = lane.get("heldout_seal")
    if not isinstance(seal, dict):
        raise DependenceHeldoutConfigurationError("The dependence lane has no held-out seal.")
    case_ids = [str(value) for value in seal.get("case_ids", [])]
    if len(case_ids) != 7 or len(set(case_ids)) != 7:
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
    protocol = lane.get("prospective_protocol")
    if not isinstance(protocol, dict):
        raise DependenceHeldoutConfigurationError("The dependence lane has no protocol.")
    assignments = {
        str(item["case_id"]): item
        for item in protocol.get("assignments", [])
        if isinstance(item, dict) and str(item.get("case_id")) in set(case_ids)
    }
    briefs = {
        str(item["case_id"]): item
        for item in manifest.get("briefs", [])
        if isinstance(item, dict) and str(item.get("case_id")) in set(case_ids)
    }
    if set(assignments) != set(case_ids) or set(briefs) != set(case_ids):
        raise DependenceHeldoutConfigurationError(
            "The sealed dependence assignments and briefs do not equal the seven-case seal."
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
    if normalized != EXPECTED_SEALED_AUTHOR_ROLES:
        raise DependenceHeldoutConfigurationError(
            "The sealed dependence author-role table differs from the sealed slot allocation."
        )
    return {
        "lane_freeze_digest": str(lane["lane_freeze_digest"]),
        "brief_manifest_digest": str(manifest["manifest_digest"]),
        "block_ids": [str(value) for value in seal.get("block_ids", [])],
        "case_ids": case_ids,
        "assignments": rows,
    }


def heldout_config(project_root: Path) -> tuple[EnvelopeConfig, dict[str, Any]]:
    """Carry the full pilot-d dependence envelope into the sealed lane."""

    block = load_sealed_block(project_root)
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
    authors = {
        AUTHOR_OPUS_21: ModelParticipant(
            participant_id=AUTHOR_OPUS_21,
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        ),
        AUTHOR_OPUS_22: ModelParticipant(
            participant_id=AUTHOR_OPUS_22,
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        ),
    }
    config = EnvelopeConfig(
        envelope_id=(
            "authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-heldout"
        ),
        pipeline_relative=PIPELINE_RELATIVE,
        check_id=base.check_id,
        canonical_issue_class=base.canonical_issue_class,
        candidate_by_role=candidate_by_role,
        task_by_role=task_by_role,
        role_constraints={},
        common_task=base.common_task,
        authors=authors,
        author_roles={key: list(value) for key, value in EXPECTED_AUTHOR_ROLES.items()},
        reviewer=ModelParticipant(
            participant_id="actor:dependence-heldout-reviewer-fable-13",
            model_id="claude-fable-5",
            model_name="Claude Fable 5",
            model_alias="fable",
        ),
        # Opus-09 fired and was spent in pilot-c; the sealed exam advances to opus-10.
        escalation_reviewer=ModelParticipant(
            participant_id="actor:dependence-heldout-reviewer-opus-10",
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        ),
        review_instructions=base.review_instructions,
        cli_binary=base.cli_binary,
        cli_binary_version=base.cli_binary_version,
        calibration_suite=base.calibration_suite,
        adr_references=list(base.adr_references),
        sealed_case_assignments=case_assignments,
        case_briefs=case_briefs,
        expected_verdict_by_role=expected,
        label_status_by_role=labels,
        author_case_requirements=base.author_case_requirements,
        mq_tolerant_roles=set(base.mq_tolerant_roles),
        contract_free_roles=set(base.contract_free_roles),
        opening_record_relative=OPENING_RELATIVE,
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
            "The dependence held-out default order does not include the authority step."
        )
    payload = {
        "artifact_kind": "dependence_heldout_opening",
        "opening_version": "1.0.0",
        "lane": {
            "lane_relative_path": LANE_RELATIVE.as_posix(),
            "lane_freeze_digest": block["lane_freeze_digest"],
            "authoring_brief_manifest_digest": block["brief_manifest_digest"],
            "heldout_seal_block_ids": block["block_ids"],
            "heldout_seal_case_ids": block["case_ids"],
        },
        "sealed_assignment_table": [
            {
                "case_id": row["case_id"],
                "case_role": row["role"],
                "sealed_author_id": row["sealed_author_id"],
                "honoring_participant_id": HONORING_PARTICIPANT_BY_SEALED_AUTHOR[
                    str(row["sealed_author_id"])
                ],
                "brief_digest": row["brief_digest"],
            }
            for row in block["assignments"]
        ],
        "threshold_authority": "pending_separate_maintainer_decision",
        "detector_output_observed": False,
        "qualification_authority": "none_opening_record_only",
    }
    return config, payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--step", action="append", choices=STEP_CHOICES)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
