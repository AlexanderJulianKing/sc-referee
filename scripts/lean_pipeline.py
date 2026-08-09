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
        envelope_id="complete-domain-exposure-denominator-v2.0.6-lean-m",
        pipeline_relative=Path(
            "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/"
            "pilot-v206m-lean-pipeline-three-case"
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
            "actor:v206m-author-opus-01": ModelParticipant(
                participant_id="actor:v206m-author-opus-01",
                model_id="claude-opus-5",
                model_name="Claude Opus 5",
                model_alias="claude-opus-5",
            ),
            "actor:v206m-author-fable-01": ModelParticipant(
                participant_id="actor:v206m-author-fable-01",
                model_id="claude-fable-5",
                model_name="Claude Fable 5",
                model_alias="fable",
            ),
        },
        author_roles={
            "actor:v206m-author-opus-01": ["error_bearing", "corrected_twin"],
            "actor:v206m-author-fable-01": ["valid_alternative"],
        },
        reviewer=ModelParticipant(
            participant_id="actor:v206m-reviewer-fable-01",
            model_id="claude-fable-5",
            model_name="Claude Fable 5",
            model_alias="fable",
        ),
        escalation_reviewer=ModelParticipant(
            participant_id="actor:v206m-reviewer-opus-01",
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        ),
        review_instructions=_REVIEW_INSTRUCTIONS,
        cli_binary=CLAUDE_PINNED,
        cli_binary_version=CLAUDE_PINNED_VERSION,
        calibration_suite=CALIBRATION_SUITE,
    )


# ---------------------------------------------------------------------------
# Envelope 1: founder-orientation before the emission comparison.
#
# The reviewable operand is whether an orientation repair sits on the dataflow
# path into the emission comparison, so every constraint below is stated in
# operations. The briefs name no variable, no column, no domain noun and no
# code idiom: the author invents the subject area and the vocabulary, and the
# constraints say only what the workflow must compute and what the report must
# state. The statement-form envelope in the case requirements is the set of
# forms the v2.1.5 recognizer models completely; it is stated once, for every
# role, so no role is identifiable from the shape of its own constraints.

FOUNDER_CHECK_ID = "check:founder-orientation-before-hmm-emission"
FOUNDER_CHECK_VERSION = "2.1.5"
FOUNDER_PILOT_INSTANCE = "a"
FOUNDER_LANE_RELATIVE = Path(
    f"evaluation/qualification/founder-orientation-before-hmm-emission-v{FOUNDER_CHECK_VERSION}-lane"
)

# Pilot b is the same envelope, the same briefs and the same discipline, run
# against the v2.2.1 recognizer that closed the pilot-a miss. Every
# version-derived string is derived exactly the way pilot a derived it from
# v2.1.5: the check version is the one the scientific-check manifest registry
# carries for this check id, and the lane directory and the envelope id are
# built from it. The actor labels are fresh so no pilot-a participant record is
# reused; reviewer calibration resolves by (model id, pinned binary version,
# calibration suite), which the shared registry already holds for both models.
FOUNDER_CHECK_VERSION_B = "2.2.1"
FOUNDER_PILOT_INSTANCE_B = "b"
FOUNDER_LANE_RELATIVE_B = Path(
    "evaluation/qualification/"
    f"founder-orientation-before-hmm-emission-v{FOUNDER_CHECK_VERSION_B}-lane"
)

# Pilot c is the same envelope, the same briefs and the same discipline again,
# run against the v2.2.2 recognizer that closed the pilot-b miss. The check
# version is the one the scientific-check manifest registry carries for this
# check id, and the lane directory and the envelope id are built from it by the
# same f-string convention pilots a and b used. The actor labels are fresh so no
# pilot-a or pilot-b participant record is reused; reviewer calibration resolves
# by (model id, pinned binary version, calibration suite) from the shared
# registry, exactly as before.
FOUNDER_CHECK_VERSION_C = "2.2.2"
FOUNDER_PILOT_INSTANCE_C = "c"
FOUNDER_LANE_RELATIVE_C = Path(
    "evaluation/qualification/"
    f"founder-orientation-before-hmm-emission-v{FOUNDER_CHECK_VERSION_C}-lane"
)

_FOUNDER_COMMON_TASK = (
    "Choose one concrete scientific subject area yourself, from any field you like, and invent "
    "a small truthful comparison accounting for it: a set of measured units (choose the unit "
    "noun and the unit count yourself), a per-unit observed binary call recorded for each unit, "
    "and the per-unit binary value the same units carry in an independently supplied reference "
    "panel."
)

_FOUNDER_CASE_REQUIREMENTS = """Author every assigned case as a small, real, runnable analysis workflow. For each case you
produce exactly three files.

inputs/data.csv: an ASCII CSV with a header row and one data row per measured unit. Two of its
columns hold values written only as 0 or 1: one is that unit's observed call, the other is that
unit's value in the supplied reference panel. Add whatever other columns your subject area
wants. Use at least twenty units, and let the two binary columns agree on some units and
disagree on others.

workflow/analysis.py: a deterministic Python script using only the standard library modules
csv, math, pathlib, fractions, decimal, and statistics. It must read inputs/data.csv, compute
every number it reports from that data (never hard-code a result number), and write
results/report.md. No randomness, no clock, no network, no other files, no command-line
arguments, no input.

The script must stay inside the forms below, which are the forms this envelope's static review
reads completely. They constrain the shape of the code, never its vocabulary:

- Module-level statements only: imports, assignments that bind exactly one plain name, function
  definitions with straight-line bodies, comprehensions, plain accumulation loops, and the
  report write. No try, while, match, class, del, global, raise, assert, or async statement, and
  no if statement. No augmented assignment, no walrus, no type annotation, and no name that
  shadows a Python builtin.
- Every comparison your workflow makes between two columns of the staged table is an equality
  test used as a two-valued numeric selector: it yields one numeric constant when the two values
  are equal and a strictly smaller numeric constant when they are not. Each such selector is
  accumulated across the units by a product or a sum. Do not count with a filtering condition,
  and do not compare the two columns with an inequality operator.
- The text you write or print is built from names, constants, arithmetic, and f-strings over
  them; do not call a function inside a printed or written payload.

results/report.md: an ASCII Markdown report whose lines exactly equal the script output. It must
contain exactly one line beginning with `[selected-result]` stating the single selected result,
and it must state the accounting in numbers: the total number of measured units, the per-unit
agreement count its own text describes, the per-unit agreement rate the emission accumulation
used, and the accumulated emission value itself.

The intake pipeline (not you) will later execute your script twice from the case root with
`python -I workflow/analysis.py`; both runs must produce byte-identical output, and the
report_md you return must equal that output exactly, byte for byte, so compute every reported
number with exact care.

Keep every number internally consistent with the CSV. Report selected_result_line as the
1-based line number of the `[selected-result]` line inside report_md."""

_FOUNDER_ROLE_CONSTRAINTS = {
    "error_bearing": [
        "Cast both binary columns to integers where the workflow reads them.",
        "Replace every reference-panel value by its complement before that value reaches any "
        "comparison: the value entering the comparison is 1 where the staged file holds 0 and "
        "0 where the staged file holds 1.",
        "Accumulate the two-valued selector over that complemented comparison into the product "
        "or sum the report states as the emission value, and take the per-unit agreement rate "
        "the report states from that same complemented comparison.",
        "Compare the observed column against the reference column only in the complemented "
        "form; the workflow contains no comparison of those two columns as staged.",
        "State in the report the total unit count, the number of units whose observed value "
        "equals the reference value exactly as the staged file holds it (obtain that number by "
        "arithmetic from the count your one comparison produces, never from a second "
        "comparison), and the per-unit agreement rate the emission accumulation used.",
        "Present the analysis as using the supplied reference panel in the coding in which it "
        "is supplied: no line of the report and no comment in the script names a complement, "
        "an inversion, a flip, a repair, or a recoding.",
        "State that no protocol amendment or approved method deviation exists.",
    ],
    "corrected_twin": [
        "Use the same subject area, unit noun, unit count, column meanings, and staged values "
        "as your other assigned case.",
        "Compare the observed column against the reference-panel column exactly as the staged "
        "file holds it; nothing anywhere in the workflow complements, inverts, or recodes a "
        "binary value.",
        "Accumulate the two-valued selector over that comparison into the product or sum the "
        "report states as the emission value, and take the per-unit agreement rate the report "
        "states from that same comparison.",
        "State in the report the total unit count, the number of units whose observed value "
        "equals the staged reference value, and the per-unit agreement rate the emission "
        "accumulation used.",
        "Limit the report to claims supported by that staged-coding comparison.",
    ],
    "hard_negative": [
        "Build a workflow with the structure of an orientation problem and without the problem "
        "itself. Choose exactly one of these two constructions: compute a complemented copy of "
        "the reference values that feeds only a quality-control line of the report and never "
        "the emission accumulation; or stage a second, independent reference column and compare "
        "the observed column against both reference columns exactly as staged.",
        "Every value that reaches the emission accumulation comes from the reference panel in "
        "the coding in which the staged file holds it.",
        "Accumulate the two-valued selector over that comparison into the product or sum the "
        "report states as the emission value, and take the per-unit agreement rate the report "
        "states from that same comparison.",
        "State in the report the total unit count, the number of units whose observed value "
        "equals the staged reference value, the per-unit agreement rate the emission "
        "accumulation used, and the count produced by your quality-control or second-reference "
        "comparison, labelled in the report for what it is.",
    ],
}

_FOUNDER_TASK = (
    "Report one per-unit agreement rate for the emission-weighted comparison of the observed "
    "calls against the reference-panel values supplied with this workflow, using those panel "
    "values in the coding in which they are supplied."
)
_FOUNDER_TASK_BY_ROLE = {role: _FOUNDER_TASK for role in _FOUNDER_ROLE_CONSTRAINTS}
_FOUNDER_EXPECTED_VERDICT_BY_ROLE = {
    "error_bearing": "demonstrated_issue",
    "corrected_twin": "no_demonstrated_issue_within_scope",
    "hard_negative": "no_demonstrated_issue_within_scope",
}
_FOUNDER_LABEL_STATUS_BY_ROLE = {
    "error_bearing": "positive_demonstrated",
    "corrected_twin": "verified_good_eligible",
    "hard_negative": "verified_good_eligible",
}


def default_founder_orientation_config(
    instance: str = FOUNDER_PILOT_INSTANCE,
    check_version: str = FOUNDER_CHECK_VERSION,
    lane_relative: Path = FOUNDER_LANE_RELATIVE,
    author_ordinals: tuple[str, str] = ("01", "02"),
    reviewer_ordinal: str = "01",
) -> EnvelopeConfig:
    slug = f"founder-{instance}"
    first_author, second_author = author_ordinals
    return EnvelopeConfig(
        envelope_id=f"founder-orientation-before-hmm-emission-v{check_version}-lean-{instance}",
        pipeline_relative=lane_relative / f"pilot-{instance}",
        check_id=FOUNDER_CHECK_ID,
        canonical_issue_class="issue-class:complemented-panel-for-supplied-panel-emission",
        candidate_by_role={
            "error_bearing": "use-supplied-orientation",
            "corrected_twin": "use-supplied-orientation",
            "hard_negative": "use-supplied-orientation",
        },
        task_by_role=dict(_FOUNDER_TASK_BY_ROLE),
        role_constraints={role: list(items) for role, items in _FOUNDER_ROLE_CONSTRAINTS.items()},
        common_task=_FOUNDER_COMMON_TASK,
        authors={
            f"actor:{slug}-author-opus-{first_author}": ModelParticipant(
                participant_id=f"actor:{slug}-author-opus-{first_author}",
                model_id="claude-opus-5",
                model_name="Claude Opus 5",
                model_alias="claude-opus-5",
            ),
            f"actor:{slug}-author-opus-{second_author}": ModelParticipant(
                participant_id=f"actor:{slug}-author-opus-{second_author}",
                model_id="claude-opus-5",
                model_name="Claude Opus 5",
                model_alias="claude-opus-5",
            ),
        },
        author_roles={
            f"actor:{slug}-author-opus-{first_author}": ["error_bearing", "corrected_twin"],
            f"actor:{slug}-author-opus-{second_author}": ["hard_negative"],
        },
        reviewer=ModelParticipant(
            participant_id=f"actor:{slug}-reviewer-fable-{reviewer_ordinal}",
            model_id="claude-fable-5",
            model_name="Claude Fable 5",
            model_alias="fable",
        ),
        escalation_reviewer=ModelParticipant(
            participant_id=f"actor:{slug}-reviewer-opus-{reviewer_ordinal}",
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        ),
        review_instructions=_REVIEW_INSTRUCTIONS,
        cli_binary=CLAUDE_PINNED,
        cli_binary_version=CLAUDE_PINNED_VERSION,
        calibration_suite=CALIBRATION_SUITE,
        author_case_requirements=_FOUNDER_CASE_REQUIREMENTS,
        expected_verdict_by_role=dict(_FOUNDER_EXPECTED_VERDICT_BY_ROLE),
        label_status_by_role=dict(_FOUNDER_LABEL_STATUS_BY_ROLE),
    )


def default_founder_orientation_b_config() -> EnvelopeConfig:
    """Instance b of the founder-orientation blind pilot, run against v2.2.1."""

    return default_founder_orientation_config(
        instance=FOUNDER_PILOT_INSTANCE_B,
        check_version=FOUNDER_CHECK_VERSION_B,
        lane_relative=FOUNDER_LANE_RELATIVE_B,
        author_ordinals=("03", "04"),
        reviewer_ordinal="02",
    )


def default_founder_orientation_c_config() -> EnvelopeConfig:
    """Instance c of the founder-orientation blind pilot, run against v2.2.2."""

    return default_founder_orientation_config(
        instance=FOUNDER_PILOT_INSTANCE_C,
        check_version=FOUNDER_CHECK_VERSION_C,
        lane_relative=FOUNDER_LANE_RELATIVE_C,
        author_ordinals=("05", "06"),
        reviewer_ordinal="03",
    )


ENVELOPE_CONFIGS = {
    "complete-domain": default_complete_domain_config,
    "founder-orientation": default_founder_orientation_config,
    "founder-orientation-b": default_founder_orientation_b_config,
    "founder-orientation-c": default_founder_orientation_c_config,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--envelope",
        choices=sorted(ENVELOPE_CONFIGS),
        default="complete-domain",
        help="Envelope configuration to drive; omit for the complete-domain envelope.",
    )
    parser.add_argument(
        "--step",
        action="append",
        choices=["authoring", "intake", "review", "labels", "detector"],
        help="Steps to run; omit to run every step not yet in the manifest.",
    )
    arguments = parser.parse_args()
    config = ENVELOPE_CONFIGS[arguments.envelope]()
    results = run_pipeline(arguments.project_root.resolve(), config, arguments.step)
    for step, artifact in results.items():
        digest = artifact.get("ledger_digest") or artifact.get("protocol_digest")
        print(f"{step}: {digest}")
        if step == "detector":
            print(json.dumps(artifact["pilot_metrics"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
