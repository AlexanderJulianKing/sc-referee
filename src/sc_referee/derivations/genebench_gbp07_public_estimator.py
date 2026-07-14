"""Pure implementation of ``genebench_gbp07_public_estimator/v1``.

The caller owns parsing and supplies only the restricted views below.  In
particular, this module has no input through which genotype, submitted results,
or a reference answer can be observed.

Donor output order is exactly ``donor_order``.  It is an explicit typed fitted
unit ledger supplied by the caller; this derivation never infers lexical order.
Within each donor, member cells retain their order in ``CellCountsView``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

import numpy as np

from sc_referee.row_ledger_digest import ledger_digest


DERIVATION_ID = "genebench_gbp07_public_estimator/v1"
ARTIFACT_SCHEMA_ID = "ContaminationBasisArtifact/v1"
DIGEST_POLICY_ID = "gbp07-estimator-digest-v2/canonical-float-digest-v1"
CANONICAL_FLOAT_DIGEST_POLICY_VERSION = "canonical-float-digest-v1"
CANONICAL_FLOAT_SIGNIFICANT_DIGITS = 12
PUBLIC_METHOD_PROVENANCE = (
    "GeneBench-Pro problems/statgen_scrna_ambient_state_eqtl/"
    "report_public.pdf equations 18-23"
)
HIGH_CONTAMINATION_THRESHOLD = 0.18
COMPARISON_SEMANTICS = "strict_greater_than"
_U64_MAX = np.iinfo(np.uint64).max


def _canonical_float_token(value: float) -> str:
    """Return the v1 digest token for one finite derived float.

    Twelve significant decimal digits give a relative rounding budget of at most
    roughly 5e-12 away from zero.  Signed zero is normalized to ``0``.  This is a
    digest policy only: estimator values and the strict 0.18 comparison retain full
    float64 precision.  Quantization reduces platform drift but cannot remove it at
    an exact rounding boundary.
    """

    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError("canonical float digests require finite values")
    if numeric == 0.0:
        return "0"
    return format(numeric, f".{CANONICAL_FLOAT_SIGNIFICANT_DIGITS}g")


def canonical_float_digest(domain: str, values) -> str:
    """Hash an ordered float array after versioned significant-digit quantization."""

    if not isinstance(domain, str) or not domain:
        raise ValueError("canonical float digest domain must be non-empty")
    array = np.asarray(values, dtype=np.float64)
    tokens = tuple(_canonical_float_token(value) for value in array.ravel(order="C"))
    return ledger_digest(
        "canonical-float-digest",
        (CANONICAL_FLOAT_DIGEST_POLICY_VERSION, domain, tuple(array.shape), tokens),
    )


@dataclass(frozen=True, order=True)
class TypedCellId:
    namespace: str
    value: str


@dataclass(frozen=True, order=True)
class TypedDonorId:
    namespace: str
    value: str


def _immutable_array(value) -> np.ndarray:
    copied = np.array(value, order="C", copy=True)
    return np.frombuffer(copied.tobytes(order="C"), dtype=copied.dtype).reshape(copied.shape)


@dataclass(frozen=True)
class EmptyDropletCountsView:
    """Restricted empty-droplet input: totals and named panel counts only."""

    total_umi: np.ndarray
    panel_gene_names: tuple[str, ...]
    panel_counts: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "total_umi", _immutable_array(self.total_umi))
        object.__setattr__(self, "panel_gene_names", tuple(self.panel_gene_names))
        object.__setattr__(self, "panel_counts", _immutable_array(self.panel_counts))


@dataclass(frozen=True)
class CellCountsView:
    """Restricted released-cell input: identity, donor, total UMI, and HBB."""

    cell_id: tuple[TypedCellId, ...]
    donor: tuple[TypedDonorId | None, ...]
    total_umi: np.ndarray
    hbb: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "cell_id", tuple(self.cell_id))
        object.__setattr__(self, "donor", tuple(self.donor))
        object.__setattr__(self, "total_umi", _immutable_array(self.total_umi))
        object.__setattr__(self, "hbb", _immutable_array(self.hbb))


class EstimatorAbstentionReason(str, Enum):
    EMPTY_INPUT = "empty_input"
    ZERO_DENOMINATOR = "zero_denominator"
    MISSING_DONOR = "missing_donor"
    DUPLICATE_DONOR = "duplicate_donor"
    DUPLICATE_CELL = "duplicate_cell"
    NON_FINITE_VALUE = "non_finite_value"
    INVALID_TYPED_INPUT = "invalid_typed_input"
    UINT64_OVERFLOW = "uint64_overflow"


@dataclass(frozen=True)
class Abstained:
    reason_code: EstimatorAbstentionReason
    message: str


@dataclass(frozen=True)
class AmbientProfileEntry:
    gene: str
    ambient_fraction: float


@dataclass(frozen=True)
class DonorContaminationRow:
    fitted_unit_id: TypedDonorId
    donor_rho: float
    high_contamination: bool
    member_cell_count: np.uint64
    member_cell_ledger_identity: str


@dataclass(frozen=True)
class ContaminationArtifactDigests:
    ambient_profile_digest: str
    per_cell_score_vector_digest: str
    donor_aggregation_ledger: str
    donor_score_digest: str
    binary_basis_digest: str
    artifact_identity: str


@dataclass(frozen=True)
class ContaminationBasisArtifact:
    schema_id: str
    derivation_id: str
    digest_policy_id: str
    public_method_provenance: str
    threshold: float
    comparison_semantics: str
    ambient_profile: tuple[AmbientProfileEntry, ...]
    ambient_hbb: float
    cell_scores: np.ndarray
    donor_table: tuple[DonorContaminationRow, ...]
    digests: ContaminationArtifactDigests
    artifact_identity: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ambient_profile", tuple(self.ambient_profile))
        object.__setattr__(self, "cell_scores", _immutable_array(np.asarray(self.cell_scores, dtype="<f8")))
        object.__setattr__(self, "donor_table", tuple(self.donor_table))


@dataclass(frozen=True)
class Estimated:
    artifact: ContaminationBasisArtifact


EstimatorResult = Estimated | Abstained


def _valid_key(value, expected_type: type) -> bool:
    return (
        isinstance(value, expected_type)
        and isinstance(value.namespace, str)
        and bool(value.namespace)
        and isinstance(value.value, str)
        and bool(value.value)
    )


def _validate_count_vector(value: np.ndarray, name: str) -> Abstained | np.ndarray:
    array = np.asarray(value)
    if array.ndim != 1 or array.dtype.kind == "b":
        return Abstained(EstimatorAbstentionReason.INVALID_TYPED_INPUT, f"{name} must be a 1D integer vector")
    if np.issubdtype(array.dtype, np.inexact) and np.any(~np.isfinite(array)):
        return Abstained(EstimatorAbstentionReason.NON_FINITE_VALUE, f"{name} contains a non-finite value")
    if not np.issubdtype(array.dtype, np.integer):
        return Abstained(EstimatorAbstentionReason.INVALID_TYPED_INPUT, f"{name} must contain exact integers")
    if np.issubdtype(array.dtype, np.signedinteger) and array.size and np.any(array < 0):
        return Abstained(EstimatorAbstentionReason.INVALID_TYPED_INPUT, f"{name} must be non-negative")
    if array.size and any(int(item) > _U64_MAX for item in array):
        return Abstained(EstimatorAbstentionReason.UINT64_OVERFLOW, f"{name} exceeds uint64")
    return np.asarray(array, dtype=np.uint64)


def _exact_u64_sum(value: np.ndarray, name: str) -> Abstained | np.uint64:
    exact = sum(int(item) for item in value)
    if exact > _U64_MAX:
        return Abstained(EstimatorAbstentionReason.UINT64_OVERFLOW, f"{name} sum exceeds uint64")
    return np.uint64(exact)


def _artifact(
    ambient_profile: tuple[AmbientProfileEntry, ...],
    ambient_hbb: float,
    cell_ids: tuple[TypedCellId, ...],
    cell_donors: tuple[TypedDonorId, ...],
    cell_scores: np.ndarray,
    donor_rows: tuple[DonorContaminationRow, ...],
) -> ContaminationBasisArtifact:
    ambient_digest = ledger_digest(
        "gbp07-ambient-profile",
        (
            tuple(entry.gene for entry in ambient_profile),
            canonical_float_digest(
                "gbp07-ambient-profile-values",
                tuple(entry.ambient_fraction for entry in ambient_profile),
            ),
        ),
    )
    cell_digest = ledger_digest(
        "gbp07-per-cell-score-vector",
        (
            tuple(zip(cell_ids, cell_donors)),
            canonical_float_digest("gbp07-per-cell-score-values", cell_scores),
        ),
    )
    aggregation_records = tuple(
        (row.fitted_unit_id, int(row.member_cell_count), row.member_cell_ledger_identity)
        for row in donor_rows
    )
    aggregation_digest = ledger_digest("gbp07-donor-aggregation-ledger", aggregation_records)
    donor_score_digest = ledger_digest(
        "gbp07-donor-score-vector",
        (
            tuple(row.fitted_unit_id for row in donor_rows),
            canonical_float_digest(
                "gbp07-donor-score-values",
                tuple(row.donor_rho for row in donor_rows),
            ),
        ),
    )
    binary_digest = ledger_digest(
        "gbp07-binary-contamination-basis",
        tuple((row.fitted_unit_id, bool(row.high_contamination)) for row in donor_rows),
    )
    identity = ledger_digest(
        "gbp07-contamination-basis-artifact",
        (
            ARTIFACT_SCHEMA_ID,
            DERIVATION_ID,
            DIGEST_POLICY_ID,
            PUBLIC_METHOD_PROVENANCE,
            HIGH_CONTAMINATION_THRESHOLD,
            COMPARISON_SEMANTICS,
            canonical_float_digest("gbp07-ambient-hbb", (ambient_hbb,)),
            ambient_digest,
            cell_digest,
            aggregation_digest,
            donor_score_digest,
            binary_digest,
        ),
    )
    digests = ContaminationArtifactDigests(
        ambient_profile_digest=ambient_digest,
        per_cell_score_vector_digest=cell_digest,
        donor_aggregation_ledger=aggregation_digest,
        donor_score_digest=donor_score_digest,
        binary_basis_digest=binary_digest,
        artifact_identity=identity,
    )
    return ContaminationBasisArtifact(
        schema_id=ARTIFACT_SCHEMA_ID,
        derivation_id=DERIVATION_ID,
        digest_policy_id=DIGEST_POLICY_ID,
        public_method_provenance=PUBLIC_METHOD_PROVENANCE,
        threshold=HIGH_CONTAMINATION_THRESHOLD,
        comparison_semantics=COMPARISON_SEMANTICS,
        ambient_profile=ambient_profile,
        ambient_hbb=float(ambient_hbb),
        cell_scores=cell_scores,
        donor_table=donor_rows,
        digests=digests,
        artifact_identity=identity,
    )


def estimate_genebench_gbp07_public_contamination(
    empty_drops: EmptyDropletCountsView,
    cells: CellCountsView,
    donor_order: tuple[TypedDonorId, ...],
) -> EstimatorResult:
    """Apply the frozen public estimator, returning a complete artifact or abstention."""

    donor_order = tuple(donor_order)
    if len(empty_drops.total_umi) == 0 or len(cells.cell_id) == 0 or len(donor_order) == 0:
        return Abstained(EstimatorAbstentionReason.EMPTY_INPUT, "empty droplets, cells, and donor order must be nonempty")
    if any(not _valid_key(key, TypedDonorId) for key in donor_order):
        return Abstained(EstimatorAbstentionReason.MISSING_DONOR, "donor order contains a missing or invalid typed donor")
    if len(set(donor_order)) != len(donor_order):
        return Abstained(EstimatorAbstentionReason.DUPLICATE_DONOR, "donor order contains a duplicate fitted unit")
    if any(not _valid_key(key, TypedCellId) for key in cells.cell_id):
        return Abstained(EstimatorAbstentionReason.INVALID_TYPED_INPUT, "cell ledger contains an invalid typed cell id")
    if len(set(cells.cell_id)) != len(cells.cell_id):
        return Abstained(EstimatorAbstentionReason.DUPLICATE_CELL, "cell ledger contains a duplicate cell id")
    if any(not _valid_key(key, TypedDonorId) for key in cells.donor):
        return Abstained(EstimatorAbstentionReason.MISSING_DONOR, "a released cell has no valid donor")

    empty_totals = _validate_count_vector(empty_drops.total_umi, "empty total_umi")
    if isinstance(empty_totals, Abstained):
        return empty_totals
    cell_totals = _validate_count_vector(cells.total_umi, "cell total_umi")
    if isinstance(cell_totals, Abstained):
        return cell_totals
    cell_hbb = _validate_count_vector(cells.hbb, "cell HBB")
    if isinstance(cell_hbb, Abstained):
        return cell_hbb

    panel = np.asarray(empty_drops.panel_counts)
    if panel.ndim != 2 or panel.shape != (len(empty_totals), len(empty_drops.panel_gene_names)):
        return Abstained(EstimatorAbstentionReason.INVALID_TYPED_INPUT, "panel counts and gene ledger shape disagree")
    if len(set(empty_drops.panel_gene_names)) != len(empty_drops.panel_gene_names) or "HBB" not in empty_drops.panel_gene_names:
        return Abstained(EstimatorAbstentionReason.INVALID_TYPED_INPUT, "panel gene ledger must contain HBB exactly once")
    if any(not isinstance(gene, str) or not gene for gene in empty_drops.panel_gene_names):
        return Abstained(EstimatorAbstentionReason.INVALID_TYPED_INPUT, "panel gene ledger contains an invalid name")
    if not (len(cells.cell_id) == len(cells.donor) == len(cell_totals) == len(cell_hbb)):
        return Abstained(EstimatorAbstentionReason.INVALID_TYPED_INPUT, "cell-aligned vectors have different lengths")

    checked_columns: list[np.ndarray] = []
    for index, gene in enumerate(empty_drops.panel_gene_names):
        checked = _validate_count_vector(panel[:, index], f"empty {gene}")
        if isinstance(checked, Abstained):
            return checked
        checked_columns.append(checked)

    total_sum = _exact_u64_sum(empty_totals, "empty total_umi")
    if isinstance(total_sum, Abstained):
        return total_sum
    if total_sum == 0:
        return Abstained(EstimatorAbstentionReason.ZERO_DENOMINATOR, "empty-droplet total UMI sum is zero")

    ambient_entries: list[AmbientProfileEntry] = []
    ambient_hbb = None
    for gene, column in zip(empty_drops.panel_gene_names, checked_columns):
        count_sum = _exact_u64_sum(column, f"empty {gene}")
        if isinstance(count_sum, Abstained):
            return count_sum
        fraction = np.float64(count_sum) / np.float64(total_sum)
        if not np.isfinite(fraction):
            return Abstained(EstimatorAbstentionReason.NON_FINITE_VALUE, f"ambient {gene} is non-finite")
        ambient_entries.append(AmbientProfileEntry(gene, float(fraction)))
        if gene == "HBB":
            ambient_hbb = np.float64(fraction)
    assert ambient_hbb is not None
    if ambient_hbb == 0 or np.any(cell_totals == 0):
        return Abstained(EstimatorAbstentionReason.ZERO_DENOMINATOR, "cell total UMI and ambient HBB must be nonzero")

    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        denominators = cell_totals.astype(np.float64) * ambient_hbb
        scores = np.clip(cell_hbb.astype(np.float64) / denominators, 0.0, 0.5).astype("<f8")
    if np.any(~np.isfinite(scores)):
        return Abstained(EstimatorAbstentionReason.NON_FINITE_VALUE, "per-cell score contains a non-finite value")

    typed_cell_donors = tuple(cells.donor)
    donor_set = set(donor_order)
    if any(donor not in donor_set for donor in typed_cell_donors):
        return Abstained(EstimatorAbstentionReason.MISSING_DONOR, "a cell donor is absent from the fitted donor order")

    donor_rows: list[DonorContaminationRow] = []
    for donor in donor_order:
        member_indices = tuple(index for index, cell_donor in enumerate(typed_cell_donors) if cell_donor == donor)
        if not member_indices:
            return Abstained(EstimatorAbstentionReason.MISSING_DONOR, "a fitted donor has no released cells")
        member_ids = tuple(cells.cell_id[index] for index in member_indices)
        member_scores = scores[np.asarray(member_indices, dtype=np.intp)]
        donor_rho = np.mean(member_scores, dtype=np.float64)
        if not np.isfinite(donor_rho):
            return Abstained(EstimatorAbstentionReason.NON_FINITE_VALUE, "donor mean is non-finite")
        donor_rows.append(
            DonorContaminationRow(
                fitted_unit_id=donor,
                donor_rho=float(donor_rho),
                high_contamination=bool(donor_rho > HIGH_CONTAMINATION_THRESHOLD),
                member_cell_count=np.uint64(len(member_indices)),
                member_cell_ledger_identity=ledger_digest("gbp07-donor-member-cell-ledger", member_ids),
            )
        )

    artifact = _artifact(
        tuple(ambient_entries),
        float(ambient_hbb),
        tuple(cells.cell_id),
        typed_cell_donors,
        scores,
        tuple(donor_rows),
    )
    return Estimated(artifact)
