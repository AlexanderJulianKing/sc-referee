"""E12 MT 2.1 recall recon harness (read-only against the repo)."""
from __future__ import annotations

import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path("/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext")
sys.path.insert(0, str(REPO / "src"))

E12 = REPO / "evaluation/development/blind-envelope-12-2026-08-26/cases"
E11 = REPO / "evaluation/development/blind-envelope-11-2026-08-25/cases"
E10 = REPO / "evaluation/development/blind-envelope-10-2026-08-24/cases"
CORPUS = REPO / "evaluation/development/multitest-open-corpus-v1"

from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_1 import (  # noqa: E402
    analyze_code_csv_multiple_testing_dataflow as run,
)


def _parse_csv(content: bytes, group_column: str):
    text = content.decode("utf-8")
    rows = list(csv.reader(io.StringIO(text, newline=""), dialect="excel", strict=True))
    header = tuple(rows[0])
    gi = header.index(group_column)
    counts = Counter(r[gi] for r in rows[1:])
    gv = tuple(sorted(counts, key=lambda v: v.encode("utf-8")))
    assert len(gv) == 2, (counts, group_column)
    return header, (gv[0], gv[1])


def envelope_inputs(case_dir: Path, source: bytes | None = None):
    prof = json.loads((case_dir / "profile_1_2_0.json").read_text())
    auth = prof["semantic_role_authority"]["authorized_test_family"]
    path = auth["material_input_path"]
    gcol = auth["group_contrast_column"]
    outs = tuple(auth["outcome_columns"])
    csv_content = (case_dir / "project" / path).read_bytes()
    header, gvals = _parse_csv(csv_content, gcol)
    content = source if source is not None else (case_dir / "project" / "analysis.py").read_bytes()
    return dict(
        content=content,
        authorized_path=path,
        group_column=gcol,
        outcome_columns=outs,
        csv_header=header,
        group_values=gvals,
        csv_content=csv_content,
    )


def analyze_envelope(case_dir: Path, source: bytes | None = None, fn=run):
    kw = envelope_inputs(case_dir, source)
    content = kw.pop("content")
    return fn(content, **kw)


# ---- open corpus: authority derived exactly as adapter_replay._authority does ----
def _finite_decimal(value: str) -> bool:
    try:
        number = float(value)
    except ValueError:
        return False
    return number == number and number not in {float("inf"), float("-inf")}


def corpus_authority(case: Path):
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


def analyze_corpus(spec: str, source: bytes | None = None, fn=run):
    case = CORPUS / "cases" / spec
    gcol, outs = corpus_authority(case)
    csv_content = (case / "data.csv").read_bytes()
    header, gvals = _parse_csv(csv_content, gcol)
    content = source if source is not None else (case / "analysis.py").read_bytes()
    return fn(
        content,
        authorized_path="data.csv",
        group_column=gcol,
        outcome_columns=outs,
        csv_header=header,
        group_values=gvals,
        csv_content=csv_content,
    )


def classify(result):
    """Match adapter_replay._classification: complete -> covered, else candidate."""
    if result.reason is not None:
        return ("abstain", result.reason)
    facts = result.facts
    classification = getattr(facts, "correction_classification", "?")
    return ("covered" if classification == "complete" else "candidate", classification)


def roles(envelope_dir: Path):
    return json.loads((envelope_dir.parent / "ROLE_MAP.json").read_text())[
        "case_roles_in_fixed_order"
    ]


if __name__ == "__main__":
    for item in roles(E12):
        r = analyze_envelope(E12 / item["case_id"])
        print(f"{item['role']:3} {item['case_id']} -> {classify(r)}")
