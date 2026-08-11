"""Hand-built obligation, mutation, and M3 attack tests for Experiment 0059."""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass, fields, replace
from decimal import Decimal
from typing import Any, cast

import pytest

from sc_referee.calculation_checks.bh import benjamini_hochberg
from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.multiple_testing_recognition import certificate as certificate_module
from sc_referee.multiple_testing_recognition.certificate import (
    family_hypothesis_token,
    family_observation_token,
    family_pvalue_token,
    multiple_testing_case_digest,
    multiple_testing_replay_digest,
    source_construct_token,
    verify_multiple_testing_certificate,
)
from sc_referee.multiple_testing_recognition.ir import (
    REQUIRED_SCOPE_BASES,
    CorrectionCall,
    EvidenceDeclaration,
    EvidencePoint,
    FamilyAuthorization,
    FamilyDomainObligation,
    FamilyScopeCheckObligation,
    FullFamilyProjectionObligation,
    MaterialInputBinding,
    MultipleTestingCaseBinding,
    MultipleTestingCertificate,
    PValueFamilyFact,
    RecordRef,
    ReportFamilyBinding,
    TestArgumentDomainFact,
    TestArgumentDomainObligation,
    TestBatteryObligation,
)
from sc_referee.scientific_checks.founder_orientation_semantic_ir import Effect, Unknown

_SOURCE_PATH = "workflow/analysis.py"
_DATA_PATH = "results/tests.csv"
_DATA_DIGEST = "sha256:" + "2" * 64
_MEASUREMENT_PATH = "inputs/measurements.csv"
_MEASUREMENT_DIGEST = "sha256:" + "4" * 64
_CLOSURE_DIGEST = "sha256:" + "3" * 64
_DEFAULT_SOURCE = """import csv
import scipy.stats
from pathlib import Path
from statsmodels.stats.multitest import multipletests
rows = list(csv.DictReader(Path("results/tests.csv").open(encoding="utf-8", newline="")))
genes = [row[\"gene\"] for row in rows]
measurement_rows = list(csv.DictReader(Path("inputs/measurements.csv").open(encoding="utf-8", newline="")))
x = {r[\"gene\"]: (float(r[\"x1\"]), float(r[\"x2\"])) for r in measurement_rows}
y = {s[\"gene\"]: (float(s[\"y1\"]), float(s[\"y2\"])) for s in measurement_rows}
pvals = [scipy.stats.ttest_ind(x[g], y[g]).pvalue for g in genes]
adjusted = multipletests(pvals[:2], method="fdr_bh")
reported = tuple(zip(genes, pvals))
Path(\"results/report.txt\").write_text(str((reported, adjusted)), encoding=\"utf-8\")
"""


@dataclass(frozen=True)
class _Fixture:
    certificate: MultipleTestingCertificate
    frozen_source_bytes: bytes
    trusted_facts: tuple[PValueFamilyFact, ...]
    trusted_argument_facts: tuple[TestArgumentDomainFact, ...]
    trusted_authorizations: tuple[FamilyAuthorization, ...]


def _span(node: ast.expr | ast.stmt) -> EvidencePoint:
    return EvidencePoint(
        path=_SOURCE_PATH,
        start_line=node.lineno,
        end_line=cast(int, node.end_lineno),
        start_column=node.col_offset + 1,
        end_column=cast(int, node.end_col_offset) + 1,
    )


def _target_assignment(tree: ast.Module, name: str) -> ast.Assign:
    matches = [
        statement
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == name
    ]
    assert len(matches) == 1
    return matches[0]


def _source_extent(source: str) -> EvidencePoint:
    lines = source.splitlines()
    return EvidencePoint(_SOURCE_PATH, 1, len(lines), 1, len(lines[-1]) + 1)


def _canonical(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _source_token(kind: str, digest: str, node: ast.expr | ast.stmt) -> str:
    return source_construct_token(kind, digest, _span(node))


def _fact(
    *,
    key_columns: tuple[str, ...] = ("gene",),
    key_values: tuple[tuple[str, ...], ...] = (("g1",), ("g2",), ("g3",)),
    raw_values: tuple[str, ...] = ("0.01", "0.04", "0.20"),
) -> PValueFamilyFact:
    row_domain = "family-rows:all"
    observations = tuple(
        family_observation_token(_DATA_PATH, _DATA_DIGEST, row_domain, index + 1)
        for index in range(len(key_values))
    )
    hypotheses = tuple(family_hypothesis_token(key_columns, values) for values in key_values)
    pvalue_tokens = tuple(
        family_pvalue_token(row_domain, index, hypothesis, "pvalue")
        for index, hypothesis in enumerate(hypotheses)
    )
    canonical = tuple(_canonical(Decimal(value)) for value in raw_values)
    return PValueFamilyFact(
        evidence_id="evidence:family-domain",
        path=_DATA_PATH,
        content_digest=_DATA_DIGEST,
        file_ref=RecordRef("file_record", "file:results/tests.csv"),
        asset_identity_ref=RecordRef("asset_identity", "asset:results/tests.csv@sha256"),
        reader_form="csv_dictreader_file",
        line_model="csv_newline",
        splitlines_only_separators_absent=True,
        dialect="excel",
        row_domain=row_domain,
        source_byte_count=128,
        header=(*key_columns, "pvalue"),
        hypothesis_key_columns=key_columns,
        pvalue_column="pvalue",
        normalization="byte_exact_utf8",
        declared_missing_value_tokens=("NA",),
        missing_key_value_count=0,
        missing_pvalue_count=0,
        row_shape_complete=True,
        row_count=len(key_values),
        observation_tokens=observations,
        key_value_tuples=key_values,
        hypothesis_tokens=hypotheses,
        raw_pvalue_lexemes=raw_values,
        canonical_pvalue_decimals=canonical,
        pvalue_tokens=pvalue_tokens,
    )


def _argument_fact(
    *,
    key_values: tuple[tuple[str, ...], ...] = (("g2",), ("g1",), ("g3",)),
) -> TestArgumentDomainFact:
    key_columns = ("gene",)
    row_domain = "test-argument-rows:all"
    hypotheses = tuple(family_hypothesis_token(key_columns, values) for values in key_values)
    observations = tuple(
        "test-argument-observation:"
        + semantic_digest(
            {
                "schema": "test-argument-observation-v1",
                "path": _MEASUREMENT_PATH,
                "content_digest": _MEASUREMENT_DIGEST,
                "row_domain": row_domain,
                "row_ordinal": index + 1,
            }
        )
        for index in range(len(key_values))
    )
    left_raw = tuple((f"{index}.0", f"{index + 1}.0") for index in range(1, 4))
    right_raw = tuple((f"{index + 1}.0", f"{index + 2}.0") for index in range(1, 4))
    return TestArgumentDomainFact(
        evidence_id="evidence:test-argument-domain",
        path=_MEASUREMENT_PATH,
        content_digest=_MEASUREMENT_DIGEST,
        file_ref=RecordRef("file_record", "file:inputs/measurements.csv"),
        asset_identity_ref=RecordRef("asset_identity", "asset:inputs/measurements.csv@sha256"),
        reader_form="csv_dictreader_file",
        line_model="csv_newline",
        splitlines_only_separators_absent=True,
        dialect="excel",
        row_domain=row_domain,
        source_byte_count=192,
        header=("gene", "x1", "x2", "y1", "y2"),
        measurement_key_columns=key_columns,
        left_measurement_columns=("x1", "x2"),
        right_measurement_columns=("y1", "y2"),
        normalization="byte_exact_utf8",
        declared_missing_value_tokens=(),
        missing_key_value_count=0,
        missing_measurement_value_count=0,
        row_shape_complete=True,
        row_count=len(key_values),
        observation_tokens=observations,
        key_value_tuples=key_values,
        hypothesis_tokens=hypotheses,
        left_raw_measurement_lexemes=left_raw,
        right_raw_measurement_lexemes=right_raw,
        left_binary64_hex=tuple(tuple(float(value).hex() for value in row) for row in left_raw),
        right_binary64_hex=tuple(tuple(float(value).hex() for value in row) for row in right_raw),
    )


def _fixture(
    source: str = _DEFAULT_SOURCE,
    *,
    fact: PValueFamilyFact | None = None,
) -> _Fixture:
    domain_fact = fact or _fact()
    argument_fact = _argument_fact()
    source_bytes = source.encode("utf-8")
    source_digest = sha256_digest(source_bytes)
    tree = ast.parse(source, feature_version=(3, 11))
    reader_assign = _target_assignment(tree, "rows")
    projection_assign = _target_assignment(tree, "genes")
    measurement_reader_assign = _target_assignment(tree, "measurement_rows")
    left_projection_assign = _target_assignment(tree, "x")
    right_projection_assign = _target_assignment(tree, "y")
    battery_assign = _target_assignment(tree, "pvals")
    correction_assign = _target_assignment(tree, "adjusted")
    report_assign = _target_assignment(tree, "reported")
    sink = next(
        statement
        for statement in tree.body
        if isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Attribute)
        and statement.value.func.attr == "write_text"
    )
    assert isinstance(projection_assign.value, ast.ListComp)
    assert isinstance(left_projection_assign.value, ast.DictComp)
    assert isinstance(right_projection_assign.value, ast.DictComp)
    assert isinstance(battery_assign.value, ast.ListComp)
    battery_element = battery_assign.value.elt
    call = (
        battery_element.value
        if isinstance(battery_element, ast.Attribute)
        and isinstance(battery_element.value, ast.Call)
        else next(node for node in ast.walk(battery_element) if isinstance(node, ast.Call))
    )
    correction_call = next(
        node for node in ast.walk(correction_assign.value) if isinstance(node, ast.Call)
    )
    battery_id = _source_token("battery-construct", source_digest, battery_assign)
    projection = FullFamilyProjectionObligation(
        battery_construct_id=battery_id,
        iterable_row_domain=domain_fact.row_domain,
        source_rows_name="rows",
        projected_family_name="genes",
        hypothesis_key_columns=domain_fact.hypothesis_key_columns,
        assignment_span=_span(projection_assign),
        listcomp_span=_span(projection_assign.value),
        element_span=_span(projection_assign.value.elt),
        evidence_ids=(
            "evidence:projection-assignment",
            "evidence:projection-listcomp",
            "evidence:projection-element",
        ),
    )
    battery = TestBatteryObligation(
        battery_construct_id=battery_id,
        iterable_row_domain=domain_fact.row_domain,
        battery_result_name="pvals",
        projected_family_name="genes",
        resolved_test_callable="scipy.stats.ttest_ind",
        assignment_span=_span(battery_assign),
        listcomp_span=_span(battery_assign.value),
        element_call_span=_span(call),
        iterable_span=_span(battery_assign.value.generators[0].iter),
        evidence_ids=(
            "evidence:battery-assignment",
            "evidence:battery-listcomp",
            "evidence:battery-call",
            "evidence:battery-iterable",
        ),
    )
    correction_input = correction_call.args[0]
    if isinstance(correction_input, ast.Name) and correction_input.id == "pvals":
        selected = tuple(range(domain_fact.row_count))
    elif isinstance(correction_input, ast.Subscript) and isinstance(
        correction_input.slice, ast.Slice
    ):
        lower_node = correction_input.slice.lower
        upper_node = correction_input.slice.upper
        lower = (
            lower_node.value
            if isinstance(lower_node, ast.Constant)
            and isinstance(lower_node.value, int)
            and not isinstance(lower_node.value, bool)
            else None
        )
        upper = (
            upper_node.value
            if isinstance(upper_node, ast.Constant)
            and isinstance(upper_node.value, int)
            and not isinstance(upper_node.value, bool)
            else None
        )
        selected = tuple(range(domain_fact.row_count)[slice(lower, upper)])
    else:
        selected = ()
    adjusted = (
        tuple(
            _canonical(value)
            for value in benjamini_hochberg(
                tuple(Decimal(domain_fact.raw_pvalue_lexemes[index]) for index in selected)
            )
        )
        if selected
        else ("0",)
    )
    correction = CorrectionCall(
        battery_construct_id=battery_id,
        iterable_row_domain=domain_fact.row_domain,
        correction_procedure_ref=RecordRef("procedure", "procedure:bh"),
        resolved_callable="statsmodels.stats.multitest.multipletests",
        result_name="adjusted",
        call_span=_span(correction_call),
        asserted_adjusted_pvalues=adjusted,
        asserts_trusted_bh_recomputation=True,
        evidence_ids=("evidence:correction",),
    )
    element_token = _source_token("test-call-template", source_digest, call)
    scope = FamilyScopeCheckObligation(
        battery_construct_id=battery_id,
        iterable_row_domain=domain_fact.row_domain,
        complete_test_call_tokens=frozenset({element_token}),
        modeled_test_call_tokens=frozenset({element_token}),
        proven_dead_test_call_tokens=frozenset(),
        corrected_test_call_tokens=frozenset({element_token}),
        bases=REQUIRED_SCOPE_BASES,
        evidence_ids=("evidence:scope",),
    )
    reader_token = _source_token("family-domain-reader", source_digest, reader_assign)
    projection_token = _source_token("full-family-projection", source_digest, projection_assign)
    measurement_reader_token = _source_token(
        "test-argument-domain-reader", source_digest, measurement_reader_assign
    )
    left_projection_token = _source_token(
        "left-test-argument-projection", source_digest, left_projection_assign
    )
    right_projection_token = _source_token(
        "right-test-argument-projection", source_digest, right_projection_assign
    )
    correction_token = _source_token("correction-call", source_digest, correction_call)
    report_token = _source_token("reported-family-binding", source_digest, report_assign)
    sink_token = _source_token("selected-report-sink", source_digest, sink)
    report = ReportFamilyBinding(
        token=sink_token,
        path="results/report.txt",
        affected_target_ref=RecordRef("result", "result:multiple-testing"),
        iterable_row_domain=domain_fact.row_domain,
        hypothesis_key_columns=domain_fact.hypothesis_key_columns,
        pvalue_column=domain_fact.pvalue_column,
        reported_name="reported",
        assignment_span=_span(report_assign),
        sink_span=_span(sink),
        selected_result=True,
        evidence_ids=("evidence:report-binding", "evidence:sink"),
        relevant_origins=frozenset(
            {
                _SOURCE_PATH,
                _DATA_PATH,
                domain_fact.row_domain,
                _MEASUREMENT_PATH,
                argument_fact.row_domain,
                "results/report.txt",
            }
        ),
        relevant_bindings=frozenset(
            {
                reader_token,
                projection_token,
                measurement_reader_token,
                left_projection_token,
                right_projection_token,
                "measurement_rows",
                "x",
                "y",
                battery_id,
                element_token,
                correction_token,
                report_token,
                sink_token,
                "pvals",
                "adjusted",
                "reported",
            }
        ),
    )
    case_binding = MultipleTestingCaseBinding(
        case_id="multiple-testing-case:primary",
        analysis_target_ref=RecordRef("analysis", "analysis:primary"),
        correction_procedure_ref=correction.correction_procedure_ref,
        affected_target_ref=report.affected_target_ref,
        family_definition_id="family-definition:all-genes",
        battery_construct_id=battery_id,
        iterable_row_domain=domain_fact.row_domain,
        authorized_family_key_columns=domain_fact.hypothesis_key_columns,
        family_input_path=domain_fact.path,
        family_input_content_digest=domain_fact.content_digest,
        measurement_input_path=argument_fact.path,
        measurement_input_content_digest=argument_fact.content_digest,
        measurement_key_columns=argument_fact.measurement_key_columns,
        left_measurement_columns=argument_fact.left_measurement_columns,
        right_measurement_columns=argument_fact.right_measurement_columns,
        measurement_reader_model=argument_fact.reader_form,
    )
    authority = FamilyAuthorization(
        record_type="human_pvalue_family_authorization",
        record_id="authorization:all-genes",
        actor_id="human:scientist",
        authority_state="authorized",
        analysis_target_ref=case_binding.analysis_target_ref,
        correction_procedure_ref=case_binding.correction_procedure_ref,
        family_definition_id=case_binding.family_definition_id,
        battery_construct_id=battery_id,
        iterable_row_domain=domain_fact.row_domain,
        authorized_family_key_columns=domain_fact.hypothesis_key_columns,
        family_member_rule="all_rows",
        family_input_path=domain_fact.path,
        family_input_content_digest=domain_fact.content_digest,
    )
    input_binding = MaterialInputBinding(
        path=domain_fact.path,
        content_digest=domain_fact.content_digest,
        file_ref=domain_fact.file_ref,
        asset_identity_ref=domain_fact.asset_identity_ref,
    )
    obligation = FamilyDomainObligation(
        input_binding=input_binding,
        reader_form=domain_fact.reader_form,
        line_model=domain_fact.line_model,
        dialect=domain_fact.dialect,
        iterable_row_domain=domain_fact.row_domain,
        hypothesis_key_columns=domain_fact.hypothesis_key_columns,
        pvalue_column=domain_fact.pvalue_column,
        reader_assignment_span=_span(reader_assign),
        reader_evidence_ids=("evidence:reader",),
    )
    argument_obligation = TestArgumentDomainObligation(
        input_binding=MaterialInputBinding(
            path=argument_fact.path,
            content_digest=argument_fact.content_digest,
            file_ref=argument_fact.file_ref,
            asset_identity_ref=argument_fact.asset_identity_ref,
        ),
        reader_form=argument_fact.reader_form,
        line_model=argument_fact.line_model,
        dialect=argument_fact.dialect,
        measurement_row_domain=argument_fact.row_domain,
        measurement_rows_name="measurement_rows",
        measurement_key_columns=argument_fact.measurement_key_columns,
        left_measurement_columns=argument_fact.left_measurement_columns,
        right_measurement_columns=argument_fact.right_measurement_columns,
        left_argument_name="x",
        right_argument_name="y",
        reader_assignment_span=_span(measurement_reader_assign),
        left_projection_span=_span(left_projection_assign),
        right_projection_span=_span(right_projection_assign),
        left_key_span=_span(left_projection_assign.value.key),
        right_key_span=_span(right_projection_assign.value.key),
        left_value_span=_span(left_projection_assign.value.value),
        right_value_span=_span(right_projection_assign.value.value),
        evidence_ids=(
            "evidence:measurement-reader",
            "evidence:left-projection",
            "evidence:right-projection",
            "evidence:left-key",
            "evidence:right-key",
            "evidence:left-value",
            "evidence:right-value",
        ),
    )
    evidence = (
        EvidenceDeclaration(domain_fact.evidence_id, EvidencePoint(_DATA_PATH, 1, 4, 1, 20)),
        EvidenceDeclaration(
            argument_fact.evidence_id,
            EvidencePoint(_MEASUREMENT_PATH, 1, 4, 1, 20),
        ),
        EvidenceDeclaration("evidence:reader", obligation.reader_assignment_span),
        EvidenceDeclaration("evidence:projection-assignment", projection.assignment_span),
        EvidenceDeclaration("evidence:projection-listcomp", projection.listcomp_span),
        EvidenceDeclaration("evidence:projection-element", projection.element_span),
        EvidenceDeclaration(
            "evidence:measurement-reader", argument_obligation.reader_assignment_span
        ),
        EvidenceDeclaration("evidence:left-projection", argument_obligation.left_projection_span),
        EvidenceDeclaration("evidence:right-projection", argument_obligation.right_projection_span),
        EvidenceDeclaration("evidence:left-key", argument_obligation.left_key_span),
        EvidenceDeclaration("evidence:right-key", argument_obligation.right_key_span),
        EvidenceDeclaration("evidence:left-value", argument_obligation.left_value_span),
        EvidenceDeclaration("evidence:right-value", argument_obligation.right_value_span),
        EvidenceDeclaration("evidence:battery-assignment", battery.assignment_span),
        EvidenceDeclaration("evidence:battery-listcomp", battery.listcomp_span),
        EvidenceDeclaration("evidence:battery-call", battery.element_call_span),
        EvidenceDeclaration("evidence:battery-iterable", battery.iterable_span),
        EvidenceDeclaration("evidence:correction", correction.call_span),
        EvidenceDeclaration(
            "evidence:scope",
            EvidencePoint(
                _SOURCE_PATH,
                battery.assignment_span.start_line,
                battery.assignment_span.start_line,
                2,
                3,
            ),
        ),
        EvidenceDeclaration("evidence:report-binding", report.assignment_span),
        EvidenceDeclaration("evidence:sink", report.sink_span),
    )
    all_constructs = frozenset(
        {
            reader_token,
            projection_token,
            measurement_reader_token,
            left_projection_token,
            right_projection_token,
            battery_id,
            element_token,
            correction_token,
            report_token,
            sink_token,
        }
    )
    certificate = MultipleTestingCertificate(
        source_path=_SOURCE_PATH,
        source_digest=source_digest,
        parser_id="python-ast",
        parser_version="3.11",
        source_extent=_source_extent(source),
        dependency_closure_digest=_CLOSURE_DIGEST,
        proposed_case_digest=multiple_testing_case_digest(case_binding),
        replay_digest="",
        case_binding=case_binding,
        family_domain_obligations=(obligation,),
        test_argument_domain_obligations=(argument_obligation,),
        full_family_projections=(projection,),
        test_batteries=(battery,),
        correction_calls=(correction,),
        family_scope_checks=(scope,),
        report_bindings=(report,),
        all_syntactic_construct_tokens=all_constructs,
        dead_syntactic_construct_tokens=frozenset(),
        all_sink_tokens=frozenset({sink_token}),
        dead_sink_tokens=frozenset(),
        effects=(),
        unknowns=(),
        output_ceiling="report_only",
        wording_ceiling="supported_normal_path_static_relationship_only",
        evidence=evidence,
    )
    certificate = replace(
        certificate,
        replay_digest=multiple_testing_replay_digest(certificate),
    )
    return _Fixture(
        certificate,
        source_bytes,
        (domain_fact,),
        (argument_fact,),
        (authority,),
    )


def _verify(fixture: _Fixture):  # type: ignore[no-untyped-def]
    return verify_multiple_testing_certificate(
        fixture.certificate,
        frozen_source_bytes=fixture.frozen_source_bytes,
        trusted_family_facts=fixture.trusted_facts,
        trusted_argument_facts=fixture.trusted_argument_facts,
        trusted_family_authorizations=fixture.trusted_authorizations,
    )


def _with_certificate(
    fixture: _Fixture,
    certificate: MultipleTestingCertificate,
    *,
    refresh_replay: bool = False,
) -> _Fixture:
    if refresh_replay:
        certificate = replace(
            certificate,
            replay_digest=multiple_testing_replay_digest(certificate),
        )
    return replace(fixture, certificate=certificate)


def test_accepting_certificate_discharges_m1_through_m12() -> None:
    verified = _verify(_fixture())
    assert verified is not None
    assert len(verified.test_result_positions) == 3
    assert verified.corrected_positions == (0, 1)
    assert verified.recomputed_adjusted_pvalues == ("0.02", "0.04")
    assert verified.reported_result_tokens == verified.performed_result_tokens
    assert Counter(verified.corrected_result_tokens) < Counter(verified.performed_result_tokens)
    assert len(set(verified.performed_result_tokens)) == 3
    assert verified.output_ceiling == "report_only"


def test_certified_reader_binding_is_mandatory_at_the_kernel_boundary() -> None:
    fixture = _fixture()
    certificate = fixture.certificate
    domain = replace(
        certificate.family_domain_obligations[0],
        reader_evidence_ids=(),
    )
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(certificate, family_domain_obligations=(domain,)),
            )
        )
        is None
    )


@pytest.mark.parametrize("obligation", [f"M{index}" for index in range(1, 13)])
def test_each_obligation_rejects_one_corrupted_field(obligation: str) -> None:
    fixture = _fixture()
    certificate = fixture.certificate
    if obligation == "M1":
        fixture = _with_certificate(
            fixture,
            replace(certificate, source_digest="sha256:" + "9" * 64),
        )
    elif obligation == "M2":
        check = replace(
            certificate.family_scope_checks[0],
            modeled_test_call_tokens=frozenset(),
        )
        fixture = _with_certificate(
            fixture,
            replace(certificate, family_scope_checks=(check,)),
            refresh_replay=True,
        )
    elif obligation == "M3":
        battery = replace(
            certificate.test_batteries[0],
            resolved_test_callable="scipy.stats.mannwhitneyu",
        )
        fixture = _with_certificate(
            fixture,
            replace(certificate, test_batteries=(battery,)),
        )
    elif obligation == "M4":
        authority = replace(
            fixture.trusted_authorizations[0],
            family_definition_id="family-definition:other",
        )
        fixture = replace(fixture, trusted_authorizations=(authority,))
    elif obligation == "M5":
        fixture = _fixture(_DEFAULT_SOURCE.replace("pvals[:2]", "pvals[:3]"))
    elif obligation == "M6":
        fact = replace(
            fixture.trusted_facts[0],
            observation_tokens=("forged", *fixture.trusted_facts[0].observation_tokens[1:]),
        )
        fixture = replace(fixture, trusted_facts=(fact,))
    elif obligation == "M7":
        report = replace(certificate.report_bindings[0], path="results/other.txt")
        fixture = _with_certificate(
            fixture,
            replace(certificate, report_bindings=(report,)),
        )
    elif obligation == "M8":
        effect = Effect(
            reads=frozenset(),
            writes=frozenset({certificate.report_bindings[0].token}),
            aliases=frozenset(),
            may_raise=False,
            opaque=False,
            reason="mutates selected sink",
        )
        fixture = _with_certificate(
            fixture,
            replace(certificate, effects=(effect,)),
        )
    elif obligation == "M9":
        fixture = _with_certificate(
            fixture,
            replace(certificate, all_sink_tokens=frozenset({"sink:other"})),
            refresh_replay=True,
        )
    elif obligation == "M10":
        check = replace(
            certificate.family_scope_checks[0],
            bases=cast(Any, REQUIRED_SCOPE_BASES[:-1]),
        )
        fixture = _with_certificate(
            fixture,
            replace(certificate, family_scope_checks=(check,)),
            refresh_replay=True,
        )
    elif obligation == "M11":
        correction = replace(
            certificate.correction_calls[0],
            asserted_adjusted_pvalues=("0.01", "0.04"),
        )
        fixture = _with_certificate(
            fixture,
            replace(certificate, correction_calls=(correction,)),
        )
    else:
        fact = replace(
            fixture.trusted_argument_facts[0],
            hypothesis_tokens=(
                "family-hypothesis:forged",
                *fixture.trusted_argument_facts[0].hypothesis_tokens[1:],
            ),
        )
        fixture = replace(fixture, trusted_argument_facts=(fact,))
    assert _verify(fixture) is None


@pytest.mark.parametrize(
    "battery_line",
    [
        "pvals = [scipy.stats.ttest_ind(x[g], y[0]).pvalue for g in genes]",
        "pvals = [scipy.stats.ttest_ind(x[g], y[genes[0]]).pvalue for g in genes]",
        "pvals = [scipy.stats.ttest_ind(x[h], y[g]).pvalue for g in genes]",
        "pvals = [scipy.stats.ttest_ind(x[g], y[g]).pvalue for g in genes if g]",
        ("pvals = [scipy.stats.ttest_ind(x[g], y[g]).pvalue for g in genes for h in genes]"),
        "pvals = [scipy.stats.ttest_ind(x[g], x[g]).pvalue for g in genes]",
        "pvals = [scipy.stats.ttest_ind(x[g], y[g]).pvalue for g in reversed(genes)]",
        "pvals = [scipy.stats.ttest_ind(x[g], y[g]).statistic for g in genes]",
    ],
)
def test_m3_position_binding_attacks_refuse(battery_line: str) -> None:
    source = _DEFAULT_SOURCE.replace(
        "pvals = [scipy.stats.ttest_ind(x[g], y[g]).pvalue for g in genes]",
        battery_line,
    )
    assert _verify(_fixture(source)) is None


def test_m3_walrus_wrapper_and_competing_battery_refuse() -> None:
    walrus = _DEFAULT_SOURCE.replace(
        "scipy.stats.ttest_ind(x[g], y[g]).pvalue",
        "(result := scipy.stats.ttest_ind(x[g], y[g])).pvalue",
    )
    assert _verify(_fixture(walrus)) is None

    wrapper = _DEFAULT_SOURCE.replace(
        'genes = [row["gene"] for row in rows]',
        'test = scipy.stats.ttest_ind\ngenes = [row["gene"] for row in rows]',
    ).replace("scipy.stats.ttest_ind(x[g], y[g])", "test(x[g], y[g])")
    assert _verify(_fixture(wrapper)) is None

    competing = _DEFAULT_SOURCE.replace(
        'adjusted = multipletests(pvals[:2], method="fdr_bh")',
        (
            "other = [scipy.stats.ttest_ind(x[g], y[g]).pvalue for g in genes]\n"
            'adjusted = multipletests(pvals[:2], method="fdr_bh")'
        ),
    )
    assert _verify(_fixture(competing)) is None


def test_certificate_has_no_derived_family_or_trusted_record_channel() -> None:
    certificate_names = {field.name for field in fields(MultipleTestingCertificate)}
    battery_names = {field.name for field in fields(TestBatteryObligation)}
    prohibited = {
        "position",
        "performed_count",
        "corrected_count",
        "performed_result_tokens",
        "corrected_result_tokens",
        "reported_result_tokens",
        "trusted_family_facts",
        "trusted_family_authorizations",
    }
    assert not certificate_names & prohibited
    assert not battery_names & prohibited
    assert (
        verify_multiple_testing_certificate(
            _fixture().certificate,
            frozen_source_bytes=_fixture().frozen_source_bytes,
        )
        is None
    )


def test_equal_numeric_pvalues_remain_distinct_position_tokens() -> None:
    repeated = _fact(raw_values=("0.04", "0.04", "0.20"))
    verified = _verify(_fixture(fact=repeated))
    assert verified is not None
    assert repeated.canonical_pvalue_decimals[:2] == ("0.04", "0.04")
    assert verified.performed_result_tokens[0] != verified.performed_result_tokens[1]


def test_trusted_channels_and_sink_noninterference_fail_closed() -> None:
    fixture = _fixture()
    assert _verify(replace(fixture, trusted_facts=())) is None
    assert (
        _verify(replace(fixture, trusted_facts=(*fixture.trusted_facts, fixture.trusted_facts[0])))
        is None
    )
    assert _verify(replace(fixture, trusted_argument_facts=())) is None
    assert (
        _verify(
            replace(
                fixture,
                trusted_argument_facts=(
                    *fixture.trusted_argument_facts,
                    fixture.trusted_argument_facts[0],
                ),
            )
        )
        is None
    )
    assert _verify(replace(fixture, trusted_authorizations=())) is None
    unknown = Unknown(
        "sink lineage unresolved",
        frozenset({next(iter(fixture.certificate.all_sink_tokens))}),
    )
    certificate = replace(fixture.certificate, unknowns=(unknown,))
    assert _verify(_with_certificate(fixture, certificate)) is None


def test_direct_nonnegative_narrowing_slice_boundaries() -> None:
    for slice_text in ("[:1]", "[:2]", "[1:]", "[1:3]", "[0:2]"):
        source = _DEFAULT_SOURCE.replace("[:2]", slice_text)
        assert _verify(_fixture(source)) is not None
    for slice_text in ("[:]", "[:3]", "[0:3]", "[1:1]", "[-1:]", "[::2]"):
        source = _DEFAULT_SOURCE.replace("[:2]", slice_text)
        assert _verify(_fixture(source)) is None


def test_regression_r1_filter_comprehension_is_not_a_kernel_route() -> None:
    source = _DEFAULT_SOURCE.replace("pvals[:2]", "[p for p in pvals if p < 0.05]")
    assert _verify(_fixture(source)) is None


def test_regression_r2_kernel_enforces_cardinality_for_each_input_kind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adverse = _fixture()
    monkeypatch.setattr(
        certificate_module,
        "_correction_input_positions",
        lambda *_args: (0, 1, 2),
    )
    assert _verify(adverse) is None

    complete = _fixture(_DEFAULT_SOURCE.replace("pvals[:2]", "pvals"))
    monkeypatch.setattr(
        certificate_module,
        "_correction_input_positions",
        lambda *_args: (0, 1),
    )
    assert _verify(complete) is None


def test_regression_r3_source_rows_and_projected_family_are_noninterfering() -> None:
    fixture = _fixture()
    effect = Effect(
        reads=frozenset({"unrelated-read"}),
        writes=frozenset({"rows"}),
        aliases=frozenset({"unrelated-alias"}),
        may_raise=False,
        opaque=False,
        reason="mutates source rows",
    )
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(fixture.certificate, effects=(effect,)),
            )
        )
        is None
    )
    unknown = Unknown("projected family unresolved", frozenset({"genes"}))
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(fixture.certificate, unknowns=(unknown,)),
            )
        )
        is None
    )


@pytest.mark.parametrize("raw", ["1e-1", "+0.1", "-0", "-0.0"])
def test_regression_r5_kernel_decimal_grammar_matches_the_prover(raw: str) -> None:
    fact = _fact(raw_values=(raw, "0.04", "0.20"))
    assert _verify(_fixture(fact=fact)) is None


def test_regression_r8_correction_assignment_value_must_be_the_call() -> None:
    source = _DEFAULT_SOURCE.replace(
        'adjusted = multipletests(pvals[:2], method="fdr_bh")',
        'adjusted = (multipletests(pvals[:2], method="fdr_bh"),)[0]',
    )
    assert _verify(_fixture(source)) is None


def test_m12_reordered_measurement_rows_join_by_hypothesis_not_position() -> None:
    fixture = _fixture()
    verified = _verify(fixture)
    assert verified is not None
    assert fixture.trusted_argument_facts[0].hypothesis_tokens != (
        verified.family_fact.hypothesis_tokens
    )
    vectors_by_hypothesis = {
        position.hypothesis_token: position.argument_vector_tokens
        for position in verified.test_result_positions
    }
    assert set(vectors_by_hypothesis) == set(verified.family_fact.hypothesis_tokens)
    assert all(len(tokens) == 2 for tokens in vectors_by_hypothesis.values())


@pytest.mark.parametrize(
    "mutation",
    ["different-key", "duplicate-key", "forged-binary64", "forged-observation"],
)
def test_m12_trusted_fact_forgery_refuses(mutation: str) -> None:
    fixture = _fixture()
    fact = fixture.trusted_argument_facts[0]
    if mutation == "different-key":
        fact = _argument_fact(key_values=(("g2",), ("g1",), ("other",)))
    elif mutation == "duplicate-key":
        fact = replace(
            fact,
            key_value_tuples=(fact.key_value_tuples[0],) * fact.row_count,
        )
    elif mutation == "forged-binary64":
        fact = replace(
            fact,
            left_binary64_hex=(("0x1.0p+9", "0x1.0p+1"), *fact.left_binary64_hex[1:]),
        )
    else:
        fact = replace(
            fact,
            observation_tokens=("test-argument-observation:forged", *fact.observation_tokens[1:]),
        )
    assert _verify(replace(fixture, trusted_argument_facts=(fact,))) is None


@pytest.mark.parametrize(
    "old,new",
    [
        (
            'y = {s["gene"]: (float(s["y1"]), float(s["y2"])) for s in measurement_rows}',
            'y = {s["gene"]: (float(s["x1"]), float(s["y2"])) for s in measurement_rows}',
        ),
        (
            'x = {r["gene"]: (float(r["x1"]), float(r["x2"])) for r in measurement_rows}',
            'x = {r["gene"]: (float(r["x1"]), float(r["x2"])) for r in measurement_rows if r}',
        ),
        (
            "scipy.stats.ttest_ind(x[g], y[g])",
            "scipy.stats.ttest_ind(y[g], x[g])",
        ),
    ],
)
def test_m12_source_projection_and_operand_attacks_refuse(old: str, new: str) -> None:
    assert _verify(_fixture(_DEFAULT_SOURCE.replace(old, new))) is None


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (
            'genes = [row["gene"] for row in rows]',
            'genes = [(row["gene"],) for row in rows]',
        ),
        (
            'x = {r["gene"]: (float(r["x1"]), float(r["x2"])) for r in measurement_rows}',
            'x = {(r["gene"],): (float(r["x1"]), float(r["x2"])) for r in measurement_rows}',
        ),
    ],
)
def test_regression_r9_kernel_refuses_single_column_tuple_forms(old: str, new: str) -> None:
    assert _verify(_fixture(_DEFAULT_SOURCE.replace(old, new))) is None


def test_m12_assignment_comprehension_import_and_builtin_names_are_disjoint() -> None:
    import_shadow = _DEFAULT_SOURCE.replace(
        'x = {r["gene"]: (float(r["x1"]), float(r["x2"])) for r in measurement_rows}',
        'x = {csv["gene"]: (float(csv["x1"]), float(csv["x2"])) for csv in measurement_rows}',
    )
    assert _verify(_fixture(import_shadow)) is None

    builtin_shadow = _DEFAULT_SOURCE.replace(
        "for r in measurement_rows", "for float in measurement_rows"
    ).replace('r["', 'float["')
    assert _verify(_fixture(builtin_shadow)) is None


@pytest.mark.parametrize("binding", ["measurement_rows", "x", "y"])
def test_m12_measurement_bindings_are_in_the_noninterference_slice(binding: str) -> None:
    fixture = _fixture()
    effect = Effect(
        reads=frozenset({"unrelated"}),
        writes=frozenset({binding}),
        aliases=frozenset(),
        may_raise=False,
        opaque=False,
        reason="mutates executable test argument lineage",
    )
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(fixture.certificate, effects=(effect,)),
            )
        )
        is None
    )
