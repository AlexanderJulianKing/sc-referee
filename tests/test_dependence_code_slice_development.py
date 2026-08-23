from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, cast

import pytest

import sc_referee.scientific_checks.code_csv_dependence_adapter_v3_0 as code_adapter_module
import sc_referee.scientific_checks.code_csv_dependence_dataflow_v3_0 as dataflow_module
from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json
from sc_referee.detectors.bounded_code_csv_dependence_conflict_v3_0 import (
    BoundedCodeCsvDependenceConflictV30Detector,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_0 import (
    CodeCsvDependenceAdapter,
)
from sc_referee.scientific_checks.core import InspectionDocument

CHECK_ID = "check:authorized-independent-unit-entry-into-row-independent-procedure"
LEDGER = Path("evaluation/development/pseudorep-code-slice-v3_0/DEVELOPMENT_LEDGER.json")
K_ROOT = Path("evaluation/development/dependence-growth-loop")
K_CONTRACT_ROOT = Path("evaluation/development/pseudorep-code-slice-v2_3/k-method-contracts")
OPENED_ROOTS = {
    envelope: Path(
        f"evaluation/development/blind-envelope-{envelope}-"
        f"{'2026-08-23' if envelope == 7 else '2026-08-22'}/cases"
    )
    for envelope in range(2, 8)
}


def _ledger() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(LEDGER.read_text(encoding="utf-8")))


def _opened_parameters() -> list[tuple[Path, str, int, str, str | None]]:
    return [
        (
            OPENED_ROOTS[int(item["envelope"])],
            str(item["case_id"]),
            int(item["expected_candidate_count"]),
            str(item["expected_state"]),
            cast(str | None, item.get("expected_reason")),
        )
        for item in _ledger()["opened_cases"]
    ]


def _material_path(lock_path: Path) -> str:
    frozen = json.loads(lock_path.read_text(encoding="utf-8"))
    return str(
        frozen["method_contract_profile"]["profile_manifest"]["authority_binding_snapshot"][
            "authorized_independent_unit_key"
        ]["material_input_path"]
    )


class _ProseDocumentTripwire:
    def __init__(self, path: str) -> None:
        self.path = path

    @property
    def content(self) -> bytes:
        raise AssertionError("3.0 code/CSV lane touched prose bytes")


class _TripwireContext:
    def __init__(self, context: Any, documents: tuple[Any, ...]) -> None:
        self._context = context
        self.documents = documents

    def __getattr__(self, name: str) -> Any:
        return getattr(self._context, name)


def test_v3_0_development_ledger_is_canonical_complete_and_evaluation_only() -> None:
    payload = LEDGER.read_bytes()
    ledger = json.loads(payload)
    assert canonical_json(ledger).encode() == payload.rstrip(b"\n")
    assert (ledger["check_version"], ledger["adapter_version"], ledger["detector_version"]) == (
        "3.0.0",
        "3.0.0",
        "3.0.0",
    )
    assert ledger["qualification_eligible"] is False
    assert ledger["project_authored_code_executed"] is False
    opened = ledger["opened_cases"]
    assert len(opened) == 68
    assert sum(item["blind_label"] == "POSITIVE" for item in opened) == 33
    assert sum(item["blind_label"] == "NEGATIVE" for item in opened) == 35
    assert sum(item["expected_candidate_count"] for item in opened) == 27
    assert not [
        item
        for item in opened
        if item["blind_label"] == "NEGATIVE" and item["expected_candidate_count"]
    ]
    assert len([item for item in opened if item["family"] == "C"]) == 10
    assert len(ledger["k_controls"]) == 6
    assert all(item["expected_candidate_count"] == 0 for item in ledger["k_controls"])


@pytest.mark.parametrize(
    ("opened_root", "case_id", "expected_candidates", "expected_state", "expected_reason"),
    _opened_parameters(),
)
def test_opened_cases_follow_v3_development_lane_and_replay(
    schema_root: Path,
    tmp_path: Path,
    opened_root: Path,
    case_id: str,
    expected_candidates: int,
    expected_state: str,
    expected_reason: str | None,
) -> None:
    source = opened_root / case_id
    project = tmp_path / f"project-{case_id}"
    shutil.copytree(source / "project", project)
    method_contract_lock = source / "method-contract/semantic.lock.json"
    audit = tmp_path / f"audit-{case_id}"
    bundle = run_audit(
        project,
        audit,
        schema_root,
        material_inputs=(_material_path(method_contract_lock),),
        method_contract_lock=method_contract_lock,
        scientific_check_lane="development",
    )
    lock = json.loads((audit / "semantic.lock.json").read_text(encoding="utf-8"))
    evaluation = lock["scientific_check_registry"]["evaluation"]
    dependence = next(item for item in evaluation["modules"] if item["check_id"] == CHECK_ID)
    assert dependence["check_version"] == "3.0.0"
    assert dependence["state"] == expected_state
    if expected_reason is not None:
        assert dependence["observations"][0]["abstention_reason"] == expected_reason
    results = [
        item
        for item in bundle["detector_results"]
        if item.get("detector_id") == BoundedCodeCsvDependenceConflictV30Detector.detector_id
        and item.get("detector_version") == "3.0.0"
    ]
    assert sum(item["state"] == "evaluation_finding_candidate" for item in results) == (
        expected_candidates
    )
    assert not [item for item in results if item["state"] == "accepted"]
    assert bundle["findings"] == []
    replayed = replay(
        audit / "semantic.lock.json",
        tmp_path / f"replay-{case_id}",
        schema_root,
    )
    assert replayed["detector_results"] == bundle["detector_results"]
    assert replayed["findings"] == bundle["findings"]
    assert replayed["coverage_records"] == bundle["coverage_records"]


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (
            "    data = load_data()",
            "    full = load_data()\n"
            "    data = full.iloc[[7, 15, 23, 31, 39, 47, 55, 63, 71, 79, 87, 95, "
            "103, 111, 119, 127, 135, 143]]",
        ),
        (
            "    data = load_data()",
            "    full = load_data()\n    data = full.dropna(subset=[OUTCOME])",
        ),
        (
            '    established = data.loc[data["binder_regimen"] == ESTABLISHED, OUTCOME]',
            '    established = data.loc[data["binder_regimen"] == ESTABLISHED, OUTCOME].dropna()',
        ),
    ],
)
def test_row_dropping_edges_cannot_be_erased_by_a_later_group_selection(
    schema_root: Path,
    tmp_path: Path,
    old: str,
    new: str,
) -> None:
    source = OPENED_ROOTS[7] / "6d9d7ed878cef263b664"
    project = tmp_path / "project-row-completeness"
    shutil.copytree(source / "project", project)
    analysis_path = project / "analysis.py"
    analysis = analysis_path.read_text(encoding="utf-8")
    assert analysis.count(old) == 1
    analysis_path.chmod(0o600)
    analysis_path.write_text(analysis.replace(old, new), encoding="utf-8")
    lock_path = source / "method-contract/semantic.lock.json"
    audit = tmp_path / "audit-row-completeness"
    bundle = run_audit(
        project,
        audit,
        schema_root,
        material_inputs=(_material_path(lock_path),),
        method_contract_lock=lock_path,
        scientific_check_lane="development",
    )
    semantic_lock = json.loads((audit / "semantic.lock.json").read_text(encoding="utf-8"))
    evaluation = semantic_lock["scientific_check_registry"]["evaluation"]
    dependence = next(item for item in evaluation["modules"] if item["check_id"] == CHECK_ID)
    assert dependence["observations"][0]["abstention_reason"] == (
        "selected-group-row-completeness-unproven"
    )
    assert not [
        item
        for item in bundle["detector_results"]
        if item.get("detector_id") == BoundedCodeCsvDependenceConflictV30Detector.detector_id
        and item.get("detector_version") == "3.0.0"
        and item.get("assessment_candidates")
    ]


def test_v3_prose_tripwire_covers_adapter_slice_and_all_five_guards(
    schema_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = OPENED_ROOTS[5] / "0b4876ceca6b0a9aede7"
    project = tmp_path / "project-tripwire"
    shutil.copytree(source / "project", project)
    lock_path = source / "method-contract/semantic.lock.json"
    calls = {
        name: 0
        for name in (
            "inspect",
            "analyze",
            "slice",
            "row_lineage",
            "sink_reachability",
            "sink_selection",
            "reducer",
            "s1",
            "s2",
            "s3",
            "s4",
            "s5",
            "detector_comparison",
        )
    }
    original_inspect = CodeCsvDependenceAdapter.inspect
    original_analyze = code_adapter_module.analyze_code_csv_dataflow

    def guarded_inspect(self: CodeCsvDependenceAdapter, context):  # type: ignore[no-untyped-def]
        calls["inspect"] += 1
        documents = tuple(
            cast(InspectionDocument, cast(Any, _ProseDocumentTripwire(document.path)))
            if document.media_type in {"text/markdown", "text/plain"}
            else document
            for document in context.documents
        )
        return original_inspect(self, cast(Any, _TripwireContext(context, documents)))

    def guarded_analyze(content: bytes, **kwargs):  # type: ignore[no-untyped-def]
        calls["analyze"] += 1
        assert isinstance(content, bytes)
        return original_analyze(content, **kwargs)

    monkeypatch.setattr(CodeCsvDependenceAdapter, "inspect", guarded_inspect)
    monkeypatch.setattr(code_adapter_module, "analyze_code_csv_dataflow", guarded_analyze)
    for key, target in (
        ("slice", (dataflow_module._Analyzer, "_backward_slice_names")),
        ("row_lineage", (dataflow_module._Analyzer, "_operand_rows_complete")),
        ("sink_reachability", (dataflow_module, "_v3_call_reachable")),
        ("sink_selection", (dataflow_module._Analyzer, "_result_sinks")),
        ("reducer", (dataflow_module, "_aggregation_call")),
        ("s1", (dataflow_module, "_v3_dependence_guard")),
        ("s2", (dataflow_module, "_v2_resampling_sibling")),
        ("s3", (dataflow_module, "_v3_statistics_guard")),
        ("s4", (dataflow_module, "_v3_syntactic_test_count")),
        ("s5", (dataflow_module, "_v3_unit_summary_guard")),
        (
            "detector_comparison",
            (BoundedCodeCsvDependenceConflictV30Detector, "evaluate"),
        ),
    ):
        owner, name = target
        original = getattr(owner, name)

        def wrapper(*args, __key=key, __original=original, **kwargs):  # type: ignore[no-untyped-def]
            calls[__key] += 1
            return __original(*args, **kwargs)

        monkeypatch.setattr(owner, name, wrapper)
    bundle = run_audit(
        project,
        tmp_path / "audit-tripwire",
        schema_root,
        material_inputs=(_material_path(lock_path),),
        method_contract_lock=lock_path,
        scientific_check_lane="development",
    )
    assert all(count >= 1 for count in calls.values())
    assert bundle["findings"] == []


@pytest.mark.parametrize(
    ("batch", "case_id", "expected_reason"),
    [
        ("batch-k1", "0de3a6061d3bb4056306", "analysis-source-envelope-unavailable"),
        ("batch-k1", "6b2da0c7167dbba3738f", "analysis-source-envelope-unavailable"),
        ("batch-k1", "e9e2718573bb47f7d17b", "analysis-source-envelope-unavailable"),
        ("batch-k2", "3ae92d0bb421d6eee99e", "analysis-source-envelope-unavailable"),
        ("batch-k2", "556f3545bebb45a3b005", "authorized-group-domain-not-exactly-two"),
        ("batch-k2", "2c458d2b523ea8c1bd90", "authorized-group-domain-not-exactly-two"),
    ],
)
def test_refrozen_k_contracts_remain_scored_development_abstentions(
    schema_root: Path,
    tmp_path: Path,
    batch: str,
    case_id: str,
    expected_reason: str,
) -> None:
    source = K_ROOT / batch / "authoring/cases" / case_id
    project = tmp_path / f"k-project-{case_id}"
    shutil.copytree(source, project)
    method_contract_lock = K_CONTRACT_ROOT / case_id / "semantic.lock.json"
    audit = tmp_path / f"k-audit-{case_id}"
    bundle = run_audit(
        project,
        audit,
        schema_root,
        report="results/report.md",
        material_inputs=("data/input.csv",),
        method_contract_lock=method_contract_lock,
        scientific_check_lane="development",
    )
    lock = json.loads((audit / "semantic.lock.json").read_text(encoding="utf-8"))
    dependence = next(
        item
        for item in lock["scientific_check_registry"]["evaluation"]["modules"]
        if item["check_id"] == CHECK_ID
    )
    assert dependence["check_version"] == "3.0.0"
    assert dependence["observations"][0]["abstention_reason"] == expected_reason
    assert not [
        item
        for item in bundle["detector_results"]
        if item.get("detector_id") == BoundedCodeCsvDependenceConflictV30Detector.detector_id
    ]
    assert bundle["findings"] == []
