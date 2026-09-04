"""Execute and byte-pin the strict MT 3.5 recall-delta prototype sweep."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from fixture_catalog import all_fixtures, new_fixtures
from harness import ADAPTER_SHORT_CIRCUIT, all_cases, current_question_keys, inputs, reference_case
from instrument import execute as execute_instrumentation
from recall_deltas_shadow import ADMISSION_KINDS, INSTALLED, analyze_v35_shadow

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results.json"
FIXTURES = ROOT / "fixtures"

EXPECTED_MOVEMENTS = (
    "E15:P3:afe47b2a7ea87ed21a69",
    "E17:N1:e2d8b1bdf4baa671a1b4",
    "E18:P2:5a9277448db34379ce78",
    "E18:P3:d1b1fc47ccdabd0c2f22",
)
#: Two catches and one clearance.  A negative may reach `covered`; it may never reach
#: `candidate`.  E17 N1 is a correct complete `multipletests` family whose only wall was an
#: integer group constant, so resolving it is a true clearance, not a false accusation.
EXPECTED_CANDIDATES = {
    "E15:P3:afe47b2a7ea87ed21a69": [
        "candidate",
        "none",
        {"authorized_count": 5, "corrected_positions": []},
    ],
    "E18:P2:5a9277448db34379ce78": [
        "candidate",
        "none",
        {"authorized_count": 6, "corrected_positions": []},
    ],
    "E18:P3:d1b1fc47ccdabd0c2f22": [
        "candidate",
        "none",
        {"authorized_count": 5, "corrected_positions": []},
    ],
}
EXPECTED_CLEARANCES = {
    "E17:N1:e2d8b1bdf4baa671a1b4": [
        "covered",
        "complete",
        {"authorized_count": 4, "corrected_positions": [0, 1, 2, 3]},
    ],
}
EXPECTED_RETRO = {
    "E10": "5/6",
    "E11": "6/6",
    "E12": "6/6",
    "E13": "4/6",
    "E14": "4/6",
    "E15": "4/6",
    "E16": "4/6",
    "E17": "6/6",
    "E18": "4/6",
}
EXPECTED_E18_BASELINE = {
    "P1": ["candidate", "none", {"authorized_count": 4, "corrected_positions": []}],
    "P2": ["abstain", "hierarchical-gatekeeping-present"],
    "P3": ["abstain", "test-operand-lineage-unresolved"],
    "P4": ["candidate", "none", {"authorized_count": 3, "corrected_positions": []}],
    "P5": ["abstain", "pvalue-family-collection-unresolved"],
    "P6": ["abstain", "authorized-reader-lineage-unavailable"],
    "N1": ["covered", "complete", {"authorized_count": 5, "corrected_positions": [0, 1, 2, 3, 4]}],
    "N2": ["abstain", "unresolved-decision-threshold"],
    "N3": ["abstain", "authorized-family-test-census-incomplete"],
    "N4": ["abstain", "extra-registered-test-outside-authorized-family"],
    "N5": ["abstain", "hierarchical-gatekeeping-present"],
    "N6": ["abstain", "authorized-reader-lineage-unavailable"],
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
    "v3.4-",
    "v3.1-",
    "comprehension",
    "iterator",
    "cap",
    "reason-routing",
    "terminal-ifexp",
)


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _case_row(case: Any) -> dict[str, Any]:
    values = inputs(case)
    content = values.pop("content")
    short_circuit = case.key in ADAPTER_SHORT_CIRCUIT
    result = analyze_v35_shadow(content, **values)
    if short_circuit:
        if result.changed:
            raise AssertionError(f"a 3.5 admission crossed the adapter short-circuit: {case.key}")
        effective = case.baseline
    else:
        effective = result.outcome
    from harness import classify

    return {
        "key": case.key,
        "envelope": case.envelope,
        "role": case.role,
        "designed_class": case.designed_class,
        "labeled_correct": case.labeled_correct,
        "source_sha256": _sha256(content),
        "baseline": case.baseline.as_json(),
        "source_analyzer_baseline": classify(result.frozen).as_json(),
        "outcome": classify(effective).as_json()
        if hasattr(effective, "reason")
        else effective.as_json(),
        "changed": (
            classify(effective).as_json() if hasattr(effective, "reason") else effective.as_json()
        )
        != case.baseline.as_json(),
        "adapter_short_circuit": short_circuit,
        "admission_census": dict(result.admission_census),
        "reanalysis_reason": result.reanalysis_reason,
    }


def _fixture_row(fixture: Any, new_names: frozenset[str]) -> dict[str, Any]:
    from harness import classify

    case = reference_case(fixture.case_key)
    values = inputs(case, fixture.source)
    content = values.pop("content")
    result = analyze_v35_shadow(content, **values)
    census = dict(result.admission_census)
    outcome = classify(result.outcome)
    baseline = classify(result.frozen)
    expected = fixture.expected
    refused = getattr(fixture, "refused_admission", None)
    admitted = getattr(fixture, "admitted", None)
    is_new = fixture.name in new_names
    if is_new and expected is not None and outcome != expected:
        raise AssertionError(
            f"fixture {fixture.name}: {outcome.as_json()} != {expected.as_json()}"
        )
    if is_new and refused is not None:
        if baseline.state in {"candidate", "covered"}:
            raise AssertionError(
                f"fixture {fixture.name}: its disqualifier assertion is vacuous, because the "
                f"shipped 3.4 baseline already classifies it and no admission is attempted"
            )
        if census[refused]:
            raise AssertionError(f"fixture {fixture.name}: the {refused} production fired")
    if is_new and admitted is not None and not census[admitted]:
        raise AssertionError(f"fixture {fixture.name}: the {admitted} production did not fire")
    if fixture.correct_analysis and outcome.state == "candidate":
        raise AssertionError(f"correct fixture became a candidate: {fixture.name}")
    if not is_new and outcome != baseline:
        raise AssertionError(f"a frozen 3.4 fixture moved: {fixture.name}")
    if is_new:
        FIXTURES.mkdir(parents=True, exist_ok=True)
        path = FIXTURES / f"{fixture.name}.py"
        path.write_bytes(fixture.source)
        source_path = path.relative_to(ROOT).as_posix()
    else:
        source_path = str(fixture.source_origin)
    return {
        "name": fixture.name,
        "case_key": fixture.case_key,
        "category": str(fixture.category),
        "new_in_v35": is_new,
        "correct_analysis": bool(fixture.correct_analysis),
        "refused_admission": refused if is_new else None,
        "required_admission": admitted if is_new else None,
        "design_clause": str(fixture.design_clause),
        "source_origin": str(fixture.source_origin),
        "source_path": source_path,
        "source_sha256": _sha256(fixture.source),
        "baseline": baseline.as_json(),
        "outcome": outcome.as_json(),
        "changed": outcome != baseline,
        "admission_census": census,
        "reanalysis_reason": result.reanalysis_reason,
    }


def execute() -> dict[str, Any]:
    instrumentation = execute_instrumentation()
    cases = all_cases()
    case_rows: list[dict[str, Any]] = []
    for index, case in enumerate(cases, 1):
        case_rows.append(_case_row(case))
        if index % 25 == 0:
            print(f"case-progress {index}", flush=True)

    measured_e18 = {row["role"]: row["baseline"] for row in case_rows if row["envelope"] == "E18"}
    if measured_e18 != EXPECTED_E18_BASELINE:
        raise AssertionError("the sealed E18 3.4 baseline does not match all fifteen pins")
    movements = tuple(row["key"] for row in case_rows if row["changed"])
    if movements != EXPECTED_MOVEMENTS:
        raise AssertionError(f"movement set changed: {movements!r}")
    by_key = {row["key"]: row for row in case_rows}
    for key, expected in {**EXPECTED_CANDIDATES, **EXPECTED_CLEARANCES}.items():
        if by_key[key]["outcome"] != expected:
            raise AssertionError(f"pinned movement {key} did not reach {expected!r}")
    gained_candidates = [
        row["key"]
        for row in case_rows
        if row["changed"] and row["outcome"][0] == "candidate"
    ]
    if sorted(gained_candidates) != sorted(EXPECTED_CANDIDATES):
        raise AssertionError(f"the candidate movement set changed: {gained_candidates!r}")

    opened = [row for row in case_rows if row["envelope"] is not None]
    corpus = [row for row in case_rows if row["envelope"] is None]
    prior = [row for row in case_rows if row["envelope"] != "E18"]
    prior_moved_keys = [row["key"] for row in prior if row["changed"]]
    if prior_moved_keys != [
        "E15:P3:afe47b2a7ea87ed21a69",
        "E17:N1:e2d8b1bdf4baa671a1b4",
    ]:
        raise AssertionError(f"a frozen 3.4 evidence row moved: {prior_moved_keys!r}")
    lost = [
        row["key"]
        for row in case_rows
        if row["baseline"][0] in {"candidate", "covered"} and row["outcome"] != row["baseline"]
    ]
    if lost:
        raise AssertionError(f"a frozen 3.4 classification was lost: {lost!r}")
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
    for envelope in ("E10", "E11", "E12", "E13", "E14", "E15", "E16", "E17", "E18"):
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
    if len(fixture_rows) != 283:
        raise AssertionError(f"fixture census is {len(fixture_rows)}, not 283")
    if sum(row["correct_analysis"] for row in fixture_rows) != 199:
        raise AssertionError("the correct-fixture census is not 199")
    correct_fixture_count = sum(row["correct_analysis"] for row in fixture_rows)
    prior_moved = [row["name"] for row in fixture_rows if not row["new_in_v35"] and row["changed"]]
    if prior_moved:
        raise AssertionError(f"a frozen 3.4 fixture moved: {prior_moved!r}")

    admission_totals = {
        kind: sum(row["admission_census"][kind] for row in (*case_rows, *fixture_rows))
        for kind in ADMISSION_KINDS
    }
    admission_rows = {
        kind: sorted(
            row.get("key", row.get("name"))
            for row in (*case_rows, *fixture_rows)
            if row["admission_census"][kind]
        )
        for kind in ADMISSION_KINDS
    }
    evidence_admission_rows = {
        kind: sorted(row["key"] for row in case_rows if row["admission_census"][kind])
        for kind in ADMISSION_KINDS
    }

    before_questions = current_question_keys()
    after_questions = frozenset(
        key
        for key in before_questions
        if key not in by_key or by_key[key]["outcome"][0] not in {"candidate", "covered"}
    )

    payload: dict[str, Any] = {
        "schema": "multitest-v3.5-recall-delta-prototype-sweep-v1",
        "baseline": "code_csv_multiple_testing 3.4.0 shipped source classifications",
        "installed_productions": list(INSTALLED),
        "specified_not_installed": [
            kind for kind in ADMISSION_KINDS if kind not in INSTALLED
        ],
        "case_count": len(case_rows),
        "opened_case_count": len(opened),
        "corpus_case_count": len(corpus),
        "prior_evidence_identity_count": len(prior),
        "fixture_count": len(fixture_rows),
        "fixture_category_counts": dict(sorted(categories.items())),
        "correct_fixture_count": correct_fixture_count,
        "new_fixture_count": sum(row["new_in_v35"] for row in fixture_rows),
        "movement_count": len(movements),
        "movement_set": list(movements),
        "candidate_movements": sorted(EXPECTED_CANDIDATES),
        "clearance_movements": sorted(EXPECTED_CLEARANCES),
        "retro_recall": retro,
        "corpus_score": corpus_score,
        "admission_totals": admission_totals,
        "admission_rows": admission_rows,
        "evidence_admission_rows": evidence_admission_rows,
        "none_flip": {
            "opened_negatives": [
                len(opened_negative_flips),
                sum(row["designed_class"] == "negative" for row in opened),
            ],
            "corpus_correct": [len(corpus_correct_flips), 25],
            "all_correct_fixtures": [len(fixture_flips), correct_fixture_count],
            "new_v35_correct_fixtures": [
                0,
                sum(row["correct_analysis"] and row["new_in_v35"] for row in fixture_rows),
            ],
            "frozen_v34_fixtures_unchanged": [
                len(prior_moved),
                sum(not row["new_in_v35"] for row in fixture_rows),
            ],
            "frozen_v34_evidence_unchanged": [
                sum(row["changed"] for row in prior),
                len(prior),
            ],
            "negatives_gaining_a_candidate": [
                len([row for row in opened if row["designed_class"] == "negative" and row["changed"]
                     and row["outcome"][0] == "candidate"]),
                sum(row["designed_class"] == "negative" for row in opened),
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
                "retro_recall": result["retro_recall"],
                "none_flip": result["none_flip"],
                "question_census": result["question_census"],
                "corpus_score": result["corpus_score"],
                "admission_totals": result["admission_totals"],
                "evidence_admission_rows": result["evidence_admission_rows"],
                "fixture_category_counts": result["fixture_category_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
