"""Execute and byte-pin the strict MT 3.4 comprehension/iterator prototype sweep."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from comprehension_iterator_shadow import ShadowResult, analyze_v34_shadow
from fixture_catalog import all_fixtures, new_fixtures
from harness import ADAPTER_SHORT_CIRCUIT, all_cases, current_question_keys, inputs, reference_case
from instrument import execute as execute_instrumentation

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results.json"
FIXTURES = ROOT / "fixtures"
EXPECTED_MOVEMENTS = (
    "E17:P3:a2e031f79e31c80fd900",
    "E17:P6:b4e507c4b55954752f14",
)
EXPECTED_CANDIDATES = {
    "E17:P3:a2e031f79e31c80fd900": [
        "candidate",
        "none",
        {"authorized_count": 6, "corrected_positions": []},
    ],
    "E17:P6:b4e507c4b55954752f14": [
        "candidate",
        "strict_subset",
        {"authorized_count": 7, "corrected_positions": [0, 1, 2]},
    ],
}
EXPECTED_RETRO = {
    "E10": "5/6",
    "E11": "6/6",
    "E12": "6/6",
    "E13": "4/6",
    "E14": "4/6",
    "E15": "3/6",
    "E16": "4/6",
    "E17": "6/6",
}
EXPECTED_E17_BASELINE = {
    "P1": ["candidate", "none", {"authorized_count": 5, "corrected_positions": []}],
    "P2": ["candidate", "none", {"authorized_count": 3, "corrected_positions": []}],
    "P3": ["abstain", "hierarchical-gatekeeping-present"],
    "P4": ["candidate", "none", {"authorized_count": 4, "corrected_positions": []}],
    "P5": ["candidate", "strict_subset", {"authorized_count": 8, "corrected_positions": [2, 3]}],
    "P6": ["abstain", "unresolved-manual-correction-present"],
    "N1": ["abstain", "test-operand-lineage-unresolved"],
    "N2": ["abstain", "unresolved-decision-threshold"],
    "N3": ["abstain", "unresolved-manual-correction-present"],
    "N4": ["abstain", "extra-registered-test-outside-authorized-family"],
    "N5": ["abstain", "test-battery-cardinality-unresolved"],
    "N6": ["abstain", "authorized-family-test-census-incomplete"],
    "N7": ["abstain", "authorized-family-test-census-incomplete"],
    "N8": ["abstain", "test-battery-cardinality-unresolved"],
    "N9": ["abstain", "unresolved-decision-threshold"],
}
FROZEN_FIXTURE_PREFIXES = (
    "frozen-v3",
    "audit-fix",
    "b5-",
    "ap-v3.2",
    "frozen-gatekeeping",
    "terminal-adversary",
    "helper-adversary",
    "terminal-positive",
    "helper-positive",
)


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _case_row(case: Any) -> dict[str, Any]:
    values = inputs(case)
    content = values.pop("content")
    short_circuit = case.key in ADAPTER_SHORT_CIRCUIT
    # On a short-circuit row the frozen baseline is the adapter reason, which precedes the source
    # analyzer.  Measure that row against the source analyzer's own 3.3 result instead, so
    # "no 3.4 admission crossed it" is a real comparison and not an artefact of the two levels.
    result: ShadowResult = analyze_v34_shadow(
        content, baseline=None if short_circuit else case.baseline, **values
    )
    if short_circuit:
        if result.changed or result.relabeled:
            raise AssertionError(f"a 3.4 admission crossed the adapter short-circuit: {case.key}")
        effective = case.baseline
    else:
        effective = result.core_outcome
    return {
        "key": case.key,
        "envelope": case.envelope,
        "role": case.role,
        "designed_class": case.designed_class,
        "labeled_correct": case.labeled_correct,
        "source_sha256": _sha256(content),
        "baseline": case.baseline.as_json(),
        "source_analyzer_baseline": result.baseline.as_json(),
        "outcome": effective.as_json(),
        "outcome_with_reason_routing": (
            case.baseline.as_json() if short_circuit else result.outcome.as_json()
        ),
        "changed": effective != case.baseline,
        "relabeled": bool(result.relabeled and not short_circuit),
        "adapter_short_circuit": short_circuit,
        "models": list(result.models),
        "admission_census": dict(result.detail["admission_census"]),  # type: ignore[arg-type]
        "detail": {
            "comprehensions": result.detail["comprehensions"],
            "relabel_witness": result.detail["relabel_witness"],
        },
        "surrogate_sha256": result.surrogate_sha256,
    }


def _fixture_row(fixture: Any, new_names: frozenset[str]) -> dict[str, Any]:
    case = reference_case(fixture.case_key)
    values = inputs(case, fixture.source)
    content = values.pop("content")
    result: ShadowResult = analyze_v34_shadow(content, **values)
    census = dict(result.detail["admission_census"])  # type: ignore[arg-type]
    category = str(fixture.category)
    expected = fixture.expected
    refused = getattr(fixture, "refused_admission", None)
    admitted = getattr(fixture, "admitted", None)
    if expected is not None and category != "v3.1-laundering-adjacent":
        if result.core_outcome != expected:
            raise AssertionError(
                f"fixture {fixture.name}: {result.core_outcome.as_json()} != {expected.as_json()}"
            )
    if refused is not None:
        if result.baseline.state in {"candidate", "covered"}:
            raise AssertionError(
                f"fixture {fixture.name}: its disqualifier assertion is vacuous, because the "
                f"shipped 3.3 baseline already classifies it and no admission is attempted"
            )
        if census[refused]:
            raise AssertionError(
                f"fixture {fixture.name}: the {refused} admission fired but must not"
            )
    if admitted is not None and not census[admitted]:
        raise AssertionError(f"fixture {fixture.name}: the {admitted} admission did not fire")
    if fixture.correct_analysis and result.core_outcome.state == "candidate":
        raise AssertionError(f"correct fixture became a candidate: {fixture.name}")
    if category.startswith(FROZEN_FIXTURE_PREFIXES) and result.changed:
        raise AssertionError(f"frozen cumulative fixture moved: {fixture.name}")
    if fixture.name in new_names:
        FIXTURES.mkdir(parents=True, exist_ok=True)
        path = FIXTURES / f"{fixture.name}.py"
        path.write_bytes(fixture.source)
        source_path = path.relative_to(ROOT).as_posix()
    else:
        source_path = str(fixture.source_origin)
    return {
        "name": fixture.name,
        "case_key": fixture.case_key,
        "category": category,
        "correct_analysis": bool(fixture.correct_analysis),
        "refused_admission": refused,
        "required_admission": admitted,
        "design_clause": str(fixture.design_clause),
        "source_origin": str(fixture.source_origin),
        "source_path": source_path,
        "source_sha256": _sha256(fixture.source),
        "frozen_expected": None if expected is None else expected.as_json(),
        "baseline": result.baseline.as_json(),
        "outcome": result.core_outcome.as_json(),
        "outcome_with_reason_routing": result.outcome.as_json(),
        "changed": result.changed,
        "relabeled": result.relabeled,
        "models": list(result.models),
        "admission_census": census,
        "surrogate_sha256": result.surrogate_sha256,
    }


def execute() -> dict[str, Any]:
    instrumentation = execute_instrumentation()
    cases = all_cases()
    case_rows: list[dict[str, Any]] = []
    for index, case in enumerate(cases, 1):
        case_rows.append(_case_row(case))
        if index % 25 == 0:
            print(f"case-progress {index}", flush=True)

    if {
        row["role"]: row["baseline"] for row in case_rows if row["envelope"] == "E17"
    } != EXPECTED_E17_BASELINE:
        raise AssertionError("the sealed E17 3.3 baseline does not match all fifteen pins")
    movements = tuple(row["key"] for row in case_rows if row["changed"])
    if movements != EXPECTED_MOVEMENTS:
        raise AssertionError(f"movement set changed: {movements!r}")
    by_key = {row["key"]: row for row in case_rows}
    for key, expected in EXPECTED_CANDIDATES.items():
        if by_key[key]["outcome"] != expected:
            raise AssertionError(f"pinned movement {key} did not reach {expected!r}")

    opened = [row for row in case_rows if row["envelope"] is not None]
    corpus = [row for row in case_rows if row["envelope"] is None]
    prior = [row for row in case_rows if row["envelope"] != "E17"]
    if any(row["changed"] for row in prior):
        raise AssertionError("one of the 155 frozen evidence rows moved")
    lost = [
        row["key"]
        for row in case_rows
        if row["baseline"][0] in {"candidate", "covered"} and row["outcome"] != row["baseline"]
    ]
    if lost:
        raise AssertionError(f"a frozen 3.3 classification was lost: {lost!r}")
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
    relabels = [row["key"] for row in case_rows if row["relabeled"]]

    retro: dict[str, str] = {}
    for envelope in ("E10", "E11", "E12", "E13", "E14", "E15", "E16", "E17"):
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

    new_names = frozenset(fixture.name for fixture in new_fixtures())
    fixtures = all_fixtures()
    fixture_rows: list[dict[str, Any]] = []
    for index, fixture in enumerate(fixtures, 1):
        fixture_rows.append(_fixture_row(fixture, new_names))
        if index % 25 == 0:
            print(f"fixture-progress {index}", flush=True)
    fixture_flips = [
        row["name"]
        for row in fixture_rows
        if row["correct_analysis"] and row["outcome"][0] == "candidate"
    ]
    if fixture_flips:
        raise AssertionError(f"correct fixture moved to candidate: {fixture_flips!r}")
    categories = Counter(row["category"] for row in fixture_rows)
    if len(fixture_rows) != 245:
        raise AssertionError(f"fixture census is {len(fixture_rows)}, not 245")
    correct_fixture_count = sum(row["correct_analysis"] for row in fixture_rows)
    if correct_fixture_count != 194:
        raise AssertionError(f"correct-fixture census is {correct_fixture_count}, not 194")

    prior_moved = [
        row["name"]
        for row in fixture_rows
        if row["category"].startswith(FROZEN_FIXTURE_PREFIXES) and row["changed"]
    ]
    if prior_moved:
        raise AssertionError(f"a frozen 3.2/3.3 fixture moved: {prior_moved!r}")

    admission_totals = {
        kind: sum(row["admission_census"][kind] for row in (*case_rows, *fixture_rows))
        for kind in ("comprehension", "terminal-ifexp", "enumerate", "cap")
    }
    admission_rows = {
        kind: sorted(
            row.get("key", row.get("name"))
            for row in (*case_rows, *fixture_rows)
            if row["admission_census"][kind]
        )
        for kind in ("comprehension", "terminal-ifexp", "enumerate", "cap")
    }

    before_questions = current_question_keys()
    after_questions = frozenset(
        key
        for key in before_questions
        if key not in by_key or by_key[key]["outcome"][0] not in {"candidate", "covered"}
    )

    payload: dict[str, Any] = {
        "schema": "multitest-v3.4-comprehension-iterator-prototype-sweep-v1",
        "baseline": "code_csv_multiple_testing 3.3.0 shipped source classifications",
        "prototype_fidelity": (
            "strict closed comprehension normalization, terminal-IfExp print-only proof, "
            "enumerate row-table admission, and adjacent if-cap fold; the unchanged 3.3 "
            "analyzer classifies every normalized source"
        ),
        "case_count": len(case_rows),
        "opened_case_count": len(opened),
        "corpus_case_count": len(corpus),
        "prior_evidence_identity_count": len(prior),
        "fixture_count": len(fixture_rows),
        "fixture_category_counts": dict(sorted(categories.items())),
        "correct_fixture_count": correct_fixture_count,
        "movement_count": len(movements),
        "movement_set": list(movements),
        "reason_routing_relabels": relabels,
        "reason_routing_relabel_count": len(relabels),
        "retro_recall": retro,
        "corpus_score": corpus_score,
        "admission_totals": admission_totals,
        "admission_rows": admission_rows,
        "none_flip": {
            "corpus_correct": [len(corpus_correct_flips), 25],
            "opened_negatives": [
                len(opened_negative_flips),
                sum(row["designed_class"] == "negative" for row in opened),
            ],
            "all_correct_fixtures": [len(fixture_flips), correct_fixture_count],
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
            "v33_terminal_helper_correct": [
                0,
                sum(
                    row["correct_analysis"]
                    for row in fixture_rows
                    if row["category"] in {"terminal-adversary", "helper-adversary"}
                ),
            ],
            "new_v34_correct": [
                0,
                sum(row["correct_analysis"] for row in fixture_rows if row["name"] in new_names),
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
                "reason_routing_relabels": result["reason_routing_relabels"],
                "retro_recall": result["retro_recall"],
                "none_flip": result["none_flip"],
                "question_census": result["question_census"],
                "corpus_score": result["corpus_score"],
                "admission_totals": result["admission_totals"],
                "fixture_category_counts": result["fixture_category_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
