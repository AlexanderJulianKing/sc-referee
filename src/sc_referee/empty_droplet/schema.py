"""Closed, immutable types for exact-or-abstain empty-droplet ingestion."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Literal, Mapping

import numpy as np
from scipy import sparse


ARTIFACT_SCHEMA_ID = "sc-referee/empty-droplet-counts-artifact/v1"
DIGEST_POLICY_ID = "sc-referee/empty-droplet-digest/v1"
DECLARATION_SCHEMA_ID = "sc-referee/empty-droplet-ingest-declaration/v1"


class EmptyDropletUnavailableReason(str, Enum):
    SOURCE_UNREADABLE_OR_UNSAFE = "source_unreadable_or_unsafe"
    INTEGRITY_DRIFT = "integrity_drift"
    CONFIRMATION_PROVENANCE_INCOMPLETE = "confirmation_provenance_incomplete"
    RAW_SOURCE_AMBIGUOUS = "raw_source_ambiguous"
    RAW_ROLE_UNCONFIRMED = "raw_role_unconfirmed"
    RAW_MATRIX_ABSENT = "raw_matrix_absent"
    UNFILTERED_BARCODE_UNIVERSE_ABSENT = "unfiltered_barcode_universe_absent"
    UNSUPPORTED_FORMAT = "unsupported_format"
    MALFORMED_MATRIX = "malformed_matrix"
    MATRIX_OR_MODALITY_AMBIGUOUS = "matrix_or_modality_ambiguous"
    NOT_RAW_INTEGER_COUNTS = "not_raw_integer_counts"
    BARCODE_IDENTITY_INVALID = "barcode_identity_invalid"
    FEATURE_IDENTITY_INVALID = "feature_identity_invalid"
    EMPTY_SET_UNDEFINED = "empty_set_undefined"
    EMPTY_METHOD_UNVERIFIABLE = "empty_method_unverifiable"
    EMPTY_BARCODE_MISMATCH = "empty_barcode_mismatch"
    EMPTY_CELL_OVERLAP = "empty_cell_overlap"
    EMPTY_AUTHORITIES_CONFLICT = "empty_authorities_conflict"
    EMPTY_POOL_DEGENERATE = "empty_pool_degenerate"
    THRESHOLD_CONTRACT_INVALID = "threshold_contract_invalid"
    RAW_FILTERED_BARCODE_MISMATCH = "raw_filtered_barcode_mismatch"
    RAW_FILTERED_FEATURE_MISMATCH = "raw_filtered_feature_mismatch"
    RAW_ASSEMBLY_SCOPE_UNVERIFIED = "raw_assembly_scope_unverified"
    DIGEST_FAILURE = "digest_failure"
    VERSION_INCOMPATIBLE = "version_incompatible"
    FILTERED_LINK_MISMATCH = "filtered_link_mismatch"


REASON_PRECEDENCE = tuple(EmptyDropletUnavailableReason)


@dataclass(frozen=True)
class EvidenceItem:
    kind: str
    detail: str


@dataclass(frozen=True)
class ArtifactUnavailable:
    reason_code: EmptyDropletUnavailableReason
    message: str
    evidence: tuple[EvidenceItem, ...]
    actionability: str
    secondary_reason_codes: tuple[EmptyDropletUnavailableReason, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", tuple(self.evidence))
        secondary = sorted(set(self.secondary_reason_codes), key=REASON_PRECEDENCE.index)
        object.__setattr__(self, "secondary_reason_codes", tuple(secondary))


@dataclass(frozen=True, order=True)
class BarcodeKey:
    namespace: str
    native_barcode: str


@dataclass(frozen=True, order=True)
class FeatureKey:
    feature_id: str
    feature_name: str | None = None
    feature_type: str = "Gene Expression"
    genome_or_reference: str | None = None


@dataclass(frozen=True)
class SourceDeclaration:
    role: str
    format: str
    compression: str
    path: str
    barcode_key_column: str
    total_count_column: str
    gene_count_columns: tuple[str, ...]
    namespace: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "gene_count_columns", tuple(self.gene_count_columns))


@dataclass(frozen=True)
class MembershipDeclaration:
    method_id: str


@dataclass(frozen=True)
class FilteredLinkDeclaration:
    path: str
    format: str
    compression: str
    cell_key_column: str
    total_count_column: str
    gene_count_columns: tuple[str, ...]
    namespace: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "gene_count_columns", tuple(self.gene_count_columns))


@dataclass(frozen=True)
class ProposalProvenance:
    proposer_kind: str
    proposer_id: str
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", tuple(self.evidence))


@dataclass(frozen=True)
class ConfirmationProvenance:
    confirmer_actor_id: str
    confirmation_event_id: str
    confirmed_at: str


@dataclass(frozen=True)
class IntegrityRecord:
    source_sha256: str
    filtered_source_sha256: str
    semantic_digest: str


@dataclass(frozen=True)
class EmptyDropletIngestDeclaration:
    schema_id: str
    confirmed_by_human: bool
    source: SourceDeclaration
    membership: MembershipDeclaration
    filtered_link: FilteredLinkDeclaration
    proposal: ProposalProvenance
    confirmation: ConfirmationProvenance
    integrity: IntegrityRecord


@dataclass(frozen=True)
class MembershipProvenance:
    method_id: str
    authority: str = "human_confirmed_table_rows"


@dataclass(frozen=True)
class SourceRecord:
    role: str
    relative_path: str
    byte_sha256: str
    format: str
    compression: str


@dataclass(frozen=True)
class FeatureMapping:
    feature_key: FeatureKey
    cells_table_column: int
    empty_feature_column: int


def _freeze_integer_vector(value, *, name: str, dtype) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if array.dtype.kind == "b" or not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{name} must contain exact integers, excluding booleans")
    if np.issubdtype(array.dtype, np.signedinteger) and array.size and np.any(array < 0):
        raise ValueError(f"{name} must be non-negative")
    copied = np.array(array, dtype=dtype, order="C", copy=True)
    return np.frombuffer(copied.tobytes(order="C"), dtype=dtype)


def freeze_u64_vector(value, *, name: str) -> np.ndarray:
    return _freeze_integer_vector(value, name=name, dtype=np.uint64)


def freeze_index_vector(value, *, name: str) -> np.ndarray:
    return _freeze_integer_vector(value, name=name, dtype=np.uint64)


def freeze_bool_vector(value, *, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 1 or array.dtype.kind != "b":
        raise ValueError(f"{name} must be a one-dimensional boolean vector")
    copied = np.array(array, dtype=np.bool_, order="C", copy=True)
    return np.frombuffer(copied.tobytes(order="C"), dtype=np.bool_)


class _FrozenCSR(sparse.csr_matrix):
    """CSR whose owned storage and structural attributes cannot be mutated."""

    _sealed = False

    def __setattr__(self, name, value):
        if getattr(self, "_sealed", False) and name in {"data", "indices", "indptr", "_shape"}:
            raise ValueError("frozen CSR structure is read-only")
        super().__setattr__(name, value)

    def __setitem__(self, key, value):
        if getattr(self, "_sealed", False):
            raise ValueError("frozen CSR values are read-only")
        return super().__setitem__(key, value)


def freeze_csr(value) -> sparse.csr_matrix:
    matrix = sparse.csr_matrix(value, copy=True)
    if matrix.ndim != 2:
        raise ValueError("counts must be two-dimensional")
    if matrix.dtype.kind == "b" or not np.issubdtype(matrix.dtype, np.integer):
        raise ValueError("counts must contain exact integers, excluding booleans")
    if np.issubdtype(matrix.dtype, np.signedinteger) and matrix.data.size and np.any(matrix.data < 0):
        raise ValueError("counts must be non-negative")
    matrix.check_format(full_check=True)
    matrix.sum_duplicates()
    matrix.sort_indices()
    matrix.eliminate_zeros()
    frozen = _FrozenCSR(matrix, copy=True)
    frozen.data = np.frombuffer(
        np.ascontiguousarray(matrix.data, dtype=np.uint64).tobytes(order="C"), dtype=np.uint64
    )
    frozen.indices = np.frombuffer(
        np.ascontiguousarray(matrix.indices, dtype=np.int64).tobytes(order="C"), dtype=np.int64
    )
    frozen.indptr = np.frombuffer(
        np.ascontiguousarray(matrix.indptr, dtype=np.int64).tobytes(order="C"), dtype=np.int64
    )
    frozen._sealed = True
    return frozen


@dataclass(frozen=True)
class FilteredBundleLink:
    filtered_bundle_identity: str
    filtered_source_identity: str
    filtered_cell_ledger: tuple[BarcodeKey, ...]
    filtered_feature_ledger: tuple[FeatureKey, ...]
    bundle_cell_to_cells_table_row: np.ndarray
    bundle_feature_mapping: tuple[FeatureMapping, ...]
    empty_vs_cell_disjoint: bool
    shared_count_coherent: bool
    total_count_coherence: Literal[True, "not_comparable"]
    namespace_policy: str
    link_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "filtered_cell_ledger", tuple(self.filtered_cell_ledger))
        object.__setattr__(self, "filtered_feature_ledger", tuple(self.filtered_feature_ledger))
        object.__setattr__(self, "bundle_feature_mapping", tuple(self.bundle_feature_mapping))
        object.__setattr__(self, "bundle_cell_to_cells_table_row", freeze_index_vector(
            self.bundle_cell_to_cells_table_row, name="bundle_cell_to_cells_table_row"
        ))


@dataclass(frozen=True)
class ArtifactDigests:
    source_byte_hash: str
    filtered_source_byte_hash: str
    confirmation_semantic_digest: str
    matrix_digest: str
    total_count_digest: str
    barcode_ledger_digest: str
    feature_ledger_digest: str
    supplied_membership_ledger_digest: str
    semantic_membership_set_digest: str
    aligned_membership_digest: str
    filtered_cell_ledger_digest: str
    filtered_feature_ledger_digest: str
    cell_mapping_digest: str
    feature_mapping_digest: str
    filtered_bundle_identity: str
    filtered_link_digest: str
    source_provenance_digest: str
    artifact_content_digest: str
    attestation_digest: str


@dataclass(frozen=True)
class EmptyDropletCountsArtifact:
    schema_id: str
    digest_policy_id: str
    counts: sparse.csr_matrix
    total_counts: np.ndarray
    shape: tuple[int, int]
    barcode_ledger: tuple[BarcodeKey, ...]
    feature_ledger: tuple[FeatureKey, ...]
    empty_membership: np.ndarray
    selected_barcodes: tuple[BarcodeKey, ...]
    membership_provenance: MembershipProvenance
    filtered_bundle_link: FilteredBundleLink
    source_provenance: tuple[SourceRecord, ...]
    digests: ArtifactDigests
    droplet_ledger_identity: str
    artifact_content_identity: str
    attestation_identity: str

    def __post_init__(self) -> None:
        counts = freeze_csr(self.counts)
        totals = freeze_u64_vector(self.total_counts, name="total_counts")
        membership = freeze_bool_vector(self.empty_membership, name="empty_membership")
        shape = tuple(self.shape)
        barcodes = tuple(self.barcode_ledger)
        features = tuple(self.feature_ledger)
        if counts.shape != shape or shape != (len(barcodes), len(features)):
            raise ValueError("artifact shape and ledgers must agree")
        if len(totals) != shape[0] or len(membership) != shape[0]:
            raise ValueError("row-aligned vectors must match artifact rows")
        object.__setattr__(self, "counts", counts)
        object.__setattr__(self, "total_counts", totals)
        object.__setattr__(self, "empty_membership", membership)
        object.__setattr__(self, "shape", shape)
        object.__setattr__(self, "barcode_ledger", barcodes)
        object.__setattr__(self, "feature_ledger", features)
        object.__setattr__(self, "selected_barcodes", tuple(self.selected_barcodes))
        object.__setattr__(self, "source_provenance", tuple(self.source_provenance))


@dataclass(frozen=True)
class Available:
    artifact: EmptyDropletCountsArtifact

    def __post_init__(self) -> None:
        if not isinstance(self.artifact, EmptyDropletCountsArtifact):
            raise TypeError("Available requires one complete EmptyDropletCountsArtifact")


EmptyDropletIngestResult = Available | ArtifactUnavailable


class EmptyDropletValidationError(ValueError):
    def __init__(self, reason_code: EmptyDropletUnavailableReason, message: str):
        super().__init__(message)
        self.reason_code = reason_code


def frozen_mapping(value: Mapping[str, str]) -> MappingProxyType:
    return MappingProxyType(dict(value))
