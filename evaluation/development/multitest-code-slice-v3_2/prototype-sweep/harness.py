"""Read-only 3.1 anchor inputs for the MT 3.2 AP(C, POS) prototype sweep."""

from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 import (
    MultipleTestingDataflowResult,
    analyze_code_csv_multiple_testing_dataflow,
)

REPO = Path(__file__).resolve().parents[4]
CORPUS = REPO / "evaluation/development/multitest-open-corpus-v1"
V3_RESULTS = REPO / "evaluation/development/multitest-code-slice-v3_0/prototype-sweep/results.json"
QUESTION_ORACLE = REPO / "evaluation/development/multitest-code-slice-v3_1/QUESTION_ORACLE.json"
ENVELOPE_ROOTS = {
    "E10": REPO / "evaluation/development/blind-envelope-10-2026-08-24",
    "E11": REPO / "evaluation/development/blind-envelope-11-2026-08-25",
    "E12": REPO / "evaluation/development/blind-envelope-12-2026-08-26",
    "E13": REPO / "evaluation/development/blind-envelope-13-2026-08-26",
    "E14": REPO / "evaluation/development/blind-envelope-14-2026-08-27",
    "E15": REPO / "evaluation/development/blind-envelope-15-2026-08-29",
}


@dataclass(frozen=True)
class Outcome:
    state: str
    reason_or_classification: str
    corrected_positions: tuple[int, ...] = ()
    authorized_count: int | None = None

    def as_json(self) -> list[object]:
        value: list[object] = [self.state, self.reason_or_classification]
        if self.state in {"candidate", "covered"}:
            value.append(
                {
                    "authorized_count": self.authorized_count,
                    "corrected_positions": list(self.corrected_positions),
                }
            )
        return value


@dataclass(frozen=True)
class CaseRef:
    key: str
    source_path: Path
    case_dir: Path
    envelope: str | None
    role: str
    designed_class: str
    labeled_correct: bool
    baseline: Outcome


def classify(result: MultipleTestingDataflowResult) -> Outcome:
    if result.reason is not None:
        return Outcome("abstain", result.reason)
    if result.facts is None:
        raise ValueError("analyzer returned neither facts nor an abstention reason")
    classification = result.facts.correction_classification
    return Outcome(
        "covered" if classification == "complete" else "candidate",
        classification,
        result.facts.corrected_positions,
        result.facts.family_size,
    )


def _outcome(value: list[object]) -> Outcome:
    state = str(value[0])
    reason = str(value[1])
    if len(value) == 2:
        return Outcome(state, reason)
    detail = value[2]
    if not isinstance(detail, dict):
        raise ValueError("coverage row is not an object")
    authorized_count = detail.get("authorized_count")
    return Outcome(
        state,
        reason,
        tuple(int(item) for item in detail["corrected_positions"]),
        None if authorized_count is None else int(authorized_count),
    )


def _parse_csv(content: bytes, group_column: str) -> tuple[tuple[str, ...], tuple[str, str]]:
    rows = list(
        csv.reader(io.StringIO(content.decode("utf-8"), newline=""), dialect="excel", strict=True)
    )
    header = tuple(rows[0])
    group_index = header.index(group_column)
    counts = Counter(row[group_index] for row in rows[1:])
    values = tuple(sorted(counts, key=lambda value: value.encode("utf-8")))
    if len(values) != 2:
        raise ValueError("prototype input group domain is not exactly binary")
    return header, (values[0], values[1])


def _finite_decimal(value: str) -> bool:
    try:
        number = float(value)
    except ValueError:
        return False
    return number == number and number not in {float("inf"), float("-inf")}


def _corpus_authority(case_dir: Path) -> tuple[str, tuple[str, ...]]:
    with (case_dir / "data.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    header = tuple(rows[0])
    group_index = 1
    outcomes = tuple(
        column
        for index, column in enumerate(header)
        if index not in {0, group_index} and all(_finite_decimal(row[index]) for row in rows[1:])
    )
    return header[group_index], outcomes


def inputs(case: CaseRef, source: bytes | None = None) -> dict[str, Any]:
    if case.envelope is None:
        group_column, outcomes = _corpus_authority(case.case_dir)
        material_path = "data.csv"
        csv_content = (case.case_dir / material_path).read_bytes()
    else:
        profile = json.loads((case.case_dir / "profile_1_2_0.json").read_text(encoding="utf-8"))
        authority = profile["semantic_role_authority"]["authorized_test_family"]
        material_path = authority["material_input_path"]
        group_column = authority["group_contrast_column"]
        outcomes = tuple(authority["outcome_columns"])
        csv_content = (case.case_dir / "project" / material_path).read_bytes()
    header, group_values = _parse_csv(csv_content, group_column)
    return {
        "content": source if source is not None else case.source_path.read_bytes(),
        "authorized_path": material_path,
        "group_column": group_column,
        "outcome_columns": outcomes,
        "csv_header": header,
        "group_values": group_values,
        "csv_content": csv_content,
    }


def analyze(case: CaseRef, source: bytes | None = None) -> MultipleTestingDataflowResult:
    values = inputs(case, source)
    content = values.pop("content")
    return analyze_code_csv_multiple_testing_dataflow(content, **values)


def _v3_rows() -> dict[str, Outcome]:
    payload = json.loads(V3_RESULTS.read_text(encoding="utf-8"))
    return {row["key"]: _outcome(row["outcome"]) for row in payload["cases"]}


def _e15_outcome(row: dict[str, Any], authorized_count: int) -> Outcome:
    state = row["dev_outcome"]
    reason = row["dev_reason_or_classification"]
    if state == "abstain":
        return Outcome("abstain", reason)
    if state == "candidate":
        return Outcome("candidate", reason, (), authorized_count)
    if state != "covered_complete":
        raise ValueError(f"unknown E15 state: {state}")
    match = re.fullmatch(r"complete positions=\[([0-9, ]*)\]", reason)
    if match is None:
        raise ValueError("E15 covered row has an unrecognized coverage string")
    positions = tuple(int(item) for item in match.group(1).split(", ") if item)
    return Outcome("covered", "complete", positions, authorized_count)


def _opened_cases(v3: dict[str, Outcome]) -> list[CaseRef]:
    result: list[CaseRef] = []
    for envelope, root in ENVELOPE_ROOTS.items():
        audit = json.loads((root / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
        for row in audit["cases"]:
            case_dir = root / "cases" / row["case_id"]
            key = f"{envelope}:{row['role']}:{row['case_id']}"
            if envelope == "E15":
                profile = json.loads((case_dir / "profile_1_2_0.json").read_text(encoding="utf-8"))
                count = len(
                    profile["semantic_role_authority"]["authorized_test_family"]["outcome_columns"]
                )
                baseline = _e15_outcome(row, count)
            else:
                baseline = v3[key]
            result.append(
                CaseRef(
                    key=key,
                    source_path=case_dir / "project/analysis.py",
                    case_dir=case_dir,
                    envelope=envelope,
                    role=row["role"],
                    designed_class=row["designed_class"],
                    labeled_correct=row["designed_class"] == "negative",
                    baseline=baseline,
                )
            )
    return result


def _corpus_cases(v3: dict[str, Outcome]) -> list[CaseRef]:
    labels = json.loads((CORPUS / "specs/labels.json").read_text(encoding="utf-8"))
    return [
        CaseRef(
            key=f"corpus:{spec}",
            source_path=CORPUS / f"cases/{spec}/analysis.py",
            case_dir=CORPUS / f"cases/{spec}",
            envelope=None,
            role=spec,
            designed_class=labels[spec]["label"],
            labeled_correct=labels[spec]["label"] == "correct",
            baseline=v3[f"corpus:{spec}"],
        )
        for spec in sorted(labels)
    ]


def all_cases() -> tuple[CaseRef, ...]:
    v3 = _v3_rows()
    cases = (*_opened_cases(v3), *_corpus_cases(v3))
    if len(cases) != 140 or len({case.key for case in cases}) != 140:
        raise ValueError("the evidence census is not exactly 140 unique cases")
    if sum(case.envelope is not None for case in cases) != 90:
        raise ValueError("the opened evidence census is not 90")
    if sum(case.envelope is None for case in cases) != 50:
        raise ValueError("the corpus evidence census is not 50")
    return cases


def question_keys() -> frozenset[str]:
    payload = json.loads(QUESTION_ORACLE.read_text(encoding="utf-8"))
    keys = frozenset(str(row["key"]) for row in payload["rows"])
    if len(keys) != 24:
        raise ValueError("the frozen 3.1 question census is not 24")
    return keys


def reference_case(key: str) -> CaseRef:
    matches = [case for case in all_cases() if case.key == key]
    if len(matches) != 1:
        raise ValueError(f"reference case {key} is not unique")
    return matches[0]
