from __future__ import annotations

import csv
import io
import json
from collections import Counter
from pathlib import Path

import pytest

from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_2 import (
    analyze_code_csv_multiple_testing_dataflow,
)

_RECON = Path("evaluation/development/multitest-recall-recon-corpus20")
_CORPUS = Path("evaluation/development/multitest-open-corpus-v1")
_ORACLE = Path("evaluation/development/multitest-code-slice-v2_1/LADDER_ORACLE.json")


def _finite(value: str) -> bool:
    try:
        number = float(value)
    except ValueError:
        return False
    return number == number and number not in {float("inf"), float("-inf")}


def _inputs(record: dict[str, str]) -> dict[str, object]:
    case = _CORPUS / "cases" / record["source_case"]
    csv_content = (case / "data.csv").read_bytes()
    rows = list(csv.reader(io.StringIO(csv_content.decode("utf-8"))))
    header = tuple(rows[0])
    group_index = 1
    counts = Counter(row[group_index] for row in rows[1:])
    return {
        "content": Path(record["path"]).read_bytes(),
        "authorized_path": "data.csv",
        "group_column": header[group_index],
        "outcome_columns": tuple(
            column
            for index, column in enumerate(header)
            if index not in {0, group_index} and all(_finite(row[index]) for row in rows[1:])
        ),
        "csv_header": header,
        "group_values": tuple(sorted(counts, key=lambda value: value.encode("utf-8"))),
        "csv_content": csv_content,
    }


_PAYLOAD = _ORACLE.read_bytes()
_MANIFEST = json.loads(_PAYLOAD)


def test_ladder_oracle_is_canonical_and_complete() -> None:
    assert canonical_json(_MANIFEST).encode() == _PAYLOAD.rstrip(b"\n")
    paths = sorted(str(path) for path in (_RECON / "lad").glob("spec-*/*.py"))
    assert _MANIFEST["profile"] == "multitest-corpus20-ladder-oracle-v2.1.0"
    assert _MANIFEST["fixture_count"] == len(paths) == 103
    assert [item["path"] for item in _MANIFEST["fixtures"]] == paths


@pytest.mark.parametrize(
    "record",
    _MANIFEST["fixtures"],
    ids=lambda item: f"{item['source_case']}-{item['construct']}",
)
def test_every_recon_ladder_rung_executes_with_its_exact_oracle(
    record: dict[str, str],
) -> None:
    path = Path(record["path"])
    assert sha256_digest(path.read_bytes()) == record["source_sha256"]
    if record["classification"] == "parser-error":
        with pytest.raises(SyntaxError):
            analyze_code_csv_multiple_testing_dataflow(**_inputs(record))
        assert record["value"] == "SyntaxError"
        return
    result = analyze_code_csv_multiple_testing_dataflow(**_inputs(record))
    if result.reason is not None:
        observed = ("abstain", result.reason)
    else:
        assert result.facts is not None
        classification = (
            "covered" if result.facts.correction_classification == "complete" else "candidate"
        )
        observed = (classification, result.facts.correction_classification)
    assert observed == (record["classification"], record["value"])
