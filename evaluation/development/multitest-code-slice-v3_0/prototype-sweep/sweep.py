"""Execute the strict MT 3.0 shadow models over pinned cases and named fixtures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from fixture_catalog import fixtures
from harness import Outcome, adapter_baseline, all_cases, analyze, classify, inputs
from prototype_models import PrototypeResult, analyze_prototype

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results.json"
FIXTURE_ROOT = ROOT / "fixtures"
EXPECTED_MOVEMENTS = (
    "E11:P5:114782f595d9c24b923d",
    "E12:P1:f9ce4de5e21d9015ecd9",
    "E12:P5:54667dd7c39067c8c2c8",
    "E12:N1:45c4b9a19d0a630f1cb0",
    "E12:N2:f256af2f5c5d98f37e65",
    "E14:P2:4fc0f5c1ef2d0e2cd5b6",
    "E14:P3:502687d9137dab93ff99",
    "E14:P4:cccde3c60f936e077f80",
    "E14:P5:5e33841b96d85ffe67be",
    "E14:N9:5d5d4e0189d4f2c73f6a",
)


def _effective(case: Any, prototype: PrototypeResult, baseline: Outcome) -> Outcome:
    if baseline.reason_or_classification == "statistics-api-imported-outside-analysis-py":
        return baseline
    return prototype.outcome if prototype.changed else baseline


def _case_row(case: Any) -> dict[str, Any]:
    values = inputs(case)
    source = values.pop("content")
    analyzer_baseline = classify(analyze(case))
    baseline = adapter_baseline(case, analyzer_baseline)
    prototype = analyze_prototype(source, **values)
    outcome = _effective(case, prototype, baseline)
    return {
        "key": case.key,
        "envelope": case.envelope,
        "role": case.role,
        "designed_class": case.designed_class,
        "labeled_correct": case.labeled_correct,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "baseline": baseline.as_json(),
        "outcome": outcome.as_json(),
        "changed": outcome != baseline,
        "models": list(prototype.models),
        "trigger_shapes": list(prototype.trigger_shapes),
        "detail": dict(prototype.detail),
    }


def _fixture_row(fixture: Any) -> dict[str, Any]:
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    source_path = FIXTURE_ROOT / f"{fixture.name}.py"
    source_path.write_text(fixture.source, encoding="utf-8")
    values = inputs(fixture.case, fixture.source.encode("utf-8"))
    source = values.pop("content")
    prototype = analyze_prototype(source, **values)
    if prototype.outcome != fixture.expected:
        raise AssertionError(
            f"fixture {fixture.name} observed {prototype.outcome.as_json()} "
            f"instead of {fixture.expected.as_json()}"
        )
    return {
        "name": fixture.name,
        "case_key": fixture.case.key,
        "correct_analysis": fixture.correct_analysis,
        "source_path": source_path.relative_to(ROOT).as_posix(),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "baseline": prototype.baseline.as_json(),
        "outcome": prototype.outcome.as_json(),
        "models": list(prototype.models),
        "trigger_shapes": list(prototype.trigger_shapes),
        "detail": dict(prototype.detail),
    }


def execute() -> dict[str, Any]:
    case_rows = [_case_row(case) for case in all_cases()]
    fixture_rows = [_fixture_row(fixture) for fixture in fixtures()]
    trigger_rows = [
        row for row in case_rows if row["baseline"][0] != "candidate" and row["trigger_shapes"]
    ]
    if len(trigger_rows) != 41:
        raise AssertionError(f"trigger census is {len(trigger_rows)}, not 41")

    movements = [row["key"] for row in case_rows if row["changed"]]
    if tuple(movements) != EXPECTED_MOVEMENTS:
        raise AssertionError(f"movement set changed: {movements!r}")
    corpus_rows = [row for row in case_rows if row["envelope"] is None]
    opened_rows = [row for row in case_rows if row["envelope"] is not None]
    corpus_correct_flips = [
        row["key"]
        for row in corpus_rows
        if row["labeled_correct"] and row["outcome"][0] == "candidate"
    ]
    opened_negative_flips = [
        row["key"]
        for row in opened_rows
        if row["designed_class"] == "negative" and row["outcome"][0] == "candidate"
    ]
    fixture_flips = [
        row["name"]
        for row in fixture_rows
        if row["correct_analysis"] and row["outcome"][0] == "candidate"
    ]
    if corpus_correct_flips or opened_negative_flips or fixture_flips:
        raise AssertionError(
            "none-flip failure: "
            f"{corpus_correct_flips!r} {opened_negative_flips!r} {fixture_flips!r}"
        )
    corpus_movements = [row["key"] for row in corpus_rows if row["changed"]]
    if corpus_movements:
        raise AssertionError(f"corpus rows moved: {corpus_movements!r}")

    retro: dict[str, str] = {}
    for envelope in ("E10", "E11", "E12", "E13", "E14"):
        positives = [
            row
            for row in opened_rows
            if row["envelope"] == envelope and str(row["role"]).startswith("P")
        ]
        caught = sum(row["outcome"][0] == "candidate" for row in positives)
        retro[envelope] = f"{caught}/{len(positives)}"
    if retro != {"E10": "5/6", "E11": "6/6", "E12": "6/6", "E13": "4/6", "E14": "4/6"}:
        raise AssertionError(f"retro recall changed: {retro!r}")

    payload: dict[str, Any] = {
        "schema": "multitest-v3-prototype-sweep-v1",
        "baseline": "code_csv_multiple_testing adapter 2.3.0 pins",
        "case_count": len(case_rows),
        "fixture_count": len(fixture_rows),
        "correct_fixture_count": sum(row["correct_analysis"] for row in fixture_rows),
        "positive_control_count": sum(not row["correct_analysis"] for row in fixture_rows),
        "movement_count": len(movements),
        "movement_set": movements,
        "retro_recall": retro,
        "none_flip": {
            "corpus_correct": [len(corpus_correct_flips), 25],
            "opened_negatives": [len(opened_negative_flips), 45],
            "new_correct_fixtures": [len(fixture_flips), 39],
        },
        "trigger_census": {
            "count": len(trigger_rows),
            "rows": [
                {
                    "key": row["key"],
                    "trigger_shapes": row["trigger_shapes"],
                    "baseline": row["baseline"],
                    "outcome": row["outcome"],
                    "movement": row["changed"],
                }
                for row in trigger_rows
            ],
        },
        "cases": case_rows,
        "fixtures": fixture_rows,
    }
    RESULTS.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return payload


if __name__ == "__main__":
    result = execute()
    print(
        json.dumps(
            {key: result[key] for key in ("movement_set", "retro_recall", "none_flip")}, indent=2
        )
    )
