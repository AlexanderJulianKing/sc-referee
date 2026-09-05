"""Input-bound harness for the MT 3.5 recall-delta prototype sweep.

The 3.5 baseline is the shipped 3.4 analyzer.  Every prior evidence row is additionally
anchored against the frozen 3.4 prototype result bytes, so a baseline drift is a hard
failure rather than a silent rebaseline.  E18 adds fifteen opened rows that carry no frozen
anchor; they are baselined on the shipped 3.4 analyzer and pinned in the sweep instead.
"""

from __future__ import annotations

import csv
import io
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 import (
    MultipleTestingDataflowResult,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
    analyze_code_csv_multiple_testing_dataflow,
)

REPO = Path(__file__).resolve().parents[4]
CORPUS = REPO / "evaluation/development/multitest-open-corpus-v1"
V34_RESULTS = REPO / "evaluation/development/multitest-code-slice-v3_4/prototype-sweep/results.json"
QUESTION_ORACLE = REPO / "evaluation/development/multitest-code-slice-v3_1/QUESTION_ORACLE.json"
ENVELOPE_ROOTS = {
    "E10": REPO / "evaluation/development/blind-envelope-10-2026-08-24",
    "E11": REPO / "evaluation/development/blind-envelope-11-2026-08-25",
    "E12": REPO / "evaluation/development/blind-envelope-12-2026-08-26",
    "E13": REPO / "evaluation/development/blind-envelope-13-2026-08-26",
    "E14": REPO / "evaluation/development/blind-envelope-14-2026-08-27",
    "E15": REPO / "evaluation/development/blind-envelope-15-2026-08-29",
    "E16": REPO / "evaluation/development/blind-envelope-16-2026-08-30",
    "E17": REPO / "evaluation/development/blind-envelope-17-2026-08-30",
    "E18": REPO / "evaluation/development/blind-envelope-18-2026-09-01",
}
# The two frozen rows whose adapter-level reason precedes the source analyzer.  Their frozen
# adapter row stays the effective baseline and no 3.4 admission may cross them.
ADAPTER_SHORT_CIRCUIT = frozenset({"E10:N7:6d2fdc67ab98bc0e0e6e", "corpus:spec-30"})


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


def outcome_from_json(value: list[object]) -> Outcome:
    state = str(value[0])
    reason = str(value[1])
    if len(value) == 2:
        return Outcome(state, reason)
    detail = value[2]
    if not isinstance(detail, dict):
        raise ValueError("coverage row is not an object")
    authorized_count = detail.get("authorized_count")
    positions = detail.get("corrected_positions")
    if not isinstance(positions, list):
        raise ValueError("coverage row has no corrected-position list")
    return Outcome(
        state,
        reason,
        tuple(int(item) for item in positions),
        None if authorized_count is None else int(authorized_count),
    )


def anchor_equal(frozen: Outcome, measured: Outcome) -> bool:
    """Compare exactly what the frozen row recorded.

    The frozen corpus rows are detail-free adapter rows carried from the 3.2 sweep: they
    record state and classification only.  Opened rows record the full detail.  Nothing is
    relaxed beyond what the frozen bytes actually contain.
    """

    if (frozen.state, frozen.reason_or_classification) != (
        measured.state,
        measured.reason_or_classification,
    ):
        return False
    if frozen.state in {"candidate", "covered"} and frozen.authorized_count is None:
        return True
    return (
        frozen.corrected_positions == measured.corrected_positions
        and frozen.authorized_count == measured.authorized_count
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


def v34_rows() -> dict[str, Outcome]:
    """The 170 frozen 3.4 prototype outcomes, used only as a drift anchor."""

    payload = json.loads(V34_RESULTS.read_text(encoding="utf-8"))
    rows = {row["key"]: outcome_from_json(row["outcome"]) for row in payload["cases"]}
    if len(rows) != 170:
        raise ValueError("the frozen 3.4 result census is not 170")
    return rows


def _opened_case_rows(root: Path) -> tuple[dict[str, str], ...]:
    role_map = root / "ROLE_MAP.json"
    if role_map.exists():
        payload = json.loads(role_map.read_text(encoding="utf-8"))
        return tuple(
            {"role": str(row["role"]), "case_id": str(row["case_id"])}
            for row in payload["case_roles_in_fixed_order"]
        )
    audit = json.loads((root / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
    return tuple(
        {"role": str(row["role"]), "case_id": str(row["case_id"])} for row in audit["cases"]
    )


def _placeholder_case(
    *, envelope: str | None, role: str, case_id: str, root: Path, baseline: Outcome
) -> CaseRef:
    case_dir = root / "cases" / case_id
    return CaseRef(
        key=f"{envelope}:{role}:{case_id}",
        source_path=case_dir / "project/analysis.py",
        case_dir=case_dir,
        envelope=envelope,
        role=role,
        designed_class="positive" if role.startswith("P") else "negative",
        labeled_correct=role.startswith("N"),
        baseline=baseline,
    )


def _opened_cases() -> list[CaseRef]:
    """Baseline every opened case on the shipped 3.4 analyzer, then anchor the frozen 170."""

    frozen = v34_rows()
    result: list[CaseRef] = []
    for envelope, root in ENVELOPE_ROOTS.items():
        for row in _opened_case_rows(root):
            key = f"{envelope}:{row['role']}:{row['case_id']}"
            provisional = _placeholder_case(
                envelope=envelope,
                role=row["role"],
                case_id=row["case_id"],
                root=root,
                baseline=Outcome("abstain", "multiple-testing-code-inspection-exception"),
            )
            measured = classify(analyze(provisional))
            if key in ADAPTER_SHORT_CIRCUIT:
                measured = frozen[key]
            elif key in frozen and not anchor_equal(frozen[key], measured):
                raise ValueError(
                    f"shipped 3.4 disagrees with the frozen 3.4 prototype row for {key}: "
                    f"{measured.as_json()} != {frozen[key].as_json()}"
                )
            result.append(
                _placeholder_case(
                    envelope=envelope,
                    role=row["role"],
                    case_id=row["case_id"],
                    root=root,
                    baseline=measured,
                )
            )
    return result


def _corpus_cases() -> list[CaseRef]:
    frozen = v34_rows()
    labels = json.loads((CORPUS / "specs/labels.json").read_text(encoding="utf-8"))
    result: list[CaseRef] = []
    for spec in sorted(labels):
        case = CaseRef(
            key=f"corpus:{spec}",
            source_path=CORPUS / f"cases/{spec}/analysis.py",
            case_dir=CORPUS / f"cases/{spec}",
            envelope=None,
            role=spec,
            designed_class=labels[spec]["label"],
            labeled_correct=labels[spec]["label"] == "correct",
            baseline=Outcome("abstain", "multiple-testing-code-inspection-exception"),
        )
        measured = classify(analyze(case))
        if case.key in ADAPTER_SHORT_CIRCUIT:
            measured = frozen[case.key]
        elif not anchor_equal(frozen[case.key], measured):
            raise ValueError(
                f"shipped 3.4 disagrees with the frozen 3.4 prototype row for {case.key}: "
                f"{measured.as_json()} != {frozen[case.key].as_json()}"
            )
        result.append(
            CaseRef(
                key=case.key,
                source_path=case.source_path,
                case_dir=case.case_dir,
                envelope=None,
                role=case.role,
                designed_class=case.designed_class,
                labeled_correct=case.labeled_correct,
                baseline=measured,
            )
        )
    return result


_CASE_CACHE: tuple[CaseRef, ...] | None = None


def all_cases() -> tuple[CaseRef, ...]:
    global _CASE_CACHE
    if _CASE_CACHE is not None:
        return _CASE_CACHE
    cases = (*_opened_cases(), *_corpus_cases())
    if len(cases) != 185 or len({case.key for case in cases}) != 185:
        raise ValueError("the evidence census is not exactly 185 unique cases")
    if sum(case.envelope is not None for case in cases) != 135:
        raise ValueError("the opened evidence census is not 135")
    if sum(case.envelope is None for case in cases) != 50:
        raise ValueError("the corpus evidence census is not 50")
    _CASE_CACHE = cases
    return cases


def reference_case(key: str) -> CaseRef:
    matches = [case for case in all_cases() if case.key == key]
    if len(matches) != 1:
        raise ValueError(f"reference case {key} is not unique")
    return matches[0]


def frozen_question_keys() -> frozenset[str]:
    """The 3.1 oracle minus the two 3.2-resolved rows: the frozen through-E15 census of 22."""

    payload = json.loads(QUESTION_ORACLE.read_text(encoding="utf-8"))
    keys = frozenset(str(row["key"]) for row in payload["rows"])
    removed = {"E15:P6:81980e878c1bc8cc216b", "corpus:spec-28"}
    result = keys - removed
    if len(result) != 22:
        raise ValueError("the frozen post-3.2 correction-scope question census is not 22")
    return result


def current_question_keys() -> frozenset[str]:
    """Extend the frozen through-E15 census with witnessed E16, E17 and E18 questions."""

    from sc_referee.scientific_checks.multiple_testing_scope_questions_v1 import (
        QUALIFYING_REASON_NAMES,
        locate_correction_scope_witness,
    )

    result = set(frozen_question_keys())
    for case in all_cases():
        if (
            case.envelope not in {"E16", "E17", "E18"}
            or case.baseline.reason_or_classification not in QUALIFYING_REASON_NAMES
        ):
            continue
        values = inputs(case)
        witness = locate_correction_scope_witness(
            values["content"],
            qualifying_reason=case.baseline.reason_or_classification,
            authorized_count=len(values["outcome_columns"]),
            outcome_columns=values["outcome_columns"],
        )
        if witness is not None:
            result.add(case.key)
    return frozenset(result)
