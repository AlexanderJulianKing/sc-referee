"""Hand-built obligation, mutation, and M3 attack tests for Experiment 0059."""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass, fields, replace
from decimal import Decimal
from typing import Any, cast

import pytest

from sc_referee.calculation_checks.bh import benjamini_hochberg
from sc_referee.core.ids import sha256_digest
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
    TestBatteryObligation,
)
from sc_referee.scientific_checks.founder_orientation_semantic_ir import Effect, Unknown

_SOURCE_PATH = "workflow/analysis.py"
_DATA_PATH = "results/tests.csv"
_DATA_DIGEST = "sha256:" + "2" * 64
_CLOSURE_DIGEST = "sha256:" + "3" * 64
_DEFAULT_SOURCE = """import csv
import scipy.stats
from pathlib import Path
from sc_referee.calculation_checks.bh import benjamini_hochberg
rows = list(csv.DictReader(Path("results/tests.csv").open(encoding="utf-8", newline="")))
genes = [row[\"gene\"] for row in rows]
pvals = [scipy.stats.ttest_ind(x[g], y[g]).pvalue for g in genes]
adjusted = benjamini_hochberg(pvals[:2])
reported = tuple(zip(genes, pvals))
Path(\"results/report.txt\").write_text(str((reported, adjusted)), encoding=\"utf-8\")
"""


@dataclass(frozen=True)
class _Fixture:
    certificate: MultipleTestingCertificate
    frozen_source_bytes: bytes
    trusted_facts: tuple[PValueFamilyFact, ...]
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


def _fixture(
    source: str = _DEFAULT_SOURCE,
    *,
    fact: PValueFamilyFact | None = None,
) -> _Fixture:
    domain_fact = fact or _fact()
    source_bytes = source.encode("utf-8")
    source_digest = sha256_digest(source_bytes)
    tree = ast.parse(source, feature_version=(3, 11))
    reader_assign = _target_assignment(tree, "rows")
    projection_assign = _target_assignment(tree, "genes")
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
    slice_node = correction_call.args[0]
    assert isinstance(slice_node, ast.Subscript) and isinstance(slice_node.slice, ast.Slice)
    lower_node = slice_node.slice.lower
    upper_node = slice_node.slice.upper
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
        resolved_callable="sc_referee.calculation_checks.bh.benjamini_hochberg",
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
            {_SOURCE_PATH, _DATA_PATH, domain_fact.row_domain, "results/report.txt"}
        ),
        relevant_bindings=frozenset(
            {
                reader_token,
                projection_token,
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
    evidence = (
        EvidenceDeclaration(domain_fact.evidence_id, EvidencePoint(_DATA_PATH, 1, 4, 1, 20)),
        EvidenceDeclaration("evidence:reader", obligation.reader_assignment_span),
        EvidenceDeclaration("evidence:projection-assignment", projection.assignment_span),
        EvidenceDeclaration("evidence:projection-listcomp", projection.listcomp_span),
        EvidenceDeclaration("evidence:projection-element", projection.element_span),
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
    return _Fixture(certificate, source_bytes, (domain_fact,), (authority,))


def _verify(fixture: _Fixture):  # type: ignore[no-untyped-def]
    return verify_multiple_testing_certificate(
        fixture.certificate,
        frozen_source_bytes=fixture.frozen_source_bytes,
        trusted_family_facts=fixture.trusted_facts,
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


def test_accepting_certificate_discharges_m1_through_m11() -> None:
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


@pytest.mark.parametrize("obligation", [f"M{index}" for index in range(1, 12)])
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
    else:
        correction = replace(
            certificate.correction_calls[0],
            asserted_adjusted_pvalues=("0.01", "0.04"),
        )
        fixture = _with_certificate(
            fixture,
            replace(certificate, correction_calls=(correction,)),
        )
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
        "adjusted = benjamini_hochberg(pvals[:2])",
        (
            "other = [scipy.stats.ttest_ind(x[g], y[g]).pvalue for g in genes]\n"
            "adjusted = benjamini_hochberg(pvals[:2])"
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
