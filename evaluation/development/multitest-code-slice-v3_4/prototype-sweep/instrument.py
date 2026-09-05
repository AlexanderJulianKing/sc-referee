"""Execute the E17 trigger traces, the P3/P6 ladders, and the B-grammar refusal probes.

Everything written here is observed against real shipped 3.3 code.  No row in this file is
an inference about what the analyzer would do.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

from comprehension_iterator_shadow import (
    _position,
    _registry_control_expressions,
    _terminal_ifexp_positions_v34,
    _v34_recognizers,
    normalize_comprehensions,
)
from fixture_catalog import new_fixtures
from harness import classify, inputs, reference_case

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 as frozen
import sc_referee.scientific_checks.code_csv_multiple_testing_terminal_presentation_v3_3 as tp
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    analyze_code_csv_multiple_testing_dataflow,
)

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "instrument_results.json"
P3_KEY = "E17:P3:a2e031f79e31c80fd900"
P6_KEY = "E17:P6:b4e507c4b55954752f14"


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _trace(case_key: str) -> dict[str, object]:
    """Record every tracked hierarchy control and its branch attribution."""

    case = reference_case(case_key)
    values = inputs(case)
    content = values.pop("content")
    recorded: list[dict[str, object]] = []
    active = False
    original_control = frozen._MtEngine._control_tracked
    original_guard = frozen._MtEngine._hierarchy_guard

    def control(self: Any, node: ast.expr) -> bool:
        tracked = original_control(self, node)
        if active and tracked:
            registry = _registry_control_expressions((*self.original_scope, *self.scope))
            recorded.append(
                {
                    "position": list(_position(node)),
                    "node_type": type(node).__name__,
                    "source": ast.unparse(node),
                    "p_origins": len(self._p_origins(node)),
                    "correction_control": bool(self._correction_control_present(node)),
                    "outcome_headers": sorted(self._outcome_headers(node, set(), 0)),
                    "registry_control": id(node) in registry,
                }
            )
        return tracked

    def guard(self: Any) -> str | None:
        nonlocal active
        active = True
        try:
            return original_guard(self)
        finally:
            active = False

    frozen._MtEngine._control_tracked = control
    frozen._MtEngine._hierarchy_guard = guard
    try:
        baseline = classify(analyze_code_csv_multiple_testing_dataflow(content, **values))
    finally:
        frozen._MtEngine._control_tracked = original_control
        frozen._MtEngine._hierarchy_guard = original_guard
    first = recorded[0] if recorded else None
    return {
        "case_key": case_key,
        "source_sha256": _sha256(content),
        "baseline": baseline.as_json(),
        "first_tracked_control": first,
        "all_tracked_controls_before_first_reason": recorded,
        "outcome_headers_only": bool(
            first is not None
            and first["registry_control"]
            and first["p_origins"] == 0
            and not first["correction_control"]
            and len(first["outcome_headers"]) >= 2
        ),
    }


def _ladder(case_key: str, rungs: tuple[tuple[str, bytes], ...]) -> dict[str, object]:
    case = reference_case(case_key)
    values = inputs(case)
    values.pop("content")
    rows: list[dict[str, object]] = []
    for name, source in rungs:
        rows.append(
            {
                "rung": name,
                "source_sha256": _sha256(source),
                "outcome": classify(
                    analyze_code_csv_multiple_testing_dataflow(source, **values)
                ).as_json(),
            }
        )
    return {"case_key": case_key, "rungs": rows}


def _p3_ladder() -> dict[str, object]:
    case = reference_case(P3_KEY)
    values = inputs(case)
    content = values.pop("content")
    text = content.decode("utf-8")
    anchor = (
        "    results = {\n"
        "        outcome: compare_settings(roadside[outcome], park[outcome])\n"
        "        for outcome in OUTCOMES\n"
        "    }\n"
    )
    if text.count(anchor) != 1:
        raise AssertionError("the E17 P3 comprehension anchor is not unique")
    explicit = text.replace(
        anchor,
        "    results = {}\n"
        "    for outcome in OUTCOMES:\n"
        "        results[outcome] = compare_settings(roadside[outcome], park[outcome])\n",
    ).encode("utf-8")
    normalized, detail = normalize_comprehensions(content, tuple(values["outcome_columns"]))
    if not detail:
        raise AssertionError("the strict comprehension lowering did not match E17 P3")
    ladder = _ladder(
        P3_KEY,
        (
            ("real-source", content),
            ("hand-written-explicit-loop", explicit),
            ("strict-comprehension-normalization", normalized),
        ),
    )
    ladder["lowering_detail"] = list(detail)
    return ladder


def _p6_ladder() -> dict[str, object]:
    case = reference_case(P6_KEY)
    values = inputs(case)
    content = values.pop("content")
    text = content.decode("utf-8")
    iterator_old = "    for position, outcome in enumerate(OUTCOMES, start=1):\n"
    iterator_new = "    for outcome in OUTCOMES:\n"
    position_print = '        print("%d. %s" % (position, outcome))'
    position_new = '        print("- %s" % (outcome,))'
    cap_old = (
        "            corrected_p = raw_p * N_COMPARISONS\n"
        "            if corrected_p > 1.0:\n"
        "                corrected_p = 1.0\n"
    )
    cap_new = "            corrected_p = min(raw_p * N_COMPARISONS, 1.0)\n"
    for anchor in (iterator_old, position_print, cap_old):
        if text.count(anchor) != 1:
            raise AssertionError("an E17 P6 ladder anchor is not unique")
    bare = text.replace(iterator_old, iterator_new).replace(position_print, position_new)
    minimum = text.replace(cap_old, cap_new)
    both = bare.replace(cap_old, cap_new)
    return _ladder(
        P6_KEY,
        (
            ("real-source", content),
            ("bare-Name-iterator-only", bare.encode("utf-8")),
            ("min-cap-only", minimum.encode("utf-8")),
            ("both-hand-rewrites", both.encode("utf-8")),
        ),
    )


def _dict_field_probe() -> dict[str, object]:
    """Observe the exact 3.3 `_dict_field_for_name` refusal on the E17 P3 verdict."""

    case = reference_case(P3_KEY)
    values = inputs(case)
    content = values.pop("content")
    normalized, _ = normalize_comprehensions(content, tuple(values["outcome_columns"]))
    rows: list[dict[str, object]] = []
    for label, source in (("real-source", content), ("normalized", normalized)):
        tree = frozen._bounded_parse(source)
        parents = tp._parents(tree)
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.IfExp)
                and tp._display_string(node.body)
                and tp._display_string(node.orelse)
            ):
                continue
            assignment = parents.get(node)
            if not (
                isinstance(assignment, (ast.Assign, ast.AnnAssign)) and assignment.value is node
            ):
                continue
            targets = (
                assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
            )
            if len(targets) != 1 or not isinstance(targets[0], ast.Name):
                continue
            rows.append(
                {
                    "source": label,
                    "verdict_name": targets[0].id,
                    "ifexp_position": list(_position(node)),
                    "dict_field_for_name": tp._dict_field_for_name(node, targets[0].id, parents),
                    "v33_admitted_positions": [
                        list(item)
                        for item in tp._terminal_ifexp_positions(tree, tp._resolver(tree))
                    ],
                    "v34_admitted_positions": [
                        list(item)
                        for item in _terminal_ifexp_positions_v34(tree, tp._resolver(tree))
                    ],
                }
            )
    return {"case_key": P3_KEY, "rows": rows}


def _terminal_ifexp_refusal_probe() -> dict[str, object]:
    """Prove the specified B grammar refuses every named store/return shape."""

    rows: list[dict[str, object]] = []
    for fixture in new_fixtures():
        if fixture.category != "terminal-ifexp-rejected-grammar":
            continue
        tree = frozen._bounded_parse(fixture.source)
        admitted = _terminal_ifexp_positions_v34(tree, tp._resolver(tree))
        rows.append(
            {
                "fixture": fixture.name,
                "source_sha256": _sha256(fixture.source),
                "v34_admitted_positions": [list(item) for item in admitted],
            }
        )
    for row in rows:
        if row["v34_admitted_positions"]:
            raise AssertionError(f"the B grammar admitted a refused shape: {row['fixture']}")
    return {"rows": rows}


def _extension_b_collision_probe() -> dict[str, object]:
    """Measure why extension B is specified but not shipped.

    On E16 P4 the frozen 3.3 proof admits exactly one `If` position and no `IfExp` position,
    which is what `prove_terminal_presentation` requires.  The B production admits one more
    position, `len(positions)` becomes two, the whole proof returns `None`, and a pinned 3.3
    candidate is lost.
    """

    rows: list[dict[str, object]] = []
    for case_key in ("E16:P4:9ced761b41ef93485acf", "E16:P2:7a43fa7b50f1b99e5034", P3_KEY):
        case = reference_case(case_key)
        values = inputs(case)
        content = values.pop("content")
        tree = frozen._bounded_parse(content)
        resolver = tp._resolver(tree)
        v33_if = tp._terminal_if_positions(tree, resolver)
        v33_ifexp = tp._terminal_ifexp_positions(tree, resolver)
        v34_ifexp = _terminal_ifexp_positions_v34(tree, resolver)
        without_b = classify(analyze_code_csv_multiple_testing_dataflow(content, **values))
        with _v34_recognizers(extension_b=True):
            with_b = classify(analyze_code_csv_multiple_testing_dataflow(content, **values))
        rows.append(
            {
                "case_key": case_key,
                "source_sha256": _sha256(content),
                "v33_admitted_if_positions": [list(item) for item in v33_if],
                "v33_admitted_ifexp_positions": [list(item) for item in v33_ifexp],
                "v34_admitted_ifexp_positions": [list(item) for item in v34_ifexp],
                "outcome_without_extension_b": without_b.as_json(),
                "outcome_with_extension_b": with_b.as_json(),
                "extension_b_regresses_row": without_b != with_b,
            }
        )
    return {"rows": rows}


def execute() -> dict[str, object]:
    result: dict[str, object] = {
        "schema": "multitest-v3.4-trigger-instrumentation-v1",
        "observed_not_inferred": True,
        "traces": [_trace(P3_KEY), _trace(P6_KEY)],
        "p3_ladder": _p3_ladder(),
        "p6_ladder": _p6_ladder(),
        "dict_field_probe": _dict_field_probe(),
        "terminal_ifexp_refusal_probe": _terminal_ifexp_refusal_probe(),
        "extension_b_collision_probe": _extension_b_collision_probe(),
    }
    OUTPUT.write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    print(json.dumps(execute(), indent=2, sort_keys=True))
