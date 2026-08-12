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
# procedure. This is the second blind dependence-recognition pilot envelope.
# The authored workflow is deliberately smaller than the registered static
# recognizer's v1 bounds, and authored code runs only in the separately managed
# SciPy 1.14.0 qualification runtime named below. The project environment is
# never extended with the pilot dependency.

DEPENDENCE_CHECK_VERSION = "1.1.0"
DEPENDENCE_PILOT_INSTANCE = "d"
DEPENDENCE_LANE_RELATIVE = Path(
    "evaluation/qualification/"
    f"authorized-independent-unit-entry-into-row-independent-procedure-v"
    f"{DEPENDENCE_CHECK_VERSION}-lane/pilot-{DEPENDENCE_PILOT_INSTANCE}"
)
DEPENDENCE_SANDBOX_PYTHON = Path(
    "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime/scipy114-venv/bin/python"
)
_DEPENDENCE_REVIEW_INSTRUCTIONS = """You are one independent blind scientific reviewer for opaque analysis
workspaces. For each case you see exactly four files: the governing task, the staged input
data, the workflow source, and the produced report. Determine independently for each case
whether the in-scope issue class {issue_class} is demonstrably present in the selected report,
using only the visible files. Attempt to falsify your own verdict and report that attempt in
the required fields. Do not guess unstated intentions. Judge only whether this exact issue class
is demonstrated in the selected report. Other methodological concerns, however serious, are
outside this review and must not be recorded as this issue class. Raise unresolved material
questions only when a genuinely blocking ambiguity remains."""

_DEPENDENCE_COMMON_TASK = (
    "Treat `k1`, `k2`, and `tag` only as specified by the governing task and `a` and `b` as "
    "finite numeric measurements. Apply the procedure named in the case instructions to the "
    "complete staged row sequence and write its single selected result."
)

_DEPENDENCE_AUTHORIZED_TASK = (
    "Apply the named procedure to the complete staged row sequence. The table stores two "
    "disjoint collections of source items. `k1` identifies a first-collection source item "
    "measured by column `a`; `k2` identifies a second-collection source item measured by "
    "column `b`. The two collections are disjoint. `tag` is an opaque annotation. The row "
    "pairing is a storage convention only; there is no matching, pairing, block, or other "
    "relationship between the `k1` item and the `k2` item in that row."
)
_DEPENDENCE_AMBIGUOUS_TASK = (
    "Apply the named procedure to the complete staged row sequence. The table stores two "
    "disjoint collections of source items measured by columns `a` and `b`. Treat `k1` and "
    "`k2` as opaque codes; `tag` is an opaque annotation. This task does not establish whether "
    "either code identifies a source item within either collection. The row pairing is a "
    "storage convention only; there is no matching, pairing, block, or other relationship "
    "between the items represented in that row."
)

_DEPENDENCE_FROZEN_WORKFLOW_BODY = """import csv
from pathlib import Path
import scipy.stats as st
rows = list(csv.DictReader(Path("inputs/data.csv").read_text(encoding="utf-8").splitlines()))
staged = rows
left = [float(row["a"]) for row in staged]
right = [float(row["b"]) for row in staged]
result = st.PROCEDURE(left, right)
Path("results/report.md").write_text(f"[selected-result] {result}\\n", encoding="utf-8")
"""
_DEPENDENCE_FROZEN_WORKFLOW_TEMPLATE = _DEPENDENCE_FROZEN_WORKFLOW_BODY.replace(
    "PROCEDURE", "{procedure}"
)
_DEPENDENCE_FROZEN_PROCEDURE_BY_ROLE = {
    "error_bearing": "ttest_ind",
    "corrected_twin": "ttest_ind",
    "valid_alternative": "mannwhitneyu",
    "hard_negative": "ttest_ind",
    "ambiguous": "ttest_ind",
    "unsupported": "ttest_rel",
}

_DEPENDENCE_BASE_VECTOR_GUIDANCE = (
    "Use `a` values in row order `1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, "
    "10.0, 11.0, 12.0` and corresponding `b` values `2.0, 4.0, 3.0, 5.0, 7.0, "
    "6.0, 9.0, 8.0, 11.0, 10.0, 13.0, 12.0`."
)
_DEPENDENCE_ERROR_KEY_GUIDANCE = (
    "Use exactly these 24 `k1,k2,tag` triples in row order: `u01,v07,t01`; "
    "`u01,v08,t02`; `u02,v09,t03`; `u02,v10,t04`; `u03,v11,t05`; "
    "`u03,v12,t06`; `u04,v13,t07`; `u04,v14,t08`; `u05,v15,t09`; "
    "`u05,v16,t10`; `u06,v17,t11`; `u06,v18,t12`; `u07,v19,t13`; "
    "`u07,v20,t14`; `u08,v21,t15`; `u08,v22,t16`; `u09,v23,t17`; "
    "`u09,v24,t18`; `u10,v01,t19`; `u10,v02,t20`; `u11,v03,t21`; "
    "`u11,v04,t22`; `u12,v05,t23`; `u12,v06,t24`. Every `k2` and `tag` "
    "is distinct, and no row has matching numeric suffixes for `k1` and `k2`."
)
_DEPENDENCE_ERROR_VECTOR_GUIDANCE = (
    "Use `a` values in row order `1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, "
    "5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, "
    "11.0, 11.5, 12.0, 12.5` and corresponding `b` values `2.0, 2.25, 4.0, "
    "4.25, 3.0, 3.25, 5.0, 5.25, 7.0, 7.25, 6.0, 6.25, 9.0, 9.25, 8.0, "
    "8.25, 11.0, 11.25, 10.0, 10.25, 13.0, 13.25, 12.0, 12.25`. Each "
    "repeated `k1` therefore carries two different `a` measurements."
)
_DEPENDENCE_TWIN_KEY_GUIDANCE = (
    "Use exactly these 12 `k1,k2,tag` triples in row order, taking the first row "
    "of each repeated unit from the error construction: `u01,v07,t01`; "
    "`u02,v09,t03`; `u03,v11,t05`; `u04,v13,t07`; `u05,v15,t09`; "
    "`u06,v17,t11`; `u07,v19,t13`; `u08,v21,t15`; `u09,v23,t17`; "
    "`u10,v01,t19`; `u11,v03,t21`; `u12,v05,t23`. Every key in each "
    "namespace and every tag is distinct, with no same-suffix `k1`,`k2` row."
)
_DEPENDENCE_HARD_KEY_GUIDANCE = (
    "Use exactly these 24 `k1,k2,tag` triples in row order: `u07,v12,t01`; "
    "`u08,v13,t02`; `u09,v14,t03`; `u10,v15,t04`; `u11,v16,t05`; "
    "`u12,v17,t06`; `u01,v18,t07`; `u02,v19,t08`; `u03,v20,t09`; "
    "`u06,v21,t10`; `u05,v22,t11`; `u04,v23,t12`; `u19,v24,t13`; "
    "`u20,v01,t14`; `u21,v02,t15`; `u22,v03,t16`; `u23,v04,t17`; "
    "`u24,v05,t18`; `u13,v06,t19`; `u14,v07,t20`; `u15,v08,t21`; "
    "`u18,v09,t22`; `u17,v10,t23`; `u16,v11,t24`. Every `k1`, `k2`, "
    "and tag is distinct, and no row has matching numeric suffixes for `k1` "
    "and `k2`."
)
_DEPENDENCE_TTEST_UNIQUE_RESULT = (
    "TtestResult(statistic=np.float64(-0.6793662204867575), "
    "pvalue=np.float64(0.5039915691282064), df=np.float64(22.0))"
)
_DEPENDENCE_TTEST_REPEATED_MEASUREMENT_RESULT = (
    "TtestResult(statistic=np.float64(-0.8581613266497022), "
    "pvalue=np.float64(0.3952529117073811), df=np.float64(46.0))"
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
        _DEPENDENCE_ERROR_KEY_GUIDANCE,
        _DEPENDENCE_ERROR_VECTOR_GUIDANCE,
        "Call `scipy.stats.ttest_ind`.",
        "The exact SciPy 1.14.0 result text for these repeated-measurement vectors is `"
        + _DEPENDENCE_TTEST_REPEATED_MEASUREMENT_RESULT
        + "`; the report must be `[selected-result] ` followed by exactly that text.",
    ],
    "corrected_twin": [
        _DEPENDENCE_TWIN_KEY_GUIDANCE,
        _DEPENDENCE_BASE_VECTOR_GUIDANCE,
        "Call `scipy.stats.ttest_ind`.",
        "The exact SciPy 1.14.0 result text for these vectors is `"
        + _DEPENDENCE_TTEST_UNIQUE_RESULT
        + "`; the report must be `[selected-result] ` followed by exactly that text.",
    ],
    "valid_alternative": [
        _DEPENDENCE_TWIN_KEY_GUIDANCE,
        _DEPENDENCE_BASE_VECTOR_GUIDANCE,
        "Call `scipy.stats.mannwhitneyu`.",
        "The exact SciPy 1.14.0 result text for these vectors is `"
        + _DEPENDENCE_MANN_WHITNEY_RESULT
        + "`; the report must be `[selected-result] ` followed by exactly that text.",
    ],
    "hard_negative": [
        _DEPENDENCE_HARD_KEY_GUIDANCE,
        _DEPENDENCE_ERROR_VECTOR_GUIDANCE,
        "Call `scipy.stats.ttest_ind`.",
        "The exact SciPy 1.14.0 result text for these vectors is `"
        + _DEPENDENCE_TTEST_REPEATED_MEASUREMENT_RESULT
        + "`; the report must be `[selected-result] ` followed by exactly that text.",
    ],
    "ambiguous": [
        "Use exactly these 12 `k1,k2,tag` triples in row order: `u01,v07,t01`; "
        "`u01,v11,t02`; `u02,v06,t03`; `u02,v09,t04`; `u03,v01,t05`; "
        "`u03,v12,t06`; `u04,v05,t07`; `u04,v03,t08`; `u05,v10,t09`; "
        "`u05,v04,t10`; `u06,v08,t11`; `u06,v02,t12`. The `k2` order "
        "`v07,v11,v06,v09,v01,v12,v05,v03,v10,v04,v08,v02` is the clean-key "
        "derangement with positions 3 and 12 exchanged so no row's `k1` and `k2` numeric "
        "suffixes coincide. Do not substitute any "
        "author-chosen string for `k1`, `k2`, or `tag`.",
        _DEPENDENCE_BASE_VECTOR_GUIDANCE,
        "Call `scipy.stats.ttest_ind`.",
        "The exact SciPy 1.14.0 result text for these vectors is `"
        + _DEPENDENCE_TTEST_UNIQUE_RESULT
        + "`; the report must be `[selected-result] ` followed by exactly that text.",
    ],
    "unsupported": [
        _DEPENDENCE_TWIN_KEY_GUIDANCE,
        _DEPENDENCE_BASE_VECTOR_GUIDANCE,
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

_DEPENDENCE_CASE_REQUIREMENTS = (
    """Produce exactly the three authored files requested by the response schema. The pipeline supplies `requirements.txt`; do not return or reproduce it.

`inputs/data.csv` must be ASCII CSV with exact header `k1,k2,tag,a,b`. Use the data-row count and key pattern specified by the case. Every field must be nonempty, and `a` and `b` must contain finite decimal literals.

workflow/analysis.py must consist of exactly these lines, byte for byte, with PROCEDURE replaced by the procedure named in your case instructions and nothing else changed:

```python
"""
    + _DEPENDENCE_FROZEN_WORKFLOW_BODY
    + """```

`results/report.md` must be ASCII, contain exactly the one `[selected-result]` line written by the script, and equal the SciPy 1.14.0 output byte-for-byte."""
)


def default_dependence_config() -> EnvelopeConfig:
    """Return the pilot-d six-role dependence-recognition blind-pilot envelope.

    Pilot-d carries forward pilot-b's correction of commit fc91a19: the official
    primary and escalation reviewers were unanimous against the answer key,
    and the retired attempt's verdicts are void.  Its added out-of-scope
    review sentence has a known one-directional effect, bearing mostly on the
    ``ttest_rel`` case.  A ``covered_negative`` result in this envelope is
    scoped only to the authorized ``k1`` namespace.
    """

    slug = f"dependence-{DEPENDENCE_PILOT_INSTANCE}"
    first_author = f"actor:{slug}-author-opus-19"
    second_author = f"actor:{slug}-author-opus-20"
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
        # Fable-11 was spent reviewing pilot-c, so pilot-d advances to fable-12.
        # Opus-09 fired and was spent in pilot-c; this frozen pilot-d config records its seat.
        reviewer=ModelParticipant(
            participant_id=f"actor:{slug}-reviewer-fable-12",
            model_id="claude-fable-5",
            model_name="Claude Fable 5",
            model_alias="fable",
        ),
        escalation_reviewer=ModelParticipant(
            participant_id=f"actor:{slug}-reviewer-opus-09",
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        ),
        review_instructions=_DEPENDENCE_REVIEW_INSTRUCTIONS,
        cli_binary=CLAUDE_PINNED,
        cli_binary_version=CLAUDE_PINNED_VERSION,
        calibration_suite=CALIBRATION_SUITE,
        author_case_requirements=_DEPENDENCE_CASE_REQUIREMENTS,
        expected_verdict_by_role=dict(_DEPENDENCE_EXPECTED_VERDICT_BY_ROLE),
        label_status_by_role=dict(_DEPENDENCE_LABEL_STATUS_BY_ROLE),
        mq_tolerant_roles={"ambiguous", "unsupported"},
        contract_free_roles={"ambiguous"},
        allowed_import_roots=DEFAULT_ALLOWED_IMPORT_ROOTS | {"scipy"},
        sandbox_python=DEPENDENCE_SANDBOX_PYTHON,
        required_sandbox_distributions={"numpy": "2.2.6", "scipy": "1.14.0"},
        controller_material_files={"requirements.txt": b"numpy==2.2.6\nscipy==1.14.0\n"},
        material_input_paths=("inputs/data.csv", "requirements.txt"),
        input_csv_row_bounds=(1, 64),
        required_input_csv_header=("k1", "k2", "tag", "a", "b"),
        frozen_workflow_template=_DEPENDENCE_FROZEN_WORKFLOW_TEMPLATE,
        frozen_workflow_procedure_by_role=dict(_DEPENDENCE_FROZEN_PROCEDURE_BY_ROLE),
    )


# ---------------------------------------------------------------------------
# Dependence generalization growth loop, batch A. This development-only free
# envelope measures the shipped recognizer without dictating source grammar.

DEPENDENCE_FREE_LANE_RELATIVE = Path("evaluation/development/dependence-growth-loop/batch-a")
_DEPENDENCE_FREE_ROLES = ("rq1", "rq2", "rq3", "rq4", "rq5", "rq6")
_DEPENDENCE_FREE_COMMON_TASK = """Study one narrowly defined error class: repeated measurements from the same independent unit entered into a row-independent statistical procedure as if independent. Invent the scientific domain, study story, vocabulary, column names, data values, number of rows, and coding style yourself. Do not copy any prior-lane material.

Build a real runnable Python analysis that reads exactly `data/input.csv` and writes `results/report.md`, stating the analysis and its result. Also provide `data-description.md`, with exactly one closed-syntax line `One row is: DESCRIPTION` and exactly one line `Independent unit column: COLUMN`, replacing DESCRIPTION with plain language and COLUMN with the actual single header name.

Do not mention sc-referee or any case-role label in any authored artifact. The Python module must execute cleanly and deterministically in the pinned SciPy runtime. No workflow template, reader idiom, procedure, literals, or source structure is prescribed."""
_DEPENDENCE_FREE_CASE_REQUIREMENTS = """Produce exactly four authored files.

`data/input.csv`: one ASCII CSV with a unique nonempty header and nonempty, non-ragged rows. Choose the row count and all names and values yourself.

`workflow/analysis.py`: runnable deterministic Python that reads exactly `data/input.csv`, performs the analysis, and writes exactly `results/report.md`. Use only allowed standard-library imports plus SciPy, NumPy, or statsmodels. Do not read any other file and do not use randomness, the clock, network access, command-line arguments, or dynamic execution.

`results/report.md`: an ASCII report equal byte-for-byte to the script's output. It must contain exactly one line beginning `[selected-result]` and state the analysis and result.

`data-description.md`: an ASCII plain-language description with exactly one line `One row is: DESCRIPTION` and exactly one line `Independent unit column: COLUMN`, replacing DESCRIPTION with what a row represents and COLUMN with the actual single CSV header name.

Return the fourth file in the `data_description` response field. Do not include a frozen workflow template, prescribed data literals, or a prescribed statistical procedure."""
_DEPENDENCE_FREE_ROLE_CONSTRAINTS = {
    "rq1": [
        "Plant the named error: the analyzed rows must include repeated measurements from an independent unit and the selected row-independent procedure must treat those rows as independent.",
        "Make the report honest about the performed analysis without naming this assignment or its role.",
    ],
    "rq2": [
        "Plant the named error independently using your own domain, names, data, procedure, and source style.",
        "The repeated measurements must enter the selected row-independent procedure as separate independent observations.",
    ],
    "rq3": [
        "Plant the named error in a third independently invented workflow.",
        "Ensure the independent-unit column genuinely repeats and the selected report describes the row-independent analysis actually run.",
    ],
    "rq4": [
        "Do not plant the named error. Use a genuinely independent design with exactly one analyzed row per independent unit.",
        "Keep the analysis and report honest and otherwise invent all details freely.",
    ],
    "rq5": [
        "Do not plant the named error. Independently invent another genuinely independent one-row-per-unit design.",
        "Choose your own valid analysis and report its actual result.",
    ],
    "rq6": [
        "Use a realistic long-format or repeated-session storage design in which the units entering the reported claim are genuinely independent with one analyzed row per independent unit.",
        "Write the data description and report as ordinary scientific artifacts for the invented study.",
    ],
}
_DEPENDENCE_FREE_EXPECTED_VERDICTS = {
    role: (
        "demonstrated_issue"
        if role in {"rq1", "rq2", "rq3"}
        else "no_demonstrated_issue_within_scope"
    )
    for role in _DEPENDENCE_FREE_ROLES
}
_DEPENDENCE_FREE_LABEL_STATUSES = {
    role: ("positive_demonstrated" if role in {"rq1", "rq2", "rq3"} else "verified_good_eligible")
    for role in _DEPENDENCE_FREE_ROLES
}


def default_dependence_free_config() -> EnvelopeConfig:
    """Return development-loop batch A; never qualification evidence."""

    authors = {
        f"actor:dependence-free-batch-a-author-opus-{ordinal}": ModelParticipant(
            participant_id=f"actor:dependence-free-batch-a-author-opus-{ordinal}",
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        )
        for ordinal in range(27, 33)
    }
    return EnvelopeConfig(
        envelope_id="development-dependence-growth-loop-batch-a-v1",
        pipeline_relative=DEPENDENCE_FREE_LANE_RELATIVE,
        check_id=DEPENDENCE_RECOGNITION_CHECK_ID,
        canonical_issue_class=(
            "issue-class:repeated-authorized-independent-unit-entry-into-row-independent-procedure"
        ),
        candidate_by_role={
            role: "one-analyzed-row-per-authorized-independent-unit"
            for role in _DEPENDENCE_FREE_ROLES
        },
        task_by_role={role: _DEPENDENCE_FREE_COMMON_TASK for role in _DEPENDENCE_FREE_ROLES},
        role_constraints={
            role: list(_DEPENDENCE_FREE_ROLE_CONSTRAINTS[role]) for role in _DEPENDENCE_FREE_ROLES
        },
        common_task=_DEPENDENCE_FREE_COMMON_TASK,
        authors=authors,
        author_roles={
            participant_id: [role]
            for participant_id, role in zip(sorted(authors), _DEPENDENCE_FREE_ROLES, strict=True)
        },
        reviewer=ModelParticipant(
            participant_id="actor:dependence-free-batch-a-reviewer-fable-16",
            model_id="claude-fable-5",
            model_name="Claude Fable 5",
            model_alias="fable",
        ),
        escalation_reviewer=ModelParticipant(
            participant_id="actor:dependence-free-batch-a-escalation-opus-13",
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        ),
        review_instructions=_DEPENDENCE_REVIEW_INSTRUCTIONS,
        cli_binary=CLAUDE_PINNED,
        cli_binary_version=CLAUDE_PINNED_VERSION,
        calibration_suite=CALIBRATION_SUITE,
        author_case_requirements=_DEPENDENCE_FREE_CASE_REQUIREMENTS,
        expected_verdict_by_role=dict(_DEPENDENCE_FREE_EXPECTED_VERDICTS),
        label_status_by_role=dict(_DEPENDENCE_FREE_LABEL_STATUSES),
        allowed_import_roots=DEFAULT_ALLOWED_IMPORT_ROOTS | {"numpy", "scipy", "statsmodels"},
        sandbox_python=DEPENDENCE_SANDBOX_PYTHON,
        required_sandbox_distributions={"numpy": "2.2.6", "scipy": "1.14.0"},
        controller_material_files={"requirements.txt": b"numpy==2.2.6\nscipy==1.14.0\n"},
        material_input_paths=("data/input.csv", "requirements.txt"),
        input_csv_row_bounds=(1, 10_000),
        authored_data_description_path="data-description.md",
        authored_input_csv_path="data/input.csv",
        allow_unprescribed_input_csv_header=True,
        dependence_authority_from_description=True,
        forbidden_artifact_markers=frozenset({"sc-referee"}),
        record_purpose="development_growth_loop",
        stateless_review_per_case=True,
        hostile_answer_key_reviewer=ModelParticipant(
            participant_id="actor:dependence-free-batch-a-hostile-fable-17",
            model_id="claude-fable-5",
            model_name="Claude Fable 5",
            model_alias="fable",
        ),
        freeze_role_key_in_review_protocol=True,
        halt_on_false_accusation=True,
        publish_count_metrics_only=True,
        authored_role_ratification=True,
        separately_reported_role="rq6",
    )


# ---------------------------------------------------------------------------
# Envelope 8: classifier-derived copy-dosage representation.
#
# Maintainer blanket authorization records the following pilot decisions:
# the registered profile names the already-shipped v2.0.4 grammar; the sandbox
# probe binds the `sklearn` import to the `scikit-learn` distribution; no
# requirements.txt is introduced because the dedicated runtime is prebuilt;
# the prospective audit snapshot digest is opted in for this envelope without
# changing legacy envelopes; and the contract-free role uses the sixth clean
# computational identifier `plain`, rather than reusing the corrected twin's
# identifier or a word that could be read as a role label.
#
# Batched-review disclosure (F2): all six cases share one input file by design,
# so a cross-case reviewer can infer which procedures are no-ops. This known
# limitation understates false-accusation risk rather than creating it.

DOSAGE_CHECK_ID = "check:classifier-derived-copy-dosage-representation"
DOSAGE_CHECK_VERSION = "2.0.4"
DOSAGE_PILOT_INSTANCE = "a"
DOSAGE_LANE_RELATIVE = Path(
    "evaluation/qualification/"
    f"classifier-derived-copy-dosage-representation-v{DOSAGE_CHECK_VERSION}-lane/"
    f"pilot-{DOSAGE_PILOT_INSTANCE}"
)
DOSAGE_SANDBOX_PYTHON = Path(
    "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime/sklearn-venv/bin/python"
)

_DOSAGE_REVIEW_INSTRUCTIONS = _DEPENDENCE_REVIEW_INSTRUCTIONS
_DOSAGE_COMMON_TASK = (
    "Treat `s1` and `s2` only as finite numeric measurements of each staged unit, `level` as "
    "an ordered integer level index recorded for each unit, `anchor` as a finite numeric "
    "reference measurement, and `y` as the recorded outcome. Apply the staged workflow to the "
    "complete staged row sequence and write its single selected result. The workflow fits "
    "several models and computes several candidate calibrated quantities from them; exactly one "
    "of those quantities supplies the association model's exposure position, and the case "
    "instructions name which one. The quantities the case does not name are computed and not "
    "used."
)
_DOSAGE_EXPECTATION_TASK = (
    "Apply the named workflow to the complete staged row sequence. The quantity that enters the "
    "association model's exposure position must be the expected value of the ordered level "
    "index under the sorter's own per-level shares, kept on its continuous scale. A quantity "
    "confined to the finite set of level values does not satisfy this task."
)
_DOSAGE_CALIBRATION_TASK = (
    "Apply the named workflow to the complete staged row sequence. The quantity that enters the "
    "association model's exposure position must be the continuous prediction of the direct "
    "calibration fitted against the supplied anchor measurement. A quantity confined to the "
    "finite set of level values does not satisfy this task."
)
_DOSAGE_WITHHELD_TASK = (
    "Apply the named workflow to the complete staged row sequence. This task does not establish "
    "which of the workflow's calibrated quantities supplies the association model's exposure "
    "position."
)

_DOSAGE_FROZEN_WORKFLOW_BODY = """import csv
from pathlib import Path
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression, RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

rows = list(csv.DictReader(Path("inputs/data.csv").read_text(encoding="utf-8").splitlines()))
first = [float(row["s1"]) for row in rows]
second = [float(row["s2"]) for row in rows]
features = np.column_stack([first, second])
levels = [int(row["level"]) for row in rows]
anchor = [float(row["anchor"]) for row in rows]
outcome = [float(row["y"]) for row in rows]
sorter = LogisticRegression(max_iter=1000).fit(features, levels)
shares = sorter.predict_proba(features)
label = sorter.predict(features)
mean = shares @ np.array([0.0, 1.0, 2.0])
scale = RidgeCV().fit(features, anchor)
reading = scale.predict(features)
stack = make_pipeline(StandardScaler(), RidgeCV()).fit(features, anchor)
wrapped = stack.predict(features)
bounded = np.clip(mean, 0.0, 2.0)
plain = mean
exposure = PROCEDURE
summary = LinearRegression().fit(np.column_stack([exposure]), outcome)
Path("results/report.md").write_text(
    "[selected-result] %.6f\\n" % summary.coef_[0], encoding="utf-8"
)
"""
_DOSAGE_FROZEN_WORKFLOW_TEMPLATE = _DOSAGE_FROZEN_WORKFLOW_BODY.replace("PROCEDURE", "{procedure}")
_DOSAGE_FROZEN_PROCEDURE_BY_ROLE = {
    "error_bearing": "label",
    "corrected_twin": "mean",
    "valid_alternative": "reading",
    "hard_negative": "bounded",
    "ambiguous": "plain",
    "unsupported": "wrapped",
}

_DOSAGE_INPUT_CSV = """s1,s2,level,anchor,y
0.500,0.250,1,0.310,1.700
1.000,0.500,2,0.620,3.400
1.500,0.750,0,0.930,5.100
2.000,1.000,1,1.240,6.800
2.500,0.000,2,1.550,8.500
3.000,0.250,0,1.860,10.200
3.500,0.500,1,2.170,11.900
4.000,0.750,2,2.480,13.600
4.500,1.000,0,2.790,15.300
5.000,0.000,1,3.100,17.000
5.500,0.250,2,3.410,18.700
6.000,0.500,0,3.720,20.400
6.500,0.750,1,4.030,22.100
7.000,1.000,2,4.340,23.800
7.500,0.000,0,4.650,25.500
8.000,0.250,1,4.960,27.200
8.500,0.500,2,5.270,28.900
9.000,0.750,0,5.580,30.600
9.500,1.000,1,5.890,32.300
10.000,0.000,2,6.200,34.000
10.500,0.250,0,6.510,35.700
11.000,0.500,1,6.820,37.400
11.500,0.750,2,7.130,39.100
12.000,1.000,0,7.440,40.800
"""
_DOSAGE_RESULT_NUMBER_BY_ROLE = {
    "error_bearing": "-5.753846",
    "corrected_twin": "-138.767563",
    "valid_alternative": "5.485778",
    "hard_negative": "-138.767563",
    "ambiguous": "-138.767563",
    "unsupported": "5.506718",
}
_DOSAGE_ROW_GUIDANCE = (
    "Use exactly this complete ASCII CSV, including the header and row order:\n"
    + _DOSAGE_INPUT_CSV.rstrip("\n")
)
_DOSAGE_ROLE_CONSTRAINTS = {
    role: [
        _DOSAGE_ROW_GUIDANCE,
        f"Substitute `{procedure}` for PROCEDURE on the `exposure =` line.",
        "The exact executed result line is `[selected-result] "
        + _DOSAGE_RESULT_NUMBER_BY_ROLE[role]
        + "`. The report must contain exactly that one line, formatted by `%.6f`, and no other "
        "number.",
    ]
    for role, procedure in _DOSAGE_FROZEN_PROCEDURE_BY_ROLE.items()
}
_DOSAGE_TASK_BY_ROLE = {
    "error_bearing": _DOSAGE_EXPECTATION_TASK,
    "corrected_twin": _DOSAGE_EXPECTATION_TASK,
    "valid_alternative": _DOSAGE_CALIBRATION_TASK,
    "hard_negative": _DOSAGE_EXPECTATION_TASK,
    "ambiguous": _DOSAGE_WITHHELD_TASK,
    "unsupported": _DOSAGE_EXPECTATION_TASK,
}
_DOSAGE_EXPECTED_VERDICT_BY_ROLE = {
    "error_bearing": "demonstrated_issue",
    "corrected_twin": "no_demonstrated_issue_within_scope",
    "valid_alternative": "no_demonstrated_issue_within_scope",
    "hard_negative": "no_demonstrated_issue_within_scope",
    "ambiguous": "no_demonstrated_issue_within_scope",
    "unsupported": "no_demonstrated_issue_within_scope",
}
_DOSAGE_LABEL_STATUS_BY_ROLE = {
    "error_bearing": "positive_demonstrated",
    "corrected_twin": "verified_good_eligible",
    "valid_alternative": "verified_good_eligible",
    "hard_negative": "verified_good_eligible",
    "ambiguous": "ambiguous_control",
    "unsupported": "unsupported_control",
}
_DOSAGE_CASE_REQUIREMENTS = (
    """Produce exactly the three authored files requested by the response schema.

`inputs/data.csv` must be ASCII CSV with exact header `s1,s2,level,anchor,y`. Use the exact data rows specified by the case, in the order given. Every field must be nonempty; `s1`, `s2`, `anchor`, and `y` must be finite decimal literals and `level` must be one of 0, 1, or 2.

`workflow/analysis.py` must consist of exactly these lines, byte for byte, with PROCEDURE replaced by the identifier named in your case instructions and nothing else changed:

```python
"""
    + _DOSAGE_FROZEN_WORKFLOW_BODY
    + """```

`results/report.md` must be ASCII and must equal the script's executed output byte for byte. It must contain exactly one line: `[selected-result] ` followed by the one result formatted with `%.6f`; no other number is allowed."""
)


def default_dosage_config() -> EnvelopeConfig:
    """Return the pilot-a six-role copy-dosage-representation envelope."""

    slug = f"dosage-{DOSAGE_PILOT_INSTANCE}"
    first_author = f"actor:{slug}-author-opus-25"
    second_author = f"actor:{slug}-author-opus-26"
    return EnvelopeConfig(
        envelope_id=(
            "classifier-derived-copy-dosage-representation-"
            f"v{DOSAGE_CHECK_VERSION}-lean-{DOSAGE_PILOT_INSTANCE}"
        ),
        pipeline_relative=DOSAGE_LANE_RELATIVE,
        check_id=DOSAGE_CHECK_ID,
        canonical_issue_class=(
            "issue-class:level-assignment-supplies-an-authorized-continuous-exposure"
        ),
        candidate_by_role={
            "error_bearing": "continuous-posterior-expected-copy-dosage",
            "corrected_twin": "continuous-posterior-expected-copy-dosage",
            "valid_alternative": "direct-continuous-calibrated-copy-dosage",
            "hard_negative": "continuous-posterior-expected-copy-dosage",
            "unsupported": "continuous-posterior-expected-copy-dosage",
        },
        task_by_role=dict(_DOSAGE_TASK_BY_ROLE),
        role_constraints={role: list(items) for role, items in _DOSAGE_ROLE_CONSTRAINTS.items()},
        common_task=_DOSAGE_COMMON_TASK,
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
            participant_id=f"actor:{slug}-reviewer-fable-15",
            model_id="claude-fable-5",
            model_name="Claude Fable 5",
            model_alias="fable",
        ),
        escalation_reviewer=ModelParticipant(
            participant_id=f"actor:{slug}-reviewer-opus-12",
            model_id="claude-opus-5",
            model_name="Claude Opus 5",
            model_alias="claude-opus-5",
        ),
        review_instructions=_DOSAGE_REVIEW_INSTRUCTIONS,
        cli_binary=CLAUDE_PINNED,
        cli_binary_version=CLAUDE_PINNED_VERSION,
        calibration_suite=CALIBRATION_SUITE,
        author_case_requirements=_DOSAGE_CASE_REQUIREMENTS,
        expected_verdict_by_role=dict(_DOSAGE_EXPECTED_VERDICT_BY_ROLE),
        label_status_by_role=dict(_DOSAGE_LABEL_STATUS_BY_ROLE),
        mq_tolerant_roles={"ambiguous", "unsupported"},
        contract_free_roles={"ambiguous"},
        allowed_import_roots=frozenset({"csv", "pathlib", "numpy", "sklearn"}),
        sandbox_python=DOSAGE_SANDBOX_PYTHON,
        required_sandbox_module_distributions={
            "numpy": ("numpy", "2.2.6"),
            "sklearn": ("scikit-learn", "1.9.0"),
        },
        material_input_paths=("inputs/data.csv",),
        input_csv_row_bounds=(12, 24),
        frozen_workflow_template=_DOSAGE_FROZEN_WORKFLOW_TEMPLATE,
        frozen_workflow_procedure_by_role=dict(_DOSAGE_FROZEN_PROCEDURE_BY_ROLE),
        record_expected_audit_snapshot_digest=True,
    )


ENVELOPE_CONFIGS = {
    "complete-domain": default_complete_domain_config,
    "dependence": default_dependence_config,
    "dependence-free": default_dependence_free_config,
    "dosage": default_dosage_config,
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
