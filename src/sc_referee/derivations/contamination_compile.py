"""Registered, proposal-bindable compiler for the ambient-contamination-eQTL derivation.

This is deliberately a narrow adapter: it restricts the contamination estimator's
inputs, then wires its exact binary donor basis into the existing Bundle and Design
and prepares values for a separate human-ratification ceremony.  The proposer
generalizes that wiring; this module does not attempt to be a generic
contamination-basis proposer.  It was first built against the released GeneBench
GB-P07 workflow, which remains the reference example it is exercised on.

The compiler emits only the authorities consumed by ``ContaminationConfoundCheck``.
It neither fits the eQTL outcome nor reads a submitted result or reference answer.
The estimator is exposure-blind given honest declared inputs; human measurement
ratification attests that the declared marker column is the real ambient measurement.
Authenticated source and column-role binding is deferred to the capsule.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import math
from io import BytesIO
import os
from pathlib import Path
import struct
from types import MappingProxyType
from zipfile import ZipFile

import numpy as np
import pandas as pd

from sc_referee.bundle import Bundle, Measure
from sc_referee.checks.base import Finding
from sc_referee.checks.contamination_confound import ContaminationConfoundCheck
from sc_referee.column_space import NUMERIC_POLICY_V1, _canonical_matrix_digest
from sc_referee.csp import CspScope, assignment_identity
from sc_referee.csp_contracts.contamination_condensed_ceremony import (
    CondensedAnswer,
    CondensedGroup,
    ratify_contamination_condensed,
)
from sc_referee.derivations.ambient_contamination_estimator import (
    CellCountsView,
    ContaminationBasisArtifact,
    EmptyDropletCountsView,
    Estimated,
    TypedCellId,
    TypedDonorId,
    estimate_ambient_contamination,
)
from sc_referee.design import Design, FittedDesignDeclaration
from sc_referee.engine import build_pseudobulk_sample_rows
from sc_referee.fitted_design import reconstruct_nuisance_design, request_from_confirmed_design


# The contamination threshold and the method provenance are NOT constants of this module.  They are
# method parameters of the analysis being audited, and they are sourced from its own ratified
# proposal (grounded in that analysis's documentation), exactly as the marker, target, and panel
# already are.  There is deliberately NO default: an analysis that documents no threshold makes the
# compilation abstain rather than silently inherit some other study's cutoff.
DEFAULT_RELEASE_ZIP = Path.home() / "Desktop/genebench_phase1_inputs/GB-P07-data.zip"
SOURCE_DIGEST_POLICY_VERSION = "contamination-source-digest-v2"


@dataclass(frozen=True)
class CompiledDerivation:
    """A proposal and everything an external caller needs to ratify it."""

    artifact: ContaminationBasisArtifact
    design: Design
    bundle: Bundle
    proposal_values: Mapping[str, object]
    scope: CspScope
    source_digests: Mapping[str, object]
    proposal_identity: str | None = None
    finding: Finding | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposal_values", MappingProxyType(dict(self.proposal_values)))
        object.__setattr__(self, "source_digests", MappingProxyType(dict(self.source_digests)))


class CompilationAbstentionReason(str, Enum):
    """Closed reasons for proposal compilation to stop before a verdict."""

    INVALID_PROPOSAL = "invalid_proposal"
    UNRESOLVED_PROPOSAL = "unresolved_proposal"
    UNKNOWN_DERIVATION = "unknown_derivation"
    INVALID_BINDING = "invalid_binding"
    INVALID_SOURCE_VALUES = "invalid_source_values"
    MISSING_SOURCE_ID = "missing_source_id"
    EMPTY_DROPLET_TABLE_MISSING_MARKER = "empty_droplet_table_missing_marker"
    ESTIMATOR_ABSTAINED = "estimator_abstained"
    BASIS_LEDGER_MISMATCH = "basis_ledger_mismatch"
    INVALID_METHOD_PARAMETER = "invalid_method_parameter"


@dataclass(frozen=True)
class ProposalCompilationAbstention:
    reason_code: CompilationAbstentionReason
    message: str
    proposal_identity: str | None


class _EmptyDropletTableMissingMarker(ValueError):
    """Internal signal mapped to the public typed compilation abstention."""


class _SourceValidationError(ValueError):
    """Internal signal preserving the typed reason for malformed source values."""

    def __init__(self, reason_code: CompilationAbstentionReason, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class _BasisLedgerMismatch(ValueError):
    """The recovered donor basis cannot bind one-to-one to fitted rows."""


@dataclass(frozen=True)
class ColumnBindings:
    cell_id: str
    cell_donor: str
    cell_total_umi: str
    cell_marker: str
    donor_id: str
    donor_genotype: str
    exposure_column: str
    empty_total_umi: str
    empty_id_columns: tuple[str, ...]
    empty_panel_columns: tuple[str, ...]
    marker_gene: str
    # Method parameters, declared by the analysis under audit (never defaulted here).
    threshold: float
    provenance: str


def release_zip_path() -> Path:
    """Resolve the released archive, with ``GBP07_ZIP`` taking precedence."""

    override = os.environ.get("GBP07_ZIP")
    return Path(override).expanduser() if override else DEFAULT_RELEASE_ZIP


def read_release(path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read the three released gzip members without extracting the archive."""

    with ZipFile(Path(path).expanduser()) as archive:
        cells = pd.read_csv(BytesIO(archive.read("cells.csv.gz")), compression="gzip")
        donors = pd.read_csv(BytesIO(archive.read("donors.csv.gz")), compression="gzip")
        empty_drops = pd.read_csv(
            BytesIO(archive.read("empty_drops.csv.gz")), compression="gzip"
        )
    return cells, donors, empty_drops


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _archive_release(
    path: str | Path,
) -> tuple[tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame], Mapping[str, object]]:
    """Read the release while binding the compilation to its exact member bytes."""

    with ZipFile(Path(path).expanduser()) as archive:
        members = tuple(sorted(info.filename for info in archive.infolist()))
        raw = {
            "cells": archive.read("cells.csv.gz"),
            "donors": archive.read("donors.csv.gz"),
            "empty_drops": archive.read("empty_drops.csv.gz"),
        }
    tables = (
        pd.read_csv(BytesIO(raw["cells"]), compression="gzip"),
        pd.read_csv(BytesIO(raw["donors"]), compression="gzip"),
        pd.read_csv(BytesIO(raw["empty_drops"]), compression="gzip"),
    )
    member_set_bytes = "\0".join(members).encode("utf-8")
    digests: Mapping[str, object] = {
        "digest_policy_version": SOURCE_DIGEST_POLICY_VERSION,
        "cells": _sha256(raw["cells"]),
        "donors": _sha256(raw["donors"]),
        "empty_drops": _sha256(raw["empty_drops"]),
        "archive_members": members,
        "archive_member_set": _sha256(member_set_bytes),
    }
    return tables, digests


def _table_source_digests(
    cells: pd.DataFrame, donors: pd.DataFrame, empty_drops: pd.DataFrame
) -> Mapping[str, object]:
    """Bind in-memory tables with the versioned canonical typed-table policy."""

    tables = {"cells": cells, "donors": donors, "empty_drops": empty_drops}
    return {
        "digest_policy_version": SOURCE_DIGEST_POLICY_VERSION,
        **{
            name: _sha256(_canonical_table_bytes(frame))
            for name, frame in tables.items()
        },
        "archive_members": (),
        "archive_member_set": _sha256(b""),
    }


def _length(value: int) -> bytes:
    return struct.pack("<Q", value)


def _framed(tag: bytes, value: bytes) -> bytes:
    return tag + _length(len(value)) + value


def _canonical_dtype_tag(series: pd.Series) -> str:
    """Return pandas-version-independent semantic dtype tags used by source v2."""

    dtype = series.dtype
    if pd.api.types.is_bool_dtype(dtype):
        return "bool"
    if pd.api.types.is_unsigned_integer_dtype(dtype):
        return "uint"
    if pd.api.types.is_integer_dtype(dtype):
        return "int"
    if pd.api.types.is_float_dtype(dtype):
        return "float64"
    if pd.api.types.is_string_dtype(dtype) or all(
        pd.isna(value) or isinstance(value, str) for value in series
    ):
        return "string"
    return "object"


def _canonical_source_scalar(value) -> bytes:
    """Encode null/bool/int/float/string values; float signed zero becomes +0."""

    if value is None or value is pd.NA or (
        isinstance(value, (float, np.floating)) and pd.isna(value)
    ):
        return b"n"
    if isinstance(value, (bool, np.bool_)):
        return b"b\x01" if bool(value) else b"b\x00"
    if isinstance(value, (int, np.integer)):
        return _framed(b"i", str(int(value)).encode("ascii"))
    if isinstance(value, (float, np.floating)):
        numeric = float(value)
        if not np.isfinite(numeric):
            raise ValueError("source tables cannot canonically encode infinite floats")
        if numeric == 0.0:
            numeric = 0.0
        return b"f" + struct.pack("<d", numeric)
    if isinstance(value, str):
        return _framed(b"s", value.encode("utf-8"))
    if isinstance(value, bytes):
        return _framed(b"y", value)
    raise TypeError(f"unsupported canonical source scalar: {type(value).__name__}")


def _canonical_table_bytes(frame: pd.DataFrame) -> bytes:
    """Encode ordered columns, semantic dtype tags, row count, and typed values.

    The DataFrame index is deliberately excluded: source-table row order is binding,
    while an incidental pandas index created during parsing is not.  Nulls have one
    token and float -0.0 is normalized to +0.0.
    """

    chunks = [
        _framed(b"v", SOURCE_DIGEST_POLICY_VERSION.encode("ascii")),
        _length(len(frame)),
        _length(len(frame.columns)),
    ]
    for column in frame.columns:
        series = frame[column]
        chunks.append(_framed(b"c", str(column).encode("utf-8")))
        chunks.append(_framed(b"d", _canonical_dtype_tag(series).encode("ascii")))
        chunks.extend(_canonical_source_scalar(value) for value in series.array)
    return b"".join(chunks)


def _validate_count_column(
    frame: pd.DataFrame,
    column: str,
    *,
    table_name: str,
    maximum: int = int(np.iinfo(np.uint64).max),
) -> None:
    """Reject values that cannot be losslessly represented as bounded counts."""

    for row_label, value in frame[column].items():
        valid = False
        if not pd.isna(value) and not isinstance(value, (bool, np.bool_)):
            if isinstance(value, (int, np.integer)):
                valid = 0 <= int(value) <= maximum
            elif isinstance(value, (float, np.floating)):
                numeric = float(value)
                valid = (
                    np.isfinite(numeric)
                    and numeric >= 0
                    and numeric.is_integer()
                    and numeric <= maximum
                )
        if not valid:
            raise _SourceValidationError(
                CompilationAbstentionReason.INVALID_SOURCE_VALUES,
                f"{table_name} column {column!r} contains an invalid count "
                f"at row {row_label!r}; counts must be finite, exact non-negative integers",
            )


def _validate_identity_column(
    frame: pd.DataFrame, column: str, *, table_name: str
) -> None:
    """Reject missing identities before any value is stringified."""

    for row_label, value in frame[column].items():
        missing = pd.isna(value) or (isinstance(value, str) and not value.strip())
        if missing:
            raise _SourceValidationError(
                CompilationAbstentionReason.MISSING_SOURCE_ID,
                f"{table_name} identity column {column!r} contains a missing or empty "
                f"identifier at row {row_label!r}",
            )


def _restricted_estimator_inputs(
    cells: pd.DataFrame,
    donors: pd.DataFrame,
    empty_drops: pd.DataFrame,
    columns: ColumnBindings,
) -> tuple[EmptyDropletCountsView, CellCountsView, tuple[TypedDonorId, ...]]:
    """Project source frames onto the estimator's closed, exposure-blind views."""

    discovered_panel_names = _count_columns(
        empty_drops,
        excluded=(columns.empty_total_umi, *columns.empty_id_columns),
        include_all_numeric=True,
    )
    panel_names = tuple(dict.fromkeys((
        *columns.empty_panel_columns,
        columns.marker_gene,
        *discovered_panel_names,
    )))
    _validate_count_column(cells, columns.cell_total_umi, table_name="cell table")
    _validate_count_column(cells, columns.cell_marker, table_name="cell table")
    _validate_count_column(
        empty_drops, columns.empty_total_umi, table_name="empty-droplet table"
    )
    for panel_name in panel_names:
        _validate_count_column(empty_drops, panel_name, table_name="empty-droplet table")
    _validate_identity_column(cells, columns.cell_id, table_name="cell table")
    _validate_identity_column(cells, columns.cell_donor, table_name="cell table")
    _validate_identity_column(donors, columns.donor_id, table_name="donor table")

    empty_view = EmptyDropletCountsView(
        total_umi=empty_drops[columns.empty_total_umi].to_numpy(dtype=np.uint64),
        panel_gene_names=panel_names,
        panel_counts=empty_drops.loc[:, panel_names].to_numpy(dtype=np.uint64),
    )
    cell_view = CellCountsView(
        cell_id=tuple(
            TypedCellId("contamination-cell", str(value)) for value in cells[columns.cell_id]
        ),
        donor=tuple(
            TypedDonorId("contamination-donor", str(value)) for value in cells[columns.cell_donor]
        ),
        total_umi=cells[columns.cell_total_umi].to_numpy(dtype=np.uint64),
        marker_counts=cells[columns.cell_marker].to_numpy(dtype=np.uint64),
    )
    donor_order = tuple(
        TypedDonorId("contamination-donor", str(value)) for value in donors[columns.donor_id]
    )
    return empty_view, cell_view, donor_order


def _run_contamination_derivation(
    cells: pd.DataFrame,
    donors: pd.DataFrame,
    empty_drops: pd.DataFrame,
    columns: ColumnBindings,
):
    """Build the derivation's restricted views and invoke its frozen estimator."""

    # The marker, threshold, and method provenance are all declared by the ratified proposal and
    # carried on the bindings.  Nothing about the method is hardcoded here or in the estimator.
    return estimate_ambient_contamination(
        *_restricted_estimator_inputs(cells, donors, empty_drops, columns),
        marker_gene=columns.marker_gene,
        threshold=columns.threshold,
        provenance=columns.provenance,
    )


DERIVATION_REGISTRY = MappingProxyType({
    "ambient_contamination_estimator/v1": _run_contamination_derivation,
})


def _count_columns(
    frame: pd.DataFrame,
    *,
    excluded: tuple[str, ...],
    include_all_numeric: bool = False,
) -> tuple[str, ...]:
    """Read the ordered count-feature ledger from a table's actual integer columns."""

    excluded_names = set(excluded)
    return tuple(
        str(column)
        for column in frame.columns
        if column not in excluded_names
        and (
            pd.api.types.is_numeric_dtype(frame[column].dtype)
            if include_all_numeric
            else pd.api.types.is_integer_dtype(frame[column].dtype)
        )
    )


def _design(
    *,
    include_basis: bool,
    analysis_type: str,
    unit_column: str,
    genotype_column: str,
    target_feature: str,
    target_coefficient: str,
) -> Design:
    adjusted = [genotype_column]
    if include_basis:
        adjusted.append("high_contamination")
    declaration = FittedDesignDeclaration(
        rows_exact=True,
        operator_kind="ordinary_fixed_effects",
        intercept=True,
        column_kinds={
            genotype_column: "continuous",
            "high_contamination": "continuous",
        },
        categorical_levels={},
        transforms={
            genotype_column: "identity",
            "high_contamination": "identity",
        },
        batch_modeling={},
    )
    return Design(
        analysis_type=analysis_type,
        confirmed_by_human=True,
        confidence={
            "analyst_adjusted_for": "high",
            "aggregation_key": "high",
            "fitted_design": "high",
        },
        condition=None,
        batch=[],
        replicate_unit=[unit_column],
        reference=None,
        test=None,
        model=f"~ {genotype_column}" + (" + high_contamination" if include_basis else ""),
        target_coefficient=target_coefficient,
        sample_unit=[unit_column],
        pairing_unit=[],
        aggregation_key=[unit_column],
        analyst_adjusted_for=adjusted,
        fitted_design=declaration,
        variant_id="rs-contamination-eqtl",
        genotype_column=genotype_column,
        target_feature=target_feature,
        estimand_id="estimand:contamination-eqtl:v1",
        csp_contracts=(),
    )


def _proposal_values(
    *, artifact: ContaminationBasisArtifact, rows, design: Design, fitted_identity: str,
    live_assignment_identity: str, vector_digest: str, exposure_column: str,
) -> dict[str, object]:
    basis_identity = "basis:high-contamination:v1"
    return {
        "measurement_kind": "external_measurement_artifact",
        "axis_identity": {
            "artifact_id": artifact.artifact_identity,
            "run_id": "run:contamination-public-estimator:v1",
            "version": "1",
            "vector_field": "high_contamination",
            "unit": "indicator",
            "scale": "binary_zero_one",
            "orientation": "one_is_high_contamination",
            "value_digest": vector_digest,
        },
        "rows_and_aggregation": {
            "input_row_ledger_identity": artifact.digests.per_cell_score_vector_digest,
            "output_row_ledger_identity": rows.row_ledger_identity,
            "source_mapping_identity": artifact.digests.donor_aggregation_ledger,
            "aggregation_ledger_identity": artifact.digests.donor_aggregation_ledger,
            "aggregation_rule": "per_unit_mean",
            "exclusions": (),
            "missing_rule": "abstain",
            "output_vector_digest": vector_digest,
        },
        # The estimator has already applied its frozen strict threshold.  The CSP replays
        # that recovered binary column exactly; it does not re-estimate or re-threshold it.
        "transform_kind": "continuous_identity",
        "transform_detail": {
            "source_vector_digest": vector_digest,
            "output_digest": vector_digest,
        },
        "basis_identity": {
            "basis_ledger_identity": basis_identity,
            "ordered_columns": ("high_contamination",),
            "output_digest": vector_digest,
        },
        "positive_evidence": {
            "kind": "empty_droplet_derived_external_fraction",
            "records": ("evidence:contamination-public-method:v1",),
        },
        "population_state_evidence": {
            "required": False,
            "records": (),
            "coverage_policy": "not_expression_proxy",
        },
        "source_stratum_applicability": {
            "source_strata": ("pool:contamination",),
            "mapping_identity": artifact.digests.donor_aggregation_ledger,
            "comparability_evidence": ("evidence:contamination-pool-comparability:v1",),
            "cross_stratum_rule": "single_source_stratum",
        },
        "blindness_attestation": {
            "blind_to": (
                "exposure", "outcomes", "target_results", "coefficient",
                "measurement_exposure_association", "containment", "desired_verdict",
            ),
            "evidence_id": "evidence:contamination-restricted-estimator-view:v1",
        },
        "measurement_scope_authority": {
            "scope_id": "scope:contamination-measurement:v1",
            "authority_id": "authority:m1-direct-ratification:v1",
            "assay": "single-cell-rna",
            "population_state": "released-study-population",
            "source": "released-empty-droplet-pool",
            "analysis_id": "analysis:contamination-eqtl:v1",
        },
        "pre_exposure": {"confirmed": True, "evidence_id": "evidence:contamination-timing:v1"},
        "non_descendancy": {
            "confirmed": True,
            "evidence_id": "evidence:contamination-non-descendancy:v1",
        },
        "outside_estimand_pathway": {
            "confirmed": True,
            "evidence_id": "evidence:contamination-outside-estimand:v1",
        },
        "required_adjustment": {
            "required": True,
            "basis": "prespecified_design_obligation",
            "evidence_id": "evidence:contamination-design-obligation:v1",
        },
        "assignment_context": {
            "kind": "observational",
            "assignment_identity": live_assignment_identity,
            "compatibility_evidence": "evidence:contamination-assignment-compatibility:v1",
        },
        "exact_basis_adequacy": {
            "required_basis_identity": basis_identity,
            "transform_kind": "continuous_identity",
            "evidence_id": "evidence:contamination-exact-binary-basis:v1",
        },
        "causal_scope_authority": {
            "scope_id": "scope:contamination-causal:v1",
            "authority_id": "authority:m1-direct-ratification:v1",
            "fitted_result_id": "fit:contamination-eqtl:v1",
            "target_coefficient": design.target_coefficient,
            "exposure_column": exposure_column,
            "row_ledger_identity": rows.row_ledger_identity,
            "estimand_id": design.estimand_id,
            "measurement_basis_identity": basis_identity,
            "fitted_design_identity": fitted_identity,
        },
    }


def _proposal(
    *, artifact: ContaminationBasisArtifact, bundle: Bundle, design: Design,
    unit_column: str, exposure_column: str,
) -> tuple[dict[str, object], CspScope]:
    rows = build_pseudobulk_sample_rows(bundle.observations, design)
    live_assignment = assignment_identity(rows.rows, exposure_column, unit_column)
    reconstruction = reconstruct_nuisance_design(
        rows.rows, design, request_from_confirmed_design(design, rows)
    )
    if reconstruction.artifact is None:
        raise ValueError(f"contamination fitted design was not reconstructable: {reconstruction.reason}")
    fitted_identity = reconstruction.artifact.matrix_digest
    fitted_ids = tuple(str(value) for value in rows.rows[unit_column])
    artifact_ids = tuple(row.fitted_unit_id.value for row in artifact.donor_table)
    if len(set(fitted_ids)) != len(fitted_ids):
        raise _BasisLedgerMismatch("fitted-row donor ledger contains duplicates")
    if len(set(artifact_ids)) != len(artifact_ids):
        raise _BasisLedgerMismatch("estimator donor basis contains duplicates")
    if set(fitted_ids) != set(artifact_ids):
        missing = sorted(set(fitted_ids).difference(artifact_ids))
        extra = sorted(set(artifact_ids).difference(fitted_ids))
        raise _BasisLedgerMismatch(
            f"estimator/fitted-row donor sets differ (missing={missing}, extra={extra})"
        )
    artifact_by_id = {row.fitted_unit_id.value: row for row in artifact.donor_table}
    donor_basis = np.asarray(
        [float(artifact_by_id[donor].high_contamination) for donor in fitted_ids],
        dtype=np.float64,
    )[:, None]
    attached_values = []
    for positions in rows.group_positions:
        group_values = bundle.observations.iloc[positions]["high_contamination"].to_numpy()
        if len(group_values) == 0 or np.any(group_values != group_values[0]):
            raise _BasisLedgerMismatch(
                "attached basis is not constant within a fitted-row donor"
            )
        attached_values.append(float(group_values[0]))
    attached_basis = np.asarray(attached_values, dtype=np.float64)[:, None]
    if not np.array_equal(donor_basis, attached_basis):
        raise _BasisLedgerMismatch(
            "reindexed estimator basis disagrees with the fitted-row attached basis"
        )
    vector_digest = _canonical_matrix_digest(
        attached_basis, policy_version=NUMERIC_POLICY_V1.version
    )
    values = _proposal_values(
        artifact=artifact,
        rows=rows,
        design=design,
        fitted_identity=fitted_identity,
        live_assignment_identity=live_assignment,
        vector_digest=vector_digest,
        exposure_column=exposure_column,
    )
    scope = CspScope(
        fitted_result_id="fit:contamination-eqtl:v1",
        contrast_name=design.name,
        target_coefficient=design.target_coefficient,
        exposure_column=exposure_column,
        row_ledger_identity=rows.row_ledger_identity,
        estimand_id=design.estimand_id,
        group_source_column=unit_column,
        assignment_identity=live_assignment,
        contract_scope={
            "measurement_artifact_identity": values["axis_identity"]["artifact_id"],
            "measurement_run_identity": values["axis_identity"]["run_id"],
            "raw_source_ledger_identity": values["rows_and_aggregation"][
                "input_row_ledger_identity"
            ],
            "measurement_vector_ledger_identity": rows.row_ledger_identity,
            "transformed_basis_ledger_identity": values["basis_identity"][
                "basis_ledger_identity"
            ],
            "basis_output_digest": vector_digest,
            "fitted_design_identity": fitted_identity,
        },
    )
    return values, scope


def _compile_tables(
    cells: pd.DataFrame,
    donors: pd.DataFrame,
    empty_drops: pd.DataFrame,
    *,
    columns: ColumnBindings,
    analysis_type: str,
    target_feature: str,
    target_coefficient: str,
    derivation_id: str,
    include_basis: bool = False,
    _source_digests: Mapping[str, object] | None = None,
) -> CompiledDerivation:
    """Shared core for direct and proposal-bound compilation."""

    derivation = DERIVATION_REGISTRY.get(derivation_id)
    if derivation is None:
        raise LookupError(f"unregistered derivation: {derivation_id}")
    if columns.marker_gene not in empty_drops.columns:
        raise _EmptyDropletTableMissingMarker(
            f"empty-droplet table does not contain required marker column "
            f"{columns.marker_gene!r}"
        )
    result = derivation(cells, donors, empty_drops, columns)
    if not isinstance(result, Estimated):
        raise ValueError(
            f"contamination estimator abstained: {result.reason_code.value}: {result.message}"
        )
    artifact = result.artifact

    donor_metadata = donors.loc[:, [columns.donor_id, columns.donor_genotype]].copy()
    if donor_metadata[columns.donor_id].duplicated().any():
        raise ValueError("donor authority contains duplicate donors")
    donor_metadata[columns.donor_id] = donor_metadata[columns.donor_id].astype(str)
    genotype_by_donor = donor_metadata.set_index(columns.donor_id)[columns.donor_genotype]
    artifact_by_donor = {
        row.fitted_unit_id.value: row for row in artifact.donor_table
    }
    cell_donors = cells[columns.cell_donor].astype(str)
    artifact_ids = tuple(row.fitted_unit_id.value for row in artifact.donor_table)
    fitted_donor_ids = tuple(dict.fromkeys(cell_donors))
    if (
        len(set(artifact_ids)) != len(artifact_ids)
        or set(artifact_ids) != set(fitted_donor_ids)
    ):
        missing = sorted(set(fitted_donor_ids).difference(artifact_ids))
        extra = sorted(set(artifact_ids).difference(fitted_donor_ids))
        raise _BasisLedgerMismatch(
            "estimator/fitted donor basis is not one-to-one "
            f"(missing={missing}, extra={extra}, duplicate_estimator_rows="
            f"{len(set(artifact_ids)) != len(artifact_ids)})"
        )
    if cell_donors.map(genotype_by_donor).isna().any():
        raise ValueError("a released cell has no genotype in the donor authority")
    if cell_donors.map(artifact_by_donor).isna().any():
        raise _BasisLedgerMismatch(
            "a fitted-row donor has no recovered donor contamination row"
        )

    observations = pd.DataFrame(
        {
            columns.donor_id: cell_donors.to_numpy(),
            columns.exposure_column: cell_donors.map(genotype_by_donor).to_numpy(dtype=np.float64),
            "high_contamination": cell_donors.map(
                lambda donor: int(artifact_by_donor[donor].high_contamination)
            ).to_numpy(dtype=np.int64),
            "donor_rho": cell_donors.map(
                lambda donor: artifact_by_donor[donor].donor_rho
            ).to_numpy(dtype=np.float64),
        },
        index=pd.Index(cells[columns.cell_id].astype(str), name=columns.cell_id),
    )
    feature_names = _count_columns(
        cells,
        excluded=(columns.cell_id, columns.cell_donor, columns.cell_total_umi),
    )
    for feature_name in feature_names:
        _validate_count_column(
            cells,
            feature_name,
            table_name="cell table",
            maximum=int(np.iinfo(np.int64).max),
        )
    counts = cells.loc[:, feature_names].to_numpy(dtype=np.int64)
    bundle = Bundle(
        observations=observations,
        measure=Measure("counts", counts, None, list(feature_names)),
        feature_metadata=pd.DataFrame(index=list(feature_names)),
        replicate_var=columns.donor_id,
    )
    design = _design(
        include_basis=include_basis,
        analysis_type=analysis_type,
        unit_column=columns.donor_id,
        genotype_column=columns.exposure_column,
        target_feature=target_feature,
        target_coefficient=target_coefficient,
    )
    proposal_values, scope = _proposal(
        artifact=artifact,
        bundle=bundle,
        design=design,
        unit_column=columns.donor_id,
        exposure_column=columns.exposure_column,
    )
    source_digests = _source_digests or _table_source_digests(cells, donors, empty_drops)
    return CompiledDerivation(
        artifact=artifact,
        design=design,
        bundle=bundle,
        proposal_values=proposal_values,
        scope=scope,
        source_digests=source_digests,
    )


def compile_contamination_tables(
    cells: pd.DataFrame,
    donors: pd.DataFrame,
    empty_drops: pd.DataFrame,
    *,
    columns: ColumnBindings,
    target_feature: str,
    target_coefficient: str,
    analysis_type: str = "eqtl",
    derivation_id: str = "ambient_contamination_estimator/v1",
    include_basis: bool = False,
    _source_digests: Mapping[str, object] | None = None,
) -> CompiledDerivation | ProposalCompilationAbstention:
    """Compile already-loaded tables through the same parameterized core.

    The caller declares the whole binding: which columns carry which role, which gene is the
    ambient marker, which panel the empty droplets were measured on, and the method parameters.
    Nothing about the analysis is assumed here, so this path carries no marker, panel, target, or
    cutoff of its own. ``analysis_type`` and ``derivation_id`` describe this module's own scope
    (the contamination-eQTL derivation), not the analysis being audited.
    """

    try:
        columns = replace(
            columns,
            threshold=_bound_threshold(columns.threshold),
            provenance=_bound_provenance(columns.provenance),
        )
    except _SourceValidationError as exc:
        return ProposalCompilationAbstention(exc.reason_code, str(exc), None)

    try:
        return _compile_tables(
            cells,
            donors,
            empty_drops,
            columns=columns,
            analysis_type=analysis_type,
            target_feature=target_feature,
            target_coefficient=target_coefficient,
            derivation_id=derivation_id,
            include_basis=include_basis,
            _source_digests=_source_digests,
        )
    except _SourceValidationError as exc:
        return ProposalCompilationAbstention(exc.reason_code, str(exc), None)
    except _BasisLedgerMismatch as exc:
        return ProposalCompilationAbstention(
            CompilationAbstentionReason.BASIS_LEDGER_MISMATCH, str(exc), None
        )


def _binding_values(proposal: BindingProposal) -> dict[Destination, object]:
    from sc_referee.compiler.proposer import REQUIRED_DESTINATIONS

    values: dict[Destination, object] = {}
    for binding in proposal.requested_bindings:
        if binding.destination in values:
            raise ValueError(
                "proposal contains duplicate binding for "
                f"{binding.destination.authority}.{binding.destination.field}"
            )
        values[binding.destination] = binding.candidate_value
    missing = set(REQUIRED_DESTINATIONS).difference(values)
    if missing:
        labels = sorted(f"{item.authority}.{item.field}" for item in missing)
        raise ValueError(f"proposal is missing required binding(s): {', '.join(labels)}")
    return values


def _column(columns: Mapping[str, object], role: str, label: str) -> str:
    value = columns.get(role)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label}.columns.{role} must be a non-empty column name")
    return value


def _bound_threshold(value: object) -> float:
    """The contamination cutoff declared by the analysis under audit.

    Accepted as a number or as the verbatim numeric text of the documentation span it was grounded
    in.  A contamination fraction, so it must be finite and strictly inside (0, 1).  There is no
    default: an undeclared threshold is an abstention, never another study's cutoff.
    """

    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise _SourceValidationError(
            CompilationAbstentionReason.INVALID_METHOD_PARAMETER,
            "detector_input.contamination_threshold must be a number or numeric string",
        )
    try:
        threshold = float(value)
    except ValueError:
        raise _SourceValidationError(
            CompilationAbstentionReason.INVALID_METHOD_PARAMETER,
            f"detector_input.contamination_threshold {value!r} is not a number",
        ) from None
    if not math.isfinite(threshold) or not 0.0 < threshold < 1.0:
        raise _SourceValidationError(
            CompilationAbstentionReason.INVALID_METHOD_PARAMETER,
            f"detector_input.contamination_threshold {threshold!r} is not a fraction in (0, 1)",
        )
    return threshold


def _bound_provenance(value: object) -> str:
    """The citation identifying the method the declared threshold came from."""

    if not isinstance(value, str) or not value.strip():
        raise _SourceValidationError(
            CompilationAbstentionReason.INVALID_METHOD_PARAMETER,
            "detector_input.method_provenance must be a non-empty citation",
        )
    return value


def _read_bound_table(folder: Path, relative_path: str) -> tuple[pd.DataFrame, str]:
    from sc_referee.compiler.inventory import confine_inventory_path

    path = confine_inventory_path(folder, relative_path)
    logical_name = path.name[:-3] if path.name.lower().endswith(".gz") else path.name
    separator = "\t" if logical_name.lower().endswith(".tsv") else ","
    return pd.read_csv(path, sep=separator), _sha256(path.read_bytes())


def _method_includes_basis(method_evidence_span: object) -> bool:
    if not isinstance(method_evidence_span, str):
        raise ValueError("fitted_design.method_evidence_span must be text")
    normalized = " ".join(method_evidence_span.lower().replace("_", " ").split())
    if "no ambient adjustment" in normalized or "without ambient adjustment" in normalized:
        return False
    return "high contamination" in normalized


def compile_from_proposal(
    proposal: BindingProposal,
    folder: str | Path,
    answers: Mapping[CondensedGroup, CondensedAnswer],
) -> CompiledDerivation | ProposalCompilationAbstention:
    """Compile, ratify, and check a fully resolved structural binding proposal."""

    from sc_referee.compiler.binding_proposal import Destination, validate_binding_proposal
    from sc_referee.compiler.table_bindings import parse_table_binding

    identity = getattr(proposal, "proposal_id", None)
    try:
        validate_binding_proposal(proposal)
    except Exception as exc:
        return ProposalCompilationAbstention(
            CompilationAbstentionReason.INVALID_PROPOSAL,
            f"binding proposal failed validation: {exc}",
            identity,
        )
    if proposal.blocks_compilation:
        details = list(proposal.unresolved)
        details.extend(
            f"{conflict.destination.authority}.{conflict.destination.field}"
            for conflict in proposal.conflicts
            if conflict.load_bearing and conflict.resolution == "unresolved"
        )
        suffix = f": {', '.join(details)}" if details else ""
        return ProposalCompilationAbstention(
            CompilationAbstentionReason.UNRESOLVED_PROPOSAL,
            "binding proposal is not fully resolved" + suffix,
            identity,
        )

    try:
        values = _binding_values(proposal)
    except (TypeError, ValueError) as exc:
        return ProposalCompilationAbstention(
            CompilationAbstentionReason.UNRESOLVED_PROPOSAL, str(exc), identity
        )

    derivation_id = values[Destination("detector_input", "derivation_id")]
    if not isinstance(derivation_id, str) or derivation_id not in DERIVATION_REGISTRY:
        return ProposalCompilationAbstention(
            CompilationAbstentionReason.UNKNOWN_DERIVATION,
            f"no registered derivation for {derivation_id!r}",
            identity,
        )

    try:
        table_destinations = (
            ("cell_table", Destination("detector_input", "cell_table")),
            ("donor_table", Destination("detector_input", "donor_table")),
            ("empty_droplet_table", Destination("empty_droplet", "empty_droplet_table")),
        )
        tables = {
            label: parse_table_binding(values[destination], label)
            for label, destination in table_destinations
        }
        cell_path, cell_columns = tables["cell_table"].artifact_path, tables["cell_table"].columns
        donor_path, donor_columns = (
            tables["donor_table"].artifact_path, tables["donor_table"].columns
        )
        empty_path, empty_columns = (
            tables["empty_droplet_table"].artifact_path,
            tables["empty_droplet_table"].columns,
        )
        genotype_column = values[Destination("design", "genotype_column")]
        if not isinstance(genotype_column, str) or not genotype_column:
            raise ValueError("design.genotype_column must be a non-empty column name")
        if _column(donor_columns, "genotype", "donor_table") != genotype_column:
            raise ValueError("donor-table genotype binding disagrees with design.genotype_column")
        marker_column = _column(cell_columns, "marker", "cell_table")
        empty_panel = empty_columns.get("panel", {})
        # The method parameters come from this analysis's own ratified proposal, grounded in its
        # documentation. A proposal that could not ground them leaves them unresolved, which has
        # already abstained above; there is no fallback cutoff to inherit.
        threshold = _bound_threshold(values[Destination("detector_input", "contamination_threshold")])
        provenance = _bound_provenance(values[Destination("detector_input", "method_provenance")])
        columns = ColumnBindings(
            cell_id=_column(cell_columns, "cell_id", "cell_table"),
            cell_donor=_column(cell_columns, "donor", "cell_table"),
            cell_total_umi=_column(cell_columns, "total_umi", "cell_table"),
            cell_marker=_column(cell_columns, "marker", "cell_table"),
            donor_id=_column(donor_columns, "donor", "donor_table"),
            donor_genotype=genotype_column,
            exposure_column=genotype_column,
            empty_total_umi=_column(empty_columns, "total_umi", "empty_droplet_table"),
            empty_id_columns=tuple(
                value
                for role in ("id", "barcode")
                if isinstance((value := empty_columns.get(role)), str)
            ),
            empty_panel_columns=tuple(empty_panel.values()),
            marker_gene=marker_column,
            threshold=threshold,
            provenance=provenance,
        )
        root = Path(folder).expanduser()
        cells, cell_digest = _read_bound_table(root, cell_path)
        donors, donor_digest = _read_bound_table(root, donor_path)
        empty_drops, empty_digest = _read_bound_table(root, empty_path)
        source_digests = {
            "digest_policy_version": SOURCE_DIGEST_POLICY_VERSION,
            "cell_table": cell_digest,
            "donor_table": donor_digest,
            "empty_droplet_table": empty_digest,
            "artifact_paths": {
                "cell_table": cell_path,
                "donor_table": donor_path,
                "empty_droplet_table": empty_path,
            },
        }
        analysis_type = values[Destination("design", "analysis_type")]
        target_feature = values[Destination("design", "target_feature")]
        target_coefficient = values[Destination("reported_claim", "target_coefficient")]
        if not all(isinstance(value, str) and value for value in (
            analysis_type, target_feature, target_coefficient
        )):
            raise ValueError("analysis type, target feature, and target coefficient must be text")
        if analysis_type != "eqtl":
            raise ValueError("the registered contamination derivation supports only eqtl analysis")
        compilation = _compile_tables(
            cells,
            donors,
            empty_drops,
            columns=columns,
            analysis_type=analysis_type,
            target_feature=target_feature,
            target_coefficient=target_coefficient,
            derivation_id=derivation_id,
            include_basis=_method_includes_basis(
                values[Destination("fitted_design", "method_evidence_span")]
            ),
            _source_digests=source_digests,
        )
    except Exception as exc:
        if isinstance(exc, _SourceValidationError):
            reason = exc.reason_code
        elif isinstance(exc, _EmptyDropletTableMissingMarker):
            reason = CompilationAbstentionReason.EMPTY_DROPLET_TABLE_MISSING_MARKER
        elif isinstance(exc, _BasisLedgerMismatch):
            reason = CompilationAbstentionReason.BASIS_LEDGER_MISMATCH
        elif "estimator abstained" in str(exc):
            reason = CompilationAbstentionReason.ESTIMATOR_ABSTAINED
        else:
            reason = CompilationAbstentionReason.INVALID_BINDING
        return ProposalCompilationAbstention(reason, str(exc), identity)

    record = ratify_contamination_condensed(
        compilation.proposal_values, compilation.scope, answers
    )
    design = replace(compilation.design, csp_contracts=(record,))
    finding = ContaminationConfoundCheck().run(design, compilation.bundle)
    return replace(
        compilation,
        design=design,
        proposal_identity=proposal.proposal_id,
        finding=finding,
    )


def compile_contamination(
    path: str | Path | None = None,
    *,
    columns: ColumnBindings,
    target_feature: str,
    target_coefficient: str,
    include_basis: bool = False,
) -> CompiledDerivation | ProposalCompilationAbstention:
    """Load a released zip and compile a deterministic proposal-only bundle.

    The bindings, target, and method parameters describe the analysis in the archive, so the
    caller declares them. This entry point assumes no marker, panel, target, or cutoff.
    """

    tables, source_digests = _archive_release(
        release_zip_path() if path is None else path
    )
    return compile_contamination_tables(
        *tables,
        columns=columns,
        target_feature=target_feature,
        target_coefficient=target_coefficient,
        include_basis=include_basis,
        _source_digests=source_digests,
    )


def ratify_contamination(
    compilation: CompiledDerivation,
    answers: Mapping[CondensedGroup, CondensedAnswer],
) -> Design:
    """Return a design carrying the record produced from caller-supplied answers."""

    record = ratify_contamination_condensed(
        compilation.proposal_values, compilation.scope, answers
    )
    return replace(compilation.design, csp_contracts=(record,))
