"""Typed proof records for the dependence semantic v1 shadow recognizer.

The future analyzer may only propose :class:`DependenceCertificate` values.
The compact kernel in :mod:`sc_referee.dependence_recognition.certificate`
recomputes the closed structural obligations before returning a
``VerifiedDependenceCertificate``.  This module intentionally contains no
analysis, parsing, filesystem, or execution logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sc_referee.scientific_checks.founder_orientation_semantic_ir import (
    Effect,
    EvidencePoint,
    LineModel,
    Unknown,
)

MAX_DEPENDENCE_CSV_DOMAIN_BYTES = 8 * 1024 * 1024
MAX_DEPENDENCE_CSV_DOMAIN_ROWS = 100_000
MAX_DEPENDENCE_CSV_DOMAIN_FIELDS = 256
MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES = 64 * 1024
MAX_V1_MEMBERSHIPS = 10_000

RECOGNIZED_LINE_MODELS: tuple[LineModel, ...] = ("splitlines", "csv_newline")
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

ReaderForm = Literal["csv_dictreader_splitlines", "csv_dictreader_file"]
RECOGNIZED_READER_MODELS: tuple[tuple[ReaderForm, LineModel], ...] = (
    ("csv_dictreader_splitlines", "splitlines"),
    ("csv_dictreader_file", "csv_newline"),
)
FrameTransformOperation = Literal["identity"]
ProcedureIndependenceModel = Literal["row_independent", "paired"]
SafeguardState = Literal["present", "absent", "not_applicable", "unknown", "unsupported"]
SafeguardBasis = Literal["completeness-equation", "recognized-collapse", "registry-match"]
DependenceConclusion = Literal["repeated_units", "one_observation_per_unit"]
DependenceOutputCeiling = Literal["evaluation_candidate"]
StaticWordingCeiling = Literal["static_code_relationship_only"]


@dataclass(frozen=True, order=True)
class RecordRef:
    """One exact internal record reference used by the closed proof language."""

    record_type: str
    record_id: str


@dataclass(frozen=True, order=True)
class HumanMethodAuthorization:
    """The existing declaration-adapter authority shape, retained exactly."""

    record_type: str
    record_id: str
    actor_id: str
    authority_state: str
    analysis_target_ref: RecordRef
    procedure_ref: RecordRef
    independent_unit_definition_id: str
    authorized_key_columns: tuple[str, ...]
    input_path: str
    input_content_digest: str


@dataclass(frozen=True, order=True)
class DependenceCaseBinding:
    """Untrusted proposal operands later checked against trusted authority."""

    case_id: str
    analysis_target_ref: RecordRef
    procedure_ref: RecordRef
    affected_target_ref: RecordRef
    independent_unit_definition_id: str
    authorized_key_columns: tuple[str, ...]


@dataclass(frozen=True, order=True)
class MaterialInputBinding:
    """One path-and-digest-bound frozen material input (O1)."""

    path: str
    content_digest: str
    file_ref: RecordRef
    asset_identity_ref: RecordRef


@dataclass(frozen=True, order=True)
class ReaderBinding:
    """One exact supported ``csv.DictReader`` runtime model (O2)."""

    token: str
    reader_form: ReaderForm
    line_model: LineModel
    dialect: str


@dataclass(frozen=True, order=True)
class UnitKeyMultiplicityFact:
    """Trusted bounded fact over one exact ordered CSV unit key (O1-O7).

    ``observation_ids`` and ``unit_ids`` are positionally aligned.  Unit ids
    are deterministic identities produced from byte-exact key tuples by the
    future trusted prover; the kernel recomputes their multiplicities.
    """

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
    key_columns: tuple[str, ...]
    normalization: str
    declared_missing_value_tokens: tuple[str, ...]
    missing_key_value_count: int
    row_shape_complete: bool
    row_count: int
    observation_ids: tuple[str, ...]
    key_value_tuples: tuple[tuple[str, ...], ...]
    unit_ids: tuple[str, ...]
    distinct_key_count: int
    multiplicities: tuple[tuple[str, int], ...]
    repeated_unit_ids: tuple[str, ...]


@dataclass(frozen=True, order=True)
class UnitKeyMultiplicityObligation:
    """Analyzer obligation discharged by one trusted multiplicity fact."""

    input_binding: MaterialInputBinding
    reader: ReaderBinding
    row_domain: str
    key_columns: tuple[str, ...]


@dataclass(frozen=True, order=True)
class FrameTransform:
    """One exact transform in the v1 frame-lineage grammar (O8)."""

    token: str
    operation: FrameTransformOperation
    input_row_domain: str
    output_row_domain: str
    grouping_columns: tuple[str, ...]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class FrameLineage:
    """A digest-bound read, closed transform chain, and procedure consumer."""

    token: str
    input_binding: MaterialInputBinding
    reader: ReaderBinding
    source_row_domain: str
    transforms: tuple[FrameTransform, ...]
    analyzed_row_domain: str
    source_observation_ids: tuple[str, ...]
    analyzed_observation_ids: tuple[str, ...]
    output_token: str
    procedure_call_token: str
    relevant_origins: frozenset[str]
    relevant_bindings: frozenset[str]


@dataclass(frozen=True, order=True)
class BoundPackageVersion:
    """One exact imported package version tied to requirements/lock evidence."""

    package_name: str
    version: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class ProcedureCall:
    """One exact resolved live call proposed against the finite v1 registry."""

    token: str
    analysis_target_ref: RecordRef
    procedure_ref: RecordRef
    resolved_callable: str
    positional_argument_tokens: tuple[str, ...]
    positional_argument_frame_bindings: tuple[tuple[str, str], ...]
    keyword_argument_names: tuple[str, ...]
    frame_lineage_token: str
    analyzed_row_domain: str
    package_version: BoundPackageVersion
    unit_operand_columns: tuple[str, ...]
    result_token: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class SafeguardCheckObligation:
    """One bound registry check and its syntactic-completeness proof (O10)."""

    safeguard_id: str
    state: SafeguardState
    analysis_target_ref: RecordRef
    procedure_ref: RecordRef
    independent_unit_definition_id: str
    evidence_ids: tuple[str, ...]
    basis: SafeguardBasis
    complete_syntactic_construct_tokens: frozenset[str]
    modeled_construct_tokens: frozenset[str]
    proven_dead_construct_tokens: frozenset[str]
    matched_construct_tokens: frozenset[str]


@dataclass(frozen=True)
class SinkLineageObligation:
    """One selected report/result sink reached by the procedure output (O12)."""

    token: str
    path: str
    affected_target_ref: RecordRef
    procedure_call_token: str
    procedure_result_token: str
    payload_tokens: frozenset[str]
    selected_result: bool
    conclusion: DependenceConclusion
    evidence_ids: tuple[str, ...]
    relevant_origins: frozenset[str]
    relevant_bindings: frozenset[str]


@dataclass(frozen=True, order=True)
class EvidenceDeclaration:
    """One stable evidence identity bound to one exact source/data span."""

    evidence_id: str
    point: EvidencePoint


@dataclass(frozen=True)
class DependenceCertificate:
    """An untrusted analyzer proposal; only the kernel may accept it."""

    source_path: str
    source_digest: str
    parser_id: str
    parser_version: str
    source_extent: EvidencePoint
    dependency_closure_digest: str
    proposed_case_digest: str
    replay_digest: str
    case_binding: DependenceCaseBinding
    frame_lineage: FrameLineage
    procedure_call: ProcedureCall
    multiplicity_obligations: tuple[UnitKeyMultiplicityObligation, ...]
    safeguard_checks: tuple[SafeguardCheckObligation, ...]
    sinks: tuple[SinkLineageObligation, ...]
    all_syntactic_construct_tokens: frozenset[str]
    dead_syntactic_construct_tokens: frozenset[str]
    all_sink_tokens: frozenset[str]
    dead_sink_tokens: frozenset[str]
    reaching_path_conclusions: tuple[frozenset[DependenceConclusion], ...]
    effects: tuple[Effect, ...]
    unknowns: tuple[Unknown, ...]
    safeguard_registry_ids: tuple[str, ...]
    output_ceiling: DependenceOutputCeiling
    wording_ceiling: StaticWordingCeiling
    evidence: tuple[EvidenceDeclaration, ...]


@dataclass(frozen=True)
class VerifiedDependenceCertificate:
    """The trusted kernel's accepted, report-only static proof."""

    source_path: str
    source_digest: str
    case_binding: DependenceCaseBinding
    frame_lineage: FrameLineage
    procedure_call: ProcedureCall
    conclusion: DependenceConclusion
    repeated_unit_ids: tuple[str, ...]
    source_frame_repeated_unit_ids: tuple[str, ...]
    applicable_safeguard_ids: tuple[str, ...]
    domain_fact: UnitKeyMultiplicityFact
    sink_tokens: tuple[str, ...]
    evidence: tuple[EvidenceDeclaration, ...]
    proposed_case_digest: str
    output_ceiling: DependenceOutputCeiling
    wording_ceiling: StaticWordingCeiling
