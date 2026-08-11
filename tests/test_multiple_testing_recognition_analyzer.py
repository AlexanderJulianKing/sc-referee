"""Adversarial tests for the Experiment-0059 Stage-3 static analyzer."""

from __future__ import annotations

import ast
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.multiple_testing_recognition.adapter import (
    MultipleTestingRecognitionShadowAdapter,
)
from sc_referee.multiple_testing_recognition.certificate import source_construct_token
from sc_referee.multiple_testing_recognition.ir import EvidencePoint
from sc_referee.multiple_testing_recognition.pvalue_domain import (
    pvalue_family_row_domain,
)
from sc_referee.multiple_testing_recognition.python_analyzer import (
    PythonMultipleTestingAnalysis,
    analyze_multiple_testing_python,
    discharge_multiple_testing_proposal,
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


def _source(
    *,
    correction_input: str = "pvals[:2]",
    correction: str = "statsmodels",
    reader: str | None = None,
    test_callable: str = "scipy.stats.ttest_ind",
    projection: str = 'genes = [row["gene"] for row in rows]',
    battery: str | None = None,
    before_reader: str = "",
    after_reader: str = "",
    measurement_reader: str | None = None,
    left_projection: str = (
        'x = {r["gene"]: (float(r["x1"]), float(r["x2"])) for r in measurement_rows}'
    ),
    right_projection: str = (
        'y = {s["gene"]: (float(s["y1"]), float(s["y2"])) for s in measurement_rows}'
    ),
    after_battery: str = "",
    include_correction: bool = True,
    include_report: bool = True,
) -> str:
    correction_import = (
        "from sc_referee.calculation_checks.bh import benjamini_hochberg"
        if correction == "repository"
        else "from statsmodels.stats.multitest import multipletests"
    )
    correction_call = (
        f"adjusted = benjamini_hochberg({correction_input})"
        if correction == "repository"
        else f'adjusted = multipletests({correction_input}, method="fdr_bh")'
    )
    reader = reader or (
        'rows = list(csv.DictReader(Path("results/tests.csv").read_text('
        'encoding="utf-8").splitlines()))'
    )
    measurement_reader = measurement_reader or (
        'measurement_rows = list(csv.DictReader(Path("inputs/measurements.csv").read_text('
        'encoding="utf-8").splitlines()))'
    )
    battery = battery or (f"pvals = [{test_callable}(x[g], y[g]).pvalue for g in genes]")
    statements = [
        "import csv",
        "import scipy.stats",
        "from pathlib import Path",
        correction_import,
        before_reader,
        reader,
        after_reader,
        projection,
        measurement_reader,
        left_projection,
        right_projection,
        battery,
        after_battery,
    ]
    if include_correction:
        statements.append(correction_call)
    if include_report:
        statements.extend(
            [
                "reported = tuple(zip(genes, pvals))",
                'Path("results/report.txt").write_text('
                'str((reported, adjusted)), encoding="utf-8")',
            ]
        )
    return "\n".join(item for item in statements if item) + "\n"


def _point(path: str, node: ast.AST) -> EvidencePoint:
    return EvidencePoint(
        path,
        node.lineno,
        node.end_lineno or node.lineno,
        node.col_offset + 1,
        (node.end_col_offset or node.col_offset) + 1,
    )


def _battery_id(source: str) -> str:
    tree = ast.parse(source)
    assignments = [item for item in tree.body if isinstance(item, ast.Assign)]
    batteries = [
        item
        for item in assignments
        if len(item.targets) == 1
        and isinstance(item.targets[0], ast.Name)
        and item.targets[0].id == "pvals"
    ]
    assert len(batteries) == 1
    source_bytes = source.encode()
    return source_construct_token(
        "battery-construct",
        sha256_digest(source_bytes),
        _point(_SOURCE_PATH, batteries[0]),
    )


def _context(
    source: str,
    *,
    data: bytes = _DATA,
    measurement_data: bytes = _MEASUREMENTS,
    authority: bool = True,
    second_authority: bool = False,
    authority_battery_id: str | None = None,
    authority_row_domain: str | None = None,
    authority_key_columns: tuple[str, ...] = ("gene",),
    authority_path: str = _DATA_PATH,
    authority_digest: str | None = None,
    authority_procedure_id: str = "procedure:correction",
    requirements: bytes = b"scipy==1.14.0\nstatsmodels==0.14.4\n",
    procedure_callable: str | None = None,
    include_procedure_callable: bool = True,
    second_document: bool = False,
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
    measurement_digest = sha256_digest(measurement_data)
    requirements_digest = sha256_digest(requirements)
    source_bytes = source.encode()
    resolved_procedure_callable = procedure_callable or (
        "statsmodels.stats.multitest.multipletests"
        if "multipletests(" in source
        else "sc_referee.calculation_checks.bh.benjamini_hochberg"
    )
    parser_payload = canonical_json(
        {"parser_id": "python-ast", "parser_version": "3.11", "state": "parsed"}
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
                **(
                    {"resolved_callable": resolved_procedure_callable}
                    if include_procedure_callable
                    else {}
                ),
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
        row_domain = authority_row_domain or pvalue_family_row_domain(
            _DATA_PATH,
            data_digest,
            "csv_newline" if '.open(encoding="utf-8", newline="")' in source else "splitlines",
        )
        records.append(
            (
                RecordRef("human_pvalue_family_authorization", "authorization:primary"),
                {
                    "record_type": "human_pvalue_family_authorization",
                    "record_id": "authorization:primary",
                    "actor_id": "human:family-owner",
                    "authority_state": "authorized",
                    "analysis_target_ref": analysis_ref.to_dict(),
                    "correction_procedure_ref": {
                        "record_type": "procedure",
                        "record_id": authority_procedure_id,
                    },
                    "family_definition_id": "family-definition:all-genes",
                    "battery_construct_id": authority_battery_id or _battery_id(source),
                    "iterable_row_domain": row_domain,
                    "authorized_family_key_columns": list(authority_key_columns),
                    "family_member_rule": "all_rows",
                    "family_input_path": authority_path,
                    "family_input_content_digest": authority_digest or data_digest,
                },
            )
        )
    if second_authority:
        first = next(
            value
            for ref, value in records
            if ref.record_type == "human_pvalue_family_authorization"
        )
        second = dict(first)
        second["record_id"] = "authorization:second"
        second["actor_id"] = "human:second-owner"
        records.append(
            (
                RecordRef("human_pvalue_family_authorization", "authorization:second"),
                second,
            )
        )

    documents = [
        InspectionDocument(
            path=_SOURCE_PATH,
            file_ref=analysis_file_ref,
            content=source_bytes,
            content_digest=sha256_digest(source_bytes),
            media_type="text/x-python",
            parser_result_ref=parser_ref,
            parser_result_payload=parser_payload,
            parser_result_digest=sha256_digest(parser_payload),
        )
    ]
    if second_document:
        other_ref = RecordRef("file_record", "file:other")
        other_parser = RecordRef("parser_result", "parser:other")
        documents.append(
            InspectionDocument(
                path="workflow/other.py",
                file_ref=other_ref,
                content=b"value = 1\n",
                content_digest=sha256_digest(b"value = 1\n"),
                media_type="text/x-python",
                parser_result_ref=other_parser,
                parser_result_payload=parser_payload,
                parser_result_digest=sha256_digest(parser_payload),
            )
        )
    return FrozenInspectionContext(
        snapshot_digest=sha256_digest(b"snapshot"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=tuple(documents),
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
                content=measurement_data,
                content_digest=measurement_digest,
            ),
        ),
    )


def _analyze(source: str, **context_kwargs: object) -> PythonMultipleTestingAnalysis:
    return analyze_multiple_testing_python(_context(source, **context_kwargs))


@pytest.mark.parametrize("correction_input", ["pvals[:2]", "pvals[1:]"])
def test_narrowing_slice_reaches_evaluation_candidate(correction_input: str) -> None:
    context = _context(_source(correction_input=correction_input))
    analysis = analyze_multiple_testing_python(context)
    discharged = discharge_multiple_testing_proposal(analysis, context)

    assert analysis.state == "proposal"
    assert discharged.state == "verified"
    assert discharged.outcome == "evaluation_candidate"
    assert discharged.verified_certificate is not None
    assert discharged.verified_certificate.conclusion == "correction_subset"
    assert discharged.verified_certificate.corrected_positions in {(0, 1), (1, 2)}


def test_regression_r1_value_predicate_filter_is_a_named_abstention() -> None:
    source = _source(correction_input="[p for p in pvals if p < 0.05]")
    context = _context(source)
    analysis = analyze_multiple_testing_python(context)
    discharged = discharge_multiple_testing_proposal(analysis, context)
    assert analysis.state == "unsupported"
    assert analysis.unsupported_constructs == ("value-predicate-correction-unsupported",)
    assert discharged.outcome == "unsupported"
    assert discharged.verified_certificate is None


def test_exact_full_battery_correction_reaches_covered_negative() -> None:
    source = _source(correction_input="pvals")
    context = _context(source)
    discharged = discharge_multiple_testing_proposal(
        analyze_multiple_testing_python(context), context
    )
    assert discharged.state == "verified"
    assert discharged.outcome == "covered_negative"
    assert discharged.verified_certificate is not None
    assert discharged.verified_certificate.conclusion == "complete_family_correction"
    assert discharged.verified_certificate.corrected_positions == (0, 1, 2)


def test_statsmodels_registry_entry_is_statically_verified_without_execution() -> None:
    source = _source(correction="statsmodels", correction_input="pvals[:2]")
    context = _context(
        source,
        requirements=b"scipy==1.14.0\nstatsmodels==0.14.4\n",
        procedure_callable="statsmodels.stats.multitest.multipletests",
    )
    discharged = discharge_multiple_testing_proposal(
        analyze_multiple_testing_python(context), context
    )
    assert discharged.outcome == "evaluation_candidate"
    assert discharged.verified_certificate is not None
    assert discharged.certificate is not None
    assert discharged.certificate.correction_calls[0].resolved_callable.endswith(".multipletests")


def test_regression_r7_procedure_record_must_declare_resolved_callable() -> None:
    analysis = _analyze(_source(), include_procedure_callable=False)
    assert analysis.state == "unsupported"
    assert analysis.unsupported_constructs == ("correction-procedure-binding-unverified",)
    assert analysis.certificate is None


@pytest.mark.parametrize(
    ("test_callable", "correction_input", "raw_pvalue", "payload_type"),
    [
        ("scipy.stats.mannwhitneyu", "pvals[:2]", "0.4142161782425251", "shadow_candidate"),
        ("scipy.stats.mannwhitneyu", "pvals", "0.4142161782425251", "coverage_note"),
        ("scipy.stats.ttest_ind", "pvals", "0.29289321881345254", "coverage_note"),
    ],
)
def test_regression_r4_executable_keyed_arguments_execute_and_are_recognized(
    tmp_path: Path,
    test_callable: str,
    correction_input: str,
    raw_pvalue: str,
    payload_type: str,
) -> None:
    runtime = Path(
        "/Users/alexanderking/Desktop/random_stuff/"
        "sc-referee-pilot-runtime/scipy114-venv/bin/python"
    )
    assert runtime.is_file(), "the mandatory multiple-testing sandbox runtime is absent"
    probe = subprocess.run(
        [
            str(runtime),
            "-I",
            "-c",
            (
                "import importlib.metadata as m, scipy, statsmodels; "
                "print(scipy.__version__, m.version('statsmodels'), statsmodels.__version__)"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert probe.returncode == 0, probe.stderr
    assert probe.stdout.strip() == "1.14.0 0.14.4 0.14.4"

    source = _source(
        correction_input=correction_input,
        test_callable=test_callable,
    )
    family_data = (
        "gene,pvalue\n" + "\n".join(f"g{index},{raw_pvalue}" for index in range(1, 4)) + "\n"
    ).encode()
    (tmp_path / "workflow").mkdir()
    (tmp_path / "results").mkdir()
    (tmp_path / "inputs").mkdir()
    (tmp_path / _SOURCE_PATH).write_text(source, encoding="utf-8")
    (tmp_path / _DATA_PATH).write_bytes(family_data)
    (tmp_path / _MEASUREMENT_PATH).write_bytes(_MEASUREMENTS)
    reports: list[bytes] = []
    for _ in range(2):
        report_path = tmp_path / _REPORT_PATH
        report_path.unlink(missing_ok=True)
        run = subprocess.run(
            [str(runtime), "-I", _SOURCE_PATH],
            cwd=tmp_path,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert run.returncode == 0, run.stderr
        assert run.stderr == ""
        reports.append(report_path.read_bytes())
    assert reports[0] == reports[1]
    assert raw_pvalue.encode() in reports[0]

    context = _context(source, data=family_data)
    payload = MultipleTestingRecognitionShadowAdapter().inspect(context)
    assert payload["payload_type"] == payload_type
    assert payload["outcome"] == (
        "evaluation_candidate" if payload_type == "shadow_candidate" else "covered_negative"
    )


def test_csv_newline_reader_model_reaches_kernel() -> None:
    reader = (
        'rows = list(csv.DictReader(Path("results/tests.csv").open(encoding="utf-8", newline="")))'
    )
    source = _source(reader=reader)
    context = _context(source)
    discharged = discharge_multiple_testing_proposal(
        analyze_multiple_testing_python(context), context
    )
    assert discharged.state == "verified"
    assert discharged.verified_certificate is not None
    assert discharged.verified_certificate.family_fact.line_model == "csv_newline"


@pytest.mark.parametrize(
    ("context_kwargs", "dimension"),
    [
        ({"authority": False}, "family-definition-unauthorized"),
        ({"authority_battery_id": "battery-construct:wrong"}, "family-definition-unauthorized"),
        ({"authority_key_columns": ("study",)}, "family-definition-unauthorized"),
        ({"second_authority": True}, "family-definition-unauthorized"),
    ],
)
def test_missing_mismatched_or_conflicting_authority_is_a_question(
    context_kwargs: dict[str, object], dimension: str
) -> None:
    analysis = _analyze(_source(), **context_kwargs)
    assert analysis.state == "question"
    assert analysis.certificate is None
    assert dimension in analysis.unresolved_dimensions
    assert analysis.outcome != "evaluation_candidate"


def test_multiple_candidate_key_columns_are_named_without_ranking() -> None:
    data = b"gene,study,pvalue\ng1,s1,0.01\ng2,s2,0.04\ng3,s3,0.20\n"
    measurements = (
        b"gene,study,x1,x2,y1,y2\n"
        b"g1,s1,1.0,2.0,2.0,3.0\n"
        b"g2,s2,2.0,3.0,3.0,4.0\n"
        b"g3,s3,3.0,4.0,4.0,5.0\n"
    )
    source = _source(
        projection='genes = [(row["gene"], row["study"]) for row in rows]',
        left_projection=(
            'x = {(r["gene"], r["study"]): '
            '(float(r["x1"]), float(r["x2"])) for r in measurement_rows}'
        ),
        right_projection=(
            'y = {(s["gene"], s["study"]): '
            '(float(s["y1"]), float(s["y2"])) for s in measurement_rows}'
        ),
    )
    analysis = _analyze(
        source,
        data=data,
        measurement_data=measurements,
        authority=False,
    )
    assert analysis.state == "question"
    assert analysis.candidate_family_key_columns == ("gene", "study")
    assert analysis.unresolved_dimensions == (
        "family-definition-unauthorized",
        "candidate_family_key:gene",
        "candidate_family_key:study",
    )


def test_absent_correction_is_the_named_cross_module_gap() -> None:
    analysis = _analyze(_source(include_correction=False))
    assert analysis.state == "unsupported"
    assert analysis.unsupported_constructs == ("cross-module-correction-unverified",)
    assert analysis.effects
    assert analysis.outcome != "evaluation_candidate"


def test_hand_typed_family_without_registered_battery_is_named_gap() -> None:
    source = _source(battery="pvals = [0.01, 0.04, 0.20]")
    analysis = _analyze(source)
    assert analysis.state == "unsupported"
    assert analysis.unsupported_constructs == ("hand-typed-correction-family-unbound",)


@pytest.mark.parametrize(
    "injected",
    [
        "def helper(value):\n    return value",
        "def wrapper(left, right):\n    return scipy.stats.ttest_ind(left, right)",
        "rows.append({})",
        "rows[0] = rows[1]",
        "for row in rows:\n    rows = rows",
        "while rows:\n    break",
        "changed = (copy := rows)",
        "try:\n    rows = rows\nexcept Exception:\n    rows = []",
        "if False:\n    rows = []",
    ],
)
def test_helpers_mutations_walrus_loops_try_and_dead_code_abstain(
    injected: str,
) -> None:
    analysis = _analyze(_source(after_reader=injected))
    assert analysis.state == "unsupported"
    assert analysis.certificate is None
    assert analysis.effects
    assert all(effect.opaque and effect.writes == frozenset({"*"}) for effect in analysis.effects)


def test_loop_built_battery_uses_the_reserved_named_gap() -> None:
    analysis = _analyze(_source(after_reader="for row in rows:\n    rows = rows"))
    assert analysis.unsupported_constructs == ("loop-built-test-battery-unrecognized",)


@pytest.mark.parametrize(
    "injected",
    [
        "import os",
        "import os\nos.system('echo forbidden')",
        "dynamic = __import__('scipy')",
        "exec('value = 1')",
    ],
)
def test_dynamic_import_execution_and_system_routes_abstain(injected: str) -> None:
    analysis = _analyze(_source(before_reader=injected))
    assert analysis.state == "unsupported"
    assert analysis.certificate is None
    assert analysis.effects


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("import scipy.stats", "import scipy.stats as st"),
        (
            "from statsmodels.stats.multitest import multipletests",
            "from statsmodels.stats.multitest import multipletests as mt",
        ),
        ("import scipy.stats", "from scipy import stats"),
        (
            "from statsmodels.stats.multitest import multipletests",
            "from statsmodels.stats.multitest import multipletests\n"
            "from statsmodels.stats.multitest import multipletests",
        ),
    ],
)
def test_aliased_rebound_or_duplicate_imports_abstain(old: str, new: str) -> None:
    source = _source().replace(old, new)
    analysis = _analyze(source)
    assert analysis.state == "unsupported"
    assert analysis.outcome != "evaluation_candidate"


@pytest.mark.parametrize(
    "injected",
    [
        "test = scipy.stats.ttest_ind",
        "scipy = csv",
        "benjamini_hochberg = scipy.stats.ttest_ind",
    ],
)
def test_callable_aliasing_and_rebinding_abstain(injected: str) -> None:
    analysis = _analyze(_source(after_reader=injected))
    assert analysis.state == "unsupported"


def test_wrapper_call_is_not_a_registered_live_callable() -> None:
    source = _source(
        before_reader="def wrapper(left, right):\n    return scipy.stats.ttest_ind(left, right)",
        test_callable="wrapper",
    )
    assert _analyze(source).state == "unsupported"


def test_conflicting_batteries_and_corrections_do_not_resolve_one() -> None:
    second_battery = "other = [scipy.stats.mannwhitneyu(x[g], y[g]).pvalue for g in genes]"
    batteries = _analyze(_source(after_battery=second_battery))
    second_correction = "other_adjusted = benjamini_hochberg(pvals[:1])"
    corrections = _analyze(_source(after_battery=second_correction))
    assert batteries.state == "question"
    assert batteries.unresolved_dimensions == ("conflicting-batteries",)
    assert corrections.state == "question"
    assert corrections.unresolved_dimensions == ("conflicting-corrections",)


def test_multiple_python_documents_are_a_question() -> None:
    analysis = _analyze(_source(), second_document=True)
    assert analysis.state == "question"
    assert analysis.unresolved_dimensions == ("multiple-python-lineages",)


def test_no_registered_battery_is_not_applicable_end_to_end() -> None:
    context = _context("value = 1\n", authority=False)
    analysis = analyze_multiple_testing_python(context)
    discharged = discharge_multiple_testing_proposal(analysis, context)
    assert analysis.state == "not_applicable"
    assert discharged.state == "not_applicable"
    assert discharged.outcome == "not_applicable"


def test_second_registered_test_callable_reaches_the_same_static_route() -> None:
    source = _source(test_callable="scipy.stats.mannwhitneyu")
    context = _context(source)
    discharged = discharge_multiple_testing_proposal(
        analyze_multiple_testing_python(context), context
    )
    assert discharged.outcome == "evaluation_candidate"
    assert discharged.certificate is not None
    assert (
        discharged.certificate.test_batteries[0].resolved_test_callable
        == "scipy.stats.mannwhitneyu"
    )


@pytest.mark.parametrize(
    "requirements",
    [
        b"",
        b"scipy>=1.14.0\n",
        b"scipy==1.13.0\n",
        b"scipy==1.14.0\nscipy==1.14.0\n",
    ],
)
def test_scipy_must_have_one_exact_supported_pin(requirements: bytes) -> None:
    analysis = _analyze(_source(), requirements=requirements)
    assert analysis.state == "unsupported"
    assert analysis.unsupported_constructs == ("unsupported-or-unpinned-scipy-version",)


@pytest.mark.parametrize(
    "requirements",
    [
        b"scipy==1.14.0\n",
        b"scipy==1.14.0\nstatsmodels>=0.14.4\n",
        b"scipy==1.14.0\nstatsmodels==0.14.3\n",
    ],
)
def test_statsmodels_requires_exact_supported_pin(requirements: bytes) -> None:
    source = _source(correction="statsmodels")
    analysis = _analyze(source, requirements=requirements)
    assert analysis.state == "unsupported"
    assert analysis.unsupported_constructs == ("unsupported-or-unpinned-statsmodels-version",)


@pytest.mark.parametrize(
    "correction_input",
    [
        "pvals[:]",
        "pvals[:3]",
        "pvals[:0]",
        "pvals[::2]",
        "pvals[-1:]",
        "pvals[n:]",
        "[p for p in pvals if p <= 0.05]",
        "[p for p in pvals if p < threshold]",
        "[p for p in pvals if p < 5e-2]",
        "[p for p in pvals if p < 0.00]",
        "selected",
    ],
)
def test_all_other_correction_input_shapes_abstain(correction_input: str) -> None:
    analysis = _analyze(_source(correction_input=correction_input))
    if analysis.state == "proposal":
        context = _context(_source(correction_input=correction_input))
        discharged = discharge_multiple_testing_proposal(analysis, context)
        assert discharged.outcome == "unsupported"
    else:
        assert analysis.state == "unsupported"
    assert analysis.outcome != "evaluation_candidate"


@pytest.mark.parametrize(
    "projection",
    [
        'genes = [row["gene"] for row in rows if row["gene"]]',
        'genes = [row["gene"].strip() for row in rows]',
        'genes = [row["gene"] for row in list(rows)]',
        'genes = [row["gene"] for row in rows]\nrows = rows[1:]',
    ],
)
def test_filtered_transformed_or_mutated_family_projection_abstains(
    projection: str,
) -> None:
    analysis = _analyze(_source(projection=projection))
    assert analysis.state == "unsupported"
    assert analysis.outcome != "evaluation_candidate"


@pytest.mark.parametrize(
    "battery",
    [
        "pvals = [scipy.stats.ttest_ind(x[g], y[g]).pvalue for g in genes if g]",
        "pvals = [scipy.stats.ttest_ind(x[g], y[g]).pvalue for g in list(genes)]",
        "pvals = [scipy.stats.ttest_ind(x[g], x[g]).pvalue for g in genes]",
        "pvals = [scipy.stats.ttest_ind(x[g], y[g]).pvalue for g, h in genes]",
        "pvals = list(map(test, genes))",
    ],
)
def test_nonexact_battery_shapes_abstain(battery: str) -> None:
    analysis = _analyze(_source(battery=battery))
    assert analysis.state in {"not_applicable", "unsupported"}
    assert analysis.outcome != "evaluation_candidate"


def test_controller_revalidates_frozen_authority_and_source() -> None:
    source = _source()
    context = _context(source)
    analysis = analyze_multiple_testing_python(context)
    assert analysis.state == "proposal"

    missing_authority = discharge_multiple_testing_proposal(
        analysis, _context(source, authority=False)
    )
    changed_source = _source(correction_input="pvals[:1]")
    changed_context = _context(changed_source)
    source_drift = discharge_multiple_testing_proposal(analysis, changed_context)
    assert missing_authority.state == "unsupported"
    assert source_drift.state == "unsupported"
    assert missing_authority.verified_certificate is None
    assert source_drift.verified_certificate is None


def test_controller_and_kernel_refuse_proposal_field_forgery() -> None:
    source = _source()
    context = _context(source)
    analysis = analyze_multiple_testing_python(context)
    assert analysis.certificate is not None
    forged = replace(
        analysis,
        certificate=replace(
            analysis.certificate,
            dependency_closure_digest="sha256:" + "0" * 64,
        ),
    )
    discharged = discharge_multiple_testing_proposal(forged, context)
    assert discharged.state == "unsupported"
    assert discharged.verified_certificate is None


def test_digest_bound_prover_failure_never_becomes_candidate() -> None:
    source = _source()
    context = _context(source, data=b"gene,pvalue\ng1,0.01\ng1,0.02\n")
    analysis = analyze_multiple_testing_python(context)
    discharged = discharge_multiple_testing_proposal(analysis, context)
    assert analysis.state == "proposal"
    assert discharged.state == "unsupported"
    assert discharged.outcome != "evaluation_candidate"


def test_parser_failure_is_localized_to_abstention() -> None:
    context = _context(_source())
    document = replace(
        context.documents[0],
        content=b"if (",
        content_digest=sha256_digest(b"if ("),
        source_location=None,
    )
    analysis = analyze_multiple_testing_python(replace(context, documents=(document,)))
    assert analysis.state == "unsupported"
    assert analysis.certificate is None


def test_every_nonadverse_end_to_end_case_is_not_a_candidate() -> None:
    cases = (
        _context(_source(correction_input="pvals")),
        _context(_source(), authority=False),
        _context(_source(include_correction=False)),
        _context(_source(), requirements=b"scipy>=1.14.0\n"),
    )
    outcomes = []
    for context in cases:
        analysis = analyze_multiple_testing_python(context)
        outcomes.append(discharge_multiple_testing_proposal(analysis, context).outcome)
    assert outcomes == ["covered_negative", "question", "unsupported", "unsupported"]


def test_repository_bh_executable_type_binding_is_a_named_abstention() -> None:
    analysis = _analyze(_source(correction="repository"))
    assert analysis.state == "unsupported"
    assert analysis.unsupported_constructs == ("repository-bh-runtime-type-binding-unverified",)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (
            "for r in measurement_rows}",
            "for r in measurement_rows if r}",
        ),
        (
            'float(s["y1"])',
            'float(s["x1"])',
        ),
        (
            "scipy.stats.ttest_ind(x[g], y[g])",
            "scipy.stats.ttest_ind(y[g], x[g])",
        ),
    ],
)
def test_executable_argument_projection_attacks_abstain(old: str, new: str) -> None:
    analysis = _analyze(_source().replace(old, new, 1))
    assert analysis.state == "unsupported"
    assert analysis.outcome != "evaluation_candidate"


def test_second_measurement_reader_is_an_unmodeled_live_subtree() -> None:
    source = _source(after_battery="other_rows = measurement_rows")
    analysis = _analyze(source)
    assert analysis.state == "unsupported"
    assert analysis.unsupported_constructs == ("unmodeled-live-subtree",)


def test_argument_assignment_cannot_shadow_an_import_binding() -> None:
    source = (
        _source()
        .replace(
            'x = {r["gene"]:',
            'csv = {r["gene"]:',
        )
        .replace("ttest_ind(x[g], y[g])", "ttest_ind(csv[g], y[g])")
    )
    context = _context(source)
    discharged = discharge_multiple_testing_proposal(
        analyze_multiple_testing_python(context),
        context,
    )
    assert discharged.outcome == "unsupported"
    assert discharged.verified_certificate is None


@pytest.mark.parametrize(
    "measurement_data",
    [
        _MEASUREMENTS.replace(b"g3,3.0", b"other,3.0"),
        _MEASUREMENTS.replace(b"g3,3.0,4.0,4.0,5.0\n", b"g1,3.0,4.0,4.0,5.0\n"),
        _MEASUREMENTS.replace(b"g3,3.0", b"g3,1e0"),
        _MEASUREMENTS.replace(b"gene,x1,x2,y1,y2", b"gene,x1,x2,y1,y2,note"),
    ],
)
def test_controller_measurement_proof_failures_never_become_candidates(
    measurement_data: bytes,
) -> None:
    context = _context(_source(), measurement_data=measurement_data)
    discharged = discharge_multiple_testing_proposal(
        analyze_multiple_testing_python(context),
        context,
    )
    assert discharged.outcome == "unsupported"
    assert discharged.verified_certificate is None
