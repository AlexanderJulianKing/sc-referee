"""Fail-closed static proposer for multiple-testing recognition v1.

The module imports the four guarded-parse helpers permitted by the dependence
precedent.  Project-authored modules are decoded and parsed as frozen bytes;
they are never imported or executed.  Every source subtree outside the exact
Stage-3 grammar produces an opaque wildcard-write :class:`Effect` over its
complete syntactic read set and causes abstention.

This analyzer is deliberately untrusted.  It may propose source spans and
bindings, but it never creates a trusted p-value fact or family authority.
``discharge_multiple_testing_proposal`` is the controller boundary: it
revalidates the frozen context and exact requirements pins, calls the
digest-bound CSV prover, constructs authorities only from closed frozen
records, fills the arithmetic assertion from the trusted fact, and supplies
the source bytes, fact, and authority independently to the certificate kernel.
"""

from __future__ import annotations

import ast
import csv
import io
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal, cast

from sc_referee.calculation_checks.bh import benjamini_hochberg
from sc_referee.core.ids import semantic_digest
from sc_referee.multiple_testing_recognition.certificate import (
    multiple_testing_case_digest,
    multiple_testing_replay_digest,
    source_construct_token,
    verify_multiple_testing_certificate,
)
from sc_referee.multiple_testing_recognition.ir import (
    MAX_MULTIPLE_TESTING_AST_NODES,
    MAX_MULTIPLE_TESTING_SOURCE_BYTES,
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
    VerifiedMultipleTestingCertificate,
)
from sc_referee.multiple_testing_recognition.pvalue_domain import (
    prove_pvalue_family,
    pvalue_family_row_domain,
)
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    InspectionDocument,
)
from sc_referee.scientific_checks.founder_orientation_dataflow import (
    _guarded_parse,
    _imports_case_module,
    _module_bans,
    _python_parser_supported,
)
from sc_referee.scientific_checks.founder_orientation_semantic_ir import Effect

AnalysisState = Literal["proposal", "question", "unsupported", "not_applicable"]
DischargeState = Literal["verified", "question", "unsupported", "not_applicable"]
RecognitionOutcome = Literal[
    "evaluation_candidate",
    "covered_negative",
    "question",
    "unsupported",
    "not_applicable",
]

_VALUE_COLUMN = "pvalue"
_DIALECT = "excel"
_SCIPY_VERSION = "1.14.0"
_STATSMODELS_VERSION = "0.14.4"
_TEST_CALLABLES = frozenset({"scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu"})
_REPOSITORY_BH_CALLABLE = "sc_referee.calculation_checks.bh.benjamini_hochberg"
_STATSMODELS_BH_CALLABLE = "statsmodels.stats.multitest.multipletests"
_CORRECTION_LOCAL_NAMES = {
    "benjamini_hochberg": _REPOSITORY_BH_CALLABLE,
    "multipletests": _STATSMODELS_BH_CALLABLE,
}
_FIXED_POINT_DECIMAL = re.compile(r"[0-9]+(?:\.[0-9]+)?", flags=re.ASCII)


@dataclass(frozen=True)
class PythonMultipleTestingAnalysis:
    """One untrusted source-analysis outcome before trusted discharge."""

    state: AnalysisState
    outcome: RecognitionOutcome
    certificate: MultipleTestingCertificate | None
    candidate_family_key_columns: tuple[str, ...]
    unresolved_dimensions: tuple[str, ...]
    unsupported_constructs: tuple[str, ...]
    effects: tuple[Effect, ...]
    basis: str


@dataclass(frozen=True)
class DischargedMultipleTestingAnalysis:
    """Controller result after fact, authority, and kernel verification."""

    state: DischargeState
    outcome: RecognitionOutcome
    certificate: MultipleTestingCertificate | None
    trusted_family_facts: tuple[PValueFamilyFact, ...]
    trusted_family_authorizations: tuple[FamilyAuthorization, ...]
    verified_certificate: VerifiedMultipleTestingCertificate | None
    basis: str


@dataclass(frozen=True)
class _AuthorityHint:
    record_id: str
    actor_id: str
    analysis_target_ref: RecordRef
    correction_procedure_ref: RecordRef
    family_definition_id: str
    battery_construct_id: str
    iterable_row_domain: str
    authorized_family_key_columns: tuple[str, ...]
    family_member_rule: str
    family_input_path: str
    family_input_content_digest: str


@dataclass(frozen=True)
class _Reader:
    assignment: ast.Assign
    target_name: str
    path: str
    reader_form: Literal["csv_dictreader_splitlines", "csv_dictreader_file"]
    line_model: Literal["splitlines", "csv_newline"]


@dataclass(frozen=True)
class _SourceShape:
    tree: ast.Module
    reader: _Reader
    projection: ast.Assign
    battery: ast.Assign
    battery_call: ast.Call
    correction: ast.Assign
    correction_call: ast.Call
    correction_callable: str
    report: ast.Assign
    sink: ast.Expr
    report_path: str


def analyze_multiple_testing_python(
    context: FrozenInspectionContext,
    *,
    parser_id: str = "python-ast",
    parser_version: str = "3.11",
) -> PythonMultipleTestingAnalysis:
    """Analyze frozen source and propose at most one exact Stage-3 certificate."""

    python_documents = tuple(
        document for document in context.documents if document.media_type == "text/x-python"
    )
    if not python_documents:
        return _without_certificate(
            "not_applicable",
            basis="No frozen Python document was available.",
        )
    if len(python_documents) != 1:
        return _without_certificate(
            "question",
            unresolved=("multiple-python-lineages",),
            basis="More than one Python document could contribute a family lineage.",
        )
    document = python_documents[0]
    if (
        not _parser_is_supported(document, parser_id, parser_version)
        or len(document.content) > MAX_MULTIPLE_TESTING_SOURCE_BYTES
    ):
        return _without_certificate(
            "unsupported",
            unsupported=("unsupported-python-parser-or-source-ceiling",),
            basis="The source lacked the exact guarded parser identity or exceeded its ceiling.",
        )
    try:
        source = document.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _without_certificate(
            "unsupported",
            unsupported=("non-utf8-python-source",),
            basis="The Python source was not strict UTF-8.",
        )
    tree = _guarded_parse(source, filename=document.path)
    if tree is None or sum(1 for _ in ast.walk(tree)) > MAX_MULTIPLE_TESTING_AST_NODES:
        return _without_certificate(
            "unsupported",
            unsupported=("python-parse-or-ast-ceiling",),
            basis="Guarded parsing failed or the AST exceeded the Stage-3 ceiling.",
        )
    if any(isinstance(node, (ast.For, ast.AsyncFor, ast.While)) for node in ast.walk(tree)):
        return _unsupported_tree(tree, "loop-built-test-battery-unrecognized")
    if _source_has_module_ban(tree, context, document):
        return _unsupported_tree(tree, "module-ban-or-dynamic-binding")

    selected_report_path = _selected_artifact_path(context)
    if selected_report_path is None:
        return _without_certificate(
            "question",
            unresolved=("selected-result-sink",),
            basis="The selected artifact did not bind one exact report path.",
        )
    shape_or_analysis = _source_shape(
        tree,
        source,
        document.path,
        selected_report_path,
    )
    if isinstance(shape_or_analysis, PythonMultipleTestingAnalysis):
        return shape_or_analysis
    shape = shape_or_analysis

    material = _material_by_path(context.material_inputs, shape.reader.path)
    if material is None:
        return _without_certificate(
            "unsupported",
            unsupported=("digest-bound-input-unavailable",),
            basis="The statically read CSV was not frozen exactly once.",
        )
    key_columns = _candidate_key_columns(material, shape.reader.line_model)
    if key_columns is None:
        return _without_certificate(
            "unsupported",
            unsupported=("pvalue-family-header-unavailable",),
            basis="The p-value family header was not exactly available under the reader model.",
        )
    if not _projection_element_matches_columns(shape.projection, key_columns):
        return _unsupported_nodes(
            shape.tree,
            "full-family-projection-unverified",
            (shape.projection,),
        )
    source_digest = document.content_digest
    battery_id = source_construct_token(
        "battery-construct", source_digest, _point(document.path, shape.battery)
    )
    row_domain = pvalue_family_row_domain(
        material.path,
        material.content_digest,
        shape.reader.line_model,
    )
    authorities, malformed_authority = _authority_hints(context)
    matching_authorities = tuple(
        item
        for item in authorities
        if item.battery_construct_id == battery_id
        and item.iterable_row_domain == row_domain
        and item.family_input_path == material.path
        and item.family_input_content_digest == material.content_digest
        and item.authorized_family_key_columns == key_columns
    )
    if malformed_authority or len(matching_authorities) != 1 or len(authorities) != 1:
        return _without_certificate(
            "question",
            candidates=key_columns,
            unresolved=(
                "family-definition-unauthorized",
                *(f"candidate_family_key:{column}" for column in key_columns),
            ),
            basis="No single matching human family authorization closed the battery and domain.",
        )
    authority = matching_authorities[0]
    if authority.family_member_rule != "all_rows":
        return _without_certificate(
            "question",
            candidates=key_columns,
            unresolved=("family-definition-unauthorized",),
            basis="The authority did not select the closed all-rows family rule.",
        )
    if not _record_ref_exists_once(context, authority.analysis_target_ref):
        return _without_certificate(
            "question",
            unresolved=("analysis-target-binding",),
            basis="The authorized analysis target did not exist exactly once.",
        )
    if not _procedure_record_allows(
        context,
        authority.correction_procedure_ref,
        shape.correction_callable,
    ):
        return _without_certificate(
            "unsupported",
            unsupported=("correction-procedure-binding-unverified",),
            basis="The authorized procedure record did not allow the resolved correction call.",
        )
    if _pinned_version(context.material_inputs, "scipy") != _SCIPY_VERSION:
        return _without_certificate(
            "unsupported",
            unsupported=("unsupported-or-unpinned-scipy-version",),
            basis="No unique frozen requirements material pinned scipy==1.14.0.",
        )
    if (
        shape.correction_callable == _STATSMODELS_BH_CALLABLE
        and _pinned_version(context.material_inputs, "statsmodels") != _STATSMODELS_VERSION
    ):
        return _without_certificate(
            "unsupported",
            unsupported=("unsupported-or-unpinned-statsmodels-version",),
            basis="No unique frozen requirements material pinned statsmodels==0.14.4.",
        )
    affected_target = _affected_target_ref(context, shape.report_path)
    if affected_target is None:
        return _without_certificate(
            "question",
            unresolved=("affected_target",),
            basis="No unique result or claim was bound to the selected report sink.",
        )

    certificate = _build_certificate(
        context=context,
        document=document,
        shape=shape,
        authority=authority,
        material=material,
        key_columns=key_columns,
        row_domain=row_domain,
        affected_target=affected_target,
        parser_id=parser_id,
        parser_version=parser_version,
    )
    return PythonMultipleTestingAnalysis(
        state="proposal",
        outcome="not_applicable",
        certificate=certificate,
        candidate_family_key_columns=key_columns,
        unresolved_dimensions=(),
        unsupported_constructs=(),
        effects=(),
        basis="One exact static family lineage awaits trusted fact and authority discharge.",
    )


def discharge_multiple_testing_proposal(
    analysis: PythonMultipleTestingAnalysis,
    context: FrozenInspectionContext,
) -> DischargedMultipleTestingAnalysis:
    """Attach controller-trusted fact/authority inputs and invoke the kernel."""

    if analysis.state != "proposal" or analysis.certificate is None:
        return DischargedMultipleTestingAnalysis(
            state=cast(DischargeState, analysis.state),
            outcome=analysis.outcome,
            certificate=None,
            trusted_family_facts=(),
            trusted_family_authorizations=(),
            verified_certificate=None,
            basis=analysis.basis,
        )
    certificate = analysis.certificate
    authorities = _trusted_authorizations(context)
    if not _proposal_matches_context(certificate, context, authorities):
        return _failed_discharge(certificate, "frozen-context-drift")
    if len(certificate.family_domain_obligations) != 1:
        return _failed_discharge(certificate, "non-singleton-family-domain")
    obligation = certificate.family_domain_obligations[0]
    material = _material(
        context.material_inputs,
        obligation.input_binding.path,
        obligation.input_binding.content_digest,
    )
    if material is None:
        return _failed_discharge(certificate, "digest-bound-input-unavailable")
    fact = prove_pvalue_family(
        material,
        path=obligation.input_binding.path,
        content_digest=obligation.input_binding.content_digest,
        value_column=obligation.pvalue_column,
        line_model=obligation.line_model,
    )
    if fact is None:
        return _failed_discharge(certificate, "pvalue-family-proof-unavailable")
    source_documents = tuple(
        item
        for item in context.documents
        if item.path == certificate.source_path and item.content_digest == certificate.source_digest
    )
    if len(source_documents) != 1:
        return _failed_discharge(certificate, "frozen-source-unavailable")
    positions = _controller_correction_positions(
        certificate,
        source_documents[0].content,
        fact,
    )
    if positions is None:
        return _failed_discharge(certificate, "correction-input-proof-unavailable")
    try:
        recomputed = benjamini_hochberg(
            tuple(Decimal(fact.raw_pvalue_lexemes[index]) for index in positions)
        )
    except (ArithmeticError, ValueError, IndexError):
        return _failed_discharge(certificate, "trusted-bh-recomputation-failed")
    correction = replace(
        certificate.correction_calls[0],
        asserted_adjusted_pvalues=tuple(_canonical_decimal(value) for value in recomputed),
        asserts_trusted_bh_recomputation=True,
    )
    data_evidence = EvidenceDeclaration(
        fact.evidence_id,
        EvidencePoint(fact.path, 1, max(1, fact.row_count + 1), 1, 1),
    )
    discharged = replace(
        certificate,
        correction_calls=(correction,),
        evidence=tuple(sorted((*certificate.evidence, data_evidence))),
    )
    trusted_facts = (fact,)
    verified = verify_multiple_testing_certificate(
        discharged,
        frozen_source_bytes=source_documents[0].content,
        trusted_family_facts=trusted_facts,
        trusted_family_authorizations=authorities,
    )
    if verified is None:
        return _failed_discharge(discharged, "certificate-kernel-refusal")
    outcome: RecognitionOutcome = (
        "evaluation_candidate" if verified.conclusion == "correction_subset" else "covered_negative"
    )
    return DischargedMultipleTestingAnalysis(
        state="verified",
        outcome=outcome,
        certificate=discharged,
        trusted_family_facts=trusted_facts,
        trusted_family_authorizations=authorities,
        verified_certificate=verified,
        basis="Trusted family evidence and the certificate kernel closed the static outcome.",
    )


def _build_certificate(
    *,
    context: FrozenInspectionContext,
    document: InspectionDocument,
    shape: _SourceShape,
    authority: _AuthorityHint,
    material: FrozenMaterialInput,
    key_columns: tuple[str, ...],
    row_domain: str,
    affected_target: RecordRef,
    parser_id: str,
    parser_version: str,
) -> MultipleTestingCertificate:
    source_digest = document.content_digest
    projection_value = cast(ast.ListComp, shape.projection.value)
    battery_value = cast(ast.ListComp, shape.battery.value)
    battery_id = source_construct_token(
        "battery-construct", source_digest, _point(document.path, shape.battery)
    )
    reader_point = _point(document.path, shape.reader.assignment)
    projection_point = _point(document.path, shape.projection)
    battery_point = _point(document.path, shape.battery)
    correction_point = _point(document.path, shape.correction_call)
    report_point = _point(document.path, shape.report)
    sink_point = _point(document.path, shape.sink)
    reader_token = source_construct_token("family-domain-reader", source_digest, reader_point)
    projection_token = source_construct_token(
        "full-family-projection", source_digest, projection_point
    )
    call_token = source_construct_token(
        "test-call-template", source_digest, _point(document.path, shape.battery_call)
    )
    correction_token = source_construct_token("correction-call", source_digest, correction_point)
    report_token = source_construct_token("reported-family-binding", source_digest, report_point)
    sink_token = source_construct_token("selected-report-sink", source_digest, sink_point)

    points = {
        "reader": reader_point,
        "projection-assignment": projection_point,
        "projection-listcomp": _point(document.path, projection_value),
        "projection-element": _point(document.path, projection_value.elt),
        "battery-assignment": battery_point,
        "battery-listcomp": _point(document.path, battery_value),
        "battery-call": _point(document.path, shape.battery_call),
        "battery-iterable": _point(document.path, battery_value.generators[0].iter),
        "correction": correction_point,
        "report-binding": report_point,
        "sink": sink_point,
    }
    evidence_ids = {
        name: _evidence_id(document.path, name, point) for name, point in points.items()
    }
    scope_point = _unused_point(document, frozenset(points.values()))
    scope_evidence_id = _evidence_id(document.path, "scope", scope_point)

    input_binding = MaterialInputBinding(
        path=material.path,
        content_digest=material.content_digest,
        file_ref=RecordRef(material.file_ref.record_type, material.file_ref.record_id),
        asset_identity_ref=RecordRef(
            material.asset_identity_ref.record_type,
            material.asset_identity_ref.record_id,
        ),
    )
    domain = FamilyDomainObligation(
        input_binding=input_binding,
        reader_form=shape.reader.reader_form,
        line_model=shape.reader.line_model,
        dialect=_DIALECT,
        iterable_row_domain=row_domain,
        hypothesis_key_columns=key_columns,
        pvalue_column=_VALUE_COLUMN,
        reader_assignment_span=reader_point,
        reader_evidence_ids=(evidence_ids["reader"],),
    )
    projection = FullFamilyProjectionObligation(
        battery_construct_id=battery_id,
        iterable_row_domain=row_domain,
        source_rows_name=shape.reader.target_name,
        projected_family_name=cast(ast.Name, shape.projection.targets[0]).id,
        hypothesis_key_columns=key_columns,
        assignment_span=projection_point,
        listcomp_span=points["projection-listcomp"],
        element_span=points["projection-element"],
        evidence_ids=(
            evidence_ids["projection-assignment"],
            evidence_ids["projection-listcomp"],
            evidence_ids["projection-element"],
        ),
    )
    battery = TestBatteryObligation(
        battery_construct_id=battery_id,
        iterable_row_domain=row_domain,
        battery_result_name=cast(ast.Name, shape.battery.targets[0]).id,
        projected_family_name=projection.projected_family_name,
        resolved_test_callable=cast(str, _dotted_name(shape.battery_call.func)),
        assignment_span=battery_point,
        listcomp_span=points["battery-listcomp"],
        element_call_span=points["battery-call"],
        iterable_span=points["battery-iterable"],
        evidence_ids=(
            evidence_ids["battery-assignment"],
            evidence_ids["battery-listcomp"],
            evidence_ids["battery-call"],
            evidence_ids["battery-iterable"],
        ),
    )
    correction = CorrectionCall(
        battery_construct_id=battery_id,
        iterable_row_domain=row_domain,
        correction_procedure_ref=authority.correction_procedure_ref,
        resolved_callable=shape.correction_callable,
        result_name=cast(ast.Name, shape.correction.targets[0]).id,
        call_span=correction_point,
        asserted_adjusted_pvalues=(),
        asserts_trusted_bh_recomputation=True,
        evidence_ids=(evidence_ids["correction"],),
    )
    scope = FamilyScopeCheckObligation(
        battery_construct_id=battery_id,
        iterable_row_domain=row_domain,
        complete_test_call_tokens=frozenset({call_token}),
        modeled_test_call_tokens=frozenset({call_token}),
        proven_dead_test_call_tokens=frozenset(),
        corrected_test_call_tokens=frozenset({call_token}),
        bases=REQUIRED_SCOPE_BASES,
        evidence_ids=(scope_evidence_id,),
    )
    report = ReportFamilyBinding(
        token=sink_token,
        path=shape.report_path,
        affected_target_ref=affected_target,
        iterable_row_domain=row_domain,
        hypothesis_key_columns=key_columns,
        pvalue_column=_VALUE_COLUMN,
        reported_name=cast(ast.Name, shape.report.targets[0]).id,
        assignment_span=report_point,
        sink_span=sink_point,
        selected_result=True,
        evidence_ids=(evidence_ids["report-binding"], evidence_ids["sink"]),
        relevant_origins=frozenset({document.path, material.path, row_domain, shape.report_path}),
        relevant_bindings=frozenset(
            {
                reader_token,
                projection_token,
                battery_id,
                call_token,
                correction_token,
                report_token,
                sink_token,
                battery.battery_result_name,
                correction.result_name,
                cast(ast.Name, shape.report.targets[0]).id,
            }
        ),
    )
    case_binding = MultipleTestingCaseBinding(
        case_id="multiple-testing-case:"
        + semantic_digest(
            {
                "source_digest": source_digest,
                "battery_construct_id": battery_id,
                "family_definition_id": authority.family_definition_id,
            }
        ),
        analysis_target_ref=authority.analysis_target_ref,
        correction_procedure_ref=authority.correction_procedure_ref,
        affected_target_ref=affected_target,
        family_definition_id=authority.family_definition_id,
        battery_construct_id=battery_id,
        iterable_row_domain=row_domain,
        authorized_family_key_columns=key_columns,
        family_input_path=material.path,
        family_input_content_digest=material.content_digest,
    )
    evidence = tuple(
        sorted(
            (
                *(EvidenceDeclaration(evidence_ids[name], point) for name, point in points.items()),
                EvidenceDeclaration(scope_evidence_id, scope_point),
            )
        )
    )
    certificate = MultipleTestingCertificate(
        source_path=document.path,
        source_digest=source_digest,
        parser_id=parser_id,
        parser_version=parser_version,
        source_extent=_module_point(document),
        dependency_closure_digest=_dependency_closure_digest(context.material_inputs),
        proposed_case_digest=multiple_testing_case_digest(case_binding),
        replay_digest="sha256:" + "0" * 64,
        case_binding=case_binding,
        family_domain_obligations=(domain,),
        full_family_projections=(projection,),
        test_batteries=(battery,),
        correction_calls=(correction,),
        family_scope_checks=(scope,),
        report_bindings=(report,),
        all_syntactic_construct_tokens=frozenset(
            {
                reader_token,
                projection_token,
                battery_id,
                call_token,
                correction_token,
                report_token,
                sink_token,
            }
        ),
        dead_syntactic_construct_tokens=frozenset(),
        all_sink_tokens=frozenset({sink_token}),
        dead_sink_tokens=frozenset(),
        effects=(),
        unknowns=(),
        output_ceiling="report_only",
        wording_ceiling="supported_normal_path_static_relationship_only",
        evidence=evidence,
    )
    return replace(certificate, replay_digest=multiple_testing_replay_digest(certificate))


def _source_shape(
    tree: ast.Module,
    source: str,
    source_path: str,
    selected_report_path: str,
) -> _SourceShape | PythonMultipleTestingAnalysis:
    assignments = [statement for statement in tree.body if isinstance(statement, ast.Assign)]
    batteries = [item for item in assignments if _battery_call(item) is not None]
    if not batteries:
        if any(_correction_call(item) is not None for item in assignments):
            return _unsupported_nodes(tree, "hand-typed-correction-family-unbound", (tree,))
        return _without_certificate(
            "not_applicable",
            basis="No registered list-comprehension test battery was present.",
        )
    if len(batteries) != 1:
        return _without_certificate(
            "question",
            unresolved=("conflicting-batteries",),
            basis="Multiple candidate batteries could not be resolved to one family.",
        )
    battery = batteries[0]
    battery_call = _battery_call(battery)
    assert battery_call is not None
    battery_value = cast(ast.ListComp, battery.value)
    projected_name = cast(ast.Name, battery_value.generators[0].iter).id
    projections = [
        item
        for item in assignments
        if _single_target(item) == projected_name and isinstance(item.value, ast.ListComp)
    ]
    if len(projections) != 1:
        return _unsupported_nodes(tree, "full-family-projection-unverified", (battery,))
    projection = projections[0]
    projection_value = cast(ast.ListComp, projection.value)
    if not (
        len(projection_value.generators) == 1
        and not projection_value.generators[0].is_async
        and not projection_value.generators[0].ifs
        and isinstance(projection_value.generators[0].target, ast.Name)
        and isinstance(projection_value.generators[0].iter, ast.Name)
    ):
        return _unsupported_nodes(tree, "full-family-projection-unverified", (projection,))
    rows_name = projection_value.generators[0].iter.id
    readers = [
        reader
        for item in assignments
        if (reader := _reader(item)) is not None and reader.target_name == rows_name
    ]
    if len(readers) != 1:
        return _unsupported_nodes(tree, "certified-csv-reader-unverified", (projection,))
    reader = readers[0]
    corrections = [
        (item, value) for item in assignments if (value := _correction_call(item)) is not None
    ]
    if not corrections:
        return _unsupported_nodes(tree, "cross-module-correction-unverified", (battery,))
    if len(corrections) != 1:
        return _without_certificate(
            "question",
            unresolved=("conflicting-corrections",),
            basis="Multiple correction calls could not be resolved to one outcome.",
        )
    correction, (correction_call, correction_callable) = corrections[0]
    if not _correction_input_is_supported(
        correction_call.args[0],
        cast(str, _single_target(battery)),
        source,
    ):
        return _unsupported_nodes(tree, "correction-input-shape-unrecognized", (correction,))
    reports = [
        item
        for item in assignments
        if _report_assignment(item, projected_name, cast(str, _single_target(battery)))
    ]
    if len(reports) != 1:
        return _unsupported_nodes(tree, "complete-family-report-binding-unverified", (tree,))
    report = reports[0]
    report_name = cast(str, _single_target(report))
    correction_name = cast(str, _single_target(correction))
    sinks = [
        item
        for item in tree.body
        if isinstance(item, ast.Expr) and _sink_path(item, report_name, correction_name) is not None
    ]
    if len(sinks) != 1:
        return _unsupported_nodes(tree, "selected-result-sink-unverified", (tree,))
    sink = sinks[0]
    report_path = _sink_path(sink, report_name, correction_name)
    assert report_path is not None
    if report_path != selected_report_path:
        return _without_certificate(
            "question",
            unresolved=("selected-result-sink",),
            basis="The exact static sink did not equal the selected report path.",
        )

    allowed = {
        id(reader.assignment),
        id(projection),
        id(battery),
        id(correction),
        id(report),
        id(sink),
    }
    unmodeled = tuple(
        statement
        for statement in tree.body
        if not isinstance(statement, (ast.Import, ast.ImportFrom)) and id(statement) not in allowed
    )
    if unmodeled:
        return _unsupported_nodes(tree, "unmodeled-live-subtree", unmodeled)
    if not _imports_are_exact(tree, correction_callable):
        return _unsupported_nodes(tree, "aliased-or-unsupported-import", tuple(tree.body))
    ordered = (reader.assignment, projection, battery, correction, report, sink)
    starts = tuple((item.lineno, item.col_offset) for item in ordered)
    if starts != tuple(sorted(starts)):
        return _unsupported_nodes(tree, "non-straight-line-analysis-order", ordered)
    return _SourceShape(
        tree=tree,
        reader=reader,
        projection=projection,
        battery=battery,
        battery_call=battery_call,
        correction=correction,
        correction_call=correction_call,
        correction_callable=correction_callable,
        report=report,
        sink=sink,
        report_path=report_path,
    )


def _reader(assignment: ast.Assign) -> _Reader | None:
    target = _single_target(assignment)
    value = assignment.value
    if not (
        target is not None
        and isinstance(value, ast.Call)
        and _dotted_name(value.func) == "list"
        and len(value.args) == 1
        and not value.keywords
        and isinstance(value.args[0], ast.Call)
        and _dotted_name(value.args[0].func) == "csv.DictReader"
        and len(value.args[0].args) == 1
        and not value.args[0].keywords
    ):
        return None
    source = value.args[0].args[0]
    if (
        isinstance(source, ast.Call)
        and isinstance(source.func, ast.Attribute)
        and source.func.attr == "splitlines"
        and not source.args
        and not source.keywords
        and isinstance(source.func.value, ast.Call)
        and isinstance(source.func.value.func, ast.Attribute)
        and source.func.value.func.attr == "read_text"
        and not source.func.value.args
        and _exact_utf8_keyword(source.func.value.keywords)
    ):
        path = _path_call(source.func.value.func.value)
        if path is not None:
            return _Reader(
                assignment,
                target,
                path,
                "csv_dictreader_splitlines",
                "splitlines",
            )
    if (
        isinstance(source, ast.Call)
        and isinstance(source.func, ast.Attribute)
        and source.func.attr == "open"
        and not source.args
        and _exact_open_keywords(source.keywords)
    ):
        path = _path_call(source.func.value)
        if path is not None:
            return _Reader(
                assignment,
                target,
                path,
                "csv_dictreader_file",
                "csv_newline",
            )
    return None


def _battery_call(assignment: ast.Assign) -> ast.Call | None:
    value = assignment.value
    if not (
        _single_target(assignment) is not None
        and isinstance(value, ast.ListComp)
        and len(value.generators) == 1
        and not value.generators[0].is_async
        and not value.generators[0].ifs
        and isinstance(value.generators[0].target, ast.Name)
        and isinstance(value.generators[0].iter, ast.Name)
        and isinstance(value.elt, ast.Attribute)
        and value.elt.attr == "pvalue"
        and isinstance(value.elt.value, ast.Call)
    ):
        return None
    call = value.elt.value
    generator_name = value.generators[0].target.id
    if (
        _dotted_name(call.func) not in _TEST_CALLABLES
        or len(call.args) != 2
        or call.keywords
        or not all(
            isinstance(argument, ast.Subscript)
            and isinstance(argument.value, ast.Name)
            and isinstance(argument.slice, ast.Name)
            and argument.slice.id == generator_name
            for argument in call.args
        )
        or len({cast(ast.Name, cast(ast.Subscript, item).value).id for item in call.args}) != 2
    ):
        return None
    return call


def _correction_call(assignment: ast.Assign) -> tuple[ast.Call, str] | None:
    if _single_target(assignment) is None or not isinstance(assignment.value, ast.Call):
        return None
    call = assignment.value
    local_name = _dotted_name(call.func)
    resolved = _CORRECTION_LOCAL_NAMES.get(local_name or "")
    if resolved is None or len(call.args) != 1:
        return None
    if resolved == _REPOSITORY_BH_CALLABLE and call.keywords:
        return None
    if resolved == _STATSMODELS_BH_CALLABLE and not (
        len(call.keywords) == 1
        and call.keywords[0].arg == "method"
        and isinstance(call.keywords[0].value, ast.Constant)
        and call.keywords[0].value.value == "fdr_bh"
    ):
        return None
    return call, resolved


def _correction_input_is_supported(node: ast.expr, battery_name: str, source: str) -> bool:
    if isinstance(node, ast.Name):
        return node.id == battery_name
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == battery_name
        and isinstance(node.slice, ast.Slice)
        and node.slice.step is None
    ):
        return (node.slice.lower is not None or node.slice.upper is not None) and all(
            _literal_nonnegative(item) for item in (node.slice.lower, node.slice.upper)
        )
    if not (
        isinstance(node, ast.ListComp)
        and isinstance(node.elt, ast.Name)
        and len(node.generators) == 1
        and not node.generators[0].is_async
        and isinstance(node.generators[0].target, ast.Name)
        and isinstance(node.generators[0].iter, ast.Name)
        and node.generators[0].iter.id == battery_name
        and len(node.generators[0].ifs) == 1
    ):
        return False
    name = node.generators[0].target.id
    predicate = node.generators[0].ifs[0]
    return (
        node.elt.id == name
        and isinstance(predicate, ast.Compare)
        and isinstance(predicate.left, ast.Name)
        and predicate.left.id == name
        and len(predicate.ops) == 1
        and isinstance(predicate.ops[0], ast.Lt)
        and len(predicate.comparators) == 1
        and _fixed_decimal_source(predicate.comparators[0], source) is not None
    )


def _report_assignment(assignment: ast.Assign, keys_name: str, pvalues_name: str) -> bool:
    value = assignment.value
    return bool(
        _single_target(assignment)
        and isinstance(value, ast.Call)
        and _dotted_name(value.func) == "tuple"
        and len(value.args) == 1
        and not value.keywords
        and isinstance(value.args[0], ast.Call)
        and _dotted_name(value.args[0].func) == "zip"
        and len(value.args[0].args) == 2
        and not value.args[0].keywords
        and all(isinstance(item, ast.Name) for item in value.args[0].args)
        and tuple(cast(ast.Name, item).id for item in value.args[0].args)
        == (keys_name, pvalues_name)
    )


def _projection_element_matches_columns(
    assignment: ast.Assign,
    columns: tuple[str, ...],
) -> bool:
    value = assignment.value
    if not isinstance(value, ast.ListComp) or len(value.generators) != 1:
        return False
    target = value.generators[0].target
    if not isinstance(target, ast.Name):
        return False
    elements = value.elt.elts if isinstance(value.elt, ast.Tuple) else [value.elt]
    if len(elements) != len(columns) or (len(columns) > 1 and not isinstance(value.elt, ast.Tuple)):
        return False
    return all(
        isinstance(element, ast.Subscript)
        and isinstance(element.value, ast.Name)
        and element.value.id == target.id
        and isinstance(element.slice, ast.Constant)
        and element.slice.value == column
        for element, column in zip(elements, columns, strict=True)
    )


def _sink_path(statement: ast.Expr, report_name: str, correction_name: str) -> str | None:
    value = statement.value
    if not (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and value.func.attr == "write_text"
        and (path := _path_call(value.func.value)) is not None
        and len(value.args) == 1
        and isinstance(value.args[0], ast.Call)
        and _dotted_name(value.args[0].func) == "str"
        and len(value.args[0].args) == 1
        and not value.args[0].keywords
        and isinstance(value.args[0].args[0], ast.Tuple)
        and len(value.args[0].args[0].elts) == 2
        and all(isinstance(item, ast.Name) for item in value.args[0].args[0].elts)
        and tuple(cast(ast.Name, item).id for item in value.args[0].args[0].elts)
        == (report_name, correction_name)
        and len(value.keywords) == 1
        and value.keywords[0].arg == "encoding"
        and isinstance(value.keywords[0].value, ast.Constant)
        and value.keywords[0].value.value == "utf-8"
    ):
        return None
    return path


def _imports_are_exact(tree: ast.Module, correction_callable: str) -> bool:
    expected = {
        ("import", "csv", None),
        ("import", "scipy.stats", None),
        ("from", "pathlib", "Path"),
        (
            "from",
            "sc_referee.calculation_checks.bh"
            if correction_callable == _REPOSITORY_BH_CALLABLE
            else "statsmodels.stats.multitest",
            "benjamini_hochberg"
            if correction_callable == _REPOSITORY_BH_CALLABLE
            else "multipletests",
        ),
    }
    observed: list[tuple[str, str, str | None]] = []
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            if len(statement.names) != 1 or statement.names[0].asname is not None:
                return False
            observed.append(("import", statement.names[0].name, None))
        elif isinstance(statement, ast.ImportFrom):
            if (
                statement.level
                or len(statement.names) != 1
                or statement.names[0].asname is not None
            ):
                return False
            observed.append(("from", statement.module or "", statement.names[0].name))
    return len(observed) == len(expected) and set(observed) == expected


def _source_has_module_ban(
    tree: ast.Module,
    context: FrozenInspectionContext,
    document: InspectionDocument,
) -> bool:
    if any(
        isinstance(node, (ast.NamedExpr, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        or isinstance(
            node,
            (
                ast.If,
                ast.IfExp,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.Try,
                ast.TryStar,
                ast.With,
                ast.AsyncWith,
                ast.Match,
                ast.Lambda,
                ast.Await,
                ast.Yield,
                ast.YieldFrom,
                ast.AugAssign,
                ast.Delete,
            ),
        )
        for node in ast.walk(tree)
    ):
        return True
    case_names = {
        Path(item.path).stem
        for item in context.documents
        if item.path != document.path and item.path.endswith(".py")
    }
    if _imports_case_module(tree, case_names):
        return True
    guarded = ast.Module(
        body=[
            statement
            for statement in tree.body
            if not isinstance(statement, (ast.Import, ast.ImportFrom))
        ],
        type_ignores=[],
    )
    return _module_bans(guarded)


def _controller_correction_positions(
    certificate: MultipleTestingCertificate,
    source_bytes: bytes,
    fact: PValueFamilyFact,
) -> tuple[int, ...] | None:
    try:
        source = source_bytes.decode("utf-8", errors="strict")
        tree = ast.parse(source, feature_version=(3, 11))
    except (UnicodeDecodeError, SyntaxError, ValueError, RecursionError, MemoryError):
        return None
    point = certificate.correction_calls[0].call_span
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _point(point.path, node) == point
    ]
    if len(calls) != 1 or len(calls[0].args) != 1:
        return None
    node = calls[0].args[0]
    battery_name = certificate.test_batteries[0].battery_result_name
    if isinstance(node, ast.Name) and node.id == battery_name:
        return tuple(range(fact.row_count))
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == battery_name
        and isinstance(node.slice, ast.Slice)
        and node.slice.step is None
    ):
        lower = _literal_value(node.slice.lower)
        upper = _literal_value(node.slice.upper)
        if lower is False or upper is False:
            return None
        positions = tuple(range(fact.row_count)[slice(lower, upper)])
        return positions if 0 < len(positions) < fact.row_count else None
    if not (
        isinstance(node, ast.ListComp)
        and isinstance(node.elt, ast.Name)
        and len(node.generators) == 1
        and isinstance(node.generators[0].target, ast.Name)
        and isinstance(node.generators[0].iter, ast.Name)
        and node.generators[0].iter.id == battery_name
        and len(node.generators[0].ifs) == 1
    ):
        return None
    name = node.generators[0].target.id
    predicate = node.generators[0].ifs[0]
    if not (
        node.elt.id == name
        and isinstance(predicate, ast.Compare)
        and isinstance(predicate.left, ast.Name)
        and predicate.left.id == name
        and len(predicate.ops) == 1
        and isinstance(predicate.ops[0], ast.Lt)
        and len(predicate.comparators) == 1
    ):
        return None
    threshold = _fixed_decimal_source(predicate.comparators[0], source)
    if threshold is None:
        return None
    positions = tuple(
        index for index, raw in enumerate(fact.raw_pvalue_lexemes) if Decimal(raw) < threshold
    )
    return positions if 0 < len(positions) < fact.row_count else None


def _proposal_matches_context(
    certificate: MultipleTestingCertificate,
    context: FrozenInspectionContext,
    authorities: tuple[FamilyAuthorization, ...],
) -> bool:
    sources = tuple(
        item
        for item in context.documents
        if item.path == certificate.source_path and item.content_digest == certificate.source_digest
    )
    if len(sources) != 1 or not _parser_is_supported(
        sources[0], certificate.parser_id, certificate.parser_version
    ):
        return False
    if len(authorities) != 1:
        return False
    authority = authorities[0]
    binding = certificate.case_binding
    obligation = certificate.family_domain_obligations[0]
    selected_path = _selected_artifact_path(context)
    affected = _affected_target_ref(context, selected_path) if selected_path else None
    required_pins = _pinned_version(context.material_inputs, "scipy") == _SCIPY_VERSION
    if certificate.correction_calls[0].resolved_callable == _STATSMODELS_BH_CALLABLE:
        required_pins = required_pins and (
            _pinned_version(context.material_inputs, "statsmodels") == _STATSMODELS_VERSION
        )
    return (
        certificate.source_extent == _module_point(sources[0])
        and certificate.dependency_closure_digest
        == _dependency_closure_digest(context.material_inputs)
        and authority.analysis_target_ref == binding.analysis_target_ref
        and authority.correction_procedure_ref == binding.correction_procedure_ref
        and authority.family_definition_id == binding.family_definition_id
        and authority.battery_construct_id == binding.battery_construct_id
        and authority.iterable_row_domain == binding.iterable_row_domain
        and authority.authorized_family_key_columns == binding.authorized_family_key_columns
        and authority.family_input_path == binding.family_input_path
        and authority.family_input_content_digest == binding.family_input_content_digest
        and authority.family_member_rule == "all_rows"
        and _record_ref_exists_once(context, authority.analysis_target_ref)
        and _procedure_record_allows(
            context,
            authority.correction_procedure_ref,
            certificate.correction_calls[0].resolved_callable,
        )
        and _material(
            context.material_inputs,
            obligation.input_binding.path,
            obligation.input_binding.content_digest,
        )
        is not None
        and selected_path == certificate.report_bindings[0].path
        and affected == binding.affected_target_ref
        and required_pins
    )


_AUTHORITY_KEYS = frozenset(
    {
        "record_type",
        "record_id",
        "actor_id",
        "authority_state",
        "analysis_target_ref",
        "correction_procedure_ref",
        "family_definition_id",
        "battery_construct_id",
        "iterable_row_domain",
        "authorized_family_key_columns",
        "family_member_rule",
        "family_input_path",
        "family_input_content_digest",
    }
)


def _authority_hints(
    context: FrozenInspectionContext,
) -> tuple[tuple[_AuthorityHint, ...], bool]:
    hints: list[_AuthorityHint] = []
    malformed = False
    for record in context.base_records:
        if record.ref.record_type != "human_pvalue_family_authorization":
            continue
        hint = _parse_authority(record)
        if hint is None:
            malformed = True
        else:
            hints.append(hint)
    return tuple(hints), malformed


def _trusted_authorizations(
    context: FrozenInspectionContext,
) -> tuple[FamilyAuthorization, ...]:
    hints, malformed = _authority_hints(context)
    if malformed:
        return ()
    return tuple(
        FamilyAuthorization(
            record_type="human_pvalue_family_authorization",
            record_id=item.record_id,
            actor_id=item.actor_id,
            authority_state="authorized",
            analysis_target_ref=item.analysis_target_ref,
            correction_procedure_ref=item.correction_procedure_ref,
            family_definition_id=item.family_definition_id,
            battery_construct_id=item.battery_construct_id,
            iterable_row_domain=item.iterable_row_domain,
            authorized_family_key_columns=item.authorized_family_key_columns,
            family_member_rule=item.family_member_rule,
            family_input_path=item.family_input_path,
            family_input_content_digest=item.family_input_content_digest,
        )
        for item in hints
    )


def _parse_authority(record: FrozenBaseRecord) -> _AuthorityHint | None:
    value = _record_value(record)
    if not isinstance(value, dict) or set(value) != _AUTHORITY_KEYS:
        return None
    analysis_ref = _recognition_ref(value.get("analysis_target_ref"), "analysis")
    procedure_ref = _recognition_ref(value.get("correction_procedure_ref"), "procedure")
    columns = value.get("authorized_family_key_columns")
    string_fields = (
        "record_id",
        "actor_id",
        "family_definition_id",
        "battery_construct_id",
        "iterable_row_domain",
        "family_input_path",
        "family_input_content_digest",
    )
    if not (
        value.get("record_type") == "human_pvalue_family_authorization"
        and value.get("authority_state") == "authorized"
        and record.ref.record_id == value.get("record_id")
        and analysis_ref is not None
        and procedure_ref is not None
        and all(
            isinstance(value.get(name), str) and _present(value[name]) for name in string_fields
        )
        and isinstance(columns, list)
        and columns
        and all(isinstance(item, str) and item for item in columns)
        and len(columns) == len(set(columns))
        and value.get("family_member_rule") == "all_rows"
        and _relative_path(cast(str, value["family_input_path"]))
        and _sha256_literal(cast(str, value["family_input_content_digest"]))
    ):
        return None
    return _AuthorityHint(
        record_id=cast(str, value["record_id"]),
        actor_id=cast(str, value["actor_id"]),
        analysis_target_ref=analysis_ref,
        correction_procedure_ref=procedure_ref,
        family_definition_id=cast(str, value["family_definition_id"]),
        battery_construct_id=cast(str, value["battery_construct_id"]),
        iterable_row_domain=cast(str, value["iterable_row_domain"]),
        authorized_family_key_columns=tuple(cast(list[str], columns)),
        family_member_rule="all_rows",
        family_input_path=cast(str, value["family_input_path"]),
        family_input_content_digest=cast(str, value["family_input_content_digest"]),
    )


def _pinned_version(
    materials: tuple[FrozenMaterialInput, ...],
    package: str,
) -> str | None:
    exact = re.compile(
        rf"^\s*{re.escape(package)}\s*==\s*([A-Za-z0-9.!+_-]+)\s*(?:#.*)?$",
        flags=re.IGNORECASE,
    )
    mention = re.compile(rf"(?i)^{re.escape(package)}(?:\b|\[|[<>=!~])")
    matches: list[str] = []
    for material in materials:
        name = Path(material.path).name.lower()
        if not (name.startswith("requirements") and name.endswith(".txt")):
            continue
        try:
            text = material.content.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return None
        versions: list[str] = []
        for line in text.splitlines():
            match = exact.fullmatch(line)
            if match is not None:
                versions.append(match.group(1))
            else:
                stripped = line.lstrip()
                if stripped and not stripped.startswith("#") and mention.match(stripped):
                    return None
        if len(versions) > 1:
            return None
        matches.extend(versions)
    return matches[0] if len(matches) == 1 else None


def _candidate_key_columns(
    material: FrozenMaterialInput,
    line_model: str,
) -> tuple[str, ...] | None:
    try:
        text = material.content.decode("utf-8", errors="strict")
        if text.startswith("\ufeff"):
            return None
        reader = (
            csv.DictReader(text.splitlines())
            if line_model == "splitlines"
            else csv.DictReader(io.StringIO(text, newline=""))
            if line_model == "csv_newline"
            else None
        )
        if reader is None:
            return None
        header = reader.fieldnames
    except (csv.Error, UnicodeError, ValueError, OverflowError):
        return None
    if (
        not header
        or len(header) != len(set(header))
        or any(not item for item in header)
        or _VALUE_COLUMN not in header
    ):
        return None
    columns = tuple(item for item in header if item != _VALUE_COLUMN)
    return columns or None


def _failed_discharge(
    certificate: MultipleTestingCertificate,
    construct: str,
) -> DischargedMultipleTestingAnalysis:
    return DischargedMultipleTestingAnalysis(
        state="unsupported",
        outcome="unsupported",
        certificate=certificate,
        trusted_family_facts=(),
        trusted_family_authorizations=(),
        verified_certificate=None,
        basis=f"Controller discharge abstained: {construct}.",
    )


def _without_certificate(
    state: AnalysisState,
    *,
    candidates: tuple[str, ...] = (),
    unresolved: tuple[str, ...] = (),
    unsupported: tuple[str, ...] = (),
    effects: tuple[Effect, ...] = (),
    basis: str,
) -> PythonMultipleTestingAnalysis:
    outcome: RecognitionOutcome = cast(RecognitionOutcome, state)
    return PythonMultipleTestingAnalysis(
        state=state,
        outcome=outcome,
        certificate=None,
        candidate_family_key_columns=candidates,
        unresolved_dimensions=tuple(dict.fromkeys(unresolved)),
        unsupported_constructs=tuple(dict.fromkeys(unsupported)),
        effects=effects,
        basis=basis,
    )


def _unsupported_tree(tree: ast.Module, construct: str) -> PythonMultipleTestingAnalysis:
    return _unsupported_nodes(tree, construct, (tree,))


def _unsupported_nodes(
    tree: ast.Module,
    construct: str,
    nodes: tuple[ast.AST, ...],
) -> PythonMultipleTestingAnalysis:
    del tree
    return _without_certificate(
        "unsupported",
        unsupported=(construct,),
        effects=tuple(_opaque_effect(node, construct) for node in nodes),
        basis=f"At least one live source subtree was outside the v1 grammar: {construct}.",
    )


def _opaque_effect(node: ast.AST, reason: str) -> Effect:
    reads = frozenset(
        item.id
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
    )
    return Effect(
        reads=reads,
        writes=frozenset({"*"}),
        aliases=frozenset(),
        may_raise=True,
        opaque=True,
        reason=f"unmodeled subtree: {reason}",
    )


def _dependency_closure_digest(materials: tuple[FrozenMaterialInput, ...]) -> str:
    return semantic_digest(
        [
            item.digest_projection()
            for item in sorted(
                materials,
                key=lambda value: (
                    value.path,
                    value.content_digest,
                    value.file_ref.record_id,
                    value.asset_identity_ref.record_id,
                ),
            )
        ]
    )


def _material_by_path(
    materials: tuple[FrozenMaterialInput, ...], path: str
) -> FrozenMaterialInput | None:
    matches = tuple(item for item in materials if item.path == path)
    return matches[0] if len(matches) == 1 else None


def _material(
    materials: tuple[FrozenMaterialInput, ...],
    path: str,
    digest: str,
) -> FrozenMaterialInput | None:
    matches = tuple(
        item for item in materials if item.path == path and item.content_digest == digest
    )
    return matches[0] if len(matches) == 1 else None


def _selected_artifact_path(context: FrozenInspectionContext) -> str | None:
    matches: list[str] = []
    for record in context.base_records:
        if record.ref != context.selected_artifact_ref:
            continue
        value = _record_value(record)
        if isinstance(value, dict) and isinstance(value.get("path"), str):
            path = value["path"]
            if _relative_path(path):
                matches.append(path)
    return matches[0] if len(matches) == 1 else None


def _affected_target_ref(context: FrozenInspectionContext, path: str) -> RecordRef | None:
    matches: list[RecordRef] = []
    for record in context.base_records:
        if record.ref.record_type not in {"result", "claim"}:
            continue
        value = _record_value(record)
        if isinstance(value, dict) and value.get("path") == path:
            matches.append(RecordRef(record.ref.record_type, record.ref.record_id))
    return matches[0] if len(matches) == 1 else None


def _record_ref_exists_once(context: FrozenInspectionContext, ref: RecordRef) -> bool:
    return (
        sum(
            record.ref.record_type == ref.record_type and record.ref.record_id == ref.record_id
            for record in context.base_records
        )
        == 1
    )


def _procedure_record_allows(
    context: FrozenInspectionContext,
    ref: RecordRef,
    resolved_callable: str,
) -> bool:
    matches = [
        record
        for record in context.base_records
        if record.ref.record_type == ref.record_type and record.ref.record_id == ref.record_id
    ]
    if len(matches) != 1:
        return False
    value = _record_value(matches[0])
    if not isinstance(value, dict):
        return False
    declared = value.get("resolved_callable")
    return declared is None or declared == resolved_callable


def _parser_is_supported(
    document: InspectionDocument,
    parser_id: str,
    parser_version: str,
) -> bool:
    try:
        return _python_parser_supported(document, parser_id, parser_version)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
        return False


def _record_value(record: FrozenBaseRecord) -> object:
    try:
        return json.loads(record.canonical_payload)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def _recognition_ref(value: object, expected: str) -> RecordRef | None:
    if not isinstance(value, dict) or set(value) != {"record_type", "record_id"}:
        return None
    if value.get("record_type") != expected or not isinstance(value.get("record_id"), str):
        return None
    record_id = value["record_id"]
    return RecordRef(expected, record_id) if _present(record_id) else None


def _single_target(assignment: ast.Assign) -> str | None:
    if len(assignment.targets) != 1 or not isinstance(assignment.targets[0], ast.Name):
        return None
    return assignment.targets[0].id


def _dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent is not None else None
    return None


def _path_call(node: ast.expr) -> str | None:
    if not (
        isinstance(node, ast.Call)
        and _dotted_name(node.func) == "Path"
        and len(node.args) == 1
        and not node.keywords
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
        and _relative_path(node.args[0].value)
    ):
        return None
    return node.args[0].value


def _exact_utf8_keyword(keywords: list[ast.keyword]) -> bool:
    return (
        len(keywords) == 1
        and keywords[0].arg == "encoding"
        and isinstance(keywords[0].value, ast.Constant)
        and keywords[0].value.value == "utf-8"
    )


def _exact_open_keywords(keywords: list[ast.keyword]) -> bool:
    values = {item.arg: item.value for item in keywords if item.arg is not None}
    return (
        len(values) == len(keywords) == 2
        and set(values) == {"encoding", "newline"}
        and isinstance(values["encoding"], ast.Constant)
        and values["encoding"].value == "utf-8"
        and isinstance(values["newline"], ast.Constant)
        and values["newline"].value == ""
    )


def _literal_nonnegative(node: ast.expr | None) -> bool:
    return node is None or (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
        and node.value >= 0
    )


def _literal_value(node: ast.expr | None) -> int | bool | None:
    if node is None:
        return None
    if not _literal_nonnegative(node):
        return False
    return cast(int, cast(ast.Constant, node).value)


def _fixed_decimal_source(node: ast.expr, source: str) -> Decimal | None:
    segment = ast.get_source_segment(source, node)
    if segment is None or _FIXED_POINT_DECIMAL.fullmatch(segment) is None:
        return None
    try:
        value = Decimal(segment)
    except InvalidOperation:
        return None
    return value if value.is_finite() and 0 <= value <= 1 else None


def _canonical_decimal(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _point(path: str, node: ast.AST) -> EvidencePoint:
    return EvidencePoint(
        path=path,
        start_line=getattr(node, "lineno", 1),
        end_line=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
        start_column=getattr(node, "col_offset", 0) + 1,
        end_column=max(
            getattr(node, "col_offset", 0) + 1,
            getattr(node, "end_col_offset", getattr(node, "col_offset", 0)) + 1,
        ),
    )


def _module_point(document: InspectionDocument) -> EvidencePoint:
    text = document.content.decode("utf-8", errors="strict")
    lines = text.splitlines()
    if not lines:
        return EvidencePoint(document.path, 1, 1, 1, 1)
    return EvidencePoint(document.path, 1, len(lines), 1, len(lines[-1]) + 1)


def _unused_point(
    document: InspectionDocument,
    used: frozenset[EvidencePoint],
) -> EvidencePoint:
    text = document.content.decode("utf-8", errors="strict")
    for line_number, line in enumerate(text.splitlines(), start=1):
        for column in range(1, len(line) + 1):
            candidate = EvidencePoint(document.path, line_number, line_number, column, column + 1)
            if candidate not in used:
                return candidate
    raise ValueError("source extent cannot allocate scope evidence")


def _evidence_id(path: str, kind: str, point: EvidencePoint) -> str:
    return "evidence:" + semantic_digest({"path": path, "kind": kind, "point": asdict(point)})


def _relative_path(value: str) -> bool:
    segments = value.split("/")
    return (
        _present(value)
        and not value.startswith("/")
        and "\\" not in value
        and "\x00" not in value
        and not any(unicodedata.category(character).startswith("C") for character in value)
        and not any(unicodedata.category(character) in {"Zl", "Zp"} for character in value)
        and all(segment not in {"", ".", ".."} for segment in segments)
        and not (len(value) >= 2 and value[0].isalpha() and value[1] == ":")
    )


def _sha256_literal(value: str) -> bool:
    suffix = value.removeprefix("sha256:")
    return (
        value.startswith("sha256:")
        and len(suffix) == 64
        and all(character in "0123456789abcdef" for character in suffix)
    )


def _present(value: str) -> bool:
    return bool(value) and value == value.strip()


__all__ = [
    "DischargedMultipleTestingAnalysis",
    "PythonMultipleTestingAnalysis",
    "analyze_multiple_testing_python",
    "discharge_multiple_testing_proposal",
]
