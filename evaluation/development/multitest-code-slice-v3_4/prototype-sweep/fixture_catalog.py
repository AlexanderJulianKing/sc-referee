"""Independent fixture catalog for the strict MT 3.4 prototype sweep.

The catalog chains the frozen 3.3 population (203 rows, itself chaining the frozen 3.2
population of 170) and adds the 3.4 positive controls, named disqualifiers, and
correct-analysis false-accusation controls.

Three orthogonal labels are carried, because conflating them is how a fixture set stops
proving anything:

* `correct_analysis`  the source is a scientifically correct analysis.  These rows may never
  reach `candidate`.  Reaching `covered` is allowed and is the desired answer.
* `refused_admission` the named 3.4 extension must not fire on this source at all.  Asserted
  against the executed admission census, not against a classification.
* `admitted`          the named 3.4 extension must fire on this source.

No adversary expectation is copied from executed output.  A disqualifier is proved by the
admission census being empty for its extension, which cannot be satisfied by accident.
"""

from __future__ import annotations

import runpy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness import REPO, Outcome, reference_case

ROOT = Path(__file__).resolve().parent
V33_CATALOG = (
    REPO / "evaluation/development/multitest-code-slice-v3_3/prototype-sweep/fixture_catalog.py"
)
P3_KEY = "E17:P3:a2e031f79e31c80fd900"
P6_KEY = "E17:P6:b4e507c4b55954752f14"


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


def _p3() -> str:
    return reference_case(P3_KEY).source_path.read_bytes().decode("utf-8")


def _p6() -> str:
    return reference_case(P6_KEY).source_path.read_bytes().decode("utf-8")


P3_COMPREHENSION = """    results = {
        outcome: compare_settings(roadside[outcome], park[outcome])
        for outcome in OUTCOMES
    }
"""
P3_LOOP_HEAD = "    for outcome in OUTCOMES:\n        result = results[outcome]\n"
P3_VERDICT = '        verdict = "SIGNIFICANT" if result["p"] < ALPHA else "not significant"\n'
P3_VERDICT_PRINT = '        print("  verdict at alpha = {}: {}".format(ALPHA, verdict))\n'
P3_T_PRINT = '        print("  t = {:.4f}".format(result["t"]))\n'
P6_ITERATOR = "    for position, outcome in enumerate(OUTCOMES, start=1):\n"
P6_BRANCH = """        if outcome in MUSCULOSKELETAL:
            # Correct by hand: multiply by the number of comparisons, cap at one.
            corrected_p = raw_p * N_COMPARISONS
            if corrected_p > 1.0:
                corrected_p = 1.0
            p_used = corrected_p
            p_label = "corrected p (raw p = %.4f, x %d, capped at 1)" % (
                raw_p, N_COMPARISONS)
        else:
            p_used = raw_p
            p_label = "raw p"
"""
P6_CAP = """            corrected_p = raw_p * N_COMPARISONS
            if corrected_p > 1.0:
                corrected_p = 1.0
"""


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
        source_origin=f"authored for MT 3.4 from {case_key}",
        refused_admission=refused_admission,
        admitted=admitted,
    )


def _p3_variant(name: str, comprehension: str, *, loop: str | None = None) -> str:
    source = _replace_once(_p3(), P3_COMPREHENSION, comprehension, name)
    if loop is not None:
        source = _replace_once(source, P3_LOOP_HEAD, loop, name)
    if "SCREENED" in comprehension:
        source = _replace_once(
            source,
            "LABELS = {",
            'SCREENED = ["nitrogen_pct", "sulfur_pct", "lead_mg_kg"]\n\nLABELS = {',
            name,
        )
    if "REORDERED" in comprehension:
        source = _replace_once(
            source, "LABELS = {", "REORDERED = list(reversed(OUTCOMES))\n\nLABELS = {", name
        )
    return source


def _p6_variant(name: str, *, iterator: str | None = None, cap: str | None = None) -> str:
    source = _p6()
    if iterator is not None:
        source = _replace_once(source, P6_ITERATOR, iterator, name)
    if cap is not None:
        source = _replace_once(source, P6_CAP, cap, name)
    return source


def comprehension_fixtures() -> tuple[Fixture, ...]:
    """Extension A: positive controls, disqualifiers, and correct-analysis controls."""

    rows: list[Fixture] = [
        _fixture(
            "positive-comprehension-dict-helper-record",
            P3_KEY,
            _p3(),
            expected=Outcome("candidate", "none", (), 6),
            category="comprehension-positive",
            design_clause="A.1 dict comprehension over the contract-order sequence",
            admitted="comprehension",
        ),
        _fixture(
            "positive-comprehension-inline-flat-record",
            P3_KEY,
            _replace_once(
                _p3_variant(
                    "positive-comprehension-inline-flat-record",
                    "    results = {\n"
                    "        outcome: {\n"
                    '            "park_mean": park[outcome].mean(),\n'
                    '            "roadside_mean": roadside[outcome].mean(),\n'
                    '            "p": stats.ttest_ind(roadside[outcome], park[outcome]).pvalue,\n'
                    "        }\n"
                    "        for outcome in OUTCOMES\n"
                    "    }\n",
                ),
                P3_T_PRINT,
                "",
                "positive-comprehension-inline-flat-record",
            ),
            category="comprehension-positive",
            design_clause="A.1 flat literal record element of scalars from the loop variable",
            admitted="comprehension",
        ),
        _fixture(
            "positive-comprehension-list-form",
            P3_KEY,
            _p3_variant(
                "positive-comprehension-list-form",
                "    results = [\n"
                "        compare_settings(roadside[outcome], park[outcome])\n"
                "        for outcome in OUTCOMES\n"
                "    ]\n",
                loop="    for outcome, result in zip(OUTCOMES, results):\n",
            ),
            category="comprehension-positive",
            design_clause="A.1 list comprehension is normalized; the record model residual stands",
            admitted="comprehension",
        ),
    ]
    disqualifiers: tuple[tuple[str, str, str | None, str], ...] = (
        (
            "correct-comprehension-with-filter",
            "    results = {\n"
            "        outcome: compare_settings(roadside[outcome], park[outcome])\n"
            "        for outcome in OUTCOMES\n"
            '        if outcome != "zinc_mg_kg"\n'
            "    }\n",
            None,
            "A.2 a filtered generator is never a complete contract family",
        ),
        (
            "correct-comprehension-over-non-contract-sequence",
            "    results = {\n"
            "        outcome: compare_settings(roadside[outcome], park[outcome])\n"
            "        for outcome in SCREENED\n"
            "    }\n",
            None,
            "A.2 the generator sequence must be order-equal to the contract family",
        ),
        (
            "correct-comprehension-key-not-loop-variable",
            "    results = {\n"
            "        LABELS[outcome]: compare_settings(roadside[outcome], park[outcome])\n"
            "        for outcome in OUTCOMES\n"
            "    }\n",
            "    for outcome in OUTCOMES:\n        result = results[LABELS[outcome]]\n",
            "A.2 the dict key must be the generator target itself",
        ),
        (
            "correct-comprehension-two-generators",
            "    results = {\n"
            "        outcome: compare_settings(roadside[outcome], park[outcome])\n"
            "        for group in [OUTCOMES]\n"
            "        for outcome in group\n"
            "    }\n",
            None,
            "A.2 exactly one generator",
        ),
        (
            "correct-comprehension-conditional-element",
            "    results = {\n"
            "        outcome: compare_settings(roadside[outcome], park[outcome])\n"
            '        if outcome != "zinc_mg_kg"\n'
            "        else compare_settings(park[outcome], roadside[outcome])\n"
            "        for outcome in OUTCOMES\n"
            "    }\n",
            None,
            "A.2 the element may not be a conditional expression",
        ),
        (
            "correct-comprehension-nested-element",
            "    results = {\n"
            "        outcome: {\n"
            '            "p": compare_settings(roadside[outcome], park[outcome])["p"],\n'
            '            "quantiles": [park[outcome].quantile(q) for q in [0.25, 0.75]],\n'
            "        }\n"
            "        for outcome in OUTCOMES\n"
            "    }\n",
            None,
            "A.2 no nested comprehension anywhere in the element",
        ),
        (
            "correct-comprehension-keyword-argument-element",
            "    results = {\n"
            "        outcome: compare_settings(\n"
            "            roadside[outcome], park_values=park[outcome]\n"
            "        )\n"
            "        for outcome in OUTCOMES\n"
            "    }\n",
            None,
            "A.2 the element call carries no keywords",
        ),
        (
            "correct-comprehension-out-of-contract-order",
            "    results = {\n"
            "        outcome: compare_settings(roadside[outcome], park[outcome])\n"
            "        for outcome in REORDERED\n"
            "    }\n",
            None,
            "A.2 sequence order must equal contract order, not merely its member set",
        ),
        (
            "correct-comprehension-target-rebound",
            "    results = {\n"
            "        outcome: compare_settings(roadside[outcome], park[outcome])\n"
            "        for outcome in OUTCOMES\n"
            "    }\n"
            '    results = {key: value for key, value in results.items() if value["p"] < 0.5}\n',
            None,
            "A.2 the collected name has exactly one Store and no rebinding",
        ),
        (
            "correct-comprehension-collection-mutated",
            "    results = {\n"
            "        outcome: compare_settings(roadside[outcome], park[outcome])\n"
            "        for outcome in OUTCOMES\n"
            "    }\n"
            '    results["nitrogen_pct"] = compare_settings(\n'
            '        park["nitrogen_pct"], roadside["nitrogen_pct"])\n',
            None,
            "A.2 no post-construction mutation of the collected name",
        ),
        (
            "correct-comprehension-element-ignores-loop-variable",
            "    results = {\n"
            '        outcome: compare_settings(roadside["nitrogen_pct"], park["nitrogen_pct"])\n'
            "        for outcome in OUTCOMES\n"
            "    }\n",
            None,
            "A.2 the element must actually depend on the loop variable",
        ),
    )
    for name, comprehension, loop, clause in disqualifiers:
        rows.append(
            _fixture(
                name,
                P3_KEY,
                _p3_variant(name, comprehension, loop=loop),
                category="comprehension-adversary",
                design_clause=clause,
                refused_admission="comprehension",
            )
        )
    rows.append(
        _fixture(
            "correct-comprehension-gates-later-test",
            P3_KEY,
            _replace_once(
                _p3(),
                P3_VERDICT_PRINT,
                P3_VERDICT_PRINT + '        if result["p"] < ALPHA:\n'
                "            confirm = stats.mannwhitneyu(roadside[outcome], park[outcome])\n"
                '            print("  confirmatory p = {:.6f}".format(confirm.pvalue))\n',
                "correct-comprehension-gates-later-test",
            ),
            correct_analysis=True,
            category="comprehension-fa-control",
            design_clause="A.3 a normalized comprehension never hides a p-gated later test",
        )
    )
    rows.append(
        _fixture(
            "correct-comprehension-corrected-family",
            P3_KEY,
            _replace_once(
                _replace_once(
                    _p3(),
                    'result["p"] < ALPHA',
                    'result["p"] < ALPHA / len(OUTCOMES)',
                    "correct-comprehension-corrected-family",
                ),
                P3_VERDICT_PRINT,
                '        print("  verdict at bonferroni alpha: {}".format(verdict))\n',
                "correct-comprehension-corrected-family",
            ),
            correct_analysis=True,
            category="comprehension-fa-control",
            design_clause="A.3 a correctly corrected comprehension family is covered, not accused",
            admitted="comprehension",
        )
    )
    return tuple(rows)


def terminal_ifexp_fixtures() -> tuple[Fixture, ...]:
    """Extension B: the specified-but-not-shipped print-only verdict production.

    These three rows are correctly Bonferroni-corrected six-outcome analyses.  They carry no
    `refused_admission`, because B is not installed in the shipped 3.4 recognizer set; the
    grammar-level refusal is proved directly by `_terminal_ifexp_refusal_probe` in
    `instrument.py`, and the reason B is not shipped is measured by
    `_extension_b_collision_probe`.
    """

    corrected = _replace_once(
        _replace_once(
            _p3(),
            'result["p"] < ALPHA',
            'result["p"] < ALPHA / len(OUTCOMES)',
            "b-corrected-base",
        ),
        P3_VERDICT_PRINT,
        '        print("  verdict at bonferroni alpha: {}".format(verdict))\n',
        "b-corrected-base",
    )
    corrected_print = '        print("  verdict at bonferroni alpha: {}".format(verdict))\n'
    return (
        _fixture(
            "correct-terminal-verdict-stored-then-printed",
            P3_KEY,
            _replace_once(
                _replace_once(
                    corrected,
                    '    print("Lichen biomonitoring survey',
                    '    verdicts = []\n    print("Lichen biomonitoring survey',
                    "correct-terminal-verdict-stored-then-printed",
                ),
                corrected_print,
                "        verdicts.append(verdict)\n" + corrected_print,
                "correct-terminal-verdict-stored-then-printed",
            ),
            correct_analysis=True,
            category="terminal-ifexp-rejected-grammar",
            design_clause="B.2 a verdict stored into any collection refuses the print-only route",
        ),
        _fixture(
            "correct-terminal-verdict-rebound-into-name",
            P3_KEY,
            _replace_once(
                corrected,
                corrected_print,
                corrected_print + '        summary = "{}: {}".format(outcome, verdict)\n'
                "        print(summary)\n",
                "correct-terminal-verdict-rebound-into-name",
            ),
            correct_analysis=True,
            category="terminal-ifexp-rejected-grammar",
            design_clause="B.2 every verdict load must be a print payload, not a fresh binding",
        ),
        _fixture(
            "correct-terminal-verdict-returned-from-helper",
            P3_KEY,
            _replace_once(
                _replace_once(
                    corrected,
                    '        verdict = "SIGNIFICANT" if result["p"] < ALPHA / len(OUTCOMES)'
                    ' else "not significant"\n',
                    "        verdict = describe(result)\n",
                    "correct-terminal-verdict-returned-from-helper",
                ),
                "def main():\n",
                "def describe(result):\n"
                '    verdict = "SIGNIFICANT" if result["p"] < ALPHA / len(OUTCOMES) '
                'else "not significant"\n'
                "    return verdict\n"
                "\n"
                "\n"
                "def main():\n",
                "correct-terminal-verdict-returned-from-helper",
            ),
            correct_analysis=True,
            category="terminal-ifexp-rejected-grammar",
            design_clause="B.2 a returned verdict is not a closed output transport",
        ),
    )


def iterator_fixtures() -> tuple[Fixture, ...]:
    """Extension C: the enumerate row table, its disqualifiers, and FA controls."""

    rows: list[Fixture] = [
        _fixture(
            "positive-ap-enumerate-start-one",
            P6_KEY,
            _p6(),
            expected=Outcome("candidate", "strict_subset", (0, 1, 2), 7),
            category="iterator-positive",
            design_clause="C.1 enumerate(NAME, start=K) binds rows in contract order",
            admitted="enumerate",
        ),
        _fixture(
            "positive-ap-enumerate-no-start",
            P6_KEY,
            _p6_variant(
                "positive-ap-enumerate-no-start",
                iterator="    for position, outcome in enumerate(OUTCOMES):\n",
            ),
            expected=Outcome("candidate", "strict_subset", (0, 1, 2), 7),
            category="iterator-positive",
            design_clause="C.1 K is irrelevant: positions come from sequence order",
            admitted="enumerate",
        ),
        _fixture(
            "positive-ap-enumerate-start-zero",
            P6_KEY,
            _p6_variant(
                "positive-ap-enumerate-start-zero",
                iterator="    for position, outcome in enumerate(OUTCOMES, start=0):\n",
            ),
            expected=Outcome("candidate", "strict_subset", (0, 1, 2), 7),
            category="iterator-positive",
            design_clause="C.1 K is irrelevant: positions come from sequence order",
            admitted="enumerate",
        ),
    ]
    disqualifiers: tuple[tuple[str, str, str], ...] = (
        (
            "correct-ap-enumerate-over-non-contract-sequence",
            "    for position, outcome in enumerate(MUSCULOSKELETAL, start=1):\n",
            "C.2 the enumerate argument must be the contract-order sequence",
        ),
        (
            "correct-ap-enumerate-over-zip",
            "    for position, (outcome, label) in enumerate(zip(OUTCOMES, OUTCOMES), start=1):\n",
            "C.2 only a bare Name argument is admitted",
        ),
        (
            "correct-ap-enumerate-single-target",
            "    for pair in enumerate(OUTCOMES, start=1):\n        position, outcome = pair\n",
            "C.2 the target must be an exact two-Name tuple",
        ),
        (
            "correct-ap-enumerate-nonliteral-start",
            "    for position, outcome in enumerate(OUTCOMES, start=N_COMPARISONS):\n",
            "C.2 start must be an integer literal",
        ),
        (
            "correct-ap-enumerate-reversed-sequence",
            "    for position, outcome in enumerate(list(reversed(OUTCOMES)), start=1):\n",
            "C.2 a call other than the bare sequence Name refuses",
        ),
    )
    for name, iterator, clause in disqualifiers:
        rows.append(
            _fixture(
                name,
                P6_KEY,
                _p6_variant(name, iterator=iterator),
                category="iterator-adversary",
                design_clause=clause,
                refused_admission="enumerate",
            )
        )
    rows.append(
        _fixture(
            "correct-ap-counter-used-in-decision",
            P6_KEY,
            _p6_variant(
                "correct-ap-counter-used-in-decision",
                cap="            if position <= 3:\n"
                "                corrected_p = min(raw_p * N_COMPARISONS, 1.0)\n"
                "            else:\n"
                "                corrected_p = raw_p\n",
            ),
            correct_analysis=True,
            category="iterator-fa-control",
            design_clause="C.3 the counter is opaque: any decision use resolves to a refusal",
        )
    )
    rows.append(
        _fixture(
            "correct-ap-counter-used-as-factor",
            P6_KEY,
            _p6_variant(
                "correct-ap-counter-used-as-factor",
                cap="            corrected_p = min(raw_p * position, 1.0)\n",
            ),
            correct_analysis=True,
            category="iterator-fa-control",
            design_clause="C.3 the counter can never supply a correction factor",
        )
    )
    rows.append(
        _fixture(
            "correct-ap-enumerate-complete-correction-min",
            P6_KEY,
            _replace_once(
                _p6(),
                P6_BRANCH,
                "        corrected_p = min(raw_p * N_COMPARISONS, 1.0)\n"
                "        p_used = corrected_p\n"
                '        p_label = "corrected p"\n',
                "correct-ap-enumerate-complete-correction-min",
            ),
            correct_analysis=True,
            category="iterator-fa-control",
            design_clause="C.3 a complete correction under enumerate is covered, not a subset",
            admitted="enumerate",
        )
    )
    return tuple(rows)


def cap_fixtures() -> tuple[Fixture, ...]:
    """Extension D: the two-statement if-cap, its disqualifiers, and FA controls."""

    rows: list[Fixture] = []
    disqualifiers: tuple[tuple[str, str, str], ...] = (
        (
            "correct-ap-cap-non-adjacent",
            "            corrected_p = raw_p * N_COMPARISONS\n"
            '            print("   raw p = %.4f" % raw_p)\n'
            "            if corrected_p > 1.0:\n"
            "                corrected_p = 1.0\n",
            "D.2 the product and the cap must be adjacent in the same block",
        ),
        (
            "correct-ap-cap-guard-on-different-name",
            "            corrected_p = raw_p * N_COMPARISONS\n"
            "            if raw_p > 1.0:\n"
            "                corrected_p = 1.0\n",
            "D.2 the guard must compare the folded Name itself",
        ),
        (
            "correct-ap-cap-guard-not-literal-one",
            "            corrected_p = raw_p * N_COMPARISONS\n"
            "            if corrected_p > ALPHA:\n"
            "                corrected_p = 1.0\n",
            "D.2 the guard comparand must be the literal one",
        ),
        (
            "correct-ap-cap-body-extra-statement",
            "            corrected_p = raw_p * N_COMPARISONS\n"
            "            if corrected_p > 1.0:\n"
            "                corrected_p = 1.0\n"
            '                print("   capped")\n',
            "D.2 the reassignment must be the sole statement in the if-body",
        ),
        (
            "correct-ap-cap-with-else",
            "            corrected_p = raw_p * N_COMPARISONS\n"
            "            if corrected_p > 1.0:\n"
            "                corrected_p = 1.0\n"
            "            else:\n"
            "                corrected_p = raw_p * N_COMPARISONS\n",
            "D.2 an else arm refuses",
        ),
        (
            "correct-ap-cap-assigns-other-value",
            "            corrected_p = raw_p * N_COMPARISONS\n"
            "            if corrected_p > 1.0:\n"
            "                corrected_p = 0.999\n",
            "D.2 the reassignment value must be the literal one",
        ),
        (
            "correct-ap-cap-augmented-reassignment",
            "            corrected_p = raw_p * N_COMPARISONS\n"
            "            if corrected_p > 1.0:\n"
            "                corrected_p -= 0.0\n",
            "D.2 an augmented Store is not the admitted reassignment",
        ),
        (
            "correct-ap-cap-reassigns-other-name",
            "            corrected_p = raw_p * N_COMPARISONS\n"
            "            if corrected_p > 1.0:\n"
            "                raw_p = 1.0\n",
            "D.2 the reassignment target must be the folded Name",
        ),
    )
    for name, cap, clause in disqualifiers:
        rows.append(
            _fixture(
                name,
                P6_KEY,
                _p6_variant(name, cap=cap),
                category="cap-adversary",
                design_clause=clause,
                refused_admission="cap",
            )
        )
    rows.append(
        _fixture(
            "positive-ap-cap-min-form-unchanged",
            P6_KEY,
            _p6_variant(
                "positive-ap-cap-min-form-unchanged",
                cap="            corrected_p = min(raw_p * N_COMPARISONS, 1.0)\n",
            ),
            expected=Outcome("candidate", "strict_subset", (0, 1, 2), 7),
            category="cap-positive",
            design_clause="D.1 the frozen min form is untouched and stays admitted",
            refused_admission="cap",
        )
    )
    rows.append(
        _fixture(
            "correct-ap-cap-complete-correction",
            P6_KEY,
            _replace_once(
                _p6(),
                P6_BRANCH,
                "        corrected_p = raw_p * N_COMPARISONS\n"
                "        if corrected_p > 1.0:\n"
                "            corrected_p = 1.0\n"
                "        p_used = corrected_p\n"
                '        p_label = "corrected p"\n',
                "correct-ap-cap-complete-correction",
            ),
            correct_analysis=True,
            category="cap-fa-control",
            design_clause="D.3 the if-cap and the min form agree: complete correction is covered",
            admitted="cap",
        )
    )
    return tuple(rows)


def reason_routing_fixtures() -> tuple[Fixture, ...]:
    """Extension E: genuine gatekeeping keeps `hierarchical-gatekeeping-present`."""

    return (
        _fixture(
            "correct-outcome-headers-genuine-screen",
            P3_KEY,
            _replace_once(
                _p3(),
                P3_COMPREHENSION,
                "    results = {}\n"
                "    for outcome in OUTCOMES:\n"
                "        if roadside[outcome].mean() > park[outcome].mean():\n"
                "            results[outcome] = compare_settings(\n"
                "                roadside[outcome], park[outcome])\n"
                "        else:\n"
                '            results[outcome] = {"park_mean": 0.0, "roadside_mean": 0.0,\n'
                '                                "t": 0.0, "p": 1.0}\n',
                "correct-outcome-headers-genuine-screen",
            ),
            correct_analysis=True,
            category="reason-routing-adversary",
            design_clause="E.2 a real screen-then-test gate never reaches a candidate",
            refused_admission="comprehension",
        ),
        _fixture(
            "correct-outcome-headers-early-exit",
            P3_KEY,
            _replace_once(
                _p3(),
                P3_COMPREHENSION,
                "    if roadside[OUTCOMES[0]].mean() > park[OUTCOMES[1]].mean():\n"
                "        return\n"
                "    results = {}\n"
                "    for outcome in OUTCOMES:\n"
                "        results[outcome] = compare_settings(\n"
                "            roadside[outcome], park[outcome])\n",
                "correct-outcome-headers-early-exit",
            ),
            correct_analysis=True,
            category="reason-routing-adversary",
            design_clause="E.2 an execution-prevention edge keeps the gatekeeping reason",
            refused_admission="comprehension",
        ),
    )


def new_fixtures() -> tuple[Fixture, ...]:
    return (
        *comprehension_fixtures(),
        *terminal_ifexp_fixtures(),
        *iterator_fixtures(),
        *cap_fixtures(),
        *reason_routing_fixtures(),
    )


def prior_fixtures() -> tuple[Any, ...]:
    namespace = runpy.run_path(str(V33_CATALOG))
    fixtures = namespace["all_fixtures"]()
    if len(fixtures) != 203:
        raise ValueError("the frozen 3.3 fixture population is not 203")
    if sum(fixture.correct_analysis for fixture in fixtures) != 183:
        raise ValueError("the frozen 3.3 correct-fixture population is not 183")
    return tuple(fixtures)


def all_fixtures() -> tuple[Any, ...]:
    result = (*prior_fixtures(), *new_fixtures())
    names = [fixture.name for fixture in result]
    if len(names) != len(set(names)):
        raise ValueError("the 3.4 fixture census contains duplicate names")
    return result
