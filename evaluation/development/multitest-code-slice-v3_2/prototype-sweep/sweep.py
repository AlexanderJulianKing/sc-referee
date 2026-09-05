"""Execute and byte-pin the strict MT 3.2 AP(C, POS) prototype sweep."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from ap_shadow import APResult, analyze_ap
from fixture_catalog import Fixture, all_fixtures, new_ap_fixtures
from harness import all_cases, analyze, classify, inputs, question_keys, reference_case

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results.json"
FIXTURES = ROOT / "fixtures"
EXPECTED_MOVEMENTS = (
    "E15:P6:81980e878c1bc8cc216b",
    "corpus:spec-28",
)
EXPECTED_QUESTIONS_AFTER = frozenset(
    {
        "E10:N2:9be74afbe9659bd50580",
        "E10:N3:b787314c170f8f690060",
        "E11:N2:d11a7136d1e91ed8e26f",
        "E11:N3:479317f1706d4fb929e5",
        "E12:N2:f256af2f5c5d98f37e65",
        "E12:N3:678e94e79226936fd647",
        "E13:P6:d0f9fcd52f47e4d64668",
        "E13:N1:b7d38f6e9284abfd3ee6",
        "E13:N2:f65170c644b90c4a893c",
        "E13:N3:c15f507ad59999fd9371",
        "E14:P6:94786af7eca95fff6d78",
        "E15:P5:3d2f92807b8138de6463",
        "E15:N3:907f9057eb9fc1d88e99",
        "corpus:spec-02",
        "corpus:spec-04",
        "corpus:spec-06",
        "corpus:spec-24",
        "corpus:spec-26",
        "corpus:spec-29",
        "corpus:spec-46",
        "corpus:spec-47",
        "corpus:spec-48",
    }
)


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _case_row(case: Any) -> dict[str, Any]:
    values = inputs(case)
    content = values.pop("content")
    result = analyze_ap(content, baseline=case.baseline, **values)
    return {
        "key": case.key,
        "envelope": case.envelope,
        "role": case.role,
        "designed_class": case.designed_class,
        "labeled_correct": case.labeled_correct,
        "source_sha256": _sha256(content),
        "baseline": case.baseline.as_json(),
        "outcome": result.outcome.as_json(),
        "changed": result.changed,
        "attempted": result.attempted,
        "ap_model": result.model,
        "corrected_positions": list(result.corrected_positions),
        "detail": dict(result.detail),
        "surrogate_sha256": result.surrogate_sha256,
    }


def _execute_fixture(fixture: Fixture) -> tuple[dict[str, Any], APResult]:
    case = reference_case(fixture.case_key)
    source = fixture.source
    if fixture.category == "ap-v3.2":
        # These checked-in sources preserve deliberate analysis idioms.  Keep the
        # formatter from mechanically changing the AST evidence after generation.
        source = b"# fmt: off\n" + source
    execution_mode = "frozen-analyzer"
    if fixture.category == "v3.1-laundering-adjacent":
        baseline = fixture.baseline
        execution_mode = "reason-bound-witness"
    else:
        baseline = classify(analyze(case, source))
        if fixture.category != "ap-v3.2" and baseline != fixture.baseline:
            raise AssertionError(
                f"frozen fixture baseline changed: {fixture.name}: "
                f"{baseline.as_json()} != {fixture.baseline.as_json()}"
            )
    values = inputs(case, source)
    content = values.pop("content")
    result = analyze_ap(content, baseline=baseline, **values)
    if fixture.expected is None or result.outcome != fixture.expected:
        expected = None if fixture.expected is None else fixture.expected.as_json()
        raise AssertionError(f"fixture {fixture.name}: {result.outcome.as_json()} != {expected}")
    if fixture.expected_gate is not None and result.detail.get("gate") != fixture.expected_gate:
        raise AssertionError(
            f"fixture {fixture.name}: gate {result.detail.get('gate')!r} "
            f"!= {fixture.expected_gate!r}"
        )
    if (
        fixture.expected_gate_reason is not None
        and result.detail.get("gate_reason") != fixture.expected_gate_reason
    ):
        raise AssertionError(
            f"fixture {fixture.name}: gate reason {result.detail.get('gate_reason')!r} "
            f"!= {fixture.expected_gate_reason!r}"
        )
    source_path: str | None = None
    if fixture.category == "ap-v3.2":
        FIXTURES.mkdir(parents=True, exist_ok=True)
        path = FIXTURES / f"{fixture.name}.py"
        path.write_bytes(source)
        source_path = path.relative_to(ROOT).as_posix()
    return (
        {
            "name": fixture.name,
            "case_key": fixture.case_key,
            "category": fixture.category,
            "correct_analysis": fixture.correct_analysis,
            "design_clause": fixture.design_clause,
            "source_origin": fixture.source_origin,
            "source_path": source_path,
            "source_sha256": _sha256(source),
            "execution_mode": execution_mode,
            "expected_gate": fixture.expected_gate,
            "expected_gate_reason": fixture.expected_gate_reason,
            "baseline": baseline.as_json(),
            "outcome": result.outcome.as_json(),
            "changed": result.changed,
            "attempted": result.attempted,
            "ap_model": result.model,
            "corrected_positions": list(result.corrected_positions),
            "detail": dict(result.detail),
            "surrogate_sha256": result.surrogate_sha256,
        },
        result,
    )


def execute() -> dict[str, Any]:
    cases = all_cases()
    case_rows = [_case_row(case) for case in cases]
    fixture_pairs = [_execute_fixture(fixture) for fixture in all_fixtures()]
    fixture_rows = [row for row, _ in fixture_pairs]

    movements = tuple(row["key"] for row in case_rows if row["changed"])
    if movements != EXPECTED_MOVEMENTS:
        raise AssertionError(f"movement set changed: {movements!r}")
    case_by_key = {row["key"]: row for row in case_rows}
    if case_by_key[EXPECTED_MOVEMENTS[0]]["outcome"] != [
        "candidate",
        "strict_subset",
        {"authorized_count": 8, "corrected_positions": [0, 1, 3]},
    ]:
        raise AssertionError("E15 P6 did not reach its strict-subset pin")
    if case_by_key[EXPECTED_MOVEMENTS[1]]["outcome"] != [
        "covered",
        "complete",
        {"authorized_count": 4, "corrected_positions": [0, 1, 2, 3]},
    ]:
        raise AssertionError("corpus spec-28 did not reach its complete pin")

    opened = [row for row in case_rows if row["envelope"] is not None]
    corpus = [row for row in case_rows if row["envelope"] is None]
    opened_negative_flips = [
        row["key"]
        for row in opened
        if row["designed_class"] == "negative" and row["outcome"][0] == "candidate"
    ]
    corpus_correct_flips = [
        row["key"] for row in corpus if row["labeled_correct"] and row["outcome"][0] == "candidate"
    ]
    correct_fixture_flips = [
        row["name"]
        for row in fixture_rows
        if row["correct_analysis"] and row["outcome"][0] == "candidate"
    ]
    if opened_negative_flips or corpus_correct_flips or correct_fixture_flips:
        raise AssertionError(
            "none-flip failure: "
            f"{opened_negative_flips!r} {corpus_correct_flips!r} {correct_fixture_flips!r}"
        )

    retro: dict[str, str] = {}
    for envelope in ("E10", "E11", "E12", "E13", "E14", "E15"):
        positives = [
            row for row in opened if row["envelope"] == envelope and row["role"].startswith("P")
        ]
        retro[envelope] = f"{sum(row['outcome'][0] == 'candidate' for row in positives)}/6"
    expected_retro = {
        "E10": "5/6",
        "E11": "6/6",
        "E12": "6/6",
        "E13": "4/6",
        "E14": "4/6",
        "E15": "3/6",
    }
    if retro != expected_retro:
        raise AssertionError(f"retro recall changed: {retro!r}")

    before_questions = question_keys()
    after_questions = frozenset(
        key
        for key in before_questions
        if not (key in case_by_key and case_by_key[key]["outcome"][0] in {"candidate", "covered"})
    )
    if after_questions != EXPECTED_QUESTIONS_AFTER:
        raise AssertionError(
            "post-AP question census differs: "
            f"removed={sorted(before_questions - after_questions)!r}"
        )

    category_counts = Counter(row["category"] for row in fixture_rows)
    cumulative_rows = [
        row for row in fixture_rows if row["category"].startswith(("frozen-v3", "audit-fix"))
    ]
    if len(cumulative_rows) != 71 or any(row["changed"] for row in cumulative_rows):
        raise AssertionError("the cumulative 71-row matrix was not outcome-identical")
    laundering_rows = [row for row in fixture_rows if row["category"] == "v3.1-laundering-adjacent"]
    if len(laundering_rows) != 16 or any(
        row["outcome"][0] == "candidate" for row in laundering_rows
    ):
        raise AssertionError("the 16 laundering-adjacent controls did not all refuse")
    b5_rows = [row for row in fixture_rows if row["category"] == "b5-expression-variant"]
    if len(b5_rows) != 63 or any(row["outcome"][0] == "candidate" for row in b5_rows):
        raise AssertionError("the 63 cumulative B5 expression variants did not all refuse")

    new_rows = [row for row in fixture_rows if row["category"] == "ap-v3.2"]
    if len(new_rows) != len(new_ap_fixtures()):
        raise AssertionError("the AP fixture census changed")
    payload: dict[str, Any] = {
        "schema": "multitest-v3.2-ap-prototype-sweep-v1",
        "baseline": "code_csv_multiple_testing 3.1.0 source classifications",
        "prototype_fidelity": "strict closed AP grammar; frozen 3.0 analyzer validates the structural surrogate",
        "case_count": len(case_rows),
        "opened_case_count": len(opened),
        "corpus_case_count": len(corpus),
        "fixture_count": len(fixture_rows),
        "fixture_category_counts": dict(sorted(category_counts.items())),
        "correct_fixture_count": sum(row["correct_analysis"] for row in fixture_rows),
        "movement_count": len(movements),
        "movement_set": list(movements),
        "retro_recall": retro,
        "none_flip": {
            "corpus_correct": [len(corpus_correct_flips), 25],
            "opened_negatives": [len(opened_negative_flips), 54],
            "all_correct_fixtures": [
                len(correct_fixture_flips),
                sum(row["correct_analysis"] for row in fixture_rows),
            ],
            "cumulative_v3_correct": [
                0,
                sum(row["correct_analysis"] for row in cumulative_rows),
            ],
            "v31_laundering_adjacent": [0, len(laundering_rows)],
            "b5_expression_variants": [0, len(b5_rows)],
            "new_ap_correct": [
                0,
                sum(row["correct_analysis"] for row in new_rows),
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
            {
                "movement_set": result["movement_set"],
                "retro_recall": result["retro_recall"],
                "none_flip": result["none_flip"],
                "question_census": result["question_census"],
            },
            indent=2,
            sort_keys=True,
        )
    )
