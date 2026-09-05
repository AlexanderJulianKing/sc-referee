"""Observed trigger attribution and grammar-level refusal probes for the MT 3.5 design.

Every value written here is captured from an executed run of shipped code, or from an
executed call of the prototype grammar itself.  Nothing in this file is read off the
recon by eye.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import recall_deltas_shadow as shadow
from harness import Outcome, classify, inputs, reference_case
from sc_referee.scientific_checks import (
    code_csv_multiple_testing_dataflow_v3_3 as df33,
)
from sc_referee.scientific_checks import (
    code_csv_multiple_testing_dataflow_v3_4 as df34,
)

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "instrument_results.json"

P2_KEY = "E18:P2:5a9277448db34379ce78"
P3_KEY = "E18:P3:d1b1fc47ccdabd0c2f22"
P6_KEY = "E18:P6:2d2f5dd68825c378126b"
N5_KEY = "E18:N5:5ed2b0a375235333b96e"
N6_KEY = "E18:N6:28cc1447cb560791b53e"
E15P3_KEY = "E15:P3:afe47b2a7ea87ed21a69"


def _analyze(key: str, source: bytes | None = None, *, kinds: tuple[str, ...] | None = None) -> Any:
    case = reference_case(key)
    values = inputs(case, source)
    content = values.pop("content")
    if kinds is None:
        return shadow.analyze_v35_shadow(content, **values)
    return shadow.analyze_v35_shadow(content, kinds=kinds, **values)


def _outcome(result: Any) -> list[object]:
    return classify(result).as_json()


def _frozen(key: str, source: bytes | None = None) -> list[object]:
    case = reference_case(key)
    values = inputs(case, source)
    content = values.pop("content")
    return _outcome(df34.analyze_code_csv_multiple_testing_dataflow(content, **values))


def _replace(source: bytes, old: str, new: str) -> bytes:
    text = source.decode("utf-8")
    if text.count(old) != 1:
        raise ValueError(f"replacement anchor count is {text.count(old)}")
    return text.replace(old, new).encode("utf-8")


# --------------------------------------------------------------------------------------
# E18 P2: the arm predicate is the whole wall
# --------------------------------------------------------------------------------------

P2_VERDICT = """        verdict = (
            "significant difference at p < {}".format(ALPHA)
            if p_value < ALPHA
            else "no significant difference at p < {}".format(ALPHA)
        )
"""


def _p2_probe() -> dict[str, Any]:
    source = reference_case(P2_KEY).source_path.read_bytes()
    tree = ast.parse(source)
    ifexps = [node for node in ast.walk(tree) if isinstance(node, ast.IfExp)]
    constants = shadow.module_constant_names(tree)
    arms = [
        {
            "span": list(shadow._span(arm)),
            "node": type(arm).__name__,
            "frozen_display_string": bool(df33._mt_v21_display_string(arm)),
            "widened_display_arm": bool(shadow.widened_display_arm(arm, constants)),
        }
        for node in ifexps
        for arm in (node.body, node.orelse)
    ]
    ladder = {
        "r0-sealed": {"frozen_3_4": _frozen(P2_KEY), "v3_5": _outcome(_analyze(P2_KEY).outcome)},
    }
    rungs = {
        "r1-bare-constant-arms": """        verdict = (
            "significant difference"
            if p_value < ALPHA
            else "no significant difference"
        )
""",
        "rB-fstring-arms": """        verdict = (
            f"significant difference at p < {ALPHA}"
            if p_value < ALPHA
            else f"no significant difference at p < {ALPHA}"
        )
""",
        "rC-if-statement-format-arms": """        if p_value < ALPHA:
            verdict = "significant difference at p < {}".format(ALPHA)
        else:
            verdict = "no significant difference at p < {}".format(ALPHA)
""",
    }
    for name, replacement in rungs.items():
        variant = _replace(source, P2_VERDICT, replacement)
        ladder[name] = {
            "frozen_3_4": _frozen(P2_KEY, variant),
            "v3_5": _outcome(_analyze(P2_KEY, variant).outcome),
        }
    return {
        "module_constant_names": sorted(constants),
        "ifexp_count": len(ifexps),
        "arms": arms,
        "ladder": ladder,
    }


# --------------------------------------------------------------------------------------
# E18 P3: which frozen route actually parses the group mask, and the second wall
# --------------------------------------------------------------------------------------

P3_CONSTANTS = "LOW_SALT = 2.0\nHIGH_SALT = 3.0\n"


def _p3_probe() -> dict[str, Any]:
    source = reference_case(P3_KEY).source_path.read_bytes()
    case = reference_case(P3_KEY)
    values = inputs(case)
    content = values.pop("content")

    frozen_mask = df33._mask
    calls: list[str] = []

    def counting_mask(node: ast.expr, receiver: str, resolver: Any) -> Any:
        calls.append(type(node).__name__)
        return frozen_mask(node, receiver, resolver)

    df33._mask = counting_mask
    try:
        df34._reanalyze_with_v34_admissions(content, **values)
    finally:
        df33._mask = frozen_mask

    tree = ast.parse(source)
    positions = shadow.group_mask_numeric_positions(
        tree,
        group_column=values["group_column"],
        group_values=values["group_values"],
        column_is_decimal=shadow.group_column_is_decimal(
            values["csv_content"], values["group_column"]
        ),
    )
    ladder = {
        "r0-sealed": {"frozen_3_4": _frozen(P3_KEY), "v3_5": _outcome(_analyze(P3_KEY).outcome)},
        "r1-string-group-constants": {},
        "d4a-only": {},
        "d4a-and-d4b": {},
    }
    variant = _replace(source, P3_CONSTANTS, 'LOW_SALT = "2.0"\nHIGH_SALT = "3.0"\n')
    ladder["r1-string-group-constants"] = {
        "frozen_3_4": _frozen(P3_KEY, variant),
        "v3_5": _outcome(_analyze(P3_KEY, variant).outcome),
    }
    ladder["d4a-only"] = {
        "v3_5_reanalysis_reason": _analyze(
            P3_KEY, kinds=("d4a-numeric-group",)
        ).reanalysis_reason,
        "outcome": _outcome(_analyze(P3_KEY, kinds=("d4a-numeric-group",)).outcome),
    }
    ladder["d4a-and-d4b"] = {
        "outcome": _outcome(
            _analyze(P3_KEY, kinds=("d4a-numeric-group", "d4b-loop-terminal")).outcome
        )
    }
    return {
        "frozen_mask_call_count": len(calls),
        "frozen_mask_call_kinds": calls,
        "admitted_comparator_spans": {
            ",".join(str(item) for item in span): token for span, token in sorted(positions.items())
        },
        "group_values": list(values["group_values"]),
        "group_column_is_decimal": shadow.group_column_is_decimal(
            values["csv_content"], values["group_column"]
        ),
        "ladder": ladder,
    }


# --------------------------------------------------------------------------------------
# E18 P6: the reader wall, and the wall behind it
# --------------------------------------------------------------------------------------


def _loose_reader_probe(key: str) -> dict[str, Any]:
    """A deliberately over-generous reader admission, used as an upper bound.

    Any module containing a `csv.DictReader` or `csv.reader` call is granted the authorized
    path.  This is strictly looser than the D3 grammar, so a rung that still fails to reach a
    classification under it cannot reach one under D3 either.
    """

    case = reference_case(key)
    values = inputs(case)
    content = values.pop("content")
    frozen_census = df33._mt_full_scope_reader_census
    authorized = values["authorized_path"]
    trigger: dict[str, Any] = {}

    def loose(tree: ast.Module, **kwargs: Any) -> Any:
        result = frozen_census(tree, **kwargs)
        found = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"DictReader", "reader"}
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "csv"
            for node in ast.walk(tree)
        )
        return [*result, authorized] if found else result

    frozen_binder = df33._bind_helper_body if hasattr(df33, "_bind_helper_body") else None
    df33._mt_full_scope_reader_census = loose
    try:
        attempted = df34._reanalyze_with_v34_admissions(content, **values)
    finally:
        df33._mt_full_scope_reader_census = frozen_census
    if attempted.reason == "helper-free-name-unbound":
        trigger = _free_name_trigger(key)
    return {
        "frozen_3_4": _frozen(key),
        "loose_reader_reanalysis": _outcome(attempted),
        "free_name_trigger": trigger,
        "d3_grammar_admits_paths": len(
            shadow.csv_reader_paths(ast.parse(case.source_path.read_bytes()))
        ),
        "unused": frozen_binder is not None,
    }


def _free_name_trigger(key: str) -> dict[str, Any]:
    """Capture the AST node held in the helper binder's frame when it refuses."""

    import sys

    case = reference_case(key)
    values = inputs(case)
    content = values.pop("content")
    frozen_census = df33._mt_full_scope_reader_census
    authorized = values["authorized_path"]
    captured: dict[str, Any] = {}
    path = df33.__file__

    def loose(tree: ast.Module, **kwargs: Any) -> Any:
        result = frozen_census(tree, **kwargs)
        found = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"DictReader", "reader"}
            for node in ast.walk(tree)
        )
        return [*result, authorized] if found else result

    def tracer(frame: Any, event: str, arg: Any) -> Any:
        if event != "call" or frame.f_code.co_filename != path:
            return None

        def local(inner: Any, inner_event: str, value: Any) -> Any:
            if (
                inner_event == "return"
                and isinstance(value, tuple)
                and len(value) == 2
                and value[1] == "helper-free-name-unbound"
                and not captured
            ):
                node = inner.f_locals.get("node")
                helper = inner.f_locals.get("helper")
                captured.update(
                    {
                        "free_name": getattr(node, "id", None),
                        "line": getattr(node, "lineno", None),
                        "helper": getattr(helper, "name", None),
                    }
                )
            return local

        return local

    df33._mt_full_scope_reader_census = loose
    sys.settrace(tracer)
    try:
        df34._reanalyze_with_v34_admissions(content, **values)
    finally:
        sys.settrace(None)
        df33._mt_full_scope_reader_census = frozen_census
    return captured


# --------------------------------------------------------------------------------------
# D2 demonstration: the set literal and the tuple select the same three positions
# --------------------------------------------------------------------------------------

P6_PANDAS = (
    ("import csv\n\nfrom scipy import stats", "import pandas as pd\n\nfrom scipy import stats"),
    (
        '    with open(path, newline="", encoding="utf-8") as handle:\n'
        "        return list(csv.DictReader(handle))",
        "    return pd.read_csv(path)",
    ),
    (
        "    return [float(row[column]) for row in rows if row[GROUP_COLUMN] == group]",
        "    return rows.loc[rows[GROUP_COLUMN] == group, column]",
    ),
    ("def mean(values):\n    return sum(values) / len(values)", "def mean(values):\n    return values.mean()"),
    (
        "    m = mean(values)\n    return (sum((v - m) ** 2 for v in values) / (len(values) - 1)) ** 0.5",
        "    return values.std(ddof=1)",
    ),
    ('print(f"Palms in file: {len(rows)}")', 'print(f"Palms in file: {rows.shape[0]}")'),
)
P6_SET = (
    'HAND_CORRECTED = {\n    "fruit_weight_g",\n    "yield_per_palm_kg",\n'
    '    "total_soluble_solids_brix",\n}'
)
P6_TUPLE = (
    'HAND_CORRECTED = (\n    "fruit_weight_g",\n    "yield_per_palm_kg",\n'
    '    "total_soluble_solids_brix",\n)'
)


def _d2_probe() -> dict[str, Any]:
    source = reference_case(P6_KEY).source_path.read_bytes()
    for old, new in P6_PANDAS:
        source = _replace(source, old, new)
    tuple_form = _replace(source, P6_SET, P6_TUPLE)
    with_d2 = ("d1-format-arm", "d2-set-selector", "d4a-numeric-group", "d4b-loop-terminal")
    return {
        "set_form_without_d2": _outcome(_analyze(P6_KEY, source).outcome),
        "set_form_with_d2": _outcome(_analyze(P6_KEY, source, kinds=with_d2).outcome),
        "tuple_form_frozen_3_4": _frozen(P6_KEY, tuple_form),
        "membership_sets": {
            name: list(values)
            for name, values in shadow.membership_sets(ast.parse(source)).items()
        },
    }


# --------------------------------------------------------------------------------------
# Grammar-level refusal probes
# --------------------------------------------------------------------------------------

D4A_REFUSALS = {
    "ambiguous-normalised-tokens": ("salt", ("2.0", "2.00"), "x = data[data['salt'] == 2.0]"),
    "non-decimal-token": ("salt", ("low", "high"), "x = data[data['salt'] == 2.0]"),
    "thousands-separator-token": ("salt", ("1,000", "2000"), "x = data[data['salt'] == 1000]"),
    "boolean-comparator": ("salt", ("2.0", "3.0"), "x = data[data['salt'] == True]"),
    "call-comparator": ("salt", ("2.0", "3.0"), "x = data[data['salt'] == float(2)]"),
    "no-matching-token": ("salt", ("2.0", "3.0"), "x = data[data['salt'] == 4.0]"),
    "not-equal-operator": ("salt", ("2.0", "3.0"), "x = data[data['salt'] != 2.0]"),
    "non-group-column": ("salt", ("2.0", "3.0"), "x = data[data['ph'] == 2.0]"),
}
D4A_ADMISSIONS = {
    "float-literal": ("salt", ("2.0", "3.0"), "x = data[data['salt'] == 2.0]", "2.0"),
    "int-literal": ("salt", ("2.0", "3.0"), "x = data[data['salt'] == 2]", "2.0"),
    "module-constant": (
        "salt",
        ("2.0", "3.0"),
        "LOW = 2.0\nx = data[data['salt'] == LOW]",
        "2.0",
    ),
    "negative-literal": ("salt", ("-1.0", "1.0"), "x = data[data['salt'] == -1.0]", "-1.0"),
}


def _d4a_grammar_probe() -> dict[str, Any]:
    refusals: dict[str, bool] = {}
    for name, (column, tokens, code) in D4A_REFUSALS.items():
        positions = shadow.group_mask_numeric_positions(
            ast.parse(code), group_column=column, group_values=tokens, column_is_decimal=True
        )
        refusals[name] = not positions
    admissions: dict[str, str | None] = {}
    for name, (column, tokens, code, expected) in D4A_ADMISSIONS.items():
        positions = shadow.group_mask_numeric_positions(
            ast.parse(code), group_column=column, group_values=tokens, column_is_decimal=True
        )
        values = sorted(set(positions.values()))
        admissions[name] = values[0] if len(values) == 1 and values[0] == expected else None
    non_decimal = shadow.group_mask_numeric_positions(
        ast.parse("x = data[data['salt'] == 2.0]"),
        group_column="salt",
        group_values=("2.0", "3.0"),
        column_is_decimal=False,
    )
    return {
        "refusals": refusals,
        "all_refused": all(refusals.values()),
        "admissions": admissions,
        "all_admitted": all(value is not None for value in admissions.values()),
        "refuses_when_column_is_not_decimal": not non_decimal,
    }


D3_REFUSALS = {
    "restkey": 'with open(p, newline="") as h:\n    return list(csv.DictReader(h, restkey="x"))',
    "explicit-delimiter": 'with open(p, newline="") as h:\n    return list(csv.reader(h, delimiter=";"))',
    "binary-mode": 'with open(p, mode="rb") as h:\n    return list(csv.reader(h))',
    "not-materialised": 'with open(p, newline="") as h:\n    return csv.DictReader(h)',
    "filtered-comprehension": (
        'with open(p, newline="") as h:\n    return [r for r in csv.DictReader(h) if r]'
    ),
    "two-with-items": 'with open(p) as h, open(q) as g:\n    return list(csv.reader(h))',
    "extra-body-statement": (
        'with open(p, newline="") as h:\n    rows = list(csv.reader(h))\n    return rows'
    ),
    "unknown-open-keyword": (
        'with open(p, buffering=1, newline="") as h:\n    return list(csv.reader(h))'
    ),
    "other-handle": 'with open(p, newline="") as h:\n    return list(csv.reader(g))',
}
D3_ADMISSIONS = {
    "dictreader": 'with open(p, newline="", encoding="utf-8") as h:\n    return list(csv.DictReader(h))',
    "reader": 'with open(p, newline="") as h:\n    return list(csv.reader(h))',
}


def _d3_grammar_probe() -> dict[str, Any]:
    def wrap(body: str) -> str:
        return "import csv\n\n\ndef read_data(p):\n" + "\n".join(
            "    " + line for line in body.splitlines()
        )

    refusals = {
        name: not shadow.csv_reader_paths(ast.parse(wrap(code)))
        for name, code in D3_REFUSALS.items()
    }
    admissions = {
        name: len(shadow.csv_reader_paths(ast.parse(wrap(code)))) == 1
        for name, code in D3_ADMISSIONS.items()
    }
    sealed = shadow.csv_reader_paths(ast.parse(reference_case(P6_KEY).source_path.read_bytes()))
    return {
        "refusals": refusals,
        "all_refused": all(refusals.values()),
        "admissions": admissions,
        "all_admitted": all(admissions.values()),
        "sealed_p6_admitted_paths": len(sealed),
    }


D2_REFUSALS = {
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
D2_ADMISSIONS = {
    "membership-in": "S = {'a', 'b'}\nx = 'a' in S",
    "membership-not-in": "S = {'a', 'b'}\nx = 'a' not in S",
    "membership-in-comprehension": "S = {'a', 'b'}\nx = [n for n in OUT if n in S]",
}


def _d2_grammar_probe() -> dict[str, Any]:
    refusals = {
        name: not shadow.membership_sets(ast.parse(code)) for name, code in D2_REFUSALS.items()
    }
    admissions = {
        name: shadow.membership_sets(ast.parse(code)).get("S") == ("a", "b")
        for name, code in D2_ADMISSIONS.items()
    }
    return {
        "refusals": refusals,
        "all_refused": all(refusals.values()),
        "admissions": admissions,
        "all_admitted": all(admissions.values()),
    }


E15P3_SUMMARY = """    n_significant = sum(result["significant"] for result in results)
    print(
        f"{n_significant} of {len(results)} declared outcomes separated the two "
        f"ventilation groups at p < {ALPHA}."
    )
"""


def _d5_probe() -> dict[str, Any]:
    """The E15 P3 ladder plus the guard-reaching census the FA argument rests on."""

    source = reference_case(E15P3_KEY).source_path.read_bytes()
    r1 = _replace(
        source,
        "f\"{n_significant} of {len(results)} declared outcomes separated the two \"",
        "f\"{n_significant} of {len(DECLARED_OUTCOMES)} declared outcomes separated the two \"",
    )
    rc = _replace(
        r1.decode("utf-8").encode("utf-8"),
        "    n_significant = sum(result[\"significant\"] for result in results)\n",
        "    n_significant = sum(result[\"significant\"] for result in results)\n"
        "    print(f\"rows: {len(results)}\")\n",
    )
    ladder = {
        "r0-sealed": {
            "frozen_3_4": _frozen(E15P3_KEY),
            "v3_5": _outcome(_analyze(E15P3_KEY).outcome),
            "v3_5_census": _analyze(E15P3_KEY).admission_census,
        },
        "r1-len-of-the-contract-table": {
            "frozen_3_4": _frozen(E15P3_KEY, r1),
            "v3_5": _outcome(_analyze(E15P3_KEY, r1).outcome),
        },
        "rC-second-len-re-added": {
            "frozen_3_4": _frozen(E15P3_KEY, rc),
            "v3_5": _outcome(_analyze(E15P3_KEY, rc).outcome),
        },
    }
    return {"ladder": ladder, "guard_reach": _off_grammar_reach()}


def _off_grammar_reach() -> dict[str, Any]:
    """Which opened cases reach the off-grammar guard, and which hold a p-derived `len()`.

    The inventory is captured from the shipped guard's own walk, not read off the source.
    """

    from harness import all_cases

    reached: list[str] = []
    with_len: list[str] = []
    frozen_guard = df33._MtEngine._off_grammar_transform_guard
    state: dict[str, Any] = {}

    def probe(engine: Any) -> Any:
        inventory = [
            node
            for node in df33._walk_statements(engine.scope)
            if isinstance(node, (ast.BinOp, ast.Call)) and engine._p_origins(node)
        ]
        state["reached"] = True
        state["len_calls"] = sum(
            isinstance(node, ast.Call) and engine.resolver.qualified(node.func) == "len"
            for node in inventory
        )
        return frozen_guard(engine)

    df33._MtEngine._off_grammar_transform_guard = probe
    try:
        for case in all_cases():
            if case.envelope is None:
                continue
            state.clear()
            values = inputs(case)
            content = values.pop("content")
            df34._reanalyze_with_v34_admissions(content, **values)
            if state.get("reached"):
                reached.append(case.key)
                if state.get("len_calls"):
                    with_len.append(case.key)
    finally:
        df33._MtEngine._off_grammar_transform_guard = frozen_guard
    return {
        "opened_cases_reaching_the_guard": sorted(reached),
        "reaching_count": len(reached),
        "negatives_reaching_the_guard": sorted(
            key for key in reached if ":N" in key
        ),
        "cases_with_a_p_derived_len": sorted(with_len),
    }


D5_REFUSALS = {
    "comparison": "n = 0\nif len(results) > 3:\n    print(n)",
    "arithmetic": "print(f'{len(results) - 1}')",
    "stored-first": "n = len(results)\nprint(f'{n}')",
    "loop-bound": "for i in range(len(results)):\n    print(i)",
    "subscript": "print(results[len(results) - 1])",
    "keyword-argument": "print(f'{len(results, x=1)}')",
}


def _gated_negative_probe() -> dict[str, Any]:
    """The two E18 negatives the installed productions could plausibly reach."""

    result: dict[str, Any] = {}
    for name, key in (("N5-two-stage-screen", N5_KEY), ("N6-overall-screen", N6_KEY)):
        run = _analyze(key)
        result[name] = {
            "frozen_3_4": _frozen(key),
            "v3_5": _outcome(run.outcome),
            "admission_census": run.admission_census,
            "reanalysis_reason": run.reanalysis_reason,
        }
    return result


def _d4b_loop_probe() -> dict[str, Any]:
    """Per-loop refusal proof for the D4b named disqualifiers.

    The E18 P3 base carries two presentation loops, so a whole-source admission census cannot
    isolate the mutated one.  This probe hooks the D4b production itself and records, for each
    disqualifier fixture, which loop line numbers it admits.  The mutated loop must be absent.
    """

    import fixture_catalog

    frozen = shadow.terminal_presentation_loop
    seen: list[tuple[int, bool]] = []

    def probe(engine: Any, node: Any) -> bool:
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
        "positive-d4-float-group-and-presentation-loop",
    }
    result: dict[str, Any] = {}
    shadow.terminal_presentation_loop = probe
    try:
        for fixture in fixture_catalog.new_fixtures():
            if fixture.name not in names:
                continue
            seen.clear()
            run = _analyze(fixture.case_key, fixture.source)
            mutated = min((line for line, _ in seen), default=None)
            result[fixture.name] = {
                "loops_offered": sorted({line for line, _ in seen}),
                "loops_admitted": sorted({line for line, ok in seen if ok}),
                "first_loop_admitted": bool(
                    mutated is not None and any(line == mutated and ok for line, ok in seen)
                ),
                "outcome": _outcome(run.outcome),
            }
    finally:
        shadow.terminal_presentation_loop = frozen
    return result


class _StubEngine:
    """Minimal stand-in for the iterator grammar, which reads only the shadowed-builtin set."""

    class resolver:  # noqa: N801
        builtins_shadowed: frozenset[str] = frozenset()


D4B_ITERATORS = {
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


def _d4b_iterator_grammar() -> dict[str, Any]:
    result: dict[str, bool] = {}
    for name, (code, expected) in D4B_ITERATORS.items():
        loop = ast.parse(code).body[0]
        assert isinstance(loop, ast.For)
        result[name] = shadow.admitted_loop_iterator(_StubEngine, loop.iter) is expected
    return {"per_form_matches_the_grammar": result, "all_match": all(result.values())}


def _e17n1_clearance_facts() -> dict[str, Any]:
    """Why the one clearance movement is true, recorded as source and CSV facts."""

    import collections
    import csv as csv_module
    import io as io_module

    key = "E17:N1:e2d8b1bdf4baa671a1b4"
    case = reference_case(key)
    values = inputs(case)
    content = values.pop("content")
    tree = ast.parse(content)
    correction_calls = sorted(
        {
            node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Name) and node.func.id == "multipletests")
                or (isinstance(node.func, ast.Attribute) and node.func.attr == "multipletests")
            )
        }
    )
    rows = list(
        csv_module.reader(
            io_module.StringIO(values["csv_content"].decode("utf-8"), newline=""),
            dialect="excel",
            strict=True,
        )
    )
    index = rows[0].index(values["group_column"])
    tokens = sorted(collections.Counter(row[index] for row in rows[1:]).items())
    run = _analyze(key)
    return {
        "frozen_3_4": _frozen(key),
        "v3_5": _outcome(run.outcome),
        "admission_census": run.admission_census,
        "correction_calls_in_source": correction_calls,
        "declared_outcome_count": len(values["outcome_columns"]),
        "group_column": values["group_column"],
        "group_tokens_with_counts": [[token, count] for token, count in tokens],
        "group_constants": {
            name: value
            for name, value in shadow.module_numeric_constants(tree).items()
            if name.startswith("GROUP_")
        },
    }


def execute() -> dict[str, Any]:
    payload = {
        "schema": "multitest-v3.5-recall-delta-instrumentation-v1",
        "observed_not_inferred": True,
        "p2_arm_predicate": _p2_probe(),
        "p3_group_mask_and_loop": _p3_probe(),
        "p6_reader_and_the_wall_behind_it": _loose_reader_probe(P6_KEY),
        "n6_reader_and_the_wall_behind_it": _loose_reader_probe(N6_KEY),
        "d2_set_selector_demonstration": _d2_probe(),
        "d1_gated_negatives": _gated_negative_probe(),
        "d2_grammar": _d2_grammar_probe(),
        "d3_grammar": _d3_grammar_probe(),
        "d4a_grammar": _d4a_grammar_probe(),
        "d5_cardinality_read": _d5_probe(),
        "d4b_loop_refusals": _d4b_loop_probe(),
        "d4b_iterator_grammar": _d4b_iterator_grammar(),
        "e17_n1_clearance_facts": _e17n1_clearance_facts(),
    }
    RESULTS.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    return payload


if __name__ == "__main__":
    print(json.dumps(execute(), indent=2, sort_keys=True))
