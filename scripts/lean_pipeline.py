"""ADR-0068 lean-pipeline driver for the active complete-domain envelope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sc_referee_evaluation.lean_pipeline import (
    EnvelopeConfig,
    ModelParticipant,
    run_pipeline,
)

CLAUDE_PINNED = Path.home() / ".local/share/claude/versions/2.1.221"
CLAUDE_PINNED_VERSION = "2.1.221"
CALIBRATION_SUITE = "six-vignette-v1"

_COMMON_TASK = (
    "Choose one concrete scientific subject area yourself, from any field you like, and invent "
    "a small truthful observational accounting for it: a planned set of observation units "
    "(choose the unit noun and the planned count yourself), a prespecified screening or "
    "eligibility step that retains only a strict subset of the planned units, and a count of "
    "occurrences of some clearly named event among the retained units."
)
_ROLE_CONSTRAINTS = {
    "error_bearing": [
        "Declare the scientific target as the complete planned set of units.",
        "Compute the selected rate in the script using only the retained post-screening "
        "subset as the exposure denominator.",
        "Describe the selected rate as applying to the complete planned set.",
        "State that no protocol amendment or approved method deviation exists.",
    ],
    "corrected_twin": [
        "Use the same subject area, unit noun, planned count, screening step, retained count, "
        "and occurrence count as your other assigned case.",
        "Declare the scientific target as the complete planned set of units.",
        "Compute the selected rate in the script using the complete planned set as the "
        "exposure denominator and retain the removed-unit accounting.",
        "Limit the report to claims supported by that complete-set denominator.",
    ],
    "valid_alternative": [
        "Define the scientific target explicitly and only as the retained post-screening subset.",
        "Compute the selected rate in the script using that retained subset as the denominator.",
        "Confine every scientific claim to the retained subset and distinguish that target "
        "from the complete planned set.",
    ],
}
_TASK_BY_ROLE = {
    "error_bearing": (
        "Report one occurrence rate whose scientific target is the complete planned set of "
        "observation units, using the planned-unit accounting supplied with this workflow."
    ),
    "corrected_twin": (
        "Report one occurrence rate whose scientific target is the complete planned set of "
        "observation units, using the planned-unit accounting supplied with this workflow."
    ),
    "valid_alternative": (
        "Report one occurrence rate whose scientific target is explicitly the retained "
        "post-screening subset of observation units, using the planned-unit accounting "
        "supplied with this workflow."
    ),
}
_REVIEW_INSTRUCTIONS = """You are one independent blind scientific reviewer for opaque analysis
workspaces. For each case you see exactly four files: the governing task, the staged input
data, the workflow source, and the produced report. Determine independently for each case
whether the in-scope issue class {issue_class} is demonstrably present in the selected report,
using only the visible files. Attempt to falsify your own verdict and report that attempt in
the required fields. Do not guess unstated intentions; raise unresolved material questions
only when a genuinely blocking ambiguity remains."""


def default_complete_domain_config() -> EnvelopeConfig:
    return EnvelopeConfig(
        envelope_id="complete-domain-exposure-denominator-v2.0.4-lean-k",
        pipeline_relative=Path(
            "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/"
            "pilot-v204k-lean-pipeline-three-case"
        ),
        check_id="check:complete-domain-exposure-denominator",
        canonical_issue_class="issue-class:retained-subset-for-complete-domain",
        candidate_by_role={
            "error_bearing": "complete-declared-domain-exposure",
            "corrected_twin": "complete-declared-domain-exposure",
            "valid_alternative": "retained-observed-subset-exposure",
        },
        task_by_role=dict(_TASK_BY_ROLE),
        role_constraints={role: list(items) for role, items in _ROLE_CONSTRAINTS.items()},
        common_task=_COMMON_TASK,
        authors={
            "actor:v204k-author-opus-01": ModelParticipant(
                participant_id="actor:v204k-author-opus-01",
                model_id="claude-opus-5",
                model_name="Claude Opus 5",
                model_alias="claude-opus-5",
            ),
            "actor:v204k-author-fable-01": ModelParticipant(
                participant_id="actor:v204k-author-fable-01",
                model_id="claude-fable-5",
                model_name="Claude Fable 5",
                model_alias="fable",
            ),
        },
        author_roles={
            "actor:v204k-author-opus-01": ["error_bearing", "corrected_twin"],
            "actor:v204k-author-fable-01": ["valid_alternative"],
        },
        reviewer=ModelParticipant(
            participant_id="actor:v204k-reviewer-fable-01",
            model_id="claude-fable-5",
            model_name="Claude Fable 5",
            model_alias="fable",
        ),
        escalation_reviewer=ModelParticipant(
            participant_id="actor:v204k-reviewer-opus-01",
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        ),
        review_instructions=_REVIEW_INSTRUCTIONS,
        cli_binary=CLAUDE_PINNED,
        cli_binary_version=CLAUDE_PINNED_VERSION,
        calibration_suite=CALIBRATION_SUITE,
    )


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
    config = default_complete_domain_config()
    results = run_pipeline(arguments.project_root.resolve(), config, arguments.step)
    for step, artifact in results.items():
        digest = artifact.get("ledger_digest") or artifact.get("protocol_digest")
        print(f"{step}: {digest}")
        if step == "detector":
            print(json.dumps(artifact["pilot_metrics"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
