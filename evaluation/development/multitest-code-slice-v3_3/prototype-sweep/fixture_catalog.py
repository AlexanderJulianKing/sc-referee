"""Independent fixture catalog for the strict MT 3.3 prototype sweep."""

from __future__ import annotations

import runpy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness import REPO, Outcome, reference_case

ROOT = Path(__file__).resolve().parent
V32_CATALOG = (
    REPO / "evaluation/development/multitest-code-slice-v3_2/prototype-sweep/fixture_catalog.py"
)


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


def _replace_once(source: str, old: str, new: str, name: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"{name}: replacement anchor count is {source.count(old)}")
    return source.replace(old, new)


def _p2() -> tuple[str, str]:
    case = reference_case("E16:P2:7a43fa7b50f1b99e5034")
    return case.key, case.source_path.read_text(encoding="utf-8")


def _p3() -> tuple[str, str]:
    case = reference_case("E16:P3:5a9c5b4377c33916d672")
    return case.key, case.source_path.read_text(encoding="utf-8")


def _p4() -> tuple[str, str]:
    case = reference_case("E16:P4:9ced761b41ef93485acf")
    return case.key, case.source_path.read_text(encoding="utf-8")


def terminal_and_helper_fixtures() -> tuple[Fixture, ...]:
    p2_key, p2 = _p2()
    p3_key, p3 = _p3()
    p4_key, p4 = _p4()
    values: list[Fixture] = []

    def add(
        name: str,
        case_key: str,
        source: str,
        *,
        expected: Outcome | None,
        correct: bool,
        category: str,
        clause: str,
        origin: str,
    ) -> None:
        values.append(
            Fixture(
                name,
                case_key,
                source.encode("utf-8"),
                expected,
                correct,
                category,
                clause,
                origin,
            )
        )

    add(
        "positive-terminal-verdict-record-print",
        p2_key,
        p2,
        expected=Outcome("candidate", "none", (), 6),
        correct=False,
        category="terminal-positive",
        clause="4.2 verdict-local production",
        origin="sealed E16 P2 bytes",
    )
    add(
        "positive-terminal-direction-if-print",
        p4_key,
        p4,
        expected=Outcome("candidate", "none", (), 7),
        correct=False,
        category="terminal-positive",
        clause="4.3 presentation-If production",
        origin="sealed E16 P4 bytes",
    )
    p4_second_loop = """    for result in results:
        if result["p_value"] < ALPHA:
            direction = "higher" if result["difference"] > 0 else "lower"
            print(
                f"{result['label']}: inoculation significantly {direction} "
                f"(mean {result['mean_treated']:.3f} vs {result['mean_control']:.3f}, "
                f"t = {result['t_stat']:.3f}, p = {result['p_value']:.3e})."
            )
        else:
            print(
                f"{result['label']}: no significant effect of inoculation "
                f"(mean {result['mean_treated']:.3f} vs {result['mean_control']:.3f}, "
                f"t = {result['t_stat']:.3f}, p = {result['p_value']:.3f})."
            )
"""
    p4_plain_loop = """    for result in results:
        print(f"{result['label']}: p = {result['p_value']:.3e}")
"""
    p4_count_only = _replace_once(
        p4, p4_second_loop, p4_plain_loop, "positive-terminal-count-output"
    )
    add(
        "positive-terminal-count-output",
        p4_key,
        p4_count_only,
        expected=Outcome("candidate", "none", (), 7),
        correct=False,
        category="terminal-positive",
        clause="4.1 exact terminal count production",
        origin="E16 P4 with only the presentation If removed",
    )

    count_anchor = '    n_significant = sum(1 for result in results if result["p_value"] < ALPHA)\n'
    p4_count_test = _replace_once(
        p4,
        count_anchor,
        count_anchor
        + "    if n_significant:\n"
        + "        stats.ttest_ind(data[OUTCOMES[0][0]], data[OUTCOMES[1][0]])\n",
        "correct-terminal-count-gates-later-test",
    )
    add(
        "correct-terminal-count-gates-later-test",
        p4_key,
        p4_count_test,
        expected=Outcome("abstain", "authorized-family-test-census-incomplete"),
        correct=True,
        category="terminal-adversary",
        clause="4.4 later registered-test disqualifier",
        origin="fresh count-to-test attack on E16 P4",
    )
    p4_sys_exit = _replace_once(
        p4, "import pandas as pd\n", "import sys\nimport pandas as pd\n", "sys-import"
    )
    p4_sys_exit = _replace_once(
        p4_sys_exit,
        count_anchor,
        count_anchor + "    if n_significant:\n        sys.exit(0)\n",
        "correct-terminal-count-sys-exit",
    )
    add(
        "correct-terminal-count-sys-exit",
        p4_key,
        p4_sys_exit,
        expected=Outcome("abstain", "hierarchical-gatekeeping-present"),
        correct=True,
        category="terminal-adversary",
        clause="4.4 execution-prevention disqualifier",
        origin="fresh sys.exit attack on E16 P4",
    )
    stage2_helper = """

def stage_two(frame):
    return stats.ttest_ind(
        frame.loc[frame[GROUP_COL] == TREATED, OUTCOMES[0][0]],
        frame.loc[frame[GROUP_COL] == CONTROL, OUTCOMES[0][0]],
    )
"""
    p4_helper = _replace_once(
        p4, "\ndef main():\n", stage2_helper + "\ndef main():\n", "stage2-helper"
    )
    p4_helper = _replace_once(
        p4_helper,
        count_anchor,
        count_anchor + "    if n_significant:\n        stage_two(data)\n",
        "correct-terminal-count-gates-helper-test",
    )
    add(
        "correct-terminal-count-gates-helper-test",
        p4_key,
        p4_helper,
        expected=Outcome("abstain", "authorized-family-test-census-incomplete"),
        correct=True,
        category="terminal-adversary",
        clause="4.4 transitive helper-test disqualifier",
        origin="fresh screen-then-test helper attack on E16 P4",
    )
    p4_record_store = _replace_once(
        p4,
        '        if result["p_value"] < ALPHA:\n',
        '        if result["p_value"] < ALPHA:\n'
        '            result["p_value"] = min(1.0, result["p_value"] * len(OUTCOMES))\n',
        "correct-presentation-if-record-store",
    )
    add(
        "correct-presentation-if-record-store",
        p4_key,
        p4_record_store,
        expected=Outcome("abstain", "unresolved-manual-correction-present"),
        correct=True,
        category="terminal-adversary",
        clause="4.4 family-record-store disqualifier",
        origin="fresh corrected-store attack on E16 P4",
    )
    p4_raise = _replace_once(
        p4,
        '        if result["p_value"] < ALPHA:\n',
        '        if result["p_value"] < ALPHA:\n'
        '            raise RuntimeError("presentation stopped")\n',
        "correct-presentation-if-raise",
    )
    add(
        "correct-presentation-if-raise",
        p4_key,
        p4_raise,
        expected=Outcome("abstain", "hierarchical-gatekeeping-present"),
        correct=True,
        category="terminal-adversary",
        clause="4.4 execution-prevention disqualifier",
        origin="fresh raise attack on E16 P4",
    )
    p4_escape = _replace_once(
        p4,
        '            direction = "higher" if result["difference"] > 0 else "lower"\n',
        '            direction = "higher" if result["difference"] > 0 else "lower"\n'
        '            fold_factor = len(OUTCOMES) if direction == "higher" else 1\n'
        '            adjusted = min(1.0, result["p_value"] * fold_factor)\n',
        "correct-presentation-local-rebound-into-fold",
    )
    add(
        "correct-presentation-local-rebound-into-fold",
        p4_key,
        p4_escape,
        expected=Outcome("abstain", "unresolved-manual-correction-present"),
        correct=True,
        category="terminal-adversary",
        clause="4.4 later-fold consumer disqualifier",
        origin="fresh presentation-local-to-correction attack on E16 P4",
    )
    p2_consumer = _replace_once(
        p2,
        "\ndef main():\n",
        "\ndef consume(value):\n    return value\n\ndef main():\n",
        "consume-helper",
    )
    p2_consumer = _replace_once(
        p2_consumer,
        '        verdict = "significant" if significant else "not significant"\n',
        '        verdict = "significant" if significant else "not significant"\n'
        "        consume(verdict)\n",
        "correct-terminal-verdict-unresolved-consumer",
    )
    add(
        "correct-terminal-verdict-unresolved-consumer",
        p2_key,
        p2_consumer,
        expected=Outcome("abstain", "hierarchical-gatekeeping-present"),
        correct=True,
        category="terminal-adversary",
        clause="4.2 total-consumer disqualifier",
        origin="fresh unresolved verdict consumer on E16 P2",
    )
    p2_second_branch = _replace_once(
        p2,
        '        verdict = "significant" if significant else "not significant"\n',
        '        verdict = "significant" if significant else "not significant"\n'
        '        if verdict == "significant":\n            print("second emission")\n',
        "correct-terminal-verdict-second-emission-branch",
    )
    add(
        "correct-terminal-verdict-second-emission-branch",
        p2_key,
        p2_second_branch,
        expected=Outcome("abstain", "hierarchical-gatekeeping-present"),
        correct=True,
        category="terminal-adversary",
        clause="4.2 sole-control-effect disqualifier",
        origin="fresh second-emission attack on E16 P2",
    )
    p2_factor = _replace_once(
        p2,
        '        verdict = "significant" if significant else "not significant"\n',
        '        verdict = "significant" if significant else "not significant"\n'
        '        factor = len(OUTCOMES) if verdict == "significant" else 1\n'
        "        adjusted = min(1.0, p_value * factor)\n",
        "correct-terminal-verdict-rebound-fold-factor",
    )
    add(
        "correct-terminal-verdict-rebound-fold-factor",
        p2_key,
        p2_factor,
        expected=Outcome("abstain", "unresolved-manual-correction-present"),
        correct=True,
        category="terminal-adversary",
        clause="4.2 correction-fold consumer disqualifier",
        origin="fresh verdict-to-factor attack on E16 P2",
    )
    p4_correction = _replace_once(
        p4,
        "from scipy import stats\n",
        "from scipy import stats\nfrom statsmodels.stats.multitest import multipletests\n",
        "correction-import",
    )
    p4_correction = _replace_once(
        p4_correction,
        '        if result["p_value"] < ALPHA:\n',
        '        if result["p_value"] < ALPHA:\n'
        '            multipletests([result["p_value"]], method="holm")\n',
        "correct-presentation-owner-correction-call",
    )
    add(
        "correct-presentation-owner-correction-call",
        p4_key,
        p4_correction,
        expected=Outcome("abstain", "hierarchical-gatekeeping-present"),
        correct=True,
        category="terminal-adversary",
        clause="3 global correction census and 4.4 owner-subtree disqualifier",
        origin="fresh correction-call attack on E16 P4",
    )

    add(
        "positive-helper-record-single-call-comprehension",
        p3_key,
        p3,
        expected=Outcome("candidate", "none", (), 5),
        correct=False,
        category="helper-positive",
        clause="5 exact single-call helper-record production",
        origin="sealed E16 P3 bytes",
    )
    p3_multicall = _replace_once(
        p3,
        "    results = {outcome: compare(data, outcome) for outcome in OUTCOMES}\n",
        "    diagnostic = compare(data, OUTCOMES[0])\n"
        "    results = {outcome: compare(data, outcome) for outcome in OUTCOMES}\n",
        "correct-helper-record-multiple-call-sites-divergent",
    )
    add(
        "correct-helper-record-multiple-call-sites-divergent",
        p3_key,
        p3_multicall,
        expected=Outcome("abstain", "extra-registered-test-outside-authorized-family"),
        correct=True,
        category="helper-adversary",
        clause="5.2 exactly-one-call-site disqualifier",
        origin="fresh divergent helper-call attack on E16 P3",
    )
    p3_global = _replace_once(p3, "ALPHA = 0.05\n", "ALPHA = 0.05\nSEEN = []\n", "seen-global")
    p3_global = _replace_once(
        p3_global,
        '    """Two-sample t-test for one outcome, shallow versus deep roofs."""\n',
        '    """Two-sample t-test for one outcome, shallow versus deep roofs."""\n'
        "    SEEN.append(outcome)\n",
        "correct-helper-record-mutates-nonlocal-state",
    )
    add(
        "correct-helper-record-mutates-nonlocal-state",
        p3_key,
        p3_global,
        expected=Outcome("abstain", "unresolved-pvalue-consumer"),
        correct=True,
        category="helper-adversary",
        clause="5.2 nonlocal/receiver mutation disqualifier",
        origin="fresh helper side-effect attack on E16 P3",
    )
    p3_raw = _replace_once(
        p3,
        '        verdict = "SIGNIFICANT" if result["significant"] else "not significant"\n',
        '        verdict = "SIGNIFICANT" if result["p_value"] < ALPHA else "not significant"\n',
        "correct-helper-record-conclusion-recomputed-from-raw-p",
    )
    add(
        "correct-helper-record-conclusion-recomputed-from-raw-p",
        p3_key,
        p3_raw,
        expected=Outcome("abstain", "unresolved-pvalue-consumer"),
        correct=True,
        category="helper-adversary",
        clause="5.3 no outside raw-p conclusion recomputation",
        origin="fresh raw-conclusion attack on E16 P3",
    )
    p3_conditional = _replace_once(
        p3,
        "    shallow = frame.loc[frame[GROUP_COLUMN] == SHALLOW, outcome]\n",
        "    if outcome == OUTCOMES[0]:\n        marker = True\n"
        "    shallow = frame.loc[frame[GROUP_COLUMN] == SHALLOW, outcome]\n",
        "correct-helper-record-conditional-store",
    )
    add(
        "correct-helper-record-conditional-store",
        p3_key,
        p3_conditional,
        expected=Outcome("abstain", "unresolved-pvalue-consumer"),
        correct=True,
        category="helper-adversary",
        clause="5.2 branch-free helper-body disqualifier",
        origin="fresh conditional helper-store attack on E16 P3",
    )
    p3_filter = _replace_once(
        p3,
        "    results = {outcome: compare(data, outcome) for outcome in OUTCOMES}\n",
        "    results = {outcome: compare(data, outcome) for outcome in OUTCOMES "
        "if outcome in OUTCOMES}\n",
        "correct-helper-record-comprehension-filter",
    )
    add(
        "correct-helper-record-comprehension-filter",
        p3_key,
        p3_filter,
        expected=Outcome("abstain", "authorized-family-test-census-incomplete"),
        correct=True,
        category="helper-adversary",
        clause="5.1 filter-free comprehension disqualifier",
        origin="fresh comprehension-filter attack on E16 P3",
    )
    p3_nested = _replace_once(
        p3,
        '        "n_shallow": int(shallow.size),\n',
        '        "meta": {"n_shallow": int(shallow.size)},\n'
        '        "n_shallow": int(shallow.size),\n',
        "correct-helper-record-nested-record",
    )
    add(
        "correct-helper-record-nested-record",
        p3_key,
        p3_nested,
        expected=Outcome("abstain", "unresolved-pvalue-consumer"),
        correct=True,
        category="helper-adversary",
        clause="5.2 flat-literal-record disqualifier",
        origin="fresh nested-record attack on E16 P3",
    )
    p3_consumer = _replace_once(
        p3,
        "\ndef main():\n",
        "\ndef inspect(value):\n    return value\n\ndef main():\n",
        "inspect-helper",
    )
    p3_consumer = _replace_once(
        p3_consumer,
        "    for outcome, result in results.items():\n",
        '    for outcome, result in results.items():\n        inspect(result["p_value"])\n',
        "correct-helper-record-unresolved-consumer",
    )
    add(
        "correct-helper-record-unresolved-consumer",
        p3_key,
        p3_consumer,
        expected=Outcome("abstain", "unresolved-pvalue-consumer"),
        correct=True,
        category="helper-adversary",
        clause="5.3 total-forward-consumer disqualifier",
        origin="fresh unresolved helper-record consumer on E16 P3",
    )
    return tuple(values)


def _explicit(
    *,
    before: str = "",
    after: str = "",
    decisions: str | None = None,
    imports: str = "",
) -> str:
    columns = ("daily_gain_g_per_day", "serum_urea_mmol_l", "haematocrit_pct")
    calls = []
    for index, column in enumerate(columns):
        calls.append(
            f'r{index} = stats.ttest_ind(df.loc[df["feed_group"] == "pellet_established", '
            f'"{column}"], df.loc[df["feed_group"] == "pellet_new", "{column}"])'
        )
    if decisions is None:
        decisions = "\n".join(f"print(r{i}.pvalue < 0.05)" for i in range(3))
    return (
        "import pandas as pd\nfrom scipy import stats\n"
        + imports
        + 'df = pd.read_csv("calves.csv")\n'
        + before
        + "\n".join(calls)
        + "\n"
        + decisions
        + "\n"
        + after
    )


def gatekeeping_fixtures() -> tuple[Fixture, ...]:
    case_key = "E10:P4:7296b0e2cf7faeefca64"
    rows: list[tuple[str, str, str]] = [
        (
            "frozen-gate-numpy-omnibus-assert",
            _explicit(
                imports="import numpy\n",
                before='gate = numpy.abs(numpy.mean(df[["daily_gain_g_per_day", "serum_urea_mmol_l", "haematocrit_pct"]].to_numpy(), axis=0)).sum()\nassert gate > 0\n',
            ),
            "hierarchical-gatekeeping-present",
        ),
        (
            "frozen-gate-match-subject-and-guard",
            _explicit(
                before='gate = df[["daily_gain_g_per_day", "serum_urea_mmol_l", "haematocrit_pct"]].to_numpy().sum()\nmatch gate:\n    case value if value > 0:\n        ready = True\n    case _:\n        ready = False\n'
            ),
            "hierarchical-gatekeeping-present",
        ),
        (
            "frozen-gate-bool-short-circuit-assert",
            _explicit(
                before='gate = df[["daily_gain_g_per_day", "serum_urea_mmol_l", "haematocrit_pct"]].to_numpy().sum()\nready = True\ncombined = ready and gate > 0\nassert combined\n'
            ),
            "hierarchical-gatekeeping-present",
        ),
        (
            "frozen-gate-rendering-unresolved-consumer",
            "def consume(value):\n    return value\n"
            + _explicit(
                decisions='s0 = "yes" if r0.pvalue < 0.05 else "no"\ns1 = "yes" if r1.pvalue < 0.05 else "no"\ns2 = "yes" if r2.pvalue < 0.05 else "no"\nprint(s0); print(s1); print(s2); consume(s0)'
            ),
            "hierarchical-gatekeeping-present",
        ),
        (
            "frozen-gate-rendering-second-branch",
            "READY = True\n"
            + _explicit(
                decisions='s0 = "yes" if r0.pvalue < 0.05 else "no"\ns1 = "yes" if r1.pvalue < 0.05 else "no"\ns2 = "yes" if r2.pvalue < 0.05 else "no"\nif READY:\n    print(s0)\nprint(s1); print(s2)'
            ),
            "hierarchical-gatekeeping-present",
        ),
        (
            "frozen-gate-rendering-call-arm",
            _explicit(
                decisions='s0 = "yes".upper() if r0.pvalue < 0.05 else "no"\ns1 = "yes" if r1.pvalue < 0.05 else "no"\ns2 = "yes" if r2.pvalue < 0.05 else "no"\nprint(s0); print(s1); print(s2)'
            ),
            "hierarchical-gatekeeping-present",
        ),
        (
            "frozen-gate-early-return",
            _explicit(
                imports="import numpy\n",
                before='gate = numpy.sum(df[["daily_gain_g_per_day", "serum_urea_mmol_l", "haematocrit_pct"]].to_numpy())\nif gate > 0:\n    return\n',
            ),
            "hierarchical-gatekeeping-present",
        ),
        (
            "frozen-gate-early-break",
            _explicit(
                imports="import numpy\n",
                before='gate = numpy.sum(df[["daily_gain_g_per_day", "serum_urea_mmol_l", "haematocrit_pct"]].to_numpy())\nfor _ in range(1):\n    if gate > 0:\n        break\n',
            ),
            "hierarchical-gatekeeping-present",
        ),
        (
            "frozen-gate-early-continue",
            _explicit(
                imports="import numpy\n",
                before='gate = numpy.sum(df[["daily_gain_g_per_day", "serum_urea_mmol_l", "haematocrit_pct"]].to_numpy())\nfor _ in range(1):\n    if gate > 0:\n        continue\n',
            ),
            "hierarchical-gatekeeping-present",
        ),
        (
            "frozen-gate-early-raise",
            _explicit(
                imports="import numpy\n",
                before='gate = numpy.sum(df[["daily_gain_g_per_day", "serum_urea_mmol_l", "haematocrit_pct"]].to_numpy())\nif gate > 0:\n    raise RuntimeError("gate")\n',
            ),
            "hierarchical-gatekeeping-present",
        ),
        (
            "frozen-gate-early-sys-exit",
            _explicit(
                imports="import numpy\nimport sys\n",
                before='gate = numpy.sum(df[["daily_gain_g_per_day", "serum_urea_mmol_l", "haematocrit_pct"]].to_numpy())\nif gate > 0:\n    sys.exit(0)\n',
            ),
            "hierarchical-gatekeeping-present",
        ),
        (
            "frozen-gate-unresolved-execution-prevention",
            _explicit(
                imports="import numpy\n",
                after='ready = True\ntry:\n    diagnostic = numpy.mean(df[["daily_gain_g_per_day", "serum_urea_mmol_l", "haematocrit_pct"]].to_numpy())\nfinally:\n    assert ready\n',
            ),
            "pvalue-control-dependence-unresolved",
        ),
    ]
    return tuple(
        Fixture(
            name,
            case_key,
            source.encode("utf-8"),
            Outcome("abstain", reason),
            True,
            "frozen-gatekeeping",
            "3.0 whole-module control registry and execution-prevention residual",
            "reproduced from tests/test_code_csv_multiple_testing_core_guards_v3.py",
        )
        for name, source, reason in rows
    )


def prior_fixtures() -> tuple[Any, ...]:
    namespace = runpy.run_path(str(V32_CATALOG))
    fixtures = namespace["all_fixtures"]()
    if len(fixtures) != 170:
        raise ValueError("the frozen 3.2 fixture population is not 170")
    return tuple(fixtures)


def all_fixtures() -> tuple[Any, ...]:
    result = (*prior_fixtures(), *gatekeeping_fixtures(), *terminal_and_helper_fixtures())
    names = [fixture.name for fixture in result]
    if len(names) != len(set(names)):
        raise ValueError("the 3.3 fixture census contains duplicate names")
    return result
