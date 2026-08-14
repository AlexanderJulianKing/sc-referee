"""Frozen proof records for the unregistered dependence growth-1 shadow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sc_referee.dependence_recognition.ir import RecordRef

MAX_V2_SOURCE_BYTES = 1 * 1024 * 1024
MAX_V2_AST_NODES = 50_000
MAX_V2_INLINE_DEPTH = 3
MAX_V2_GROUPS = 256

CastKind = Literal["none", "float", "int"]
GrowthConclusion = Literal["repeated_units", "one_observation_per_unit"]


@dataclass(frozen=True, order=True)
class GroupValueSequence:
    """One byte-exact group and its ordered, multiplicity-preserving rows."""

    group_key: str
    row_indices: tuple[int, ...]
    observation_ids: tuple[str, ...]
    authorized_unit_ids: tuple[str, ...]
    source_values: tuple[str, ...]
    cast_value_reprs: tuple[str, ...]


@dataclass(frozen=True)
class GroupValueSequenceFact:
    """Trusted frozen-CSV fact used by the growth certificate kernel."""

    evidence_id: str
    path: str
    content_digest: str
    file_ref: RecordRef
    asset_identity_ref: RecordRef
    line_model: str
    reader_form: str
    encoding: str
    ascii_bytes_proven: bool
    header: tuple[str, ...]
    authorized_unit_column: str
    group_key_column: str
    value_column: str
    cast_kind: CastKind
    row_count: int
    groups: tuple[GroupValueSequence, ...]
    predeclared_bucket_keys: tuple[str, ...]


@dataclass(frozen=True, order=True)
class GroupValueSequenceObligation:
    """Analyzer request discharged only from controller-frozen bytes."""

    path: str
    content_digest: str
    line_model: str
    reader_form: str
    encoding: str
    authorized_unit_column: str
    group_key_column: str
    value_column: str
    cast_kind: CastKind
    predeclared_bucket_keys: tuple[str, ...]


@dataclass(frozen=True, order=True)
class OperandGroupBinding:
    """One procedure positional argument bound to one proven group key."""

    position: int
    argument_name: str
    group_key: str


@dataclass(frozen=True, order=True)
class AlphaRename:
    """One mandatory fresh-name witness for a single inlined call site."""

    function_name: str
    call_token: str
    original_name: str
    fresh_name: str


@dataclass(frozen=True)
class DependenceGrowthCertificate:
    """Untrusted proposal checked against source and a trusted group fact."""

    certificate_id: str
    source_path: str
    source_digest: str
    source_extent: tuple[int, int]
    analysis_target_ref: RecordRef
    procedure_ref: RecordRef
    authority_record_id: str
    independent_unit_definition_id: str
    obligation: GroupValueSequenceObligation
    resolved_callable: str
    procedure_call_token: str
    result_name: str
    sink_token: str
    group_container_name: str
    operand_bindings: tuple[OperandGroupBinding, ...]
    alpha_renames: tuple[AlphaRename, ...]
    dead_syntactic_construct_tokens: tuple[str, ...]
    conclusion: GrowthConclusion


@dataclass(frozen=True)
class VerifiedDependenceGrowthCertificate:
    """Kernel-authorized growth conclusion and its exact bound fact."""

    certificate_id: str
    source_path: str
    source_digest: str
    resolved_callable: str
    conclusion: GrowthConclusion
    fact: GroupValueSequenceFact
    operand_bindings: tuple[OperandGroupBinding, ...]
    repeated_unit_ids: tuple[str, ...]
    alpha_renames: tuple[AlphaRename, ...]
    dead_syntactic_construct_tokens: tuple[str, ...]


@dataclass(frozen=True)
class GrowthAnalysis:
    """Untrusted analyzer result before controller-side proof discharge."""

    state: Literal["proposal", "question", "unsupported", "not_applicable"]
    certificate: DependenceGrowthCertificate | None
    obligation: GroupValueSequenceObligation | None
    abstention_reasons: tuple[str, ...]
    candidate_key_columns: tuple[str, ...]
    basis: str


@dataclass(frozen=True)
class DischargedGrowthAnalysis:
    """Controller-side proof and kernel outcome."""

    state: Literal["verified", "question", "unsupported", "not_applicable"]
    verified_certificate: VerifiedDependenceGrowthCertificate | None
    abstention_reasons: tuple[str, ...]
    candidate_key_columns: tuple[str, ...]
    basis: str
