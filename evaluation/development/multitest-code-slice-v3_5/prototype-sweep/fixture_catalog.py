"""Independent fixture catalog for the strict MT 3.5 recall-delta prototype sweep.

The catalog chains the frozen 3.4 population (245 rows, itself chaining the frozen 3.3
population of 203) and adds the 3.5 positive controls, named disqualifiers, and
correct-analysis false-accusation controls.

Three orthogonal labels are carried:

* `correct_analysis`  the source is a scientifically correct analysis.  These rows may never
  reach `candidate`.  Reaching `covered` is allowed and is the desired answer.
* `refused_admission` the named 3.5 production must not fire on this source at all.  It is
  asserted against the executed admission census, never against a classification.
* `admitted`          the named 3.5 production must fire on this source.

Every new fixture is a single-construct mutation of a sealed E18 source, so the base
program's science is fixed and only the spelling under test moves.  The two correct-analysis
bases are E18 N1 (a complete `multipletests` correction) and E18 N5 (a genuine two-stage
screen-then-validate design); a candidate on either is a false accusation.
"""

from __future__ import annotations

import runpy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness import REPO, Outcome, reference_case

ROOT = Path(__file__).resolve().parent
V34_CATALOG = (
    REPO / "evaluation/development/multitest-code-slice-v3_4/prototype-sweep/fixture_catalog.py"
)

P2_KEY = "E18:P2:5a9277448db34379ce78"
P3_KEY = "E18:P3:d1b1fc47ccdabd0c2f22"
N1_KEY = "E18:N1:5c091f9052becdb5c3ea"
N5_KEY = "E18:N5:5ed2b0a375235333b96e"
E15P3_KEY = "E15:P3:afe47b2a7ea87ed21a69"

D1 = "d1-format-arm"
D5 = "d5-cardinality-read"
D4A = "d4a-numeric-group"
D4B = "d4b-loop-terminal"


@dataclass(frozen=True)
class Fixture:
    name: str
    case_key: str
    source: bytes
    expected: Outcome | None
    correct_analysis: bool
    category: str
    design_clause: str
    source_origin: str
    refused_admission: str | None = None
    admitted: str | None = None


def _replace_once(source: str, old: str, new: str, name: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"{name}: replacement anchor count is {source.count(old)}")
    return source.replace(old, new)


def _source(key: str) -> str:
    return reference_case(key).source_path.read_bytes().decode("utf-8")


def _fixture(
    name: str,
    case_key: str,
    source: str,
    *,
    expected: Outcome | None = None,
    correct_analysis: bool = False,
    category: str,
    design_clause: str,
    refused_admission: str | None = None,
    admitted: str | None = None,
) -> Fixture:
    return Fixture(
        name=name,
        case_key=case_key,
        source=source.encode("utf-8"),
        expected=expected,
        correct_analysis=correct_analysis,
        category=category,
        design_clause=design_clause,
        source_origin=f"authored for MT 3.5 from {case_key}",
        refused_admission=refused_admission,
        admitted=admitted,
    )


# --------------------------------------------------------------------------------------
# D1 bases
# --------------------------------------------------------------------------------------

P2_VERDICT = """        verdict = (
            "significant difference at p < {}".format(ALPHA)
            if p_value < ALPHA
            else "no significant difference at p < {}".format(ALPHA)
        )
"""
P2_TEST_LINE = (
    "        t_statistic, p_value = stats.ttest_ind(values_a, values_b, equal_var=False)\n"
)
N1_VERDICT = '        verdict = "DIFFERENT" if adjusted_p < ALPHA else "NO DIFFERENCE"\n'
N5_VERDICT = '        verdict = "pass" if result["p"] < level else "not passed"\n'


def _p2(name: str, verdict: str, *, extra: str | None = None) -> str:
    source = _replace_once(_source(P2_KEY), P2_VERDICT, verdict, name)
    if extra is not None:
        source = _replace_once(source, P2_TEST_LINE, P2_TEST_LINE + extra, name)
    return source


def d1_fixtures() -> tuple[Fixture, ...]:
    six = Outcome("candidate", "none", (), 6)
    return (
        _fixture(
            "positive-d1-format-arms",
            P2_KEY,
            _source(P2_KEY),
            expected=six,
            category="v3.5-d1",
            design_clause="1.1 admitted arm form 2",
            admitted=D1,
        ),
        _fixture(
            "positive-d1-fstring-arms",
            P2_KEY,
            _p2(
                "positive-d1-fstring-arms",
                """        verdict = (
            f"significant difference at p < {ALPHA}"
            if p_value < ALPHA
            else f"no significant difference at p < {ALPHA}"
        )
""",
            ),
            expected=six,
            category="v3.5-d1",
            design_clause="1.1 admitted arm form 3",
            admitted=D1,
        ),
        _fixture(
            "positive-d1-fstring-format-spec",
            P2_KEY,
            _p2(
                "positive-d1-fstring-format-spec",
                """        verdict = (
            f"significant difference at p < {ALPHA:.2f}"
            if p_value < ALPHA
            else f"no significant difference at p < {ALPHA:.2f}"
        )
""",
            ),
            expected=six,
            category="v3.5-d1",
            design_clause="1.1 constant-only format spec",
            admitted=D1,
        ),
        _fixture(
            "correct-d1-arm-interpolates-p-value",
            P2_KEY,
            _p2(
                "correct-d1-arm-interpolates-p-value",
                """        verdict = (
            "significant difference, p = {}".format(p_value)
            if p_value < ALPHA
            else "no significant difference, p = {}".format(p_value)
        )
""",
            ),
            category="v3.5-d1",
            design_clause="1.1 refusal: interpolated value is not an ARGVAL",
            refused_admission=D1,
        ),
        _fixture(
            "correct-d1-arm-contains-call",
            P2_KEY,
            _p2(
                "correct-d1-arm-contains-call",
                """        verdict = (
            "significant difference at p < {}".format(round(ALPHA, 3))
            if p_value < ALPHA
            else "no significant difference at p < {}".format(round(ALPHA, 3))
        )
""",
            ),
            category="v3.5-d1",
            design_clause="1.1 refusal: a call inside the arm",
            refused_admission=D1,
        ),
        _fixture(
            "positive-d1-arm-interpolates-an-outcome-label",
            P2_KEY,
            _p2(
                "positive-d1-arm-interpolates-an-outcome-label",
                """        verdict = (
            "significant difference for {}".format(label)
            if p_value < ALPHA
            else "no significant difference for {}".format(label)
        )
""",
            ),
            expected=six,
            category="v3.5-d1",
            design_clause=(
                "1.1 observed: the frozen loop normalisation substitutes the declared-outcome "
                "label, so the arm reaches the grammar as a Constant ARGVAL"
            ),
            admitted=D1,
        ),
        _fixture(
            "correct-d1-arm-interpolates-a-data-derived-local",
            P2_KEY,
            _p2(
                "correct-d1-arm-interpolates-a-data-derived-local",
                """        verdict = (
            "significant difference over {} patients".format(n_patients)
            if p_value < ALPHA
            else "no significant difference over {} patients".format(n_patients)
        )
""",
                extra="        n_patients = len(values_a) + len(values_b)\n",
            ),
            category="v3.5-d1",
            design_clause="1.1 refusal: the name is neither a constant nor a module constant",
            refused_admission=D1,
        ),
        _fixture(
            "correct-d1-arm-format-keyword",
            P2_KEY,
            _p2(
                "correct-d1-arm-format-keyword",
                """        verdict = (
            "significant difference at p < {a}".format(a=ALPHA)
            if p_value < ALPHA
            else "no significant difference at p < {a}".format(a=ALPHA)
        )
""",
            ),
            category="v3.5-d1",
            design_clause="1.1 refusal: keyword arguments",
            refused_admission=D1,
        ),
        _fixture(
            "correct-d1-arm-percent-form",
            P2_KEY,
            _p2(
                "correct-d1-arm-percent-form",
                """        verdict = (
            "significant difference at p < %s" % ALPHA
            if p_value < ALPHA
            else "no significant difference at p < %s" % ALPHA
        )
""",
            ),
            category="v3.5-d1",
            design_clause="1.1 refusal: the percent form is not admitted",
            refused_admission=D1,
        ),
        _fixture(
            "correct-d1-arm-attribute-not-format",
            P2_KEY,
            _p2(
                "correct-d1-arm-attribute-not-format",
                """        verdict = (
            "significant difference".upper()
            if p_value < ALPHA
            else "no significant difference".upper()
        )
""",
            ),
            category="v3.5-d1",
            design_clause="1.1 refusal: an attribute call other than str.format",
            refused_admission=D1,
        ),
        _fixture(
            "correct-d1-arm-fstring-nested-call",
            P2_KEY,
            _p2(
                "correct-d1-arm-fstring-nested-call",
                """        verdict = (
            f"significant difference at p < {round(ALPHA, 3)}"
            if p_value < ALPHA
            else f"no significant difference at p < {round(ALPHA, 3)}"
        )
""",
            ),
            category="v3.5-d1",
            design_clause="1.1 refusal: a call inside an f-string interpolation",
            refused_admission=D1,
        ),
        _fixture(
            "correct-d1-gated-family-format-arms",
            N5_KEY,
            _replace_once(
                _source(N5_KEY),
                N5_VERDICT,
                '        verdict = ("pass at {}".format(level) if result["p"] < level '
                'else "not passed at {}".format(level))\n',
                "correct-d1-gated-family-format-arms",
            ),
            correct_analysis=True,
            category="v3.5-d1",
            design_clause="7.1 the gated design keeps refusing when its arms are formatted",
        ),
        _fixture(
            "correct-d1-complete-correction-format-arms",
            N1_KEY,
            _replace_once(
                _source(N1_KEY),
                N1_VERDICT,
                '        verdict = ("DIFFERENT at {}".format(ALPHA) if adjusted_p < ALPHA '
                'else "NO DIFFERENCE at {}".format(ALPHA))\n',
                "correct-d1-complete-correction-format-arms",
            ),
            correct_analysis=True,
            category="v3.5-d1",
            design_clause="7.1 a complete correction stays covered when its arms are formatted",
        ),
        _fixture(
            "correct-d1-hand-complete-correction-format-arms",
            P2_KEY,
            _p2(
                "correct-d1-hand-complete-correction-format-arms",
                """        verdict = (
            "significant difference at p < {}".format(ALPHA)
            if p_used < ALPHA
            else "no significant difference at p < {}".format(ALPHA)
        )
""",
                extra="        p_used = min(p_value * len(DECLARED_OUTCOMES), 1.0)\n",
            ),
            correct_analysis=True,
            category="v3.5-d1",
            design_clause="7.1 a complete hand correction with formatted arms is not accused",
        ),
    )


# --------------------------------------------------------------------------------------
# D4 bases
# --------------------------------------------------------------------------------------

P3_CONSTANTS = 'LOW_SALT = 2.0\nHIGH_SALT = 3.0\n'
P3_MASKS = """    low = data[data[GROUP_COLUMN] == LOW_SALT]
    high = data[data[GROUP_COLUMN] == HIGH_SALT]
"""
P3_LOOP_HEAD = """    for position, result in enumerate(results, start=1):
        d = result["decimals"]
"""
P3_LOOP_TAIL = '        print("   Verdict: %s" % verdict)\n'
P3_LOOP_BLOCK = (
    '    for position, result in enumerate(results, start=1):\n'
    '        d = result["decimals"]\n'
    "        verdict = (\n"
    '            "significant difference at the 0.05 level"\n'
    '            if result["p_value"] < ALPHA\n'
    '            else "no significant difference at the 0.05 level"\n'
    "        )\n"
    "        print()\n"
    '        print("%d. %s  [%s]" % (position, result["label"], result["column"]))\n'
    "        print(\n"
    '            "   2.0%% salt: n = %d, mean = %.*f, SD = %.*f"\n'
    '            % (result["n_low"], d, result["mean_low"], d, result["sd_low"])\n'
    "        )\n"
    "        print(\n"
    '            "   3.0%% salt: n = %d, mean = %.*f, SD = %.*f"\n'
    '            % (result["n_high"], d, result["mean_high"], d, result["sd_high"])\n'
    "        )\n"
    '        print("   p-value: %.6g" % result["p_value"])\n'
    '        print("   Verdict: %s" % verdict)\n'
)


def _p3(name: str, *, constants: str | None = None, masks: str | None = None,
        loop_head: str | None = None, loop_tail: str | None = None) -> str:
    source = _source(P3_KEY)
    if constants is not None:
        source = _replace_once(source, P3_CONSTANTS, constants, name)
    if masks is not None:
        source = _replace_once(source, P3_MASKS, masks, name)
    if loop_head is not None:
        source = _replace_once(source, P3_LOOP_HEAD, loop_head, name)
    if loop_tail is not None:
        source = _replace_once(source, P3_LOOP_TAIL, loop_tail, name)
    return source


def d4_fixtures() -> tuple[Fixture, ...]:
    five = Outcome("candidate", "none", (), 5)
    return (
        _fixture(
            "positive-d4-float-group-and-presentation-loop",
            P3_KEY,
            _source(P3_KEY),
            expected=five,
            category="v3.5-d4",
            design_clause="1.4 the pinned E18 P3 pair",
            admitted=D4A,
        ),
        _fixture(
            "positive-d4a-integer-group-constants",
            P3_KEY,
            _p3("positive-d4a-integer-group-constants", constants="LOW_SALT = 2\nHIGH_SALT = 3\n"),
            expected=five,
            category="v3.5-d4",
            design_clause="1.4 an integer literal naming the same decimal token",
            admitted=D4A,
        ),
        _fixture(
            "positive-d4a-inline-float-literals",
            P3_KEY,
            _p3(
                "positive-d4a-inline-float-literals",
                masks="""    low = data[data[GROUP_COLUMN] == 2.0]
    high = data[data[GROUP_COLUMN] == 3.0]
""",
            ),
            expected=five,
            category="v3.5-d4",
            design_clause="1.4 the comparator written inline",
            admitted=D4A,
        ),
        _fixture(
            "correct-d4a-not-equal-operator",
            P3_KEY,
            _p3(
                "correct-d4a-not-equal-operator",
                masks="""    low = data[data[GROUP_COLUMN] != HIGH_SALT]
    high = data[data[GROUP_COLUMN] != LOW_SALT]
""",
            ),
            category="v3.5-d4",
            design_clause="1.4 refusal: only `==` is admitted",
            refused_admission=D4A,
        ),
        _fixture(
            "correct-d4a-non-group-column",
            P3_KEY,
            _p3(
                "correct-d4a-non-group-column",
                masks="""    low = data[data["ph"] == LOW_SALT]
    high = data[data["ph"] == HIGH_SALT]
""",
            ),
            category="v3.5-d4",
            design_clause="1.4 refusal: the mask does not read the group column",
            refused_admission=D4A,
        ),
        _fixture(
            "correct-d4a-boolean-comparator",
            P3_KEY,
            _p3(
                "correct-d4a-boolean-comparator",
                constants="LOW_SALT = True\nHIGH_SALT = False\n",
            ),
            category="v3.5-d4",
            design_clause="1.4 refusal: a bool is not a decimal token",
            refused_admission=D4A,
        ),
        _fixture(
            "correct-d4a-call-comparator",
            P3_KEY,
            _p3(
                "correct-d4a-call-comparator",
                masks="""    low = data[data[GROUP_COLUMN] == float(LOW_SALT)]
    high = data[data[GROUP_COLUMN] == float(HIGH_SALT)]
""",
            ),
            category="v3.5-d4",
            design_clause="1.4 refusal: the comparator is a call, not a literal",
            refused_admission=D4A,
        ),
        _fixture(
            "correct-d4a-string-group-constants",
            P3_KEY,
            _p3(
                "correct-d4a-string-group-constants",
                constants='LOW_SALT = "2.0"\nHIGH_SALT = "3.0"\n',
            ),
            expected=five,
            category="v3.5-d4",
            design_clause="1.4 the frozen string path is untouched, D4a does not fire",
            refused_admission=D4A,
            admitted=D4B,
        ),
        _fixture(
            "correct-d4b-loop-early-return",
            P3_KEY,
            _p3(
                "correct-d4b-loop-early-return",
                loop_tail=P3_LOOP_TAIL + "        if position > 3:\n            return\n",
            ),
            category="v3.5-d4",
            design_clause="1.4 refusal: an execution-prevention edge under the loop",
            
        ),
        _fixture(
            "correct-d4b-loop-break",
            P3_KEY,
            _p3(
                "correct-d4b-loop-break",
                loop_tail=P3_LOOP_TAIL + "        if position > 3:\n            break\n",
            ),
            category="v3.5-d4",
            design_clause="1.4 refusal: a break under the loop",
            
        ),
        _fixture(
            "correct-d4b-binding-escapes-the-loop",
            P3_KEY,
            _p3(
                "correct-d4b-binding-escapes-the-loop",
                loop_head=P3_LOOP_HEAD,
                loop_tail=P3_LOOP_TAIL,
            ).replace(
                '    print()\n    print("=" * 66)\n    print("Summary of verdicts, in declared order:")\n',
                '    print()\n    print("=" * 66)\n    print("Last verdict: %s" % verdict)\n'
                '    print("Summary of verdicts, in declared order:")\n',
                1,
            ),
            category="v3.5-d4",
            design_clause="1.4 refusal: a loop binding is read after the loop",
            
        ),
        _fixture(
            "correct-d4b-loop-does-not-render",
            P3_KEY,
            _replace_once(
                _source(P3_KEY),
                P3_LOOP_BLOCK,
                """    widths = []
    for position, result in enumerate(results, start=1):
        d = result["decimals"]
        widths.append(d + position)
""",
                "correct-d4b-loop-does-not-render",
            ),
            category="v3.5-d4",
            design_clause="1.4 refusal: the loop does not render",
            
        ),
        _fixture(
            "correct-d4b-call-iterator",
            P3_KEY,
            _p3(
                "correct-d4b-call-iterator",
                loop_head='    for position, result in enumerate(list(results), start=1):\n        d = result["decimals"]\n',
            ),
            category="v3.5-d4",
            design_clause="1.4 refusal: the iterator argument is not a bare Name",
            
        ),
        _fixture(
            "correct-d4b-test-after-the-loop",
            P3_KEY,
            _p3(
                "correct-d4b-test-after-the-loop",
                loop_tail=P3_LOOP_TAIL,
            ).replace(
                '    print()\n    print("=" * 66)\n    print("Summary of verdicts, in declared order:")\n',
                '    print()\n    print("=" * 66)\n'
                '    confirm = stats.ttest_ind(low["ph"], high["ph"]).pvalue\n'
                '    print("Confirmatory pass: %.6g" % confirm)\n'
                '    print("Summary of verdicts, in declared order:")\n',
                1,
            ),
            category="v3.5-d4",
            design_clause="1.4 refusal: a registered test sits after the loop",
            
        ),
        _fixture(
            "correct-d4b-gated-two-stage-design",
            N5_KEY,
            _source(N5_KEY),
            correct_analysis=True,
            category="v3.5-d4",
            design_clause="7.4 the gated two-stage design keeps refusing",
            
        ),
        _fixture(
            "correct-d4b-complete-correction-loop",
            N1_KEY,
            _source(N1_KEY),
            correct_analysis=True,
            category="v3.5-d4",
            design_clause="7.4 a complete correction stays covered",
        ),
    )


E15P3_SUMMARY = """    n_significant = sum(result["significant"] for result in results)
    print(
        f"{n_significant} of {len(results)} declared outcomes separated the two "
        f"ventilation groups at p < {ALPHA}."
    )
"""


def _e15p3(name: str, summary: str, *, extra: str | None = None) -> str:
    source = _replace_once(_source(E15P3_KEY), E15P3_SUMMARY, summary, name)
    if extra is not None:
        source = _replace_once(source, "    for result in results:\n", extra + "    for result in results:\n", name)
    return source


def d5_fixtures() -> tuple[Fixture, ...]:
    five = Outcome("candidate", "none", (), 5)
    return (
        _fixture(
            "positive-d5-cardinality-read",
            E15P3_KEY,
            _source(E15P3_KEY),
            expected=five,
            category="v3.5-d5",
            design_clause="1.5 the pinned E15 P3 cardinality read",
            admitted=D5,
        ),
        _fixture(
            "positive-d5-cardinality-read-in-format-call",
            E15P3_KEY,
            _e15p3(
                "positive-d5-cardinality-read-in-format-call",
                """    n_significant = sum(result["significant"] for result in results)
    print(
        "{} of {} declared outcomes separated the two groups.".format(
            n_significant, len(results)
        )
    )
""",
            ),
            expected=five,
            category="v3.5-d5",
            design_clause="1.5 the same read through str.format",
            admitted=D5,
        ),
        _fixture(
            "correct-d5-len-in-a-comparison",
            E15P3_KEY,
            _e15p3(
                "correct-d5-len-in-a-comparison",
                """    n_significant = sum(result["significant"] for result in results)
    if len(results) > 3:
        print(f"{n_significant} of many declared outcomes separated the groups.")
""",
            ),
            category="v3.5-d5",
            design_clause="1.5 refusal: the value enters a comparison",
            refused_admission=D5,
        ),
        _fixture(
            "correct-d5-len-as-a-threshold-divisor",
            E15P3_KEY,
            _e15p3(
                "correct-d5-len-as-a-threshold-divisor",
                """    n_significant = sum(result["significant"] for result in results)
    adjusted = ALPHA / len(results)
    print(f"{n_significant} outcomes separated the groups at p < {adjusted}.")
""",
            ),
            category="v3.5-d5",
            design_clause="1.5 refusal: the value becomes a threshold",
            refused_admission=D5,
        ),
        _fixture(
            "correct-d5-len-as-a-loop-bound",
            E15P3_KEY,
            _e15p3(
                "correct-d5-len-as-a-loop-bound",
                """    n_significant = sum(result["significant"] for result in results)
    for index in range(len(results)):
        print(f"{index}: {n_significant} declared outcomes separated the groups.")
""",
            ),
            category="v3.5-d5",
            design_clause="1.5 refusal: the value becomes a loop bound",
            refused_admission=D5,
        ),
        _fixture(
            "correct-d5-len-of-a-filtered-copy",
            E15P3_KEY,
            _e15p3(
                "correct-d5-len-of-a-filtered-copy",
                """    hits = [result for result in results if result["significant"]]
    print(f"{len(hits)} declared outcomes separated the two groups at p < {ALPHA}.")
""",
            ),
            category="v3.5-d5",
            design_clause="1.5 refusal: the argument is a filtered copy, not the family",
            refused_admission=D5,
        ),
        _fixture(
            "correct-d5-len-bound-to-a-local-first",
            E15P3_KEY,
            _e15p3(
                "correct-d5-len-bound-to-a-local-first",
                """    n_significant = sum(result["significant"] for result in results)
    n_declared = len(results)
    print(f"{n_significant} of {n_declared} declared outcomes separated the groups.")
""",
            ),
            category="v3.5-d5",
            design_clause="1.5 refusal: the value is stored before it is displayed",
            refused_admission=D5,
        ),
        _fixture(
            "correct-d5-len-in-arithmetic",
            E15P3_KEY,
            _e15p3(
                "correct-d5-len-in-arithmetic",
                """    n_significant = sum(result["significant"] for result in results)
    print(f"{n_significant} of {len(results) - 1} other declared outcomes separated them.")
""",
            ),
            category="v3.5-d5",
            design_clause="1.5 refusal: the value enters arithmetic",
            refused_admission=D5,
        ),
    )


def new_fixtures() -> tuple[Fixture, ...]:
    return (*d1_fixtures(), *d4_fixtures(), *d5_fixtures())


def prior_fixtures() -> tuple[Any, ...]:
    namespace = runpy.run_path(str(V34_CATALOG))
    fixtures = namespace["all_fixtures"]()
    if len(fixtures) != 245:
        raise ValueError("the frozen 3.4 fixture population is not 245")
    if sum(fixture.correct_analysis for fixture in fixtures) != 194:
        raise ValueError("the frozen 3.4 correct-fixture population is not 194")
    return tuple(fixtures)


def all_fixtures() -> tuple[Any, ...]:
    result = (*prior_fixtures(), *new_fixtures())
    names = [fixture.name for fixture in result]
    if len(names) != len(set(names)):
        raise ValueError("the 3.5 fixture census contains duplicate names")
    return result
