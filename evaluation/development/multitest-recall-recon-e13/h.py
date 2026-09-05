"""Read-only MT 2.2 analyzer and real-adapter harness for the E13 recon."""

from __future__ import annotations

import csv
import io
import json
import shutil
import tempfile
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from sc_referee.controller import run_audit
from sc_referee.method_contract_run import run_method_contract
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_2 import (
    MultipleTestingDataflowResult,
    analyze_code_csv_multiple_testing_dataflow,
)

REPO = Path(__file__).resolve().parents[3]
E10 = REPO / "evaluation/development/blind-envelope-10-2026-08-24/cases"
E11 = REPO / "evaluation/development/blind-envelope-11-2026-08-25/cases"
E12 = REPO / "evaluation/development/blind-envelope-12-2026-08-26/cases"
E13 = REPO / "evaluation/development/blind-envelope-13-2026-08-26/cases"
CORPUS = REPO / "evaluation/development/multitest-open-corpus-v1"
SCHEMAS = REPO / "reference/schemas-v0.21.0"
CHECK_ID = "check:authorized-complete-family-correction-over-code-test-battery"


def _parse_csv(content: bytes, group_column: str) -> tuple[tuple[str, ...], tuple[str, str]]:
    rows = list(
        csv.reader(io.StringIO(content.decode("utf-8"), newline=""), dialect="excel", strict=True)
    )
    header = tuple(rows[0])
    group_index = header.index(group_column)
    counts = Counter(row[group_index] for row in rows[1:])
    values = tuple(sorted(counts, key=lambda value: value.encode("utf-8")))
    if len(values) != 2:
        raise ValueError("recon input group domain is not exactly binary")
    return header, (values[0], values[1])


def envelope_inputs(case_dir: Path, source: bytes | None = None) -> dict[str, Any]:
    profile = json.loads((case_dir / "profile_1_2_0.json").read_text(encoding="utf-8"))
    authority = profile["semantic_role_authority"]["authorized_test_family"]
    material_path = authority["material_input_path"]
    group_column = authority["group_contrast_column"]
    csv_content = (case_dir / "project" / material_path).read_bytes()
    header, group_values = _parse_csv(csv_content, group_column)
    return {
        "content": source
        if source is not None
        else (case_dir / "project" / "analysis.py").read_bytes(),
        "authorized_path": material_path,
        "group_column": group_column,
        "outcome_columns": tuple(authority["outcome_columns"]),
        "csv_header": header,
        "group_values": group_values,
        "csv_content": csv_content,
    }


def analyze_envelope(
    case_dir: Path,
    source: bytes | None = None,
    *,
    fn: Callable[..., MultipleTestingDataflowResult] = analyze_code_csv_multiple_testing_dataflow,
) -> MultipleTestingDataflowResult:
    inputs = envelope_inputs(case_dir, source)
    content = inputs.pop("content")
    return fn(content, **inputs)


def _finite_decimal(value: str) -> bool:
    try:
        number = float(value)
    except ValueError:
        return False
    return number == number and number not in {float("inf"), float("-inf")}


def corpus_authority(case: Path) -> tuple[str, tuple[str, ...]]:
    with (case / "data.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    header = tuple(rows[0])
    group_index = 1
    outcomes = tuple(
        column
        for index, column in enumerate(header)
        if index not in {0, group_index} and all(_finite_decimal(row[index]) for row in rows[1:])
    )
    return header[group_index], outcomes


def analyze_corpus(
    spec: str,
    source: bytes | None = None,
    *,
    fn: Callable[..., MultipleTestingDataflowResult] = analyze_code_csv_multiple_testing_dataflow,
) -> MultipleTestingDataflowResult:
    case = CORPUS / "cases" / spec
    group_column, outcomes = corpus_authority(case)
    csv_content = (case / "data.csv").read_bytes()
    header, group_values = _parse_csv(csv_content, group_column)
    return fn(
        source if source is not None else (case / "analysis.py").read_bytes(),
        authorized_path="data.csv",
        group_column=group_column,
        outcome_columns=outcomes,
        csv_header=header,
        group_values=group_values,
        csv_content=csv_content,
    )


def classify(result: MultipleTestingDataflowResult) -> tuple[str, str]:
    if result.reason is not None:
        return "abstain", result.reason
    if result.facts is None:
        raise ValueError("result has neither facts nor a reason")
    classification = result.facts.correction_classification
    return ("covered" if classification == "complete" else "candidate", classification)


def adapter_envelope(case_dir: Path, source: bytes) -> dict[str, Any]:
    """Execute the real development-lane 2.2 adapter via contract + audit."""

    with tempfile.TemporaryDirectory(prefix="sc-referee-e13-adapter-", dir="/tmp") as raw:
        root = Path(raw)
        project = root / "project"
        shutil.copytree(case_dir / "project", project)
        (project / "analysis.py").write_bytes(source)
        (project / "recon-task.txt").write_bytes((case_dir / "PROMPT.txt").read_bytes())
        profile = json.loads((case_dir / "profile_1_2_0.json").read_text(encoding="utf-8"))
        material_path = profile["semantic_role_authority"]["authorized_test_family"][
            "material_input_path"
        ]
        contract = root / "contract"
        run_method_contract(
            project,
            "recon-task.txt",
            contract,
            SCHEMAS,
            profile=profile,
            actor_id="human:multitest-e13-recon",
            created_at="2026-08-26T00:00:00Z",
        )
        audit = root / "audit"
        bundle = run_audit(
            project,
            audit,
            SCHEMAS,
            material_inputs=(material_path,),
            method_contract_lock=contract / "semantic.lock.json",
            scientific_check_lane="development",
        )
        lock = json.loads((audit / "semantic.lock.json").read_text(encoding="utf-8"))
        module = next(
            item
            for item in lock["scientific_check_registry"]["evaluation"]["modules"]
            if item["check_id"] == CHECK_ID
        )
        observation = module["observations"][0]
        evidence = observation.get("multiple_testing_evidence")
        if observation["abstention_reason"] is not None:
            outcome = ["abstain", observation["abstention_reason"]]
        else:
            classification = evidence["correction_classification"]
            outcome = ["covered" if classification == "complete" else "candidate", classification]
        return {
            "outcome": outcome,
            "corrected_positions": None if evidence is None else evidence["corrected_positions"],
            "authorized_count": None if evidence is None else evidence["authorized_count"],
            "candidate_records": sum(
                item["state"] == "evaluation_finding_candidate"
                for item in bundle["detector_results"]
                if item["detector_id"] == "detector:bounded-code-csv-multiple-testing-conflict"
            ),
            "finding_count": len(bundle["findings"]),
        }
