"""Execute the E16 trigger trace and the P3 mutation ladder against real 3.2 code."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from harness import classify, inputs, reference_case
from terminal_presentation_shadow import (
    _helper_record_surrogate,
    _position,
    _skip_proved_controls,
)

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 as frozen
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_2 import (
    analyze_code_csv_multiple_testing_dataflow,
)

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "instrument_results.json"


def _trace(case_key: str) -> dict[str, object]:
    case = reference_case(case_key)
    values = inputs(case)
    content = values.pop("content")
    recorded: list[dict[str, object]] = []
    in_hierarchy = False
    original_control = frozen._MtEngine._control_tracked
    original_hierarchy = frozen._MtEngine._hierarchy_guard

    def control(self: Any, node: ast.expr) -> bool:
        tracked = original_control(self, node)
        if in_hierarchy and tracked:
            recorded.append(
                {
                    "position": list(_position(node)),
                    "node_type": type(node).__name__,
                    "ast": ast.dump(node, include_attributes=False),
                }
            )
        return tracked

    def hierarchy(self: Any) -> str | None:
        nonlocal in_hierarchy
        in_hierarchy = True
        try:
            return original_hierarchy(self)
        finally:
            in_hierarchy = False

    frozen._MtEngine._control_tracked = control
    frozen._MtEngine._hierarchy_guard = hierarchy
    try:
        baseline = classify(analyze_code_csv_multiple_testing_dataflow(content, **values))
    finally:
        frozen._MtEngine._control_tracked = original_control
        frozen._MtEngine._hierarchy_guard = original_hierarchy
    if not recorded:
        raise AssertionError(f"{case_key} produced no tracked hierarchy expression")
    first = recorded[0]
    position = tuple(int(item) for item in first["position"])
    with _skip_proved_controls(frozenset({position})):
        after_skip = classify(analyze_code_csv_multiple_testing_dataflow(content, **values))
    return {
        "case_key": case_key,
        "source_sha256": "sha256:" + __import__("hashlib").sha256(content).hexdigest(),
        "baseline": baseline.as_json(),
        "first_tracked_control": first,
        "all_tracked_controls_before_first_reason": recorded,
        "after_skipping_only_first_control": after_skip.as_json(),
    }


def _p3_ladder() -> dict[str, object]:
    case = reference_case("E16:P3:5a9c5b4377c33916d672")
    values = inputs(case)
    content = values.pop("content")
    text = content.decode("utf-8")
    anchor = "    results = {outcome: compare(data, outcome) for outcome in OUTCOMES}\n"
    explicit = text.replace(
        anchor,
        "    results = {}\n"
        "    for outcome in OUTCOMES:\n"
        "        results[outcome] = compare(data, outcome)\n",
    ).encode("utf-8")
    transformed = _helper_record_surrogate(content, tuple(values["outcome_columns"]))
    if transformed is None:
        raise AssertionError("strict P3 helper-record lowering did not match")
    surrogate, proof = transformed
    rows = []
    for name, source in (
        ("real-source", content),
        ("explicit-loop-helper-call", explicit),
        ("strict-single-call-helper-record-surrogate", surrogate),
    ):
        rows.append(
            {
                "rung": name,
                "source_sha256": "sha256:" + __import__("hashlib").sha256(source).hexdigest(),
                "outcome": classify(
                    analyze_code_csv_multiple_testing_dataflow(source, **values)
                ).as_json(),
            }
        )
    return {"case_key": case.key, "rungs": rows, "strict_proof": dict(proof)}


def execute() -> dict[str, object]:
    result = {
        "schema": "multitest-v3.3-trigger-instrumentation-v1",
        "observed_not_inferred": True,
        "traces": [
            _trace("E16:P2:7a43fa7b50f1b99e5034"),
            _trace("E16:P4:9ced761b41ef93485acf"),
        ],
        "p3_ladder": _p3_ladder(),
    }
    OUTPUT.write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    print(json.dumps(execute(), indent=2, sort_keys=True))
