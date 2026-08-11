"""Frozen proof records for multiple-testing recognition v1.

The future analyzer may propose :class:`MultipleTestingCertificate` records,
but it cannot supply expanded test positions, family cardinalities, normalized
slice positions, or precomputed family relations.  The trusted kernel derives
those values by parsing the frozen module bytes and joining them to a separately
trusted ordered family fact and human family authorization.

This module is intentionally stdlib-only apart from the three shared founder IR
value types.  It performs no parsing, I/O, analysis, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sc_referee.scientific_checks.founder_orientation_semantic_ir import (
    Effect,
    EvidencePoint,
    Unknown,
)

# Duplicated rather than imported from any other recognizer or calculation
# adapter.  These constants are part of this recognizer's independent envelope.
MAX_MULTIPLE_TESTING_SOURCE_BYTES = 1_000_000
MAX_MULTIPLE_TESTING_AST_NODES = 50_000
MAX_PVALUE_FAMILY_SOURCE_BYTES = 1_000_000
MAX_PVALUE_FAMILY_ROWS = 10_000
MAX_PVALUE_FAMILY_COLUMNS = 64
MAX_PVALUE_FAMILY_FIELD_BYTES = 64 * 1024
MAX_PVALUE_FAMILY_PROOF_RECORD_BYTES = 8 * 1024 * 1024
MAX_TEST_ARGUMENT_DOMAIN_SOURCE_BYTES = 1_000_000
MAX_TEST_ARGUMENT_DOMAIN_ROWS = 10_000
MAX_TEST_ARGUMENT_DOMAIN_COLUMNS = 64
MAX_TEST_ARGUMENT_DOMAIN_FIELD_BYTES = 64 * 1024
MAX_TEST_ARGUMENT_DOMAIN_PROOF_RECORD_BYTES = 8 * 1024 * 1024
MAX_MULTIPLE_TESTING_EVIDENCE_DECLARATIONS = 4_096

SPLITLINES_ONLY_SEPARATORS = (
    "\x0b",
    "\x0c",
    "\x1c",
    "\x1d",
    "\x1e",
    "\x85",
    "\u2028",
    "\u2029",
)

LineModel = Literal["splitlines", "csv_newline"]
ReaderForm = Literal["csv_dictreader_splitlines", "csv_dictreader_file"]
MultipleTestingOutputCeiling = Literal["report_only"]
MultipleTestingWordingCeiling = Literal["supported_normal_path_static_relationship_only"]
MultipleTestingConclusion = Literal["correction_subset", "complete_family_correction"]
FamilyScopeBasis = Literal[
    "bounded-ast-completeness",
    "trusted-family-domain",
    "literal-narrowing-slice",
    "token-multiset-relation",
    "trusted-bh-recomputation",
]

RECOGNIZED_READER_MODELS: tuple[tuple[ReaderForm, LineModel], ...] = (
    ("csv_dictreader_splitlines", "splitlines"),
    ("csv_dictreader_file", "csv_newline"),
)
REQUIRED_SCOPE_BASES: tuple[FamilyScopeBasis, ...] = (
    "bounded-ast-completeness",
    "trusted-family-domain",
    "literal-narrowing-slice",
    "token-multiset-relation",
    "trusted-bh-recomputation",
)


@dataclass(frozen=True, order=True)
class RecordRef:
    """One exact internal record reference in the closed proof language."""

    record_type: str
    record_id: str


@dataclass(frozen=True, order=True)
class MaterialInputBinding:
    """One path-and-digest-bound family table."""

    path: str
    content_digest: str
    file_ref: RecordRef
    asset_identity_ref: RecordRef


@dataclass(frozen=True, order=True)
class FamilyAuthorization:
    """Controller-supplied human authority for one semantic p-value family.

    ``battery_construct_id`` is a source-location token recomputed from the
    frozen source digest and the exact battery-assignment span. It is not a
    semantic identity independent of source layout. ``iterable_row_domain`` is
    also insufficient alone: the input identity and ordered key columns remain
    part of the authorization.
    """

    record_type: str
    record_id: str
    actor_id: str
    authority_state: str
    analysis_target_ref: RecordRef
    correction_procedure_ref: RecordRef
    family_definition_id: str
    battery_construct_id: str
    iterable_row_domain: str
    authorized_family_key_columns: tuple[str, ...]
    family_member_rule: str
    family_input_path: str
    family_input_content_digest: str


@dataclass(frozen=True, order=True)
class MultipleTestingCaseBinding:
    """Untrusted case operands that must exactly match trusted authority."""

    case_id: str
    analysis_target_ref: RecordRef
    correction_procedure_ref: RecordRef
    affected_target_ref: RecordRef
    family_definition_id: str
    battery_construct_id: str
    iterable_row_domain: str
    authorized_family_key_columns: tuple[str, ...]
    family_input_path: str
    family_input_content_digest: str
    measurement_input_path: str
    measurement_input_content_digest: str
    measurement_key_columns: tuple[str, ...]
    left_measurement_columns: tuple[str, ...]
    right_measurement_columns: tuple[str, ...]
    measurement_reader_model: ReaderForm


@dataclass(frozen=True, order=True)
class FamilyDomainObligation:
    """Lookup key for one independently proven ordered p-value family."""

    input_binding: MaterialInputBinding
    reader_form: ReaderForm
    line_model: LineModel
    dialect: str
    iterable_row_domain: str
    hypothesis_key_columns: tuple[str, ...]
    pvalue_column: str
    reader_assignment_span: EvidencePoint
    reader_evidence_ids: tuple[str, ...]


@dataclass(frozen=True, order=True)
class PValueFamilyFact:
    """Trusted, digest-bound ordered family evidence supplied outside a certificate."""

    evidence_id: str
    path: str
    content_digest: str
    file_ref: RecordRef
    asset_identity_ref: RecordRef
    reader_form: ReaderForm
    line_model: LineModel
    splitlines_only_separators_absent: bool
    dialect: str
    row_domain: str
    source_byte_count: int
    header: tuple[str, ...]
    hypothesis_key_columns: tuple[str, ...]
    pvalue_column: str
    normalization: str
    declared_missing_value_tokens: tuple[str, ...]
    missing_key_value_count: int
    missing_pvalue_count: int
    row_shape_complete: bool
    row_count: int
    observation_tokens: tuple[str, ...]
    key_value_tuples: tuple[tuple[str, ...], ...]
    hypothesis_tokens: tuple[str, ...]
    raw_pvalue_lexemes: tuple[str, ...]
    canonical_pvalue_decimals: tuple[str, ...]
    pvalue_tokens: tuple[str, ...]


@dataclass(frozen=True, order=True)
class TestArgumentDomainObligation:
    """M12 source and material binding for the two keyed test operands.

    The proposal carries only exact material identity, literal selectors, bare
    binding names, and source spans.  It cannot carry a key map, row positions,
    parsed values, binary64 values, or position-specific argument tokens.
    """

    input_binding: MaterialInputBinding
    reader_form: ReaderForm
    line_model: LineModel
    dialect: str
    measurement_row_domain: str
    measurement_rows_name: str
    measurement_key_columns: tuple[str, ...]
    left_measurement_columns: tuple[str, ...]
    right_measurement_columns: tuple[str, ...]
    left_argument_name: str
    right_argument_name: str
    reader_assignment_span: EvidencePoint
    left_projection_span: EvidencePoint
    right_projection_span: EvidencePoint
    left_key_span: EvidencePoint
    right_key_span: EvidencePoint
    left_value_span: EvidencePoint
    right_value_span: EvidencePoint
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, order=True)
class TestArgumentDomainFact:
    """Trusted digest-bound keyed measurement evidence supplied externally."""

    evidence_id: str
    path: str
    content_digest: str
    file_ref: RecordRef
    asset_identity_ref: RecordRef
    reader_form: ReaderForm
    line_model: LineModel
    splitlines_only_separators_absent: bool
    dialect: str
    row_domain: str
    source_byte_count: int
    header: tuple[str, ...]
    measurement_key_columns: tuple[str, ...]
    left_measurement_columns: tuple[str, ...]
    right_measurement_columns: tuple[str, ...]
    normalization: str
    declared_missing_value_tokens: tuple[str, ...]
    missing_key_value_count: int
    missing_measurement_value_count: int
    row_shape_complete: bool
    row_count: int
    observation_tokens: tuple[str, ...]
    key_value_tuples: tuple[tuple[str, ...], ...]
    hypothesis_tokens: tuple[str, ...]
    left_raw_measurement_lexemes: tuple[tuple[str, ...], ...]
    right_raw_measurement_lexemes: tuple[tuple[str, ...], ...]
    left_binary64_hex: tuple[tuple[str, ...], ...]
    right_binary64_hex: tuple[tuple[str, ...], ...]


@dataclass(frozen=True, order=True)
class FullFamilyProjectionObligation:
    """Source references for the exact ordered key projection consumed by a battery."""

    battery_construct_id: str
    iterable_row_domain: str
    source_rows_name: str
    projected_family_name: str
    hypothesis_key_columns: tuple[str, ...]
    assignment_span: EvidencePoint
    listcomp_span: EvidencePoint
    element_span: EvidencePoint
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, order=True)
class TestBatteryObligation:
    """Source references for one supported list-comprehension test battery.

    No dynamic position, result token, cardinality, or expanded family is
    represented here; those values exist only after kernel replay.
    """

    battery_construct_id: str
    iterable_row_domain: str
    battery_result_name: str
    projected_family_name: str
    resolved_test_callable: str
    assignment_span: EvidencePoint
    listcomp_span: EvidencePoint
    element_call_span: EvidencePoint
    iterable_span: EvidencePoint
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, order=True)
class CorrectionCall:
    """Source reference and numerical assertion for one direct narrowing correction."""

    battery_construct_id: str
    iterable_row_domain: str
    correction_procedure_ref: RecordRef
    resolved_callable: str
    result_name: str
    call_span: EvidencePoint
    asserted_adjusted_pvalues: tuple[str, ...]
    asserts_trusted_bh_recomputation: bool
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class FamilyScopeCheckObligation:
    """M2 completeness inputs over the syntactic test-call predicate."""

    battery_construct_id: str
    iterable_row_domain: str
    complete_test_call_tokens: frozenset[str]
    modeled_test_call_tokens: frozenset[str]
    proven_dead_test_call_tokens: frozenset[str]
    corrected_test_call_tokens: frozenset[str]
    bases: tuple[FamilyScopeBasis, ...]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReportFamilyBinding:
    """Exact full-family report binding and selected same-module sink."""

    token: str
    path: str
    affected_target_ref: RecordRef
    iterable_row_domain: str
    hypothesis_key_columns: tuple[str, ...]
    pvalue_column: str
    reported_name: str
    assignment_span: EvidencePoint
    sink_span: EvidencePoint
    selected_result: bool
    evidence_ids: tuple[str, ...]
    relevant_origins: frozenset[str]
    relevant_bindings: frozenset[str]


@dataclass(frozen=True, order=True)
class EvidenceDeclaration:
    """One stable evidence identity bound to an exact code or data span."""

    evidence_id: str
    point: EvidencePoint


@dataclass(frozen=True)
class MultipleTestingCertificate:
    """Untrusted proposal; trusted facts, source bytes, and authority stay external."""

    source_path: str
    source_digest: str
    parser_id: str
    parser_version: str
    source_extent: EvidencePoint
    dependency_closure_digest: str
    proposed_case_digest: str
    replay_digest: str
    case_binding: MultipleTestingCaseBinding
    family_domain_obligations: tuple[FamilyDomainObligation, ...]
    test_argument_domain_obligations: tuple[TestArgumentDomainObligation, ...]
    full_family_projections: tuple[FullFamilyProjectionObligation, ...]
    test_batteries: tuple[TestBatteryObligation, ...]
    correction_calls: tuple[CorrectionCall, ...]
    family_scope_checks: tuple[FamilyScopeCheckObligation, ...]
    report_bindings: tuple[ReportFamilyBinding, ...]
    all_syntactic_construct_tokens: frozenset[str]
    dead_syntactic_construct_tokens: frozenset[str]
    all_sink_tokens: frozenset[str]
    dead_sink_tokens: frozenset[str]
    effects: tuple[Effect, ...]
    unknowns: tuple[Unknown, ...]
    output_ceiling: MultipleTestingOutputCeiling
    wording_ceiling: MultipleTestingWordingCeiling
    evidence: tuple[EvidenceDeclaration, ...]


@dataclass(frozen=True, order=True)
class TestResultPosition:
    """Kernel-created position binding for one virtual supported-path test result."""

    position: int
    row_ordinal: int
    hypothesis_token: str
    source_observation_token: str
    element_call_template_token: str
    argument_template_tokens: tuple[str, str]
    argument_vector_tokens: tuple[str, str]
    result_token: str


@dataclass(frozen=True)
class VerifiedMultipleTestingCertificate:
    """Kernel-authorized report-only proof of one exact correction-family relation."""

    source_path: str
    source_digest: str
    conclusion: MultipleTestingConclusion
    case_binding: MultipleTestingCaseBinding
    family_authorization: FamilyAuthorization
    family_fact: PValueFamilyFact
    test_argument_fact: TestArgumentDomainFact
    test_result_positions: tuple[TestResultPosition, ...]
    performed_result_tokens: tuple[str, ...]
    corrected_result_tokens: tuple[str, ...]
    reported_result_tokens: tuple[str, ...]
    corrected_positions: tuple[int, ...]
    recomputed_adjusted_pvalues: tuple[str, ...]
    sink_tokens: tuple[str, ...]
    evidence: tuple[EvidenceDeclaration, ...]
    proposed_case_digest: str
    output_ceiling: MultipleTestingOutputCeiling
    wording_ceiling: MultipleTestingWordingCeiling


__all__ = [
    "CorrectionCall",
    "Effect",
    "EvidenceDeclaration",
    "EvidencePoint",
    "FamilyAuthorization",
    "FamilyDomainObligation",
    "FamilyScopeBasis",
    "FamilyScopeCheckObligation",
    "FullFamilyProjectionObligation",
    "LineModel",
    "MaterialInputBinding",
    "MultipleTestingCaseBinding",
    "MultipleTestingCertificate",
    "MultipleTestingConclusion",
    "PValueFamilyFact",
    "ReaderForm",
    "RecordRef",
    "ReportFamilyBinding",
    "TestArgumentDomainFact",
    "TestArgumentDomainObligation",
    "TestBatteryObligation",
    "TestResultPosition",
    "Unknown",
    "VerifiedMultipleTestingCertificate",
]
