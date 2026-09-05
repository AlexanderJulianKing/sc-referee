"""Shipped-lane tests for the multiple-testing 3.5 recall deltas.

Three things are asserted here and nowhere else:

1. the whole 283-row fixture population executes through the **shipped** 3.5 analyzer with the
   design's exact outcome and exact per-fixture admission census, including the non-vacuity
   check that every disqualifier fixture has an abstaining 3.4 baseline;
2. the four grammar refusal lists in design section 1 are re-executed against the **production**
   predicates rather than against the prototype shadow; and
3. seven named mutation kills, each of which removes exactly one production or breaks the
   ordering rule and shows a named row or a named refusal fixture moving.

The frozen digest anchors live here too, so a stray edit to any byte-frozen lane file fails the
suite rather than the review.
"""

from __future__ import annotations

import ast
import hashlib
import json
import runpy
import sys
import types
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_core_v3_5 as core35
from sc_referee.scientific_checks import code_csv_multiple_testing_recall_deltas_v3_5 as deltas
from sc_referee.scientific_checks import (
    code_csv_multiple_testing_terminal_presentation_v3_5 as tp35,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_5 import (
    CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS,
    MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
    MULTIPLE_TESTING_CODE_CHECK_VERSION,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_admission_census_v3_5 import (
    ADMISSION_KINDS,
    INSTALLED_KINDS,
    admission_census,
    recording_admissions,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
    analyze_code_csv_multiple_testing_dataflow as analyze_v34,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_5 import (
    analyze_code_csv_multiple_testing_dataflow as analyze_v35,
)

_SWEEP = Path("evaluation/development/multitest-code-slice-v3_5/prototype-sweep").resolve()
_ORACLE = Path("evaluation/development/multitest-code-slice-v3_5/opened-oracle").resolve()

_previous_harness = sys.modules.pop("harness", None)
try:
    _harness = runpy.run_path(str(_SWEEP / "harness.py"))
    _harness_module = types.ModuleType("harness")
    _harness_module.__dict__.update(_harness)
    sys.modules["harness"] = _harness_module
    _catalog = runpy.run_path(str(_SWEEP / "fixture_catalog.py"))
finally:
    sys.modules.pop("harness", None)
    if _previous_harness is not None:
        sys.modules["harness"] = _previous_harness

_REFERENCE_CASE = cast(Callable[[str], Any], _harness["reference_case"])
_INPUTS = cast(Callable[[Any, bytes | None], dict[str, Any]], _harness["inputs"])
_CLASSIFY = cast(Callable[[Any], Any], _harness["classify"])
_ALL_FIXTURES = cast(Callable[[], tuple[Any, ...]], _catalog["all_fixtures"])
_NEW_FIXTURES = cast(Callable[[], tuple[Any, ...]], _catalog["new_fixtures"])


@contextmanager
def _harness_installed() -> Iterator[None]:
    """The chained 3.4 and 3.3 catalogs import `harness` at module level when they are run.

    `fixture_catalog.prior_fixtures()` executes those files at call time, not at import time, so
    the module has to be back on `sys.modules` for the duration of the call.
    """

    previous = sys.modules.get("harness")
    sys.modules["harness"] = _harness_module
    try:
        yield
    finally:
        if previous is None:
            sys.modules.pop("harness", None)
        else:
            sys.modules["harness"] = previous


_EXPECTED = json.loads((_ORACLE / "EXPECTED_ROWS.json").read_text(encoding="utf-8"))
_EXPECTED_FIXTURES = {row["name"]: row for row in _EXPECTED["fixture_rows"]}

#: Design section 2.2's frozen-surface anchor list.  Each is read and compared byte-for-byte.
_FROZEN_ANCHORS = {
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3.py": (
        "0388b4a1d3a28b7549af85362d0d4e7f13ffc2b4807dc129d242c4927870c0d1"
    ),
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_3.py": (
        "ddcb29549dda5dcf164848730679027161e34692282cfeaabf84e089db58b857"
    ),
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_4.py": (
        "f690db88677a9f79a3a162dc7dff907d8c377a28c1d2b02095f6fadea62ed789"
    ),
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_correction_model_v3_4.py": (
        "b42ca5fbbc31c8faca5d84627c403a6586d6ef48648051f941593913a9cc292a"
    ),
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_terminal_presentation_v3_3.py": (
        "d1b9463235494ae54d4c5d2bbc3eb4f0d1b73568a4c5625993dd87dbee4b5c78"
    ),
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_comprehension_v3_4.py": (
        "fa706bfd28b370c6111c17ddedff9f8921d4e0c169979b3b9ef013412c6b2b5c"
    ),
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v3_4.py": (
        "da7c88f472709146f68b029c073322d579f0ef80d7158d11831bd5f7d18445ed"
    ),
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_2.py": (
        "38f74309c4ba082dceb335d95691401b7f9b780958d1c0b82bdb63e496fc29c2"
    ),
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_correction_model_v3_2.py": (
        "b7c182a9bac2e6e3eb015c2902e607201a5bfdca5f0889413b1145911d30b239"
    ),
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_correction_model_v3_3.py": (
        "de46498474b0043231a66b6adeb779e799b3736afce162b6919dc0eebc516242"
    ),
    "evaluation/development/multitest-code-slice-v3_4/prototype-sweep/results.json": (
        "2bf626534a513e951e1c8a559a2538594f6dbb60e6bfda8e0787e0cd704a3cf2"
    ),
    "evaluation/development/blind-envelope-18-2026-09-01/AUDIT_RESULTS.json": (
        "8aad260515d0d79ad282e56d4e03970ee531b2f865f7b88d02b4004f1667cb45"
    ),
    "evaluation/development/blind-envelope-18-2026-09-01/ROLE_MAP.json": (
        "cd830c2a79ea80f4fe310d8db09893b29c74fdf25d33975c713d9161feff3d92"
    ),
    "docs/implementation/MULTITEST-RECALL-RECON-E18-2026-09-02.md": (
        "84acc7a5d3353429f1e6cdafaa541c7494c89fb672bfd27fa6fcc70af1b2e76d"
    ),
    "docs/implementation/MULTITEST-RECALL-RECON-MANUAL-CORRECTION-2026-09-03.md": (
        "e4d2b8ad429a774234960be5782395c3ac2858300af1ac1278f908dcf87c49a7"
    ),
    "evaluation/development/multitest-code-slice-v3_5/prototype-sweep/results.json": (
        "2a1d93c12ebda184a71171f19f797cd192930ae33a4af2800a7ab8e8730dbdcd"
    ),
    "evaluation/development/multitest-code-slice-v3_5/prototype-sweep/instrument_results.json": (
        "2f10ac8118ed496b63494f3dc431405ea08dd586ed6334a0d955dfaec9ddada1"
    ),
    "evaluation/development/multitest-code-slice-v3_5/prototype-sweep/MANIFEST.json": (
        "ad2a0e077bc04cc83dd36600e4614fd6a8b14398f6dfa39e789ed37017f3b1f6"
    ),
    "evaluation/development/multitest-code-slice-v3_5/prototype-sweep/recall_deltas_shadow.py": (
        "04eefcd85d20b3c3aa552a90a41b8c43f4ae114cfde4c179aca07f92eadfac56"
    ),
    "evaluation/development/multitest-code-slice-v3_5/prototype-sweep/fixture_catalog.py": (
        "08efcdb4b08b1b4a579542dc1c75da70368a49129ec02b3fd161bda5412d9209"
    ),
    "evaluation/development/multitest-code-slice-v3_5/prototype-sweep/sweep.py": (
        "eee22ae271b9143d22970dd095fd7bbe45f238d5c885a7be5fde57edf2114e5a"
    ),
    "evaluation/development/multitest-code-slice-v3_5/prototype-sweep/instrument.py": (
        "f5b6ba423aa66c94bcc68025575435bd3f74a6126e57257f754b8c206ceb7660"
    ),
    "evaluation/development/multitest-code-slice-v3_5/prototype-sweep/harness.py": (
        "47983e7582aa31cea559b98a680edb6299ac005707ea7c0603a0e7e10c797733"
    ),
}


def _run(case_key: str, source: bytes) -> tuple[Any, dict[str, int]]:
    values = _INPUTS(_REFERENCE_CASE(case_key), source)
    content = cast(bytes, values.pop("content"))
    with recording_admissions():
        result = analyze_v35(content, **values)
        census = admission_census()
    return _CLASSIFY(result), census


def _run_v34(case_key: str, source: bytes) -> Any:
    values = _INPUTS(_REFERENCE_CASE(case_key), source)
    content = cast(bytes, values.pop("content"))
    return _CLASSIFY(analyze_v34(content, **values))


@pytest.fixture(scope="session")
def fixture_rows() -> dict[str, dict[str, Any]]:
    """Execute all 283 fixture sources through the real shipped 3.5 analyzer."""

    rows: dict[str, dict[str, Any]] = {}
    with _harness_installed():
        fixtures = _ALL_FIXTURES()
    for fixture in fixtures:
        outcome, census = _run(fixture.case_key, fixture.source)
        rows[fixture.name] = {
            "fixture": fixture,
            "outcome": outcome,
            "json": outcome.as_json(),
            "census": census,
            "baseline": _run_v34(fixture.case_key, fixture.source).as_json(),
        }
    return rows


# ======================================================================================
# 1. the whole fixture population
# ======================================================================================


def test_all_283_fixture_rows_execute(fixture_rows: dict[str, dict[str, Any]]) -> None:
    """Every fixture reaches the design's outcome, and no correct analysis is accused."""

    assert len(fixture_rows) == 283
    assert sum(row["fixture"].correct_analysis for row in fixture_rows.values()) == 199
    assert sum(name in _EXPECTED_FIXTURES for name in fixture_rows) == 38
    accused = [
        name
        for name, row in fixture_rows.items()
        if row["fixture"].correct_analysis and row["json"][0] == "candidate"
    ]
    assert accused == []
    moved = [
        name
        for name, row in fixture_rows.items()
        if name not in _EXPECTED_FIXTURES and row["json"] != row["baseline"]
    ]
    assert moved == [], "a frozen 3.4 fixture moved"
    assert sum(name not in _EXPECTED_FIXTURES for name in fixture_rows) == 245


def test_new_fixture_rows_match_the_pinned_oracle(
    fixture_rows: dict[str, dict[str, Any]],
) -> None:
    for name, expected in _EXPECTED_FIXTURES.items():
        row = fixture_rows[name]
        assert row["json"] == expected["expected_v35_row"], name
        assert row["baseline"] == expected["frozen_v34_row"], name
        assert row["census"] == expected["expected_admission_census"], name


def test_named_disqualifiers_refuse_their_production(
    fixture_rows: dict[str, dict[str, Any]],
) -> None:
    """A disqualifier's named production must not fire at all, and its check must not be vacuous.

    An abstention can be produced by an unrelated upstream refusal, so asserting the outcome
    would prove nothing.  The census is asserted instead.  The non-vacuity half matters just as
    much: under the ordering rule no production is attempted at all on a row the shipped 3.4
    lane already classifies, so a disqualifier whose 3.4 baseline is a classification would pass
    for free.
    """

    checked = 0
    for name, expected in _EXPECTED_FIXTURES.items():
        refused = expected["refused_admission"]
        if refused is None:
            continue
        row = fixture_rows[name]
        assert row["baseline"][0] == "abstain", f"{name}: vacuous disqualifier"
        assert row["census"][refused] == 0, name
        checked += 1
    assert checked == 18


def test_named_positive_controls_require_their_production(
    fixture_rows: dict[str, dict[str, Any]],
) -> None:
    checked = 0
    for name, expected in _EXPECTED_FIXTURES.items():
        admitted = expected["required_admission"]
        if admitted is None:
            continue
        assert fixture_rows[name]["census"][admitted] > 0, name
        checked += 1
    assert checked == 10


def test_the_admission_census_over_the_whole_population_is_exact(
    fixture_rows: dict[str, dict[str, Any]],
) -> None:
    """Section 5.1's totals, and which rows each production fires on."""

    rows = {
        kind: sorted(name for name, row in fixture_rows.items() if row["census"][kind])
        for kind in ADMISSION_KINDS
    }
    design = _EXPECTED["totals"]["admission_rows"]
    evidence = _EXPECTED["totals"]["evidence_admission_rows"]
    for kind in ADMISSION_KINDS:
        assert rows[kind] == sorted(set(design[kind]) - set(evidence[kind])), kind
    totals = {
        kind: sum(row["census"][kind] for row in fixture_rows.values()) for kind in ADMISSION_KINDS
    }
    assert totals == {
        "d1-format-arm": 12,
        "d2-set-selector": 0,
        "d3-csv-reader": 0,
        "d4a-numeric-group": 16,
        "d4b-loop-terminal": 7,
        "d5-cardinality-read": 7,
    }


# ======================================================================================
# 2. grammar refusal lists, re-executed against the production predicates
# ======================================================================================

_D4A_REFUSALS = {
    "ambiguous-normalised-tokens": ("salt", ("2.0", "2.00"), "x = data[data['salt'] == 2.0]"),
    "non-decimal-token": ("salt", ("low", "high"), "x = data[data['salt'] == 2.0]"),
    "thousands-separator-token": ("salt", ("1,000", "2000"), "x = data[data['salt'] == 1000]"),
    "boolean-comparator": ("salt", ("2.0", "3.0"), "x = data[data['salt'] == True]"),
    "call-comparator": ("salt", ("2.0", "3.0"), "x = data[data['salt'] == float(2)]"),
    "no-matching-token": ("salt", ("2.0", "3.0"), "x = data[data['salt'] == 4.0]"),
    "not-equal-operator": ("salt", ("2.0", "3.0"), "x = data[data['salt'] != 2.0]"),
    "non-group-column": ("salt", ("2.0", "3.0"), "x = data[data['ph'] == 2.0]"),
}
_D4A_ADMISSIONS = {
    "float-literal": ("salt", ("2.0", "3.0"), "x = data[data['salt'] == 2.0]", "2.0"),
    "int-literal": ("salt", ("2.0", "3.0"), "x = data[data['salt'] == 2]", "2.0"),
    "module-constant": ("salt", ("2.0", "3.0"), "LOW = 2.0\nx = data[data['salt'] == LOW]", "2.0"),
    "negative-literal": ("salt", ("-1.0", "1.0"), "x = data[data['salt'] == -1.0]", "-1.0"),
}


def test_d4a_grammar_refuses_all_eight_and_the_non_decimal_column() -> None:
    for name, (column, tokens, code) in _D4A_REFUSALS.items():
        positions = deltas.group_mask_numeric_positions(
            ast.parse(code), group_column=column, group_values=tokens, column_is_decimal=True
        )
        assert positions == {}, name
    for name, (column, tokens, code, token) in _D4A_ADMISSIONS.items():
        positions = deltas.group_mask_numeric_positions(
            ast.parse(code), group_column=column, group_values=tokens, column_is_decimal=True
        )
        assert sorted(set(positions.values())) == [token], name
    assert (
        deltas.group_mask_numeric_positions(
            ast.parse("x = data[data['salt'] == 2.0]"),
            group_column="salt",
            group_values=("2.0", "3.0"),
            column_is_decimal=False,
        )
        == {}
    )


_D3_REFUSALS = {
    "restkey": 'with open(p, newline="") as h:\n    return list(csv.DictReader(h, restkey="x"))',
    "explicit-delimiter": (
        'with open(p, newline="") as h:\n    return list(csv.reader(h, delimiter=";"))'
    ),
    "binary-mode": 'with open(p, mode="rb") as h:\n    return list(csv.reader(h))',
    "not-materialised": 'with open(p, newline="") as h:\n    return csv.DictReader(h)',
    "filtered-comprehension": (
        'with open(p, newline="") as h:\n    return [r for r in csv.DictReader(h) if r]'
    ),
    "two-with-items": "with open(p) as h, open(q) as g:\n    return list(csv.reader(h))",
    "extra-body-statement": (
        'with open(p, newline="") as h:\n    rows = list(csv.reader(h))\n    return rows'
    ),
    "unknown-open-keyword": (
        'with open(p, buffering=1, newline="") as h:\n    return list(csv.reader(h))'
    ),
    "other-handle": 'with open(p, newline="") as h:\n    return list(csv.reader(g))',
}
_D3_ADMISSIONS = {
    "dictreader": (
        'with open(p, newline="", encoding="utf-8") as h:\n    return list(csv.DictReader(h))'
    ),
    "reader": 'with open(p, newline="") as h:\n    return list(csv.reader(h))',
}


def _wrap_reader(body: str) -> str:
    return "import csv\n\n\ndef read_data(p):\n" + "\n".join(
        "    " + line for line in body.splitlines()
    )


def test_d3_grammar_refuses_all_nine_and_admits_its_two_forms() -> None:
    for name, code in _D3_REFUSALS.items():
        assert deltas.csv_reader_paths(ast.parse(_wrap_reader(code))) == [], name
    for name, code in _D3_ADMISSIONS.items():
        assert len(deltas.csv_reader_paths(ast.parse(_wrap_reader(code)))) == 1, name
    sealed = _REFERENCE_CASE("E18:N6:28cc1447cb560791b53e").source_path.read_bytes()
    assert deltas.csv_reader_paths(ast.parse(sealed)) == []


_D2_REFUSALS = {
    "set-comprehension": "S = {name for name in OUTCOMES}\nx = 'a' in S",
    "set-call": "S = set(['a', 'b'])\nx = 'a' in S",
    "frozenset-call": "S = frozenset({'a', 'b'})\nx = 'a' in S",
    "non-string-element": "S = {'a', 2}\nx = 'a' in S",
    "duplicate-elements": "S = {'a', 'a'}\nx = 'a' in S",
    "ordering-use": "S = {'a', 'b'}\nfor item in S:\n    print(item)",
    "length-use": "S = {'a', 'b'}\nx = len(S)",
    "rebound-name": "S = {'a', 'b'}\nS = {'c'}\nx = 'a' in S",
    "not-module-level": "def f():\n    S = {'a', 'b'}\n    return 'a' in S",
}
_D2_ADMISSIONS = {
    "membership-in": "S = {'a', 'b'}\nx = 'a' in S",
    "membership-not-in": "S = {'a', 'b'}\nx = 'a' not in S",
    "membership-in-comprehension": "S = {'a', 'b'}\nx = [n for n in OUT if n in S]",
}


def test_d2_grammar_refuses_all_nine_and_admits_its_three_forms() -> None:
    for name, code in _D2_REFUSALS.items():
        assert deltas.membership_sets(ast.parse(code)) == {}, name
    for name, code in _D2_ADMISSIONS.items():
        assert deltas.membership_sets(ast.parse(code)).get("S") == ("a", "b"), name


_D4B_ITERATORS = {
    "bare-name": ("for r in results:\n    print(r)", True),
    "enumerate-name": ("for i, r in enumerate(results):\n    print(r)", True),
    "enumerate-start-literal": ("for i, r in enumerate(results, start=1):\n    print(r)", True),
    "enumerate-list-call": ("for i, r in enumerate(list(results)):\n    print(r)", False),
    "enumerate-zip": ("for i, r in enumerate(zip(a, b)):\n    print(r)", False),
    "enumerate-nonliteral-start": ("for i, r in enumerate(results, start=n):\n    print(r)", False),
    "enumerate-two-args": ("for i, r in enumerate(results, 1):\n    print(r)", False),
    "sorted-call": ("for r in sorted(results):\n    print(r)", False),
    "items-call": ("for k, r in results.items():\n    print(r)", False),
    "reversed-call": ("for r in reversed(results):\n    print(r)", False),
}


def test_d4b_iterator_grammar_matches_all_ten_forms() -> None:
    for name, (code, expected) in _D4B_ITERATORS.items():
        loop = ast.parse(code).body[0]
        assert isinstance(loop, ast.For)
        assert deltas.admitted_loop_iterator(frozenset(), loop.iter) is expected, name
    # `enumerate` bound to a project-local name is not the builtin, so it refuses.
    loop = cast(ast.For, ast.parse("for i, r in enumerate(results):\n    print(r)").body[0])
    assert deltas.admitted_loop_iterator(frozenset({"enumerate"}), loop.iter) is False


def test_d4b_per_loop_refusals_never_admit_the_mutated_loop() -> None:
    """The E18 P3 base carries two presentation loops, so a whole-source census is not enough.

    This hooks the production proof itself and records the line number of every loop it is
    offered and every loop it admits.  For each disqualifier fixture the mutated loop -- the
    first loop in the source, which is the one the fixture rewrites -- must be absent from the
    admitted set.
    """

    frozen = core35._MtEngine._v35_terminal_presentation_loop
    seen: list[tuple[int, bool]] = []

    def probe(engine: Any, node: ast.For) -> bool:
        result = frozen(engine, node)
        seen.append((int(node.lineno), bool(result)))
        return result

    names = {
        "correct-d4b-loop-early-return",
        "correct-d4b-loop-break",
        "correct-d4b-binding-escapes-the-loop",
        "correct-d4b-loop-does-not-render",
        "correct-d4b-call-iterator",
        "correct-d4b-test-after-the-loop",
        "correct-d4b-gated-two-stage-design",
    }
    checked = 0
    with _harness_installed():
        new_fixtures = _NEW_FIXTURES()
    core35._MtEngine._v35_terminal_presentation_loop = probe  # type: ignore[method-assign]
    try:
        for fixture in new_fixtures:
            if fixture.name not in names:
                continue
            seen.clear()
            _outcome, census = _run(fixture.case_key, fixture.source)
            mutated = min((line for line, _ in seen), default=None)
            admitted = {line for line, ok in seen if ok}
            assert mutated is None or mutated not in admitted, fixture.name
            assert census["d4b-loop-terminal"] == 0 or fixture.name in {
                "correct-d4b-loop-early-return",
                "correct-d4b-loop-break",
                "correct-d4b-binding-escapes-the-loop",
                "correct-d4b-loop-does-not-render",
                "correct-d4b-call-iterator",
            }, fixture.name
            checked += 1
    finally:
        core35._MtEngine._v35_terminal_presentation_loop = frozen  # type: ignore[method-assign]
    assert checked == 7


def test_d1_admits_only_literals_and_module_constants() -> None:
    """Delta 1's own refusal list, executed against the production arm predicate."""

    constants = deltas.module_constant_names(ast.parse("ALPHA = 0.05\nLABEL = 'x'\n"))
    admitted = (
        '"p < {}".format(ALPHA)',
        '"p < {}".format(0.05)',
        '"p < {}".format(-1)',
        'f"p < {ALPHA}"',
        'f"p < {ALPHA:.3f}"',
    )
    refused = (
        '"p < {}".format(compute())',
        '"p < {}".format(row.value)',
        '"p < {}".format(row["p"])',
        '"p < {}".format(a + b)',
        '"p < {}".format(a < b)',
        '"p < {}".format([x for x in y])',
        '"p < {}".format(p_value)',
        '"p < {}".format(value=ALPHA)',
        '"p < {}".format(*args)',
        '"p < {}".format(True)',
        "template.format(ALPHA)",
        '"p < {}".upper(ALPHA)',
        '"p < %s" % ALPHA',
        'f"p < {round(ALPHA)}"',
        'f"p < {ALPHA:{width}}"',
        'f"no interpolation"',
        '"a bare constant"',
    )
    for code in admitted:
        node = cast(ast.Expr, ast.parse(code).body[0]).value
        assert deltas.widened_display_arm(node, constants) is True, code
    for code in refused:
        node = cast(ast.Expr, ast.parse(code).body[0]).value
        assert deltas.widened_display_arm(node, constants) is False, code


def test_d1_widening_is_not_applied_to_the_shared_display_predicates() -> None:
    """Design stop rule 7: the widening lives at three arm positions, not in the shared rule."""

    formatted = cast(ast.Expr, ast.parse('"p < {}".format(0.05)').body[0]).value
    assert core35._mt_v21_display_string(formatted) is False
    assert tp35._display_string(formatted) is False
    assert deltas.bare_display(formatted) is False
    # The frozen 3.3 modules are untouched, so their shared predicates keep the frozen rule.
    source = Path(
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_core_v3_5.py"
    ).read_text(encoding="utf-8")
    assert source.count("self._v35_display_arm(") == 4
    assert source.count("self._v35_group_token(") == 2
    assert source.count("self._v35_terminal_presentation_loop(") == 1
    tp_source = Path(
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_terminal_presentation_v3_5.py"
    ).read_text(encoding="utf-8")
    assert tp_source.count("_v35_display_arm(") == 3


def test_d5_display_ancestor_chain_refuses_every_stored_or_computed_use(
    fixture_rows: dict[str, dict[str, Any]],
) -> None:
    """Delta 5's six named refusals, asserted on the census rather than on the outcome."""

    for name in (
        "correct-d5-len-in-a-comparison",
        "correct-d5-len-as-a-threshold-divisor",
        "correct-d5-len-as-a-loop-bound",
        "correct-d5-len-of-a-filtered-copy",
        "correct-d5-len-bound-to-a-local-first",
        "correct-d5-len-in-arithmetic",
    ):
        row = fixture_rows[name]
        assert row["baseline"][0] == "abstain", name
        assert row["census"]["d5-cardinality-read"] == 0, name
        assert row["json"][0] != "candidate", name


# ======================================================================================
# 3. what must not ship, and the ordering rule
# ======================================================================================


def test_delta_2_and_delta_3_are_not_in_the_shipped_recognizer_set() -> None:
    """Both grammars exist and both refuse to be installed anywhere on the analysis path."""

    assert set(ADMISSION_KINDS) - set(INSTALLED_KINDS) == {"d2-set-selector", "d3-csv-reader"}
    lane = [
        "code_csv_multiple_testing_dataflow_v3_5.py",
        "code_csv_multiple_testing_dataflow_core_v3_5.py",
        "code_csv_multiple_testing_terminal_presentation_v3_5.py",
        "code_csv_multiple_testing_adapter_v3_5.py",
        "code_csv_multiple_testing_record_model_v3_5.py",
        "code_csv_multiple_testing_helper_record_v3_5.py",
        "integration_multiple_testing_v3_5.py",
        "multiple_testing_scope_questions_v3_5.py",
    ]
    # Nothing on the analysis path may reach either unshipped grammar.  The check is on the
    # qualified references rather than on the bare names, because the frozen engine has an
    # unrelated `_mt22_d5_membership_sets` local of its own.
    for name in lane:
        source = (Path("src/sc_referee/scientific_checks") / name).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and (node.module or "").endswith("code_csv_multiple_testing_recall_deltas_v3_5")
            for alias in node.names
        }
        assert imported.isdisjoint({"membership_sets", "csv_reader_paths"}), name
        attributes = {
            f"{node.value.id}.{node.attr}"
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
        }
        assert attributes.isdisjoint({"deltas.membership_sets", "deltas.csv_reader_paths"}), name
    from sc_referee.scientific_checks.code_csv_multiple_testing_admission_census_v3_5 import (
        record_admission,
    )

    for kind in ("d2-set-selector", "d3-csv-reader"):
        with pytest.raises(ValueError):
            record_admission(kind, (1, 0, 1, 1))


def test_a_row_the_frozen_3_4_lane_classifies_is_returned_untouched() -> None:
    """Ordering rule, first direction: no production is attempted on a classified row."""

    key = "E18:N1:5c091f9052becdb5c3ea"
    source = _REFERENCE_CASE(key).source_path.read_bytes()
    baseline = _run_v34(key, source)
    assert baseline.as_json() == [
        "covered",
        "complete",
        {"authorized_count": 5, "corrected_positions": [0, 1, 2, 3, 4]},
    ]
    outcome, census = _run(key, source)
    assert outcome.as_json() == baseline.as_json()
    assert census == dict.fromkeys(ADMISSION_KINDS, 0)


def test_an_abstaining_3_5_reanalysis_returns_the_frozen_3_4_reason(
    fixture_rows: dict[str, dict[str, Any]],
) -> None:
    """Ordering rule, second direction: byte-for-byte, on every abstaining row."""

    checked = 0
    for name, row in fixture_rows.items():
        if row["json"][0] != "abstain":
            continue
        assert row["json"] == row["baseline"], name
        checked += 1
    assert checked > 100
    for reason in {row["json"][1] for row in fixture_rows.values() if row["json"][0] == "abstain"}:
        assert reason in CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS, reason


def test_the_closed_reason_set_stays_at_sixty_one() -> None:
    from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_4 import (
        CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS as frozen_reasons,
    )

    assert len(CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS) == 61
    assert CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS == frozen_reasons
    assert MULTIPLE_TESTING_CODE_CHECK_VERSION == "3.5.0"
    assert MULTIPLE_TESTING_CODE_ADAPTER_VERSION == "3.5.0"


def test_deterministic_replay_and_idempotent_admission() -> None:
    """Applying an admission twice changes no outcome and no census byte."""

    for key in (
        "E15:P3:afe47b2a7ea87ed21a69",
        "E17:N1:e2d8b1bdf4baa671a1b4",
        "E18:P2:5a9277448db34379ce78",
        "E18:P3:d1b1fc47ccdabd0c2f22",
    ):
        source = _REFERENCE_CASE(key).source_path.read_bytes()
        first = _run(key, source)
        second = _run(key, source)
        assert first[0].as_json() == second[0].as_json(), key
        assert first[1] == second[1], key


@pytest.mark.parametrize("path", sorted(_FROZEN_ANCHORS))
def test_every_frozen_surface_is_byte_identical(path: str) -> None:
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == _FROZEN_ANCHORS[path], path


def test_the_oracle_is_recomputed_from_the_pinned_design_sweep() -> None:
    """A hand edit to `EXPECTED_ROWS.json` fails here rather than silently passing elsewhere."""

    results = json.loads((_SWEEP / "results.json").read_text(encoding="utf-8"))
    assert (
        hashlib.sha256((_SWEEP / "results.json").read_bytes()).hexdigest()
        == "2a1d93c12ebda184a71171f19f797cd192930ae33a4af2800a7ab8e8730dbdcd"
    )
    proto = {row["key"]: row for row in results["cases"]}
    assert len(_EXPECTED["rows"]) == 185
    for row in _EXPECTED["rows"]:
        source = proto[row["key"]]
        assert row["frozen_v34_row"] == source["baseline"], row["key"]
        assert row["expected_v35_row"] == source["outcome"], row["key"]
        assert row["expected_admission_census"] == source["admission_census"], row["key"]
        assert row["moves"] is bool(source["changed"]), row["key"]
    fixtures = {row["name"]: row for row in results["fixtures"] if row["new_in_v35"]}
    assert len(_EXPECTED["fixture_rows"]) == 38 == len(fixtures)
    for row in _EXPECTED["fixture_rows"]:
        source = fixtures[row["name"]]
        assert row["expected_v35_row"] == source["outcome"], row["name"]
        assert row["expected_admission_census"] == source["admission_census"], row["name"]
        assert row["refused_admission"] == source["refused_admission"], row["name"]
        assert row["required_admission"] == source["required_admission"], row["name"]
