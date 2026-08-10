"""End-to-end tests for the unregistered dependence-recognition shadow adapter."""

from __future__ import annotations

import pytest

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition import adapter as adapter_module
from sc_referee.dependence_recognition import python_analyzer as analyzer_module
from sc_referee.dependence_recognition.adapter import (
    DEPENDENCE_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST,
    DEPENDENCE_RECOGNITION_DEPENDENCY_FILES,
    DependenceRecognitionShadowAdapter,
)
from sc_referee.dependence_recognition.ir import MAX_DEPENDENCE_CSV_DOMAIN_BYTES
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    InspectionDocument,
    RecordRef,
)

_DATA_PATH = "inputs/data.csv"
_REPORT_PATH = "results/report.txt"
_ADVERSE_DATA = b"participant_id,site_id,a,b\np1,s1,1,2\np1,s1,2,3\np2,s2,4,5\np2,s2,5,6\n"


def _source(
    *,
    reader: str | None = None,
    before_operands: str = "",
    frame_name: str = "rows",
    call: str = "result = st.ttest_ind(group_a, group_b)",
) -> str:
    reader = reader or (
        'rows = list(csv.DictReader(Path("inputs/data.csv").open(newline="", encoding="utf-8")))'
    )
    return "\n".join(
        item
        for item in (
            "import csv",
            "from pathlib import Path",
            "import scipy.stats as st",
            reader,
            before_operands,
            f'group_a = [float(row["a"]) for row in {frame_name}]',
            f'group_b = [float(row["b"]) for row in {frame_name}]',
            call,
            'Path("results/report.txt").write_text(str(result), encoding="utf-8")',
            "",
        )
        if item
    )


def _context(
    source: str,
    *,
    data: bytes = _ADVERSE_DATA,
    authority_columns: tuple[str, ...] | None = ("participant_id",),
    requirements: bytes = b"scipy==1.14.0\n",
    second_authority: bool = False,
) -> FrozenInspectionContext:
    surface_ref = RecordRef("publication_surface", "surface:primary")
    artifact_ref = RecordRef("artifact", "artifact:report")
    snapshot_ref = RecordRef("repository_snapshot", "snapshot:primary")
    analysis_file_ref = RecordRef("file_record", "file:analysis")
    parser_ref = RecordRef("parser_result", "parser:analysis")
    data_file_ref = RecordRef("file_record", "file:data")
    data_identity_ref = RecordRef("asset_identity", "asset:data")
    requirements_file_ref = RecordRef("file_record", "file:requirements")
    requirements_identity_ref = RecordRef("asset_identity", "asset:requirements")
    analysis_ref = RecordRef("analysis", "analysis:primary")
    procedure_ref = RecordRef("procedure", "procedure:test")
    result_ref = RecordRef("result", "result:report")
    data_digest = sha256_digest(data)
    requirements_digest = sha256_digest(requirements)
    parser_payload = canonical_json(
        {"parser_id": "python-ast", "parser_version": "3.11", "state": "parsed"}
    ).encode()
    source_bytes = source.encode()

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
                "extensions": {"x-material-full-digest-paths": [_DATA_PATH, "requirements.txt"]},
            },
        ),
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
        (analysis_file_ref, {"file_record_id": analysis_file_ref.record_id}),
        (parser_ref, {"parser_result_id": parser_ref.record_id}),
        (analysis_ref, {"analysis_id": analysis_ref.record_id}),
        (procedure_ref, {"procedure_id": procedure_ref.record_id}),
        (result_ref, {"result_id": result_ref.record_id, "path": _REPORT_PATH}),
    ]
    if authority_columns is not None:
        records.append(
            _authority_record(
                "authorization:primary",
                "human:method-owner",
                authority_columns,
                data_digest,
            )
        )
    if second_authority:
        records.append(
            _authority_record(
                "authorization:second",
                "human:second-owner",
                ("site_id",),
                data_digest,
                unit_definition_id="unit-definition:site",
            )
        )

    return FrozenInspectionContext(
        snapshot_digest=sha256_digest(b"snapshot"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(
            InspectionDocument(
                path="workflow/analysis.py",
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
        ),
    )


def _authority_record(
    record_id: str,
    actor_id: str,
    columns: tuple[str, ...],
    data_digest: str,
    *,
    unit_definition_id: str = "unit-definition:participant",
) -> tuple[RecordRef, dict[str, object]]:
    ref = RecordRef("human_method_authorization", record_id)
    return (
        ref,
        {
            "record_type": "human_method_authorization",
            "record_id": record_id,
            "actor_id": actor_id,
            "authority_state": "authorized",
            "analysis_target_ref": {
                "record_type": "analysis",
                "record_id": "analysis:primary",
            },
            "procedure_ref": {
                "record_type": "procedure",
                "record_id": "procedure:test",
            },
            "independent_unit_definition_id": unit_definition_id,
            "authorized_key_columns": list(columns),
            "input_path": _DATA_PATH,
            "input_content_digest": data_digest,
        },
    )


@pytest.fixture
def shadow_adapter() -> DependenceRecognitionShadowAdapter:
    return DependenceRecognitionShadowAdapter()


def _assert_not_candidate(payload: dict[str, object]) -> None:
    assert payload["payload_type"] != "shadow_candidate"
    assert payload["outcome"] != "evaluation_candidate"


def _coverage_classes(payload: dict[str, object]) -> tuple[str, ...]:
    body = payload["payload"]
    assert isinstance(body, dict)
    value = body.get("coverage_classes")
    assert isinstance(value, list)
    return tuple(str(item) for item in value)


def test_adverse_workflow_emits_report_only_shadow_candidate(
    shadow_adapter: DependenceRecognitionShadowAdapter,
) -> None:
    payload = shadow_adapter.inspect(_context(_source()))
    assert payload["payload_type"] == "shadow_candidate"
    assert payload["outcome"] == "evaluation_candidate"
    assert payload["delivery_plane"] == "unregistered_shadow_report_only"
    body = payload["payload"]
    assert body["record_type"] == "dependence_shadow_candidate"
    assert body["report_only"] is True
    assert body["promotion_state"] == "unregistered_shadow_only"
    assert body["authorized_key_columns"] == ["participant_id"]
    assert body["resolved_callable"] == "scipy.stats.ttest_ind"
    forbidden_keys = {"finding_id", "finding_type", "severity", "remediation"}
    assert not forbidden_keys & set(payload)
    assert not forbidden_keys & set(body)


def test_regression_n3_unit_groupby_mean_is_a_named_abstention(
    shadow_adapter: DependenceRecognitionShadowAdapter,
) -> None:
    source = _source(
        before_operands='unit_rows = rows.groupby("participant_id").mean()',
        frame_name="unit_rows",
    )
    payload = shadow_adapter.inspect(_context(source))
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "abstention"
    assert payload["outcome"] == "unsupported"
    assert "unit-level-aggregation-unrecognized" in _coverage_classes(payload)


def test_one_row_per_unit_is_a_verified_coverage_note(
    shadow_adapter: DependenceRecognitionShadowAdapter,
) -> None:
    data = b"participant_id,site_id,a,b\np1,s1,1,2\np2,s1,2,3\np3,s2,4,5\n"
    payload = shadow_adapter.inspect(_context(_source(), data=data))
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "coverage_note"
    assert payload["reason_code"] == "one_observation_per_independent_unit"


def test_absent_authority_names_both_repeated_candidates_without_ranking(
    shadow_adapter: DependenceRecognitionShadowAdapter,
) -> None:
    payload = shadow_adapter.inspect(_context(_source(), authority_columns=None))
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "material_question"
    body = payload["payload"]
    assert {"participant_id", "site_id"} <= set(body["candidate_key_columns"])
    assert body["ranking"] is None
    assert body["none_of_these_option"] is True
    assert body["ordered_composite_key_state"] == "unresolved"
    assert all(
        dimension["selection_state"] == "unresolved" for dimension in body["candidate_dimensions"]
    )


def test_present_but_column_mismatched_authority_is_a_question(
    shadow_adapter: DependenceRecognitionShadowAdapter,
) -> None:
    payload = shadow_adapter.inspect(
        _context(_source(), authority_columns=("different_unit_column",))
    )
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "material_question"
    assert "authorized-unit-key-column-binding" in payload["payload"]["unresolved_dimensions"]


def test_two_conflicting_authorizations_never_select_one(
    shadow_adapter: DependenceRecognitionShadowAdapter,
) -> None:
    payload = shadow_adapter.inspect(_context(_source(), second_authority=True))
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "material_question"
    assert payload["payload"]["ranking"] is None


@pytest.mark.parametrize(
    ("source", "requirements", "expected_class"),
    [
        (
            _source(reader='rows = pandas.read_csv("inputs/data.csv")').replace(
                "import scipy.stats as st", "import scipy.stats as st\nimport pandas"
            ),
            b"scipy==1.14.0\n",
            "pandas-frame-model",
        ),
        (
            _source(
                before_operands=("def wrapper(left, right):\n    return st.ttest_ind(left, right)"),
                call="result = wrapper(group_a, group_b)",
            ),
            b"scipy==1.14.0\n",
            "helper-or-wrapper-function",
        ),
        (_source(), b"scipy>=1.14\n", "unsupported-or-unpinned-scipy-version"),
        (
            _source(
                before_operands=('filtered = [row for row in rows if row["site_id"] == "s1"]'),
                frame_name="filtered",
            ),
            b"scipy==1.14.0\n",
            "unsupported-assignment",
        ),
    ],
)
def test_unsupported_source_routes_are_named_non_accusatory_abstentions(
    shadow_adapter: DependenceRecognitionShadowAdapter,
    source: str,
    requirements: bytes,
    expected_class: str,
) -> None:
    payload = shadow_adapter.inspect(_context(source, requirements=requirements))
    _assert_not_candidate(payload)
    assert payload["payload_type"] == "abstention"
    assert expected_class in _coverage_classes(payload)
    assert payload["payload"]["accusatory_output"] is False


def test_membership_above_cap_is_named_abstention(
    shadow_adapter: DependenceRecognitionShadowAdapter,
) -> None:
    rows = b"".join(
        f"p{index % 2},s{index % 2},{index},{index + 1}\n".encode() for index in range(10_001)
    )
    data = b"participant_id,site_id,a,b\n" + rows
    payload = shadow_adapter.inspect(_context(_source(), data=data))
    _assert_not_candidate(payload)
    assert "membership-scale-above-v1-bound" in _coverage_classes(payload)


def test_file_above_byte_ceiling_is_named_abstention(
    shadow_adapter: DependenceRecognitionShadowAdapter,
) -> None:
    header = b"participant_id,site_id,a,b\n"
    data = header + b"x" * (MAX_DEPENDENCE_CSV_DOMAIN_BYTES - len(header) + 1)
    payload = shadow_adapter.inspect(_context(_source(), data=data))
    _assert_not_candidate(payload)
    assert "unit-key-multiplicity-proof-unavailable" in _coverage_classes(payload)


def test_analyzer_exception_is_caught_as_named_abstention(
    shadow_adapter: DependenceRecognitionShadowAdapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_context: FrozenInspectionContext) -> None:
        raise RuntimeError("injected analyzer failure")

    monkeypatch.setattr(adapter_module, "analyze_dependence_python", fail)
    payload = shadow_adapter.inspect(_context(_source()))
    _assert_not_candidate(payload)
    assert _coverage_classes(payload) == ("analyzer-exception",)


def test_prover_none_is_an_abstention_not_a_candidate(
    shadow_adapter: DependenceRecognitionShadowAdapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        analyzer_module, "prove_unit_key_multiplicity", lambda *args, **kwargs: None
    )
    payload = shadow_adapter.inspect(_context(_source()))
    _assert_not_candidate(payload)
    assert "unit-key-multiplicity-proof-unavailable" in _coverage_classes(payload)


def test_prover_exception_is_caught_at_the_controller_boundary(
    shadow_adapter: DependenceRecognitionShadowAdapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise RuntimeError("injected prover failure")

    monkeypatch.setattr(analyzer_module, "prove_unit_key_multiplicity", fail)
    payload = shadow_adapter.inspect(_context(_source()))
    _assert_not_candidate(payload)
    assert _coverage_classes(payload) == ("controller-discharge-exception",)


@pytest.mark.parametrize("mode", ["refuse", "raise"])
def test_kernel_refusal_or_exception_never_reaches_a_candidate(
    shadow_adapter: DependenceRecognitionShadowAdapter,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    if mode == "refuse":
        monkeypatch.setattr(
            analyzer_module,
            "verify_dependence_certificate",
            lambda *args, **kwargs: None,
        )
    else:

        def fail(*args: object, **kwargs: object) -> None:
            raise AttributeError("injected type-invalid proposal")

        monkeypatch.setattr(analyzer_module, "verify_dependence_certificate", fail)
    payload = shadow_adapter.inspect(_context(_source()))
    _assert_not_candidate(payload)
    expected = (
        "certificate-kernel-refusal" if mode == "refuse" else "controller-discharge-exception"
    )
    assert expected in _coverage_classes(payload)


def test_question_and_unsupported_routes_bypass_kernel_acceptance(
    shadow_adapter: DependenceRecognitionShadowAdapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("the non-accusatory route must not call the kernel")

    monkeypatch.setattr(analyzer_module, "verify_dependence_certificate", forbidden)
    question = shadow_adapter.inspect(_context(_source(), authority_columns=None))
    unsupported_source = _source(reader='rows = pandas.read_csv("inputs/data.csv")').replace(
        "import scipy.stats as st", "import scipy.stats as st\nimport pandas"
    )
    unsupported = shadow_adapter.inspect(_context(unsupported_source))
    for payload in (question, unsupported):
        _assert_not_candidate(payload)
    assert question["payload_type"] == "material_question"
    assert unsupported["payload_type"] == "abstention"


def test_core_exception_is_caught_as_named_abstention(
    shadow_adapter: DependenceRecognitionShadowAdapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_case: object) -> None:
        raise ValueError("injected core failure")

    monkeypatch.setattr(adapter_module, "evaluate_dependence_case", fail)
    payload = shadow_adapter.inspect(_context(_source()))
    _assert_not_candidate(payload)
    assert _coverage_classes(payload) == ("dependence-core-exception",)


def test_same_frozen_input_produces_byte_identical_payload_and_closure(
    shadow_adapter: DependenceRecognitionShadowAdapter,
) -> None:
    context = _context(_source())
    first = shadow_adapter.inspect(context)
    second = shadow_adapter.inspect(context)
    assert canonical_json(first).encode() == canonical_json(second).encode()
    assert first["implementation_dependency_closure_digest"] == (
        DEPENDENCE_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST
    )
    assert first["implementation_dependency_closure_digest"] == semantic_digest(
        {"dependency_closure": first["implementation_dependency_closure"]}
    )
    assert tuple(first["implementation_dependency_closure"]) == (
        DEPENDENCE_RECOGNITION_DEPENDENCY_FILES
    )
