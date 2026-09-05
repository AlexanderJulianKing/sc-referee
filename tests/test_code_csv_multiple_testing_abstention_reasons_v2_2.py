from __future__ import annotations

import ast
import inspect
import runpy
import textwrap
from pathlib import Path
from typing import Any, cast

import pytest

import sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v2_2 as adapter_module
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_2 as dataflow
from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v2_2 import _CLOSED_REASONS
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    InspectionDocument,
    RecordRef,
)
from sc_referee.scientific_checks.profiles import scientific_check_release_registry

_CHECK_ID = "check:authorized-complete-family-correction-over-code-test-battery"
_COLUMNS = ("m1", "m2", "m3")
_CSV = b"group,m1,m2,m3\na,1,2,3\na,2,3,4\nb,4,5,6\nb,5,6,7\n"
_X4_REASONS = (
    "helper-callee-not-simple-name",
    "helper-definition-unavailable-or-nonunique",
    "helper-parameter-shape-unsupported",
    "helper-parameter-default-unsupported",
    "helper-variadic-parameter-unsupported",
    "helper-argument-binding-unsupported",
    "helper-recursion-unsupported",
    "helper-return-count-unsupported",
    "helper-return-position-unsupported",
    "helper-return-expression-unsupported",
    "helper-global-nonlocal-unsupported",
    "helper-closure-or-nested-definition-unsupported",
    "helper-async-decorator-or-yield-unsupported",
    "helper-body-statement-unsupported",
    "helper-free-name-unbound",
    "helper-inlining-depth-exceeded",
    "helper-call-site-reentry-unsupported",
)
_DOCUMENTED_UNREACHABLE_REASONS = frozenset({"conclusion-output-sink-unavailable"})


def _source() -> str:
    return (
        "import pandas as pd\n"
        "from scipy import stats\n"
        'df = pd.read_csv("data.csv")\n'
        'r0 = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
        'df.loc[df["group"] == "b", "m1"])\n'
        'r1 = stats.ttest_ind(df.loc[df["group"] == "a", "m2"], '
        'df.loc[df["group"] == "b", "m2"])\n'
        'r2 = stats.ttest_ind(df.loc[df["group"] == "a", "m3"], '
        'df.loc[df["group"] == "b", "m3"])\n'
        "print(r0.pvalue < 0.05)\n"
        "print(r1.pvalue < 0.05)\n"
        "print(r2.pvalue < 0.05)\n"
    )


def _run(source: str) -> dataflow.MultipleTestingDataflowResult:
    return dataflow.analyze_code_csv_multiple_testing_dataflow(
        source.encode(),
        authorized_path="data.csv",
        group_column="group",
        outcome_columns=_COLUMNS,
        csv_header=("group", *_COLUMNS),
        group_values=("a", "b"),
        csv_content=_CSV,
    )


@pytest.mark.parametrize(
    ("source", "reason"),
    [
        ("print = lambda *values: None\n" + _source(), "api-resolution-ambiguous"),
        (
            _source() + 'second = pd.read_csv("data.csv")\n',
            "candidate",
        ),
        (
            _source().replace('pd.read_csv("data.csv")', 'pd.read_csv("other.csv")'),
            "additional-accepted-reader-present",
        ),
        (
            _source().replace(
                'r2 = stats.ttest_ind(df.loc[df["group"] == "a", "m3"], '
                'df.loc[df["group"] == "b", "m3"])\n',
                "",
            ),
            "authorized-family-test-census-incomplete",
        ),
        (
            _source().replace("r2 = stats.ttest_ind", "r2 = stats.mannwhitneyu"),
            "mixed-test-api-family",
        ),
        (
            _source().replace(
                'df.loc[df["group"] == "b", "m3"]',
                'df.loc[df["group"] == "b", "m2"]',
                1,
            ),
            "test-operand-lineage-unresolved",
        ),
        (
            _source()
            + "pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\n"
            + "member = 0\nprint(pvalues[member] < 0.05)\n",
            "pvalue-family-collection-unresolved",
        ),
    ],
)
def test_non_x4_dataflow_reasons_have_exact_first_reason(source: str, reason: str) -> None:
    result = _run(source)
    if reason == "candidate":
        assert result.reason is None
        assert result.facts is not None
    else:
        assert result.reason == reason


def test_dataflow_source_ceiling_has_exact_first_reason() -> None:
    source = _source() + "#" + "x" * (1 << 20)
    assert _run(source).reason == "dataflow-definition-ceiling-exceeded"


def test_localized_dataflow_exception_has_exact_first_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise ValueError("isolated inspection failure")

    monkeypatch.setattr(dataflow, "_mt_csv_rows", fail)
    assert _run(_source()).reason == "multiple-testing-code-inspection-exception"


def test_conclusion_sink_unavailable_is_a_documented_unreachable_invariant() -> None:
    source = textwrap.dedent(inspect.getsource(dataflow._MtEngine._conclusion_positions))
    assert "if not sink.p_result_eligible:\n            continue" in source
    assert "positions.update(local)\n            sink_kinds.add(sink.kind)" in source
    assert "positions.add(position)\n                sink_kinds.update(" in source
    assert _DOCUMENTED_UNREACHABLE_REASONS <= _CLOSED_REASONS


def _file_record(path: str, identifier: str) -> FrozenBaseRecord:
    return FrozenBaseRecord.from_record(
        RecordRef("file_record", identifier),
        {
            "record_type": "file_record",
            "file_record_id": identifier,
            "path": path,
            "entry_kind": "regular_file",
        },
    )


def _document(path: str, source: bytes, identifier: str) -> InspectionDocument:
    payload = canonical_json(
        {
            "parser_id": "parser:python-ast-tokenize",
            "parser_version": "0.15.1",
            "coverage_status": "covered",
            "source_ref": {"path": path, "content_digest": sha256_digest(source)},
        }
    ).encode()
    return InspectionDocument(
        path=path,
        file_ref=RecordRef("file_record", identifier),
        content=source,
        content_digest=sha256_digest(source),
        media_type="text/x-python",
        parser_result_ref=RecordRef("parser_result", f"parser-result:{identifier}"),
        parser_result_payload=payload,
        parser_result_digest=sha256_digest(payload),
    )


def test_source_envelope_reasons_have_exact_first_reason() -> None:
    assert (
        dataflow.select_code_source_envelope(base_records=(), documents=()).reason
        == "analysis-source-envelope-unavailable"
    )
    analysis_record = _file_record("analysis.py", "file:analysis")
    analysis = _document("analysis.py", _source().encode(), "file:analysis")
    alternate = dataflow.select_code_source_envelope(
        base_records=(analysis_record, _file_record("notebook.ipynb", "file:notebook")),
        documents=(analysis,),
    )
    assert alternate.reason == "alternate-analysis-file-present"
    other = dataflow.select_code_source_envelope(
        base_records=(analysis_record, _file_record("helper.py", "file:helper")),
        documents=(
            analysis,
            _document("helper.py", b"import scipy.stats\n", "file:helper"),
        ),
    )
    assert other.reason == "statistics-api-imported-outside-analysis-py"


class _ProsePayloadTripwire:
    def __init__(self, path: str) -> None:
        self.path = path

    @property
    def content(self) -> bytes:
        raise AssertionError("multiple-testing source envelope touched prose bytes")


def test_report_and_markdown_add_remove_is_invariant_for_every_guard_fixture() -> None:
    fixtures = runpy.run_path(
        "evaluation/development/multitest-code-slice-v2_1/ADVERSARY_FIXTURES.py"
    )["FIXTURES"]
    for fixture in fixtures.values():
        analysis_record = _file_record("analysis.py", "file:analysis")
        analysis = _document("analysis.py", fixture["source"].encode(), "file:analysis")
        absent = dataflow.select_code_source_envelope(
            base_records=(analysis_record,), documents=(analysis,)
        )
        present = dataflow.select_code_source_envelope(
            base_records=(
                analysis_record,
                _file_record("report.md", "file:report"),
                _file_record("notes.md", "file:notes"),
            ),
            documents=(
                analysis,
                cast(InspectionDocument, cast(Any, _ProsePayloadTripwire("report.md"))),
                cast(InspectionDocument, cast(Any, _ProsePayloadTripwire("notes.md"))),
            ),
        )
        assert absent.reason is None
        assert present.reason is None
        assert absent.analysis == present.analysis == analysis


def _minimal_context() -> FrozenInspectionContext:
    surface = RecordRef("publication_surface", "surface:multiple-testing-reason")
    artifact = RecordRef("artifact", "artifact:multiple-testing-reason")
    return FrozenInspectionContext(
        snapshot_digest=sha256_digest("multiple-testing-reason-snapshot"),
        selected_surface_ref=surface,
        selected_artifact_ref=artifact,
        documents=(),
        base_records=(
            FrozenBaseRecord.from_record(surface, {"publication_surface_id": surface.record_id}),
            FrozenBaseRecord.from_record(artifact, {"artifact_id": artifact.record_id}),
        ),
    )


def _adapter() -> adapter_module.CodeCsvMultipleTestingAdapter:
    registry = scientific_check_release_registry()
    module = next(
        item
        for item in registry.modules_for_lane("development")
        if item.manifest.check_id == _CHECK_ID
    )
    active = module.adapters[0]
    return adapter_module.CodeCsvMultipleTestingAdapter(
        check_manifest=active.check_manifest,
        adapter_manifest=active.adapter_manifest,
        complete_operand=active.complete_operand,
        none_operand=active.none_operand,
        strict_subset_operand=active.strict_subset_operand,
        role_bindings=adapter_module.MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    )


def test_verified_authority_unavailable_is_the_first_adapter_reason() -> None:
    observation = _adapter().inspect(_minimal_context())
    assert observation.abstention_reason == "verified-contract-authority-unavailable"


@pytest.mark.parametrize(
    "reason",
    [
        "authorized-test-family-shape-unsupported",
        "authorized-family-cardinality-below-three",
        "frozen-authority-material-mismatch",
    ],
)
def test_closed_authority_boundary_reasons_serialize_exactly(reason: str) -> None:
    observation = _adapter()._abstain("unsupported", reason)
    assert observation.abstention_reason == reason
    assert observation.receipts[0].description == reason


@pytest.mark.parametrize("reason", _X4_REASONS)
def test_every_x4_reason_projects_as_the_exact_first_reason(
    reason: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        dataflow,
        "_expand_relevant_helpers",
        lambda **kwargs: dataflow._Expansion(None, reason),
    )
    assert _run(_source()).reason == reason


def test_x4_fixture_matrix_equals_the_closed_helper_registry() -> None:
    assert frozenset(_X4_REASONS) == dataflow._MT_HELPER_REASONS


def test_fixture_emissions_plus_documented_unreachable_annex_equal_closed_reasons() -> None:
    observed: set[str] = set()
    for path in Path("tests").glob("*multiple_testing*v2_2.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        observed.update(
            str(node.value)
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and node.value in _CLOSED_REASONS
        )
    fixture_emissions = observed - _DOCUMENTED_UNREACHABLE_REASONS
    assert fixture_emissions == _CLOSED_REASONS - _DOCUMENTED_UNREACHABLE_REASONS
    assert fixture_emissions | _DOCUMENTED_UNREACHABLE_REASONS == _CLOSED_REASONS
