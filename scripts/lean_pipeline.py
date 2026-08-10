"""ADR-0068 lean-pipeline driver for the active complete-domain envelope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sc_referee_evaluation.lean_pipeline import (
    DEFAULT_ALLOWED_IMPORT_ROOTS,
    DEPENDENCE_RECOGNITION_CHECK_ID,
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

# Pilot d is the same envelope, the same briefs and the same discipline once
# more, run against the v2.2.4 recognizer that closed the pilot-c miss. The
# check version is the one the scientific-check manifest registry carries for
# this check id, and the lane directory and the envelope id are built from it by
# the same f-string convention pilots a, b and c used. The actor labels are
# fresh so no earlier participant record is reused; reviewer calibration
# resolves by (model id, pinned binary version, calibration suite) from the
# shared registry, exactly as before.
FOUNDER_CHECK_VERSION_D = "2.2.4"
FOUNDER_PILOT_INSTANCE_D = "d"
FOUNDER_LANE_RELATIVE_D = Path(
    "evaluation/qualification/"
    f"founder-orientation-before-hmm-emission-v{FOUNDER_CHECK_VERSION_D}-lane"
)

# Pilot e is the same envelope, the same briefs and the same discipline once
# more, run against the v2.2.6 recognizer that closed the pilot-d miss. The
# check version is the one the scientific-check manifest registry carries for
# this check id, and the lane directory and the envelope id are built from it by
# the same f-string convention pilots a, b, c and d used. The actor labels are
# fresh so no earlier participant record is reused; reviewer calibration
# resolves by (model id, pinned binary version, calibration suite) from the
# shared registry, exactly as before.
FOUNDER_CHECK_VERSION_E = "2.2.6"
FOUNDER_PILOT_INSTANCE_E = "e"
FOUNDER_LANE_RELATIVE_E = Path(
    "evaluation/qualification/"
    f"founder-orientation-before-hmm-emission-v{FOUNDER_CHECK_VERSION_E}-lane"
)

# Pilot f is the same envelope, the same briefs and the same discipline once
# more, but the detector set under it is now fused. Two adapters are installed
# under this check id: the frozen v2.2.6 dataflow recognizer that pilots a-e
# exercised, and a new v3.1.1 semantic shadow recognizer. The module reducer
# treats a disagreement between the two applicable adapters as ambiguous, and
# either applicable adapter can drive the single module operand; the check stays
# question-only and emits no Finding.
#
# The version string in the lane and envelope names is derived here exactly the
# way pilots a-e derived theirs: from the scientific-check manifest registry, at
# run configuration time. Pilots a-e read the module's check_version, which the
# registry still carries as 2.2.6 for this fused module. That string no longer
# names what is under test, because the fused module bumped no check_version
# when it gained the second adapter. The recognizer whose generalization pilot f
# measures is the v3 semantic shadow adapter, so instance f mirrors the same
# registry derivation against that adapter's adapter_version (3.1.1) and records
# it in a semantic-named lane, so the lane states the recognizer version it
# actually exercised rather than the unchanged module version.
_FOUNDER_REGISTRY_RELATIVE = Path(
    "src/sc_referee/resources/scientific-check-manifests-v1/registry.json"
)
_FOUNDER_SEMANTIC_ADAPTER_ID_SUFFIX = "orientation-semantic-v3"


def _founder_semantic_adapter_version() -> str:
    """Return the v3 semantic shadow recognizer's adapter_version from the registry."""

    registry_path = Path(__file__).resolve().parent.parent / _FOUNDER_REGISTRY_RELATIVE
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    module = next(item for item in registry["modules"] if item["check_id"] == FOUNDER_CHECK_ID)
    adapter = next(
        item
        for item in module["adapters"]
        if str(item["adapter_id"]).endswith(_FOUNDER_SEMANTIC_ADAPTER_ID_SUFFIX)
    )
    return str(adapter["adapter_version"])


FOUNDER_SEMANTIC_ADAPTER_VERSION_F = _founder_semantic_adapter_version()
FOUNDER_PILOT_INSTANCE_F = "f"
FOUNDER_LANE_RELATIVE_F = Path(
    "evaluation/qualification/"
    f"founder-orientation-semantic-v{FOUNDER_SEMANTIC_ADAPTER_VERSION_F}-lane"
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
    escalation_ordinal: str | None = None,
) -> EnvelopeConfig:
    slug = f"founder-{instance}"
    first_author, second_author = author_ordinals
    # The two reviewer ordinals move independently so that retiring a spent
    # primary identity never renames an escalation reviewer that has observed
    # nothing. Omitting the escalation ordinal keeps the pilot-a, b and c
    # behavior exactly: both reviewers carry the same ordinal.
    escalation_ordinal = reviewer_ordinal if escalation_ordinal is None else escalation_ordinal
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
            participant_id=f"actor:{slug}-reviewer-opus-{escalation_ordinal}",
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


def default_founder_orientation_d_config() -> EnvelopeConfig:
    """Instance d of the founder-orientation blind pilot, run against v2.2.4.

    The primary reviewer ordinal is 05 rather than 04 because pilot d's first
    review attempt is retired. That attempt, actor:founder-d-reviewer-fable-04,
    completed its single model call and then failed deterministic projection:
    one quoted evidence span was a hybrid of two adjacent rows of the staged
    CSV and so matched no line of any visible file, and the frozen projector
    failed closed on it. Under the envelope-10 precedent a failed attempt is
    retired rather than repaired: its process capture stays in the lane, its
    packets are moved aside by the pipeline into packets-primary-retired, and
    the cases, which that attempt's model never had a recorded verdict over,
    are reviewed once more by an identity that has seen nothing.

    Re-firing the retained call is forbidden, and the fresh participant id is
    what makes it impossible here rather than merely disallowed. The process
    capture directory, the session identity and the transmitted prompt are all
    keyed by participant, so attempt 2 cannot land on attempt 1's retained
    bytes: it gets its own capture path, and the retained-call reuse check
    binds a capture to one exact prompt digest and participant id.

    The escalation reviewer keeps ordinal 04. It never ran in attempt 1 and
    never observed a case, so its identity is unspent and a rename would only
    obscure that. Calibration resolves by (model id, pinned binary version,
    calibration suite), so the fresh primary identity reuses the same passing
    fable calibration entry without re-running the suite.
    """

    return default_founder_orientation_config(
        instance=FOUNDER_PILOT_INSTANCE_D,
        check_version=FOUNDER_CHECK_VERSION_D,
        lane_relative=FOUNDER_LANE_RELATIVE_D,
        author_ordinals=("07", "08"),
        reviewer_ordinal="05",
        escalation_ordinal="04",
    )


def default_founder_orientation_e_config() -> EnvelopeConfig:
    """Instance e of the founder-orientation blind pilot, run against v2.2.6.

    Both reviewer ordinals are fresh and neither has observed a case. The
    escalation reviewer takes 05 rather than repeating pilot d's 04: the two
    ordinals moved apart in pilot d, so continuing each from its own last
    issued value is what keeps a spent identity from being reused.

    The primary reviewer's single call completed and projected on the first
    attempt, so the pilot-d retired-attempt precedent was not invoked here and
    this lane holds no retirement disclosure.
    """

    return default_founder_orientation_config(
        instance=FOUNDER_PILOT_INSTANCE_E,
        check_version=FOUNDER_CHECK_VERSION_E,
        lane_relative=FOUNDER_LANE_RELATIVE_E,
        author_ordinals=("09", "10"),
        reviewer_ordinal="06",
        escalation_ordinal="05",
    )


def default_founder_orientation_f_config() -> EnvelopeConfig:
    """Instance f of the founder-orientation blind pilot, run against the fused set.

    The check id now carries two installed adapters: the frozen v2.2.6 dataflow
    recognizer and the new v3.1.1 semantic shadow recognizer. The authoring step
    freezes the whole registry module into the detector tuple, so both adapters
    run in the one detector observation and the module reducer combines them:
    disagreement between two applicable adapters is ambiguous, and either
    applicable adapter can drive the single question-only module operand.

    The lane and envelope version string is the v3 semantic adapter_version read
    from the registry (see _founder_semantic_adapter_version), not the module's
    unchanged 2.2.6 check_version, so the lane records that the v3 shadow
    recognizer is the recognizer under test.

    Authors are opus-11 and opus-12, and the escalation reviewer is opus-06; the
    two reviewer ordinals continue to move independently, as they have since
    pilot d. Reviewer calibration resolves by (model id, pinned binary version,
    calibration suite) from the shared registry, so the fresh identities reuse
    the existing passing calibration entries without re-running the suite.

    The primary reviewer ordinal is 09 rather than 08 because pilot f's first
    review attempt is retired under the envelope-10 retired-attempt precedent.
    That attempt, actor:founder-f-reviewer-fable-08 (session
    164023d9-e564-5108-ae9e-7d821df5b14d), completed its single one-shot call
    transport-clean but returned its batch review payload wrapped in a
    ```json ...``` markdown fence. The frozen review path parses the returned
    text as JSON directly and strips no fence, so the payload could not be
    projected into review records, exactly as a span that matches no visible
    line could not be projected in pilot d. Under the precedent the attempt is
    retired rather than repaired: its process capture stays in the lane as
    retained evidence (review/process-captures/primary-founder-f-reviewer-fable-08),
    its attempt-1 prompt is preserved as review/prompt-primary-attempt-1-retired.txt,
    its rebuilt packets are moved aside by the pipeline into
    review/packets-primary-retired, a retirement disclosure is written at the
    lane root RETIREMENT_ATTEMPT_1.md, and the cases -- over which that attempt's
    model never had a recorded verdict -- are reviewed once more by an identity
    that has seen nothing.

    Re-firing the retained call is forbidden, and the fresh participant id is
    what makes it impossible rather than merely disallowed: the process-capture
    path, the session identity and the transmitted prompt are all keyed by
    participant, so attempt 2 gets its own capture path and cannot land on
    attempt 1's retained bytes. The escalation reviewer keeps ordinal 06: it
    never ran in attempt 1 and observed no case, so its identity is unspent and
    a rename would only obscure that.
    """

    return default_founder_orientation_config(
        instance=FOUNDER_PILOT_INSTANCE_F,
        check_version=FOUNDER_SEMANTIC_ADAPTER_VERSION_F,
        lane_relative=FOUNDER_LANE_RELATIVE_F,
        author_ordinals=("11", "12"),
        reviewer_ordinal="09",
        escalation_ordinal="06",
    )


# ---------------------------------------------------------------------------
# Envelope 7: authorized independent-unit entry into a row-independent
# procedure. This is the first blind dependence-recognition pilot envelope.
# The authored workflow is deliberately smaller than the registered static
# recognizer's v1 bounds, and authored code runs only in the separately managed
# SciPy 1.14.0 qualification runtime named below. The project environment is
# never extended with the pilot dependency.

DEPENDENCE_CHECK_VERSION = "1.1.0"
DEPENDENCE_PILOT_INSTANCE = "a"
DEPENDENCE_LANE_RELATIVE = Path(
    "evaluation/qualification/"
    f"authorized-independent-unit-entry-into-row-independent-procedure-v"
    f"{DEPENDENCE_CHECK_VERSION}-lane/pilot-{DEPENDENCE_PILOT_INSTANCE}"
)
DEPENDENCE_SANDBOX_PYTHON = Path(
    "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime/scipy114-venv/bin/python"
)

_DEPENDENCE_COMMON_TASK = (
    "Choose a neutral scientific subject area and instantiate the assigned small table. "
    "Treat `k1`, `k2`, and `tag` as opaque codes and `a` and `b` as two finite numeric "
    "measurements. Apply the procedure named in the case instructions to the complete staged "
    "row sequence and write its single selected result."
)

_DEPENDENCE_AUTHORIZED_TASK = (
    "Apply the named procedure to the complete staged row sequence. Treat each distinct "
    "ordered `k1`,`k2` pair as one source item; rows carrying the same ordered pair originate "
    "from the same source item."
)
_DEPENDENCE_AMBIGUOUS_TASK = (
    "Apply the named procedure to the complete staged row sequence. Treat every code as "
    "opaque; this task does not establish which code or ordered code tuple denotes one source "
    "item."
)

_DEPENDENCE_BASE_VECTOR_GUIDANCE = (
    "Use `a` values in row order `1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, "
    "10.0, 11.0, 12.0` and corresponding `b` values `2.0, 4.0, 3.0, 5.0, 7.0, "
    "6.0, 9.0, 8.0, 11.0, 10.0, 13.0, 12.0`."
)
_DEPENDENCE_TTEST_UNIQUE_RESULT = (
    "TtestResult(statistic=np.float64(-0.6793662204867575), "
    "pvalue=np.float64(0.5039915691282064), df=np.float64(22.0))"
)
_DEPENDENCE_TTEST_DUPLICATED_RESULT = (
    "TtestResult(statistic=np.float64(-0.9823619317924353), "
    "pvalue=np.float64(0.33106037814548595), df=np.float64(46.0))"
)
_DEPENDENCE_MANN_WHITNEY_RESULT = (
    "MannwhitneyuResult(statistic=np.float64(60.5), pvalue=np.float64(0.5243792697676437))"
)
_DEPENDENCE_PAIRED_RESULT = (
    "TtestResult(statistic=np.float64(-3.63318042491699), "
    "pvalue=np.float64(0.00393470596182021), df=np.int64(11))"
)

_DEPENDENCE_ROLE_CONSTRAINTS = {
    "error_bearing": [
        "Use exactly 24 data rows formed from twelve ordered pairs `u01,v01` through "
        "`u12,v12`; place each pair in two consecutive rows, with the same `tag`, `a`, and "
        "`b` values in both copies.",
        _DEPENDENCE_BASE_VECTOR_GUIDANCE
        + " Duplicate each corresponding numeric row consecutively when constructing the "
        "24-row table.",
        "Use `tag` values `t01` through `t12`, repeating each tag with its duplicated pair.",
        "Call `scipy.stats.ttest_ind`.",
        "The exact SciPy 1.14.0 result text for these duplicated vectors is `"
        + _DEPENDENCE_TTEST_DUPLICATED_RESULT
        + "`; the report must be `[selected-result] ` followed by exactly that text.",
    ],
    "corrected_twin": [
        "Use exactly the same twelve source items, ordered pairs `u01,v01` through `u12,v12`, "
        "numeric values, and tags as your other assigned case, but stage each pair exactly "
        "once for a total of 12 data rows.",
        _DEPENDENCE_BASE_VECTOR_GUIDANCE,
        "Use `tag` values `t01` through `t12`, one per row.",
        "Call `scipy.stats.ttest_ind`.",
        "The exact SciPy 1.14.0 result text for these vectors is `"
        + _DEPENDENCE_TTEST_UNIQUE_RESULT
        + "`; the report must be `[selected-result] ` followed by exactly that text.",
    ],
    "valid_alternative": [
        "Use exactly 12 data rows with unique ordered pairs `u01,v01` through `u12,v12`.",
        _DEPENDENCE_BASE_VECTOR_GUIDANCE,
        "Use unique `tag` values `t01` through `t12`.",
        "Call `scipy.stats.mannwhitneyu`.",
        "The exact SciPy 1.14.0 result text for these vectors is `"
        + _DEPENDENCE_MANN_WHITNEY_RESULT
        + "`; the report must be `[selected-result] ` followed by exactly that text.",
    ],
    "hard_negative": [
        "Use exactly 12 data rows with unique ordered pairs `u01,v01` through `u12,v12`.",
        _DEPENDENCE_BASE_VECTOR_GUIDANCE,
        "Use the identical `tag` value `shared` in every row; only `tag` repeats.",
        "Call `scipy.stats.ttest_ind`.",
        "The exact SciPy 1.14.0 result text for these vectors is `"
        + _DEPENDENCE_TTEST_UNIQUE_RESULT
        + "`; the report must be `[selected-result] ` followed by exactly that text.",
    ],
    "ambiguous": [
        "Use exactly 12 data rows. Make each ordered `k1`,`k2` pair unique, repeat every `k1` "
        "value twice, repeat every `k2` value three times in a crossing pattern, and repeat "
        "`tag` values without identifying any of those codes as a source-item key.",
        _DEPENDENCE_BASE_VECTOR_GUIDANCE,
        "Call `scipy.stats.ttest_ind`.",
        "The exact SciPy 1.14.0 result text for these vectors is `"
        + _DEPENDENCE_TTEST_UNIQUE_RESULT
        + "`; the report must be `[selected-result] ` followed by exactly that text.",
    ],
    "unsupported": [
        "Use exactly 12 data rows with unique ordered pairs `u01,v01` through `u12,v12`.",
        _DEPENDENCE_BASE_VECTOR_GUIDANCE,
        "Use unique `tag` values `t01` through `t12`.",
        "Call `scipy.stats.ttest_rel`.",
        "The exact SciPy 1.14.0 result text for these vectors is `"
        + _DEPENDENCE_PAIRED_RESULT
        + "`; the report must be `[selected-result] ` followed by exactly that text.",
    ],
}

_DEPENDENCE_TASK_BY_ROLE = {
    role: (_DEPENDENCE_AMBIGUOUS_TASK if role == "ambiguous" else _DEPENDENCE_AUTHORIZED_TASK)
    for role in _DEPENDENCE_ROLE_CONSTRAINTS
}
_DEPENDENCE_EXPECTED_VERDICT_BY_ROLE = {
    "error_bearing": "demonstrated_issue",
    "corrected_twin": "no_demonstrated_issue_within_scope",
    "valid_alternative": "no_demonstrated_issue_within_scope",
    "hard_negative": "no_demonstrated_issue_within_scope",
    "ambiguous": "no_demonstrated_issue_within_scope",
    "unsupported": "no_demonstrated_issue_within_scope",
}
_DEPENDENCE_LABEL_STATUS_BY_ROLE = {
    "error_bearing": "positive_demonstrated",
    "corrected_twin": "verified_good_eligible",
    "valid_alternative": "verified_good_eligible",
    "hard_negative": "verified_good_eligible",
    "ambiguous": "ambiguous_control",
    "unsupported": "unsupported_control",
}

_DEPENDENCE_CASE_REQUIREMENTS = """Produce exactly the three authored files requested by the response schema. The pipeline supplies `requirements.txt`; do not return or reproduce it.

`inputs/data.csv` must be ASCII CSV with exact header `k1,k2,tag,a,b`. Use the data-row count and key pattern specified by the case. Every field must be nonempty, and `a` and `b` must contain finite decimal literals.

`workflow/analysis.py` must consist only of module-level imports and assignments in the following forms:

- Import `csv`, `Path` from `pathlib`, and one direct `scipy.stats` binding.
- Bind `rows` using exactly one of:
  - `rows = list(csv.DictReader(Path("inputs/data.csv").read_text(encoding="utf-8").splitlines()))`
  - `rows = list(csv.DictReader(Path("inputs/data.csv").open(newline="", encoding="utf-8")))`
- Zero or more row-sequence aliases may use only `alias = rows` or `alias, = rows,`.
- Build the two procedure vectors as complete ordered projections:
  - `left = [float(row["a"]) for row in <row-sequence>]`
  - `right = [float(row["b"]) for row in <row-sequence>]`
- Bind `result` by calling exactly the procedure named in the case: `scipy.stats.ttest_ind`, `scipy.stats.mannwhitneyu`, or `scipy.stats.ttest_rel`. The call must have exactly `left` and `right` as two positional arguments and no keyword arguments.
- Write the sole report directly with:
  - `Path("results/report.md").write_text(f"[selected-result] {result}\n", encoding="utf-8")`

Do not filter, slice, sample, merge, aggregate, deduplicate, mutate, or loop-build the row sequence. Do not use helper functions, branches, exception handling, randomness, clocks, network access, command-line arguments, environment variables, or any other read or write.

`results/report.md` must be ASCII, contain exactly the one `[selected-result]` line written by the script, and equal the SciPy 1.14.0 output byte-for-byte."""


def default_dependence_config() -> EnvelopeConfig:
    """Return the first six-role dependence-recognition blind-pilot envelope."""

    slug = f"dependence-{DEPENDENCE_PILOT_INSTANCE}"
    first_author = f"actor:{slug}-author-opus-13"
    second_author = f"actor:{slug}-author-opus-14"
    return EnvelopeConfig(
        envelope_id=(
            "authorized-independent-unit-entry-into-row-independent-procedure-"
            f"v{DEPENDENCE_CHECK_VERSION}-lean-{DEPENDENCE_PILOT_INSTANCE}"
        ),
        pipeline_relative=DEPENDENCE_LANE_RELATIVE,
        check_id=DEPENDENCE_RECOGNITION_CHECK_ID,
        canonical_issue_class=(
            "issue-class:repeated-authorized-independent-unit-entry-into-row-independent-procedure"
        ),
        candidate_by_role={
            role: "one-analyzed-row-per-authorized-independent-unit"
            for role in _DEPENDENCE_ROLE_CONSTRAINTS
            if role != "ambiguous"
        },
        task_by_role=dict(_DEPENDENCE_TASK_BY_ROLE),
        role_constraints={
            role: list(items) for role, items in _DEPENDENCE_ROLE_CONSTRAINTS.items()
        },
        common_task=_DEPENDENCE_COMMON_TASK,
        authors={
            first_author: ModelParticipant(
                participant_id=first_author,
                model_id="claude-opus-5",
                model_name="Claude Opus 5",
                model_alias="claude-opus-5",
            ),
            second_author: ModelParticipant(
                participant_id=second_author,
                model_id="claude-opus-5",
                model_name="Claude Opus 5",
                model_alias="claude-opus-5",
            ),
        },
        author_roles={
            first_author: ["error_bearing", "corrected_twin"],
            second_author: [
                "valid_alternative",
                "hard_negative",
                "ambiguous",
                "unsupported",
            ],
        },
        reviewer=ModelParticipant(
            participant_id=f"actor:{slug}-reviewer-fable-10",
            model_id="claude-fable-5",
            model_name="Claude Fable 5",
            model_alias="fable",
        ),
        escalation_reviewer=ModelParticipant(
            participant_id=f"actor:{slug}-reviewer-opus-07",
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        ),
        review_instructions=_REVIEW_INSTRUCTIONS,
        cli_binary=CLAUDE_PINNED,
        cli_binary_version=CLAUDE_PINNED_VERSION,
        calibration_suite=CALIBRATION_SUITE,
        author_case_requirements=_DEPENDENCE_CASE_REQUIREMENTS,
        expected_verdict_by_role=dict(_DEPENDENCE_EXPECTED_VERDICT_BY_ROLE),
        label_status_by_role=dict(_DEPENDENCE_LABEL_STATUS_BY_ROLE),
        mq_tolerant_roles={"ambiguous"},
        contract_free_roles={"ambiguous"},
        allowed_import_roots=DEFAULT_ALLOWED_IMPORT_ROOTS | {"scipy"},
        sandbox_python=DEPENDENCE_SANDBOX_PYTHON,
        required_sandbox_distributions={"scipy": "1.14.0"},
        controller_material_files={"requirements.txt": b"scipy==1.14.0\n"},
        material_input_paths=("inputs/data.csv", "requirements.txt"),
        input_csv_row_bounds=(1, 64),
    )


ENVELOPE_CONFIGS = {
    "complete-domain": default_complete_domain_config,
    "dependence": default_dependence_config,
    "founder-orientation": default_founder_orientation_config,
    "founder-orientation-b": default_founder_orientation_b_config,
    "founder-orientation-c": default_founder_orientation_c_config,
    "founder-orientation-d": default_founder_orientation_d_config,
    "founder-orientation-e": default_founder_orientation_e_config,
    "founder-orientation-f": default_founder_orientation_f_config,
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
        choices=["authoring", "intake", "authority", "review", "labels", "detector"],
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
