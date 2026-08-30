"""Execute and byte-pin the strict MT 3.3 terminal/helper prototype sweep."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from fixture_catalog import (
    all_fixtures,
    gatekeeping_fixtures,
    terminal_and_helper_fixtures,
)
from harness import all_cases, current_question_keys, inputs, reference_case
from instrument import execute as execute_instrumentation
from terminal_presentation_shadow import ShadowResult, analyze_v33_shadow

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results.json"
FIXTURES = ROOT / "fixtures"
EXPECTED_MOVEMENTS = (
    "E16:P2:7a43fa7b50f1b99e5034",
    "E16:P3:5a9c5b4377c33916d672",
    "E16:P4:9ced761b41ef93485acf",
)
EXPECTED_RETRO = {
    "E10": "5/6",
    "E11": "6/6",
    "E12": "6/6",
    "E13": "4/6",
    "E14": "4/6",
    "E15": "3/6",
    "E16": "4/6",
}
EXPECTED_E16_BASELINE = {
    "P1": ["candidate", "none", {"authorized_count": 4, "corrected_positions": []}],
    "P2": ["abstain", "hierarchical-gatekeeping-present"],
    "P3": ["abstain", "unresolved-pvalue-consumer"],
    "P4": ["abstain", "hierarchical-gatekeeping-present"],
    "P5": ["abstain", "test-battery-cardinality-unresolved"],
    "P6": ["abstain", "unresolved-manual-correction-present"],
    "N1": [
        "covered",
        "complete",
        {"authorized_count": 5, "corrected_positions": [0, 1, 2, 3, 4]},
    ],
    "N2": ["abstain", "unresolved-decision-threshold"],
    "N3": ["abstain", "unresolved-manual-correction-present"],
    "N4": ["abstain", "extra-registered-test-outside-authorized-family"],
    "N5": ["abstain", "extra-registered-test-outside-authorized-family"],
    "N6": ["abstain", "authorized-reader-lineage-unavailable"],
    "N7": ["abstain", "authorized-family-test-census-incomplete"],
    "N8": ["abstain", "test-battery-cardinality-unresolved"],
    "N9": ["abstain", "unresolved-decision-threshold"],
}


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _case_row(case: Any) -> tuple[dict[str, Any], ShadowResult]:
    values = inputs(case)
    content = values.pop("content")
    result = analyze_v33_shadow(content, **values)
    same_class = (
        result.baseline.state == case.baseline.state
        and result.baseline.reason_or_classification == case.baseline.reason_or_classification
    )
    adapter_short_circuit = case.key in {
        "E10:N7:6d2fdc67ab98bc0e0e6e",
        "corpus:spec-30",
    }
    if adapter_short_circuit:
        if result.changed:
            raise AssertionError(f"source admission crossed adapter short-circuit for {case.key}")
        effective = case.baseline
    elif not same_class:
        raise AssertionError(
            f"3.2 baseline drifted for {case.key}: "
            f"{result.baseline.as_json()} != {case.baseline.as_json()}"
        )
    else:
        effective = result.outcome if result.changed else case.baseline
    return (
        {
            "key": case.key,
            "envelope": case.envelope,
            "role": case.role,
            "designed_class": case.designed_class,
            "labeled_correct": case.labeled_correct,
            "source_sha256": _sha256(content),
            "baseline": case.baseline.as_json(),
            "source_analyzer_baseline": result.baseline.as_json(),
            "outcome": effective.as_json(),
            "changed": effective != case.baseline,
            "adapter_short_circuit": adapter_short_circuit,
            "attempted": result.attempted,
            "models": list(result.models),
            "detail": dict(result.detail),
            "surrogate_sha256": result.surrogate_sha256,
        },
        result,
    )


def _fixture_row(fixture: Any, new_names: frozenset[str]) -> tuple[dict[str, Any], ShadowResult]:
    case = reference_case(fixture.case_key)
    source = fixture.source
    values = inputs(case, source)
    content = values.pop("content")
    result = analyze_v33_shadow(content, **values)
    category = str(fixture.category)
    expected = fixture.expected
    if category != "v3.1-laundering-adjacent" and expected is not None:
        if result.outcome != expected:
            raise AssertionError(
                f"fixture {fixture.name}: {result.outcome.as_json()} != {expected.as_json()}"
            )
    if category.startswith(("frozen-v3", "audit-fix", "b5-", "ap-v3.2")) and result.changed:
        raise AssertionError(f"frozen cumulative fixture moved: {fixture.name}")
    source_path: str
    if fixture.name in new_names:
        FIXTURES.mkdir(parents=True, exist_ok=True)
        path = FIXTURES / f"{fixture.name}.py"
        path.write_bytes(source)
        source_path = path.relative_to(ROOT).as_posix()
    else:
        source_path = str(fixture.source_origin)
    return (
        {
            "name": fixture.name,
            "case_key": fixture.case_key,
            "category": category,
            "correct_analysis": bool(fixture.correct_analysis),
            "design_clause": str(fixture.design_clause),
            "source_origin": str(fixture.source_origin),
            "source_path": source_path,
            "source_sha256": _sha256(source),
            "frozen_expected": None if expected is None else expected.as_json(),
            "baseline": result.baseline.as_json(),
            "outcome": result.outcome.as_json(),
            "changed": result.changed,
            "attempted": result.attempted,
            "models": list(result.models),
            "detail": dict(result.detail),
            "surrogate_sha256": result.surrogate_sha256,
        },
        result,
    )


def execute() -> dict[str, Any]:
    instrumentation = execute_instrumentation()
    cases = all_cases()
    case_pairs: list[tuple[dict[str, Any], ShadowResult]] = []
    for index, case in enumerate(cases, 1):
        case_pairs.append(_case_row(case))
        if index % 25 == 0:
            print(f"case-progress {index}", flush=True)
    case_rows = [row for row, _ in case_pairs]

    if {
        row["role"]: row["baseline"] for row in case_rows if row["envelope"] == "E16"
    } != EXPECTED_E16_BASELINE:
        raise AssertionError("the sealed E16 3.2 baseline does not match all fifteen pins")
    movements = tuple(row["key"] for row in case_rows if row["changed"])
    if movements != EXPECTED_MOVEMENTS:
        raise AssertionError(f"movement set changed: {movements!r}")
    by_key = {row["key"]: row for row in case_rows}
    expected_candidates = {
        EXPECTED_MOVEMENTS[0]: [
            "candidate",
            "none",
            {"authorized_count": 6, "corrected_positions": []},
        ],
        EXPECTED_MOVEMENTS[1]: [
            "candidate",
            "none",
            {"authorized_count": 5, "corrected_positions": []},
        ],
        EXPECTED_MOVEMENTS[2]: [
            "candidate",
            "none",
            {"authorized_count": 7, "corrected_positions": []},
        ],
    }
    for key, expected in expected_candidates.items():
        if by_key[key]["outcome"] != expected:
            raise AssertionError(f"pinned movement {key} did not reach {expected!r}")

    opened = [row for row in case_rows if row["envelope"] is not None]
    corpus = [row for row in case_rows if row["envelope"] is None]
    prior = [row for row in case_rows if row["envelope"] != "E16"]
    if any(row["changed"] for row in prior):
        raise AssertionError("one of the frozen 140 evidence rows moved")
    opened_negative_flips = [
        row["key"]
        for row in opened
        if row["designed_class"] == "negative" and row["outcome"][0] == "candidate"
    ]
    corpus_correct_flips = [
        row["key"] for row in corpus if row["labeled_correct"] and row["outcome"][0] == "candidate"
    ]
    if opened_negative_flips or corpus_correct_flips:
        raise AssertionError(
            f"evidence none-flip failure: {opened_negative_flips!r} {corpus_correct_flips!r}"
        )

    retro: dict[str, str] = {}
    for envelope in ("E10", "E11", "E12", "E13", "E14", "E15", "E16"):
        positives = [
            row for row in opened if row["envelope"] == envelope and row["role"].startswith("P")
        ]
        retro[envelope] = f"{sum(row['outcome'][0] == 'candidate' for row in positives)}/6"
    if retro != EXPECTED_RETRO:
        raise AssertionError(f"retro recall changed: {retro!r}")
    corpus_correct = [row for row in corpus if row["designed_class"] == "correct"]
    corpus_misstep = [row for row in corpus if row["designed_class"] == "misstep"]
    corpus_score = {
        "correct_candidates": sum(row["outcome"][0] == "candidate" for row in corpus_correct),
        "correct_count": len(corpus_correct),
        "misstep_candidates": sum(row["outcome"][0] == "candidate" for row in corpus_misstep),
        "misstep_count": len(corpus_misstep),
    }
    if corpus_score != {
        "correct_candidates": 0,
        "correct_count": 25,
        "misstep_candidates": 19,
        "misstep_count": 25,
    }:
        raise AssertionError(f"corpus score changed: {corpus_score!r}")

    new = (*gatekeeping_fixtures(), *terminal_and_helper_fixtures())
    new_names = frozenset(fixture.name for fixture in new)
    fixtures = all_fixtures()
    fixture_pairs: list[tuple[dict[str, Any], ShadowResult]] = []
    for index, fixture in enumerate(fixtures, 1):
        fixture_pairs.append(_fixture_row(fixture, new_names))
        if index % 25 == 0:
            print(f"fixture-progress {index}", flush=True)
    fixture_rows = [row for row, _ in fixture_pairs]
    fixture_flips = [
        row["name"]
        for row in fixture_rows
        if row["correct_analysis"] and row["outcome"][0] == "candidate"
    ]
    if fixture_flips:
        raise AssertionError(f"correct fixture moved to candidate: {fixture_flips!r}")
    categories = Counter(row["category"] for row in fixture_rows)
    if len(fixture_rows) != 203:
        raise AssertionError(f"fixture census is {len(fixture_rows)}, not 203")
    if sum(row["correct_analysis"] for row in fixture_rows) != 183:
        raise AssertionError("correct-fixture census is not 183")

    before_questions = current_question_keys()
    after_questions = frozenset(
        key
        for key in before_questions
        if key not in by_key or by_key[key]["outcome"][0] not in {"candidate", "covered"}
    )
    if after_questions != before_questions:
        raise AssertionError(
            "3.3 changed the correction-scope question census despite no mover carrying one"
        )

    payload: dict[str, Any] = {
        "schema": "multitest-v3.3-terminal-presentation-prototype-sweep-v1",
        "baseline": "code_csv_multiple_testing 3.2.0 source classifications",
        "prototype_fidelity": (
            "strict closed terminal-presentation and single-call helper-record proofs; "
            "the unchanged 3.2 analyzer classifies every admitted surrogate"
        ),
        "case_count": len(case_rows),
        "opened_case_count": len(opened),
        "corpus_case_count": len(corpus),
        "prior_evidence_identity_count": len(prior),
        "fixture_count": len(fixture_rows),
        "fixture_category_counts": dict(sorted(categories.items())),
        "correct_fixture_count": sum(row["correct_analysis"] for row in fixture_rows),
        "movement_count": len(movements),
        "movement_set": list(movements),
        "retro_recall": retro,
        "corpus_score": corpus_score,
        "none_flip": {
            "corpus_correct": [len(corpus_correct_flips), 25],
            "opened_negatives": [len(opened_negative_flips), 63],
            "all_correct_fixtures": [len(fixture_flips), 183],
            "cumulative_v3_correct": [
                0,
                sum(
                    row["correct_analysis"]
                    for row in fixture_rows
                    if row["category"].startswith(("frozen-v3", "audit-fix"))
                ),
            ],
            "b5_expression_variants": [0, categories["b5-expression-variant"]],
            "v31_laundering_adjacent": [0, categories["v3.1-laundering-adjacent"]],
            "ap_correct": [
                0,
                sum(
                    row["correct_analysis"] for row in fixture_rows if row["category"] == "ap-v3.2"
                ),
            ],
            "frozen_gatekeeping": [0, categories["frozen-gatekeeping"]],
            "new_terminal_helper_correct": [
                0,
                sum(
                    row["correct_analysis"]
                    for row in fixture_rows
                    if row["category"] in {"terminal-adversary", "helper-adversary"}
                ),
            ],
        },
        "question_census": {
            "before": {
                "opened": sum(not key.startswith("corpus:") for key in before_questions),
                "corpus": sum(key.startswith("corpus:") for key in before_questions),
                "total": len(before_questions),
            },
            "after": {
                "opened": sum(not key.startswith("corpus:") for key in after_questions),
                "corpus": sum(key.startswith("corpus:") for key in after_questions),
                "total": len(after_questions),
            },
            "removed": sorted(before_questions - after_questions),
            "note": (
                "E16 P2/P3/P4 carried no correction-scope question under 3.2; their only "
                "sealed MaterialQuestion was the unrelated publication-surface question"
            ),
        },
        "instrumentation_sha256": _sha256((ROOT / "instrument_results.json").read_bytes()),
        "instrumentation_observed": instrumentation["observed_not_inferred"],
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
            {
                "movement_set": result["movement_set"],
                "retro_recall": result["retro_recall"],
                "none_flip": result["none_flip"],
                "question_census": result["question_census"],
                "corpus_score": result["corpus_score"],
            },
            indent=2,
            sort_keys=True,
        )
    )
