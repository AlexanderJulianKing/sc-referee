from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, cast

import pytest

import sc_referee.scientific_checks.code_csv_dependence_adapter as code_adapter_module
import sc_referee.scientific_checks.code_csv_dependence_dataflow as dataflow_module
from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json
from sc_referee.detectors.bounded_code_csv_dependence_conflict_v2_2 import (
    BoundedCodeCsvDependenceConflictV22Detector,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter import CodeCsvDependenceAdapter
from sc_referee.scientific_checks.core import InspectionDocument

CHECK_ID = "check:authorized-independent-unit-entry-into-row-independent-procedure"
OPENED_ROOT = Path("evaluation/development/blind-envelope-2026-08-21/cases")
OPENED_2_ROOT = Path("evaluation/development/blind-envelope-2-2026-08-22/cases")
OPENED_3_ROOT = Path("evaluation/development/blind-envelope-3-2026-08-22/cases")
OPENED_4_ROOT = Path("evaluation/development/blind-envelope-4-2026-08-22/cases")
OPENED_5_ROOT = Path("evaluation/development/blind-envelope-5-2026-08-22/cases")
LEDGER = Path("evaluation/development/pseudorep-code-slice-v2_2/DEVELOPMENT_LEDGER.json")
K_ROOT = Path("evaluation/development/dependence-growth-loop")
K_CONTRACT_ROOT = Path("evaluation/development/pseudorep-code-slice-v2_2/k-method-contracts")


class _ProseDocumentTripwire:
    def __init__(self, path: str) -> None:
        self.path = path

    @property
    def content(self) -> bytes:
        raise AssertionError("CodeCsvDependenceAdapter.inspect touched prose bytes")


class _TripwireContext:
    def __init__(self, context: Any, documents: tuple[Any, ...]) -> None:
        self._context = context
        self.documents = documents

    def __getattr__(self, name: str) -> Any:
        return getattr(self._context, name)


def test_v2_2_development_ledger_is_canonical_and_evaluation_only() -> None:
    payload = LEDGER.read_bytes()
    ledger = json.loads(payload)
    assert canonical_json(ledger).encode() == payload.rstrip(b"\n")
    assert ledger["check_version"] == "2.2.0"
    assert ledger["adapter_version"] == "2.2.0"
    assert ledger["detector_version"] == "2.2.0"
    assert ledger["qualification_eligible"] is False
    assert len(ledger["opened_cases"]) == 44
    assert sum(item["expected_candidate_count"] for item in ledger["opened_cases"]) == 21
    assert all(item["expected_finding_count"] == 0 for item in ledger["opened_cases"])
    assert len(ledger["k_controls"]) == 6
    assert all(item["expected_candidate_count"] == 0 for item in ledger["k_controls"])


@pytest.mark.parametrize(
    ("opened_root", "case_id", "expected_candidate", "expected_state", "expected_reason"),
    [
        (OPENED_ROOT, "45dcad2f6496a0fd5778", True, "applicable", None),
        (OPENED_ROOT, "88e59abe85a8eea2b8cd", True, "applicable", None),
        (OPENED_ROOT, "0f721a41bac71a461dd2", True, "applicable", None),
        (
            OPENED_ROOT,
            "5994e65153b07855b07c",
            False,
            "unsupported",
            "aggregation-on-test-operand-path",
        ),
        (
            OPENED_ROOT,
            "e804a86a1e05b781f292",
            False,
            "not_applicable",
            "no-repeated-authorized-unit",
        ),
        (
            OPENED_ROOT,
            "11af5bb3f9b7e8e0b293",
            False,
            "unsupported",
            "tracked-value-mutation",
        ),
        (
            OPENED_2_ROOT,
            "e8f97fe750189052f726",
            True,
            "applicable",
            None,
        ),
        (
            OPENED_2_ROOT,
            "2df3396d80adbb63dffb",
            True,
            "applicable",
            None,
        ),
        (
            OPENED_2_ROOT,
            "ca18f96d45dff1b921ad",
            True,
            "applicable",
            None,
        ),
        (
            OPENED_2_ROOT,
            "15b07ef7670800ba88e0",
            False,
            "unsupported",
            "two-group-row-selection-unavailable",
        ),
        (
            OPENED_2_ROOT,
            "5ef43dbf631adcf3daec",
            False,
            "not_applicable",
            "no-repeated-authorized-unit",
        ),
        (
            OPENED_2_ROOT,
            "e60c84d0cda3cc465df7",
            False,
            "unsupported",
            "tracked-value-mutation",
        ),
        (
            OPENED_2_ROOT,
            "6090fc1b1b6dbfcd6eee",
            False,
            "unsupported",
            "additional-accepted-reader-present",
        ),
        (
            OPENED_2_ROOT,
            "d4d95cdd4f4e698d675c",
            False,
            "unsupported",
            "unregistered-component-consumer",
        ),
        (OPENED_3_ROOT, "a28f42e4bd1fe1c5e048", True, "applicable", None),
        (OPENED_3_ROOT, "29893ac47ebe4ca60cce", True, "applicable", None),
        (OPENED_3_ROOT, "df67e751158d62c4cbf4", True, "applicable", None),
        (OPENED_3_ROOT, "045708a55a9f3e2ec449", True, "applicable", None),
        (OPENED_3_ROOT, "2d47b05c996177f2afd7", True, "applicable", None),
        (
            OPENED_3_ROOT,
            "d92b542e0bb28fa3c950",
            True,
            "applicable",
            None,
        ),
        (
            OPENED_3_ROOT,
            "0b9b803536c12e3870eb",
            False,
            "unsupported",
            "helper-closure-or-nested-definition-unsupported",
        ),
        (
            OPENED_3_ROOT,
            "5b80f0787b1b6c47048b",
            False,
            "not_applicable",
            "no-repeated-authorized-unit",
        ),
        (
            OPENED_3_ROOT,
            "245226f0f9f97f6acda2",
            False,
            "unsupported",
            "tracked-value-mutation",
        ),
        (
            OPENED_3_ROOT,
            "f4e4d89ac44385a18261",
            False,
            "unsupported",
            "helper-closure-or-nested-definition-unsupported",
        ),
        (
            OPENED_3_ROOT,
            "19824e3f6b1e3980872f",
            False,
            "unsupported",
            "unregistered-component-consumer",
        ),
        (
            OPENED_3_ROOT,
            "3c650ec217b884e5f35e",
            False,
            "unsupported",
            "aggregation-on-test-operand-path",
        ),
        (OPENED_4_ROOT, "5c26014c176bf905c121", True, "applicable", None),
        (
            OPENED_4_ROOT,
            "5bdfa31a22a40d58e20c",
            False,
            "unsupported",
            "admission-call-off-list",
        ),
        (
            OPENED_4_ROOT,
            "4f622f87ad3c8a93a2d8",
            False,
            "unsupported",
            "admission-call-off-list",
        ),
        (OPENED_4_ROOT, "c07cc7c1a1f9730a3c9f", True, "applicable", None),
        (
            OPENED_4_ROOT,
            "34b1ade6d028cfda2a75",
            False,
            "unsupported",
            "two-group-row-selection-unavailable",
        ),
        (OPENED_4_ROOT, "675de846f46beae7d442", True, "applicable", None),
        (
            OPENED_4_ROOT,
            "540f7dfdf1614ceda57d",
            False,
            "unsupported",
            "multiple-rowwise-test-candidates",
        ),
        (
            OPENED_4_ROOT,
            "9cd65ce93b9b8f846eb8",
            False,
            "not_applicable",
            "no-repeated-authorized-unit",
        ),
        (
            OPENED_4_ROOT,
            "23cc44d49100a68655c5",
            False,
            "unsupported",
            "two-group-row-selection-unavailable",
        ),
        (
            OPENED_4_ROOT,
            "c69bb7590d57d2057ee0",
            False,
            "unsupported",
            "additional-accepted-reader-present",
        ),
        (
            OPENED_4_ROOT,
            "0e06da6bdb3963daae4e",
            False,
            "unsupported",
            "helper-closure-or-nested-definition-unsupported",
        ),
        (
            OPENED_4_ROOT,
            "e303f93351acf5df0457",
            False,
            "unsupported",
            "aggregation-on-test-operand-path",
        ),
        (OPENED_5_ROOT, "0b4876ceca6b0a9aede7", True, "applicable", None),
        (OPENED_5_ROOT, "1975f22bc0022b19331f", True, "applicable", None),
        (OPENED_5_ROOT, "2448bea72701b75fce2a", True, "applicable", None),
        (OPENED_5_ROOT, "a1541d5c671f3d6d58ce", True, "applicable", None),
        (OPENED_5_ROOT, "e50e676afb2cd3593234", True, "applicable", None),
        (OPENED_5_ROOT, "f1a04b5358a7b9b9d57c", True, "applicable", None),
        (
            OPENED_5_ROOT,
            "0d274a0eccdb84966940",
            False,
            "unsupported",
            "aggregation-on-test-operand-path",
        ),
        (
            OPENED_5_ROOT,
            "4afe430c936bbe560a5e",
            False,
            "not_applicable",
            "no-repeated-authorized-unit",
        ),
        (
            OPENED_5_ROOT,
            "4d64fa6416ee8406f678",
            False,
            "unsupported",
            "tracked-value-mutation",
        ),
        (
            OPENED_5_ROOT,
            "4e24fb76c83774381e41",
            False,
            "unsupported",
            "additional-accepted-reader-present",
        ),
        (
            OPENED_5_ROOT,
            "be94cec09f73d4a3036a",
            False,
            "unsupported",
            "unregistered-component-consumer",
        ),
        (
            OPENED_5_ROOT,
            "094fcb05ef85e4f7f406",
            False,
            "unsupported",
            "aggregation-on-test-operand-path",
        ),
    ],
)
def test_opened_cases_follow_code_lane_normal_path_and_replay(
    schema_root: Path,
    tmp_path: Path,
    opened_root: Path,
    case_id: str,
    expected_candidate: bool,
    expected_state: str,
    expected_reason: str | None,
) -> None:
    source = opened_root / case_id
    project = tmp_path / f"project-{case_id}"
    shutil.copytree(source / "project", project)
    method_contract_lock = source / "method-contract/semantic.lock.json"
    frozen_contract = json.loads(method_contract_lock.read_text(encoding="utf-8"))
    material_path = frozen_contract["method_contract_profile"]["profile_manifest"][
        "authority_binding_snapshot"
    ]["authorized_independent_unit_key"]["material_input_path"]
    audit = tmp_path / f"audit-{case_id}"
    bundle = run_audit(
        project,
        audit,
        schema_root,
        material_inputs=(material_path,),
        method_contract_lock=method_contract_lock,
    )
    lock = json.loads((audit / "semantic.lock.json").read_text(encoding="utf-8"))
    evaluation = lock["scientific_check_registry"]["evaluation"]
    dependence = next(item for item in evaluation["modules"] if item["check_id"] == CHECK_ID)
    assert dependence["state"] == expected_state
    if expected_reason is not None:
        assert dependence["observations"][0]["abstention_reason"] == expected_reason

    results = [
        item
        for item in bundle["detector_results"]
        if item.get("detector_id") == BoundedCodeCsvDependenceConflictV22Detector.detector_id
    ]
    assert bool([item for item in results if item["state"] == "evaluation_finding_candidate"]) is (
        expected_candidate
    )
    assert not [item for item in results if item["state"] == "accepted"]
    assert not bundle["findings"]

    replayed = replay(
        audit / "semantic.lock.json",
        tmp_path / f"replay-{case_id}",
        schema_root,
    )
    assert replayed["detector_results"] == bundle["detector_results"]
    assert replayed["findings"] == bundle["findings"]
    assert replayed["coverage_records"] == bundle["coverage_records"]


def test_section_12_1_tripwire_covers_adapter_inspect_and_dataflow_entry(
    schema_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case_id = "e50e676afb2cd3593234"
    source = OPENED_5_ROOT / case_id
    project = tmp_path / "project-tripwire"
    shutil.copytree(source / "project", project)
    lock_path = source / "method-contract/semantic.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    material_path = lock["method_contract_profile"]["profile_manifest"][
        "authority_binding_snapshot"
    ]["authorized_independent_unit_key"]["material_input_path"]

    inspect_calls = 0
    analyze_calls = 0
    helper_expansion_calls = 0
    slice_calls = 0
    forward_slice_calls = 0
    admission_calls = 0
    member_calls = 0
    annotation_exclusion_calls = 0
    descriptive_aggregation_calls = 0
    pandas_readonly_calls = 0
    loop_normalization_calls = 0
    reconstruction_member_calls = 0
    binding_substitution_calls = 0
    original_inspect = CodeCsvDependenceAdapter.inspect
    original_analyze = code_adapter_module.analyze_code_csv_dataflow
    original_expand = dataflow_module._expand_relevant_helpers
    original_slice = dataflow_module._Analyzer._backward_slice_names
    original_forward_slice = dataflow_module._Analyzer._tainted_name_closure
    original_admission = dataflow_module._Analyzer._admission_reason
    original_member = dataflow_module._container_member_expression
    original_runtime_walk = dataflow_module._walk_helper_runtime
    original_descriptive_aggregation = dataflow_module._Analyzer._post_test_descriptive_aggregation
    original_pandas_readonly = dataflow_module._v2_pandas_call
    original_loop_normalization = dataflow_module._normalize_contract_domain_loops
    original_reconstruction_member = dataflow_module._literal_subscript_member
    original_binding_visit = dataflow_module._ContractLoopBindingTransformer.visit_Name

    def guarded_inspect(self: CodeCsvDependenceAdapter, context):  # type: ignore[no-untyped-def]
        nonlocal inspect_calls
        inspect_calls += 1
        documents = tuple(
            cast(
                InspectionDocument,
                cast(Any, _ProseDocumentTripwire(document.path)),
            )
            if document.media_type in {"text/markdown", "text/plain"}
            else document
            for document in context.documents
        )
        return original_inspect(self, cast(Any, _TripwireContext(context, documents)))

    def guarded_analyze(content: bytes, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal analyze_calls
        analyze_calls += 1
        assert isinstance(content, bytes)
        return original_analyze(content, **kwargs)

    def guarded_expand(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal helper_expansion_calls
        helper_expansion_calls += 1
        return original_expand(*args, **kwargs)

    def guarded_slice(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal slice_calls
        slice_calls += 1
        return original_slice(self, *args, **kwargs)

    def guarded_forward_slice(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal forward_slice_calls
        forward_slice_calls += 1
        return original_forward_slice(self, *args, **kwargs)

    def guarded_admission(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal admission_calls
        admission_calls += 1
        return original_admission(self, *args, **kwargs)

    def guarded_member(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal member_calls
        member_calls += 1
        return original_member(*args, **kwargs)

    def guarded_runtime_walk(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal annotation_exclusion_calls
        annotation_exclusion_calls += 1
        yield from original_runtime_walk(*args, **kwargs)

    def guarded_descriptive_aggregation(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal descriptive_aggregation_calls
        descriptive_aggregation_calls += 1
        return original_descriptive_aggregation(self, *args, **kwargs)

    def guarded_pandas_readonly(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal pandas_readonly_calls
        pandas_readonly_calls += 1
        return original_pandas_readonly(*args, **kwargs)

    def guarded_loop_normalization(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal loop_normalization_calls
        loop_normalization_calls += 1
        return original_loop_normalization(*args, **kwargs)

    def guarded_reconstruction_member(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal reconstruction_member_calls
        reconstruction_member_calls += 1
        return original_reconstruction_member(*args, **kwargs)

    def guarded_binding_visit(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal binding_substitution_calls
        binding_substitution_calls += 1
        return original_binding_visit(self, *args, **kwargs)

    monkeypatch.setattr(CodeCsvDependenceAdapter, "inspect", guarded_inspect)
    monkeypatch.setattr(code_adapter_module, "analyze_code_csv_dataflow", guarded_analyze)
    monkeypatch.setattr(dataflow_module, "_expand_relevant_helpers", guarded_expand)
    monkeypatch.setattr(dataflow_module._Analyzer, "_backward_slice_names", guarded_slice)
    monkeypatch.setattr(dataflow_module._Analyzer, "_tainted_name_closure", guarded_forward_slice)
    monkeypatch.setattr(dataflow_module._Analyzer, "_admission_reason", guarded_admission)
    monkeypatch.setattr(dataflow_module, "_container_member_expression", guarded_member)
    monkeypatch.setattr(dataflow_module, "_walk_helper_runtime", guarded_runtime_walk)
    monkeypatch.setattr(
        dataflow_module._Analyzer,
        "_post_test_descriptive_aggregation",
        guarded_descriptive_aggregation,
    )
    monkeypatch.setattr(dataflow_module, "_v2_pandas_call", guarded_pandas_readonly)
    monkeypatch.setattr(
        dataflow_module,
        "_normalize_contract_domain_loops",
        guarded_loop_normalization,
    )
    monkeypatch.setattr(
        dataflow_module,
        "_literal_subscript_member",
        guarded_reconstruction_member,
    )
    monkeypatch.setattr(
        dataflow_module._ContractLoopBindingTransformer,
        "visit_Name",
        guarded_binding_visit,
    )
    bundle = run_audit(
        project,
        tmp_path / "audit-tripwire",
        schema_root,
        material_inputs=(material_path,),
        method_contract_lock=lock_path,
    )
    descriptive_source = OPENED_3_ROOT / "d92b542e0bb28fa3c950"
    descriptive_project = tmp_path / "project-tripwire-descriptive"
    shutil.copytree(descriptive_source / "project", descriptive_project)
    descriptive_lock_path = descriptive_source / "method-contract/semantic.lock.json"
    descriptive_lock = json.loads(descriptive_lock_path.read_text(encoding="utf-8"))
    descriptive_material_path = descriptive_lock["method_contract_profile"]["profile_manifest"][
        "authority_binding_snapshot"
    ]["authorized_independent_unit_key"]["material_input_path"]
    run_audit(
        descriptive_project,
        tmp_path / "audit-tripwire-descriptive",
        schema_root,
        material_inputs=(descriptive_material_path,),
        method_contract_lock=descriptive_lock_path,
    )
    assert inspect_calls == 2
    frozen = json.loads(
        (tmp_path / "audit-tripwire/semantic.lock.json").read_text(encoding="utf-8")
    )
    dependence_observation = next(
        item
        for item in frozen["scientific_check_registry"]["evaluation"]["modules"]
        if item["check_id"] == CHECK_ID
    )
    assert analyze_calls == 2, dependence_observation
    assert helper_expansion_calls == 2
    assert slice_calls >= 1
    assert forward_slice_calls >= 1
    assert admission_calls >= 1
    assert member_calls >= 1
    assert annotation_exclusion_calls >= 1
    assert descriptive_aggregation_calls >= 1
    assert pandas_readonly_calls >= 1
    assert loop_normalization_calls == 2
    assert reconstruction_member_calls >= 1
    assert binding_substitution_calls >= 1
    assert not bundle["findings"]


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
def test_refrozen_k_contracts_are_live_scored_abstentions(
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
    frozen = json.loads(method_contract_lock.read_text(encoding="utf-8"))
    assert (
        frozen["method_contract_profile"]["profile_manifest"]["check_manifest"]["check_version"]
        == "2.2.0"
    )

    audit = tmp_path / f"k-audit-{case_id}"
    bundle = run_audit(
        project,
        audit,
        schema_root,
        report="results/report.md",
        material_inputs=("data/input.csv",),
        method_contract_lock=method_contract_lock,
    )
    lock = json.loads((audit / "semantic.lock.json").read_text(encoding="utf-8"))
    dependence = next(
        item
        for item in lock["scientific_check_registry"]["evaluation"]["modules"]
        if item["check_id"] == CHECK_ID
    )
    assert dependence["state"] == "unsupported"
    assert dependence["observations"][0]["abstention_reason"] == expected_reason
    assert not bundle["findings"]
    assert not [
        item
        for item in bundle["detector_results"]
        if item.get("detector_id") == BoundedCodeCsvDependenceConflictV22Detector.detector_id
        and item.get("state") in {"evaluation_finding_candidate", "finding_candidate", "accepted"}
    ]

    replayed = replay(audit / "semantic.lock.json", tmp_path / f"k-replay-{case_id}", schema_root)
    assert replayed["detector_results"] == bundle["detector_results"]
    assert replayed["findings"] == bundle["findings"]
    assert replayed["coverage_records"] == bundle["coverage_records"]
