"""Read-only MT 2.3 inputs and adapter-level baseline for the 3.0 prototype sweep."""

from __future__ import annotations

import ast
import csv
import io
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_3 import (
    MultipleTestingDataflowResult,
    analyze_code_csv_multiple_testing_dataflow,
)

REPO = Path(__file__).resolve().parents[4]
CORPUS = REPO / "evaluation/development/multitest-open-corpus-v1"
ENVELOPE_ROOTS = {
    "E10": REPO / "evaluation/development/blind-envelope-10-2026-08-24/cases",
    "E11": REPO / "evaluation/development/blind-envelope-11-2026-08-25/cases",
    "E12": REPO / "evaluation/development/blind-envelope-12-2026-08-26/cases",
    "E13": REPO / "evaluation/development/blind-envelope-13-2026-08-26/cases",
    "E14": REPO / "evaluation/development/blind-envelope-14-2026-08-27/cases",
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
    role: str | None
    designed_class: str
    labeled_correct: bool


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


def _opened_cases() -> list[CaseRef]:
    result: list[CaseRef] = []
    for envelope, cases_root in ENVELOPE_ROOTS.items():
        audit = json.loads((cases_root.parent / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
        for row in audit["cases"]:
            case_dir = cases_root / row["case_id"]
            result.append(
                CaseRef(
                    key=f"{envelope}:{row['role']}:{row['case_id']}",
                    source_path=case_dir / "project/analysis.py",
                    case_dir=case_dir,
                    envelope=envelope,
                    role=row["role"],
                    designed_class=row["designed_class"],
                    labeled_correct=row["designed_class"] == "negative",
                )
            )
    return result


def _corpus_cases() -> list[CaseRef]:
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
        )
        for spec in sorted(labels)
    ]


def all_cases() -> tuple[CaseRef, ...]:
    cases = (*_opened_cases(), *_corpus_cases())
    if len(cases) != 125 or len({case.key for case in cases}) != 125:
        raise ValueError("the pinned case census is not exactly 125 unique cases")
    return cases


def _statistics_api_outside_analysis(case: CaseRef) -> bool:
    if case.envelope is None:
        return False
    project = case.case_dir / "project"
    prefixes = (
        "scipy.stats",
        "statsmodels",
        "pingouin",
        "pymer4",
        "bambi",
        "gpboost",
        "merf",
        "linearmodels",
        "sklearn",
        "pymc",
        "numpyro",
        "stan",
        "cmdstanpy",
        "rpy2",
        "lifelines",
    )
    for path in project.glob("*.py"):
        if path.name == "analysis.py":
            continue
        tree = ast.parse(path.read_bytes())
        for node in ast.walk(tree):
            modules: tuple[str, ...] = ()
            if isinstance(node, ast.Import):
                modules = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                modules = (
                    node.module,
                    *(f"{node.module}.{alias.name}" for alias in node.names),
                )
            if any(
                module == prefix or module.startswith(prefix + ".")
                for module in modules
                for prefix in prefixes
            ):
                return True
    return False


def adapter_baseline(case: CaseRef, analyzer_outcome: Outcome) -> Outcome:
    """Apply the two adapter-only pins without pretending the prototype is installed."""

    if _statistics_api_outside_analysis(case):
        return Outcome("abstain", "statistics-api-imported-outside-analysis-py")
    if case.envelope is None:
        record = json.loads(
            (CORPUS / "adapter_replay_records_v2_1.json").read_text(encoding="utf-8")
        )["2.1.0"]["results"][case.role]
        state, reason = record[:2]
        positions: tuple[int, ...] = ()
        count: int | None = None
        if len(record) == 3:
            positions = tuple(record[2]["corrected_positions"])
            count = int(record[2]["authorized_count"])
        return Outcome(state, reason, positions, count)
    return analyzer_outcome


def reference_case(envelope: str, role: str) -> CaseRef:
    matches = [case for case in all_cases() if case.envelope == envelope and case.role == role]
    if len(matches) != 1:
        raise ValueError(f"reference case {envelope}:{role} is not unique")
    return matches[0]
