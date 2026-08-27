from __future__ import annotations

import hashlib
import json
import runpy
import sys
import types
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_3 as dataflow

_ROOT = Path("evaluation/development/blind-envelope-13-2026-08-26")
_RECON = Path("evaluation/development/multitest-recall-recon-e13")
sys.path.insert(0, str(_RECON.resolve()))
_HARNESS = runpy.run_path(str(_RECON / "h.py"))
_CACHED_H = sys.modules.pop("h", None)
_RECON_H = types.ModuleType("h")
_RECON_H.__dict__.update(_HARNESS)
sys.modules["h"] = _RECON_H
try:
    _LADDERS = runpy.run_path(str(_RECON / "ladders.py"))
finally:
    sys.modules.pop("h", None)
    if _CACHED_H is not None:
        sys.modules["h"] = _CACHED_H
_ADAPTER = cast(Callable[[Path, bytes], dict[str, Any]], _HARNESS["adapter_envelope"])
_INPUTS = cast(Callable[[Path], dict[str, Any]], _HARNESS["envelope_inputs"])

_EXPECTED = {
    "686d1432762cd49d9b54": ("candidate", "none"),
    "c336be2521785ab6a954": ("abstain", "extra-registered-test-outside-authorized-family"),
    "4f042d10b3f9a43d1099": ("candidate", "none"),
    "ffbe12246cf8a4227210": ("candidate", "none"),
    "80091f37c722eba28e18": ("candidate", "strict_subset"),
    "d0f9fcd52f47e4d64668": ("abstain", "unresolved-manual-correction-present"),
    "b7d38f6e9284abfd3ee6": ("abstain", "correction-family-lineage-unresolved"),
    "f65170c644b90c4a893c": ("abstain", "unresolved-decision-threshold"),
    "c15f507ad59999fd9371": ("abstain", "unresolved-manual-correction-present"),
    "cfbb5edfd1534e7419fd": ("abstain", "extra-registered-test-outside-authorized-family"),
    "8f37c5176ab3c0a61e4d": ("abstain", "test-battery-cardinality-unresolved"),
    "6a102a97a065f9c8879f": ("abstain", "authorized-reader-lineage-unavailable"),
    "aba768f8d0b3f3548683": ("abstain", "authorized-family-test-census-incomplete"),
    "325c686a92196956359a": ("abstain", "test-battery-cardinality-unresolved"),
    "ab70cdb37bb2977d725c": ("abstain", "unresolved-decision-threshold"),
}
_MOVEMENTS = {
    "80091f37c722eba28e18",
    "d0f9fcd52f47e4d64668",
    "b7d38f6e9284abfd3ee6",
    "ab70cdb37bb2977d725c",
}


def _active_row(case_id: str) -> dict[str, Any]:
    case = _ROOT / "cases" / case_id
    return _ADAPTER(case, (case / "project" / "analysis.py").read_bytes())


def test_e13_adapter_oracle() -> None:
    sealed = json.loads((_ROOT / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
    baseline = {
        item["case_id"]: (item["dev_outcome"], item["dev_reason_or_classification"])
        for item in sealed["cases"]
    }
    observed: dict[str, dict[str, Any]] = {}
    for case_id, expected in _EXPECTED.items():
        row = _active_row(case_id)
        assert tuple(row["outcome"]) == expected
        assert row["finding_count"] == 0
        observed[case_id] = row

    p5_inputs = _INPUTS(_ROOT / "cases" / "80091f37c722eba28e18")
    p5_source = cast(bytes, p5_inputs.pop("content"))
    p5 = dataflow.analyze_code_csv_multiple_testing_dataflow(p5_source, **p5_inputs)
    assert p5.facts is not None
    assert p5.facts.correction_methods == ("holm",)
    assert observed["80091f37c722eba28e18"]["corrected_positions"] == [0, 1]
    assert observed["80091f37c722eba28e18"]["authorized_count"] == 7
    assert observed["80091f37c722eba28e18"]["candidate_records"] == 1

    changed = {
        case_id for case_id, row in observed.items() if tuple(row["outcome"]) != baseline[case_id]
    }
    assert changed == _MOVEMENTS
    replay = json.loads((_ROOT / "adapter_replay_records_v2_3.json").read_text())
    assert replay == {"adapter_version": "2.3.0", "rows": observed}


def test_e13_replay_record_is_canonical_and_matches_adapter() -> None:
    path = _ROOT / "adapter_replay_records_v2_3.json"
    payload = path.read_bytes()
    record = json.loads(payload)
    assert json.dumps(record, sort_keys=True, separators=(",", ":")).encode() == payload.rstrip(
        b"\n"
    )
    for case_id, expected in _EXPECTED.items():
        assert tuple(record["rows"][case_id]["outcome"]) == expected


def test_eligible_local_reader_site_census_is_exact() -> None:
    expected = {
        "c336be2521785ab6a954",
        "80091f37c722eba28e18",
        "d0f9fcd52f47e4d64668",
        "b7d38f6e9284abfd3ee6",
        "ab70cdb37bb2977d725c",
    }
    found: set[str] = set()
    roots = [
        Path("evaluation/development/blind-envelope-10-2026-08-24"),
        Path("evaluation/development/blind-envelope-11-2026-08-25"),
        Path("evaluation/development/blind-envelope-12-2026-08-26"),
        _ROOT,
    ]
    for root in roots:
        for case in sorted((root / "cases").iterdir()):
            inputs = _INPUTS(case)
            source = cast(bytes, inputs["content"])
            tree = dataflow._bounded_parse(source)
            scope = tuple(item for item in tree.body if not dataflow._is_docstring(item))
            resolver, reason = dataflow._resolver(scope)
            assert reason is None and resolver is not None
            paths = dataflow._mt23_local_reader_paths(
                tree,
                resolver=resolver,
                authorized_path=cast(str, inputs["authorized_path"]),
                csv_header=cast(tuple[str, ...], inputs["csv_header"]),
                unit_column=cast(tuple[str, ...], inputs["outcome_columns"])[0],
                group_column=cast(str, inputs["group_column"]),
            )
            if paths:
                found.add(case.name)
    assert found == expected

    p2_inputs = _INPUTS(_ROOT / "cases" / "c336be2521785ab6a954")
    p2_source = cast(bytes, p2_inputs.pop("content"))
    p2 = dataflow.analyze_code_csv_multiple_testing_dataflow(p2_source, **p2_inputs)
    assert p2.reason == "extra-registered-test-outside-authorized-family"


@pytest.mark.parametrize(
    ("factory", "case_id", "expected"),
    [
        (
            "p2_rungs",
            "c336be2521785ab6a954",
            [
                ("abstain", "extra-registered-test-outside-authorized-family"),
                ("candidate", "none"),
                ("candidate", "none"),
            ],
        ),
        (
            "p5_rungs",
            "80091f37c722eba28e18",
            [
                ("candidate", "strict_subset"),
                ("candidate", "strict_subset"),
                ("candidate", "strict_subset"),
            ],
        ),
        (
            "p6_rungs",
            "d0f9fcd52f47e4d64668",
            [
                ("abstain", "unresolved-manual-correction-present"),
                ("abstain", "unresolved-manual-correction-present"),
                ("abstain", "analysis-scope-structure-unsupported"),
                ("abstain", "analysis-scope-structure-unsupported"),
                ("abstain", "unresolved-manual-correction-present"),
                ("candidate", "strict_subset"),
            ],
        ),
    ],
)
def test_e13_ladders_execute(factory: str, case_id: str, expected: list[tuple[str, str]]) -> None:
    rows = cast(Callable[[], list[tuple[str, str, str]]], _LADDERS[factory])()
    actual = [
        tuple(_ADAPTER(_ROOT / "cases" / case_id, source.encode())["outcome"])
        for _name, _mutation, source in rows
    ]
    assert actual == expected


def test_e13_custody_digests_are_frozen() -> None:
    assert hashlib.sha256((_ROOT / "AUDIT_RESULTS.json").read_bytes()).hexdigest() == (
        "dce37ab885bf077ee29692bfe00680ae6d21c1d7ead8559539d62061c200ec76"
    )
    assert hashlib.sha256((_ROOT / "ROLE_MAP.json").read_bytes()).hexdigest() == (
        "456780e6ab2a5decb7c99d31de9a6e898b7f3936e40bf378932aa51e3cda74cb"
    )


def test_six_false_accusation_fixtures_have_zero_adapter_candidates() -> None:
    fixture_root = Path("evaluation/development/multitest-code-slice-v2_2/e12-ladders")
    saved_h = sys.modules.pop("h", None)
    saved_path = list(sys.path)
    try:
        sys.path.insert(0, str(fixture_root.resolve()))
        fixtures = runpy.run_path(str(fixture_root / "fa.py"))["FIXTURES"]
    finally:
        sys.path[:] = saved_path
        sys.modules.pop("h", None)
        if saved_h is not None:
            sys.modules["h"] = saved_h
    expected = [
        ("abstain", "unresolved-manual-correction-present"),
        ("covered", "complete"),
        ("abstain", "unresolved-manual-correction-present"),
        ("abstain", "analysis-scope-structure-unsupported"),
        ("covered", "complete"),
        ("abstain", "unresolved-pvalue-consumer"),
    ]
    observed = [
        tuple(_ADAPTER(case, source.encode())["outcome"]) for _label, case, source in fixtures
    ]
    assert observed == expected
    assert sum(item[0] == "candidate" for item in observed) == 0
