"""Analyzer-level harness for the MT open corpus (read-only over the clone)."""
from __future__ import annotations

import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path("/Users/alexanderking/.cache/recon-scratch/vnext")
CORPUS = REPO / "evaluation/development/multitest-open-corpus-v1"
sys.path.insert(0, str(REPO / "src"))

from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2 import (  # noqa: E402
    analyze_code_csv_multiple_testing_dataflow as run,
)

LABELS = json.loads((CORPUS / "specs" / "labels.json").read_text())


def _finite(value: str) -> bool:
    try:
        number = float(value)
    except ValueError:
        return False
    return number == number and number not in {float("inf"), float("-inf")}


def inputs(spec: str, source: Path | str | None = None) -> dict:
    case = CORPUS / "cases" / spec
    csv_content = (case / "data.csv").read_bytes()
    rows = list(csv.reader(io.StringIO(csv_content.decode("utf-8"))))
    header = tuple(rows[0])
    gi = 1
    group_column = header[gi]
    counts = Counter(row[gi] for row in rows[1:])
    assert len(counts) == 2, (spec, counts)
    group_values = tuple(sorted(counts, key=lambda v: v.encode("utf-8")))
    outcomes = tuple(
        column
        for index, column in enumerate(header)
        if index not in {0, gi} and all(_finite(row[index]) for row in rows[1:])
    )
    if source is None:
        content = (case / "analysis.py").read_bytes()
    elif isinstance(source, Path):
        content = source.read_bytes()
    else:
        content = source.encode("utf-8")
    return {
        "content": content,
        "authorized_path": "data.csv",
        "group_column": group_column,
        "outcome_columns": outcomes,
        "csv_header": header,
        "group_values": group_values,
        "csv_content": csv_content,
    }


def analyze(spec: str, source: Path | str | None = None):
    return run(**inputs(spec, source))


def reason(spec: str, source: Path | str | None = None) -> str:
    result = analyze(spec, source)
    if result.reason is not None:
        return result.reason
    return "CANDIDATE:" + str(
        getattr(result.facts, "correction_classification", getattr(result.facts, "classification", "?"))
    )


if __name__ == "__main__":
    records = json.loads((CORPUS / "adapter_replay_records.json").read_text())["2.0.0"]["results"]
    mismatch = 0
    for spec in sorted(LABELS):
        observed = reason(spec)
        expected = records[spec][1] if records[spec][0] == "abstain" else "CANDIDATE"
        ok = observed == expected or (observed.startswith("CANDIDATE") and expected == "CANDIDATE")
        if not ok:
            mismatch += 1
        print(f"{spec} {LABELS[spec]['label']:8} {'OK ' if ok else 'DIFF'} observed={observed} adapter={expected}")
    print("mismatches:", mismatch)
