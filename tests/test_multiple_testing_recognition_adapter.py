"""End-to-end tests for the Experiment-0059 report-only shadow adapter."""

from __future__ import annotations

import ast
from dataclasses import replace

import pytest

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.multiple_testing_recognition import adapter as adapter_module
from sc_referee.multiple_testing_recognition import python_analyzer as analyzer_module
from sc_referee.multiple_testing_recognition.adapter import (
    MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST,
    MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_FILES,
    MultipleTestingRecognitionShadowAdapter,
)
from sc_referee.multiple_testing_recognition.certificate import source_construct_token
from sc_referee.multiple_testing_recognition.ir import EvidencePoint
from sc_referee.multiple_testing_recognition.pvalue_domain import (
    pvalue_family_row_domain,
)
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    InspectionDocument,
    RecordRef,
)

_SOURCE_PATH = "workflow/analysis.py"
_DATA_PATH = "results/tests.csv"
_MEASUREMENT_PATH = "inputs/measurements.csv"
_REPORT_PATH = "results/report.txt"
_DATA = b"gene,pvalue\ng1,0.01\ng2,0.04\ng3,0.20\n"
_MEASUREMENTS = b"gene,x1,x2,y1,y2\ng2,2.0,3.0,3.0,4.0\ng1,1.0,2.0,2.0,3.0\ng3,3.0,4.0,4.0,5.0\n"


class _BoundaryFailure(BaseException):
    """Non-Exception failure proving the adapter catches BaseException."""


def _source(
    *,
    correction_input: str = "pvals[:2]",
    include_correction: bool = True,
    after_reader: str = "",
) -> str:
    statements = [
        "import csv",
        "import scipy.stats",
        "from pathlib import Path",
        "from statsmodels.stats.multitest import multipletests",
        (
            'rows = list(csv.DictReader(Path("results/tests.csv").read_text('
            'encoding="utf-8").splitlines()))'
        ),
        after_reader,
        'genes = [row["gene"] for row in rows]',
        (
            'measurement_rows = list(csv.DictReader(Path("inputs/measurements.csv").read_text('
            'encoding="utf-8").splitlines()))'
        ),
        'x = {r["gene"]: (float(r["x1"]), float(r["x2"])) for r in measurement_rows}',
        'y = {s["gene"]: (float(s["y1"]), float(s["y2"])) for s in measurement_rows}',
        "pvals = [scipy.stats.ttest_ind(x[g], y[g]).pvalue for g in genes]",
    ]
    if include_correction:
        statements.append(f'adjusted = multipletests({correction_input}, method="fdr_bh")')
    statements.extend(
        [
            "reported = tuple(zip(genes, pvals))",
            'Path("results/report.txt").write_text(str((reported, adjusted)), encoding="utf-8")',
        ]
    )
    return "\n".join(item for item in statements if item) + "\n"


def _point(node: ast.AST) -> EvidencePoint:
    return EvidencePoint(
        _SOURCE_PATH,
        node.lineno,
        node.end_lineno or node.lineno,
        node.col_offset + 1,
        (node.end_col_offset or node.col_offset) + 1,
    )


def _battery_id(source: str) -> str:
    tree = ast.parse(source)
    matches = [
        item
        for item in tree.body
        if isinstance(item, ast.Assign)
        and len(item.targets) == 1
        and isinstance(item.targets[0], ast.Name)
        and item.targets[0].id == "pvals"
        and isinstance(item.value, ast.ListComp)
    ]
    assert len(matches) == 1
    source_bytes = source.encode()
    return source_construct_token(
        "battery-construct",
        sha256_digest(source_bytes),
        _point(matches[0]),
    )


def _context(
    source: str,
    *,
    authority: bool = True,
    data: bytes = _DATA,
    parser_id: str = "python-ast",
    parser_version: str = "3.11",
) -> FrozenInspectionContext:
    surface_ref = RecordRef("publication_surface", "surface:primary")
    artifact_ref = RecordRef("artifact", "artifact:report")
    snapshot_ref = RecordRef("repository_snapshot", "snapshot:primary")
    analysis_file_ref = RecordRef("file_record", "file:analysis")
    parser_ref = RecordRef("parser_result", "parser:analysis")
    data_file_ref = RecordRef("file_record", "file:data")
    data_identity_ref = RecordRef("asset_identity", "asset:data")
    measurement_file_ref = RecordRef("file_record", "file:measurements")
    measurement_identity_ref = RecordRef("asset_identity", "asset:measurements")
    requirements_file_ref = RecordRef("file_record", "file:requirements")
    requirements_identity_ref = RecordRef("asset_identity", "asset:requirements")
    analysis_ref = RecordRef("analysis", "analysis:primary")
    procedure_ref = RecordRef("procedure", "procedure:correction")
    result_ref = RecordRef("result", "result:report")
    data_digest = sha256_digest(data)
    measurement_digest = sha256_digest(_MEASUREMENTS)
    requirements = b"scipy==1.14.0\nstatsmodels==0.14.4\n"
    requirements_digest = sha256_digest(requirements)
    source_bytes = source.encode()
    parser_payload = canonical_json(
        {"parser_id": parser_id, "parser_version": parser_version, "state": "parsed"}
    ).encode()

    records: list[tuple[RecordRef, dict[str, object]]] = [
        (
            surface_ref,
            {
                "publication_surface_id": surface_ref.record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [artifact_ref.to_dict()]},
            },
        ),
        (
            artifact_ref,
            {
                "artifact_id": artifact_ref.record_id,
                "kind": "report",
                "path": _REPORT_PATH,
            },
        ),
        (
            snapshot_ref,
            {
                "snapshot_id": snapshot_ref.record_id,
                "extensions": {
                    "x-material-full-digest-paths": [
                        _DATA_PATH,
                        _MEASUREMENT_PATH,
                        "requirements.txt",
                    ]
                },
            },
        ),
        (analysis_file_ref, {"file_record_id": analysis_file_ref.record_id}),
        (parser_ref, {"parser_result_id": parser_ref.record_id}),
        (analysis_ref, {"analysis_id": analysis_ref.record_id}),
        (
            procedure_ref,
            {
                "procedure_id": procedure_ref.record_id,
                "resolved_callable": "statsmodels.stats.multitest.multipletests",
            },
        ),
        (result_ref, {"result_id": result_ref.record_id, "path": _REPORT_PATH}),
        (
            data_file_ref,
            {
                "file_record_id": data_file_ref.record_id,
                "path": _DATA_PATH,
                "entry_kind": "regular_file",
                "asset_identity_ref": data_identity_ref.to_dict(),
            },
        ),
        (
            data_identity_ref,
            {
                "asset_identity_id": data_identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": data_file_ref.to_dict(),
                "identity_evidence": {"kind": "full_digest", "digest": data_digest},
            },
        ),
        (
            measurement_file_ref,
            {
                "file_record_id": measurement_file_ref.record_id,
                "path": _MEASUREMENT_PATH,
                "entry_kind": "regular_file",
                "asset_identity_ref": measurement_identity_ref.to_dict(),
            },
        ),
        (
            measurement_identity_ref,
            {
                "asset_identity_id": measurement_identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": measurement_file_ref.to_dict(),
                "identity_evidence": {
                    "kind": "full_digest",
                    "digest": measurement_digest,
                },
            },
        ),
        (
            requirements_file_ref,
            {
                "file_record_id": requirements_file_ref.record_id,
                "path": "requirements.txt",
                "entry_kind": "regular_file",
                "asset_identity_ref": requirements_identity_ref.to_dict(),
            },
        ),
        (
            requirements_identity_ref,
            {
                "asset_identity_id": requirements_identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": requirements_file_ref.to_dict(),
                "identity_evidence": {
                    "kind": "full_digest",
                    "digest": requirements_digest,
                },
            },
        ),
    ]
    if authority:
        records.append(
            (
                RecordRef("human_pvalue_family_authorization", "authorization:primary"),
                {
                    "record_type": "human_pvalue_family_authorization",
                    "record_id": "authorization:primary",
                    "actor_id": "human:family-owner",
                    "authority_state": "authorized",
                    "analysis_target_ref": analysis_ref.to_dict(),
                    "correction_procedure_ref": procedure_ref.to_dict(),
                    "family_definition_id": "family-definition:all-genes",
                    "battery_construct_id": _battery_id(source),
                    "iterable_row_domain": pvalue_family_row_domain(
                        _DATA_PATH,
                        data_digest,
                        "splitlines",
                    ),
                    "authorized_family_key_columns": ["gene"],
                    "family_member_rule": "all_rows",
                    "family_input_path": _DATA_PATH,
                    "family_input_content_digest": data_digest,
                },
            )
        )

    return FrozenInspectionContext(
        snapshot_digest=sha256_digest(b"snapshot"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(
            InspectionDocument(
                path=_SOURCE_PATH,
                file_ref=analysis_file_ref,
                content=source_bytes,
                content_digest=sha256_digest(source_bytes),
                media_type="text/x-python",
                parser_result_ref=parser_ref,
                parser_result_payload=parser_payload,
                parser_result_digest=sha256_digest(parser_payload),
            ),
        ),
        base_records=tuple(FrozenBaseRecord.from_record(ref, value) for ref, value in records),
        material_inputs=(
            FrozenMaterialInput(
                path=_DATA_PATH,
                file_ref=data_file_ref,
                asset_identity_ref=data_identity_ref,
                content=data,
                content_digest=data_digest,
            ),
            FrozenMaterialInput(
                path="requirements.txt",
                file_ref=requirements_file_ref,
                asset_identity_ref=requirements_identity_ref,
                content=requirements,
                content_digest=requirements_digest,
            ),
            FrozenMaterialInput(
                path=_MEASUREMENT_PATH,
                file_ref=measurement_file_ref,
                asset_identity_ref=measurement_identity_ref,
                content=_MEASUREMENTS,
                content_digest=measurement_digest,
            ),
        ),
    )


@pytest.fixture
def shadow_adapter() -> MultipleTestingRecognitionShadowAdapter:
    return MultipleTestingRecognitionShadowAdapter()


def _body(payload: dict[str, object]) -> dict[str, object]:
    body = payload["payload"]
    assert isinstance(body, dict)
    return body


def _coverage_classes(payload: dict[str, object]) -> tuple[str, ...]:
    value = _body(payload).get("coverage_classes")
    assert isinstance(value, list)
    return tuple(str(item) for item in value)


def _assert_not_candidate(payload: dict[str, object]) -> None:
    assert payload["payload_type"] != "shadow_candidate"
    assert payload["outcome"] != "evaluation_candidate"


def _assert_report_only_without_finding_fields(payload: dict[str, object]) -> None:
    assert payload["delivery_plane"] == "unregistered_shadow_report_only"
    assert payload["output_ceiling"] == "evaluation_candidate"
    forbidden = {"finding_id", "finding_type", "severity", "remediation"}
    assert not forbidden & set(payload)
    assert not forbidden & set(_body(payload))


def test_subset_correction_emits_report_only_shadow_candidate(
    shadow_adapter: MultipleTestingRecognitionShadowAdapter,
) -> None:
    payload = shadow_adapter.inspect(_context(_source(correction_input="pvals[:2]")))
    assert payload["payload_type"] == "shadow_candidate"
    assert payload["outcome"] == "evaluation_candidate"
    body = _body(payload)
    assert body["record_type"] == "multiple_testing_shadow_candidate"
    assert body["corrected_positions"] == [0, 1]
    assert body["corrected_count"] == 2
    assert body["performed_count"] == 3
    assert body["authorized_family_key_columns"] == ["gene"]
    assert body["measurement_input_binding"] == {
        "path": _MEASUREMENT_PATH,
        "content_digest": sha256_digest(_MEASUREMENTS),
    }
    assert body["measurement_key_columns"] == ["gene"]
    assert body["left_measurement_columns"] == ["x1", "x2"]
    assert body["right_measurement_columns"] == ["y1", "y2"]
    assert len(body["argument_vector_tokens"]) == 3
    assert body["report_only"] is True
    assert body["evidence_declarations"]
    _assert_report_only_without_finding_fields(payload)


def test_registered_capture_parser_identity_reaches_the_kernel() -> None:
    payload = MultipleTestingRecognitionShadowAdapter().inspect(
        _context(
            _source(correction_input="pvals[:2]"),
            parser_id="parser:python-ast-tokenize",
            parser_version="0.15.1",
        )
    )
    assert payload["payload_type"] == "shadow_candidate"
    assert payload["outcome"] == "evaluation_candidate"
    assert _body(payload)["evidence_declarations"]


def test_regression_r1_h1_never_read_pvalue_values_cannot_control_a_finding(
    shadow_adapter: MultipleTestingRecognitionShadowAdapter,
) -> None:
    source = _source(correction_input="[p for p in pvals if p < 0.05]")
    csv_variants = (
        b"gene,pvalue\ng1,0.01\ng2,0.04\ng3,0.20\n",
        b"gene,pvalue\ng1,0.90\ng2,0.80\ng3,0.70\n",
        b"gene,pvalue\ng1,0.001\ng2,0.002\ng3,0.003\n",
    )
    payloads = [shadow_adapter.inspect(_context(source, data=data)) for data in csv_variants]
    assert len({canonical_json(payload) for payload in payloads}) == 1
    for payload in payloads:
        _assert_not_candidate(payload)
        assert payload["payload_type"] == "abstention"
        assert _coverage_classes(payload) == ("value-predicate-correction-unsupported",)


def test_full_battery_correction_is_a_verified_coverage_note(
    shadow_adapter: MultipleTestingRecognitionShadowAdapter,
) -> None:
    payload = shadow_adapter.inspect(_context(_source(correction_input="pvals")))
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "coverage_note"
    assert payload["outcome"] == "covered_negative"
    body = _body(payload)
    assert body["coverage_class"] == "complete_family_correction"
    assert body["corrected_positions"] == [0, 1, 2]
    assert body["corrected_count"] == body["performed_count"] == 3
    assert body["evidence_declarations"]
    _assert_report_only_without_finding_fields(payload)


def test_absent_authority_names_candidate_battery_without_ranking(
    shadow_adapter: MultipleTestingRecognitionShadowAdapter,
) -> None:
    payload = shadow_adapter.inspect(_context(_source(), authority=False))
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "material_question"
    body = _body(payload)
    candidates = body["candidate_batteries"]
    assert isinstance(candidates, list)
    assert len(candidates) == 1
    assert candidates[0]["battery_construct_id"].startswith("battery-construct:")
    assert candidates[0]["selection_state"] == "unresolved"
    assert body["candidate_family_key_columns"] == ["gene"]
    assert body["ranking"] is None
    assert body["none_of_these_option"] is True


def test_loop_built_battery_is_a_named_abstention(
    shadow_adapter: MultipleTestingRecognitionShadowAdapter,
) -> None:
    source = _source(after_reader="for row in rows:\n    rows = rows")
    payload = shadow_adapter.inspect(_context(source, authority=False))
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "abstention"
    assert _coverage_classes(payload) == ("loop-built-test-battery-unrecognized",)


def test_missing_same_module_correction_is_the_named_cross_module_gap(
    shadow_adapter: MultipleTestingRecognitionShadowAdapter,
) -> None:
    payload = shadow_adapter.inspect(_context(_source(include_correction=False), authority=False))
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "abstention"
    assert _coverage_classes(payload) == ("cross-module-correction-unverified",)


@pytest.mark.parametrize(
    ("boundary", "expected_class"),
    [
        ("analyzer", "analyzer-exception"),
        ("discharge", "controller-discharge-exception"),
        ("prover", "controller-discharge-exception"),
        ("kernel", "controller-discharge-exception"),
        ("projection", "shadow-projection-exception"),
    ],
)
def test_every_boundary_catches_baseexception_as_named_abstention(
    monkeypatch: pytest.MonkeyPatch,
    shadow_adapter: MultipleTestingRecognitionShadowAdapter,
    boundary: str,
    expected_class: str,
) -> None:
    def fail(*_args: object, **_kwargs: object) -> object:
        raise _BoundaryFailure(boundary)

    if boundary == "analyzer":
        monkeypatch.setattr(adapter_module, "analyze_multiple_testing_python", fail)
    elif boundary == "discharge":
        monkeypatch.setattr(adapter_module, "discharge_multiple_testing_proposal", fail)
    elif boundary == "prover":
        monkeypatch.setattr(analyzer_module, "prove_pvalue_family", fail)
    elif boundary == "kernel":
        monkeypatch.setattr(analyzer_module, "verify_multiple_testing_certificate", fail)
    else:
        monkeypatch.setattr(MultipleTestingRecognitionShadowAdapter, "_candidate", fail)

    payload = shadow_adapter.inspect(_context(_source()))
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "abstention"
    assert _coverage_classes(payload) == (expected_class,)


@pytest.mark.parametrize("correction_input", ["pvals[:2]", "pvals"])
def test_candidate_and_coverage_both_require_a_verified_certificate(
    monkeypatch: pytest.MonkeyPatch,
    shadow_adapter: MultipleTestingRecognitionShadowAdapter,
    correction_input: str,
) -> None:
    context = _context(_source(correction_input=correction_input))
    analysis = analyzer_module.analyze_multiple_testing_python(context)
    discharged = analyzer_module.discharge_multiple_testing_proposal(analysis, context)
    assert discharged.state == "verified"
    monkeypatch.setattr(
        adapter_module,
        "discharge_multiple_testing_proposal",
        lambda *_args, **_kwargs: replace(discharged, verified_certificate=None),
    )
    payload = shadow_adapter.inspect(context)
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "abstention"
    assert _coverage_classes(payload) == ("verified-certificate-required",)


def test_conclusion_outcome_mismatch_gate_refuses_projection(
    monkeypatch: pytest.MonkeyPatch,
    shadow_adapter: MultipleTestingRecognitionShadowAdapter,
) -> None:
    context = _context(_source())
    analysis = analyzer_module.analyze_multiple_testing_python(context)
    discharged = analyzer_module.discharge_multiple_testing_proposal(analysis, context)
    assert discharged.verified_certificate is not None
    forged = replace(
        discharged,
        verified_certificate=replace(
            discharged.verified_certificate,
            conclusion="complete_family_correction",
        ),
    )
    monkeypatch.setattr(
        adapter_module,
        "discharge_multiple_testing_proposal",
        lambda *_args, **_kwargs: forged,
    )
    payload = shadow_adapter.inspect(context)
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "abstention"
    assert payload["reason_code"] == "conclusion-outcome-mismatch"
    assert _coverage_classes(payload) == ("conclusion-outcome-mismatch",)


def test_verified_result_from_a_different_source_cannot_be_projected(
    monkeypatch: pytest.MonkeyPatch,
    shadow_adapter: MultipleTestingRecognitionShadowAdapter,
) -> None:
    inspected = _context(_source(correction_input="pvals[:2]"))
    other = _context(_source(correction_input="pvals"))
    other_analysis = analyzer_module.analyze_multiple_testing_python(other)
    other_discharged = analyzer_module.discharge_multiple_testing_proposal(
        other_analysis,
        other,
    )
    assert other_discharged.state == "verified"
    monkeypatch.setattr(
        adapter_module,
        "discharge_multiple_testing_proposal",
        lambda *_args, **_kwargs: other_discharged,
    )
    payload = shadow_adapter.inspect(inspected)
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "abstention"
    assert payload["reason_code"] == "analysis-discharge-binding-mismatch"


def test_every_nonadverse_workflow_is_blocked_by_the_zero_fa_guard(
    shadow_adapter: MultipleTestingRecognitionShadowAdapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workflows = [
        _context(_source(correction_input="pvals")),
        _context(_source(), authority=False),
        _context(
            _source(after_reader="for row in rows:\n    rows = rows"),
            authority=False,
        ),
        _context(_source(include_correction=False), authority=False),
    ]
    payloads = [shadow_adapter.inspect(context) for context in workflows]

    def fail(*_args: object, **_kwargs: object) -> object:
        raise _BoundaryFailure("injected")

    monkeypatch.setattr(adapter_module, "analyze_multiple_testing_python", fail)
    payloads.append(shadow_adapter.inspect(_context(_source())))
    assert [item["payload_type"] for item in payloads] == [
        "coverage_note",
        "material_question",
        "abstention",
        "abstention",
        "abstention",
    ]
    for payload in payloads:
        _assert_not_candidate(payload)
        _assert_report_only_without_finding_fields(payload)


def test_same_inputs_produce_byte_identical_payload_and_closed_digest(
    shadow_adapter: MultipleTestingRecognitionShadowAdapter,
) -> None:
    context = _context(_source())
    first = shadow_adapter.inspect(context)
    second = shadow_adapter.inspect(context)
    assert canonical_json(first).encode() == canonical_json(second).encode()
    assert first["implementation_dependency_closure_digest"] == (
        MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST
    )
    assert first["implementation_dependency_closure_digest"] == semantic_digest(
        {"dependency_closure": first["implementation_dependency_closure"]}
    )
    assert tuple(first["implementation_dependency_closure"]) == (
        MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_FILES
    )
