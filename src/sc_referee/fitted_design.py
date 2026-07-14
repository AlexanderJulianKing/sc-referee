"""Exact, narrow reconstruction of ordinary fixed-effect nuisance geometry."""
from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Literal, Mapping

import numpy as np
import pandas as pd

from sc_referee import statuses as S
from sc_referee.column_space import (
    NUMERIC_POLICY_V1,
    CertificationState,
    ColumnSpaceCertificate,
    _canonical_matrix_digest,
    certify_column_space,
)
from sc_referee.design import Design, confidence_high
from sc_referee.design_matrix import (
    DesignMatrixError,
    RowIdentity,
    _canonical_scalar,
    build_fixed_effect_matrix,
)
from sc_referee.row_ledger import RowsExactBasis


@dataclass(frozen=True)
class FixedEffectReconstructionRequest:
    rows_exact: bool
    row_ledger_identity: str
    operator_kind: Literal[
        "ordinary_fixed_effects", "random_intercept_only", "unsupported"
    ]
    intercept: bool
    column_kinds: Mapping[str, Literal["continuous", "categorical"]]
    categorical_levels: Mapping[str, tuple[object, ...]]
    transforms: Mapping[str, Literal["identity"]]
    exposure_columns: tuple[str, ...]
    rows_exact_basis: RowsExactBasis = RowsExactBasis.HUMAN_DECLARED
    weight_role: str | None = None
    offset_role: str | None = None
    unsupported_reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "column_kinds", MappingProxyType(dict(self.column_kinds)))
        object.__setattr__(
            self,
            "categorical_levels",
            MappingProxyType(
                {source: tuple(levels) for source, levels in self.categorical_levels.items()}
            ),
        )
        object.__setattr__(self, "transforms", MappingProxyType(dict(self.transforms)))
        object.__setattr__(self, "exposure_columns", tuple(self.exposure_columns))


def request_from_confirmed_design(design: Design, fitted_rows) -> FixedEffectReconstructionRequest:
    """Project only independently ratified fitted facts; never infer them from ``design.model``."""
    declaration = design.fitted_design
    contrast_column, _, _ = design.contrast_column_and_levels()
    exposures = (contrast_column,) if isinstance(contrast_column, str) else ()
    if declaration is None or not confidence_high(design, "fitted_design"):
        return FixedEffectReconstructionRequest(
            rows_exact=False,
            row_ledger_identity=getattr(fitted_rows, "row_ledger_identity", ""),
            operator_kind="unsupported",
            intercept=True,
            column_kinds={}, categorical_levels={}, transforms={},
            exposure_columns=exposures,
            rows_exact_basis=RowsExactBasis.UNAVAILABLE,
            unsupported_reason="fitted design declaration was not ratified at high confidence",
        )
    operator_kind = declaration.operator_kind
    unsupported_reason = declaration.unsupported_reason
    if operator_kind == "ordinary_fixed_effects" and design.model is not None:
        formula = design.model.strip()
        body = formula[1:] if formula.startswith("~") else formula
        terms = [term.strip() for term in body.split("+")]
        additive_identity = bool(terms) and all(
            re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", term) for term in terms
        )
        if not additive_identity:
            operator_kind = "unsupported"
            unsupported_reason = "unsupported_nonadditive_operator"
    return FixedEffectReconstructionRequest(
        rows_exact=bool(declaration.rows_exact and getattr(fitted_rows, "exact", False)),
        row_ledger_identity=getattr(fitted_rows, "row_ledger_identity", ""),
        operator_kind=operator_kind,
        intercept=declaration.intercept,
        column_kinds=declaration.column_kinds,
        categorical_levels=declaration.categorical_levels,
        transforms=declaration.transforms,
        exposure_columns=exposures,
        rows_exact_basis=getattr(fitted_rows, "rows_exact_basis", RowsExactBasis.HUMAN_DECLARED),
        weight_role=declaration.weight_role,
        offset_role=declaration.offset_role,
        unsupported_reason=unsupported_reason,
    )


@dataclass(frozen=True)
class FittedDesignArtifact:
    c: np.ndarray
    c_column_ids: tuple[str, ...]
    c_source_columns: tuple[str, ...]
    c_source_column_indices: tuple[tuple[str, tuple[int, ...]], ...]
    excluded_exposure_columns: tuple[str, ...]
    row_identity: RowIdentity
    row_ledger_identity: str
    matrix_digest: str


@dataclass(frozen=True)
class FittedDesignResult:
    state: CertificationState
    reason: str
    machine_reason: str
    artifact: FittedDesignArtifact | None = None

    @property
    def exact(self) -> bool:
        return self.artifact is not None and self.state is CertificationState.CERTIFIED


def _not_audited(reason: str, machine_reason: str) -> FittedDesignResult:
    return FittedDesignResult(
        state=CertificationState.NOT_AUDITED,
        reason=reason,
        machine_reason=machine_reason,
    )


def _validate_excluded_source(
    rows: pd.DataFrame,
    source: str,
    request: FixedEffectReconstructionRequest,
) -> None:
    """Validate an excluded source without ever coding it into the nuisance matrix."""
    if source not in rows.columns:
        raise DesignMatrixError(f"missing source column {source!r}")
    if source not in request.column_kinds:
        raise DesignMatrixError(f"missing column kind for source {source!r}")
    series = rows[source]
    raw = series.to_numpy()
    if pd.api.types.is_bool_dtype(series.dtype) or any(
        isinstance(value, (bool, np.bool_)) for value in raw
    ):
        raise DesignMatrixError(f"boolean source {source!r} is unsupported")
    if series.isna().any():
        raise DesignMatrixError(f"missing values in source {source!r}")
    if request.column_kinds[source] == "continuous":
        if not pd.api.types.is_numeric_dtype(series.dtype):
            raise DesignMatrixError(f"continuous source {source!r} must be numeric")
        values = np.asarray(raw, dtype=np.float64)
        if not np.isfinite(values).all():
            raise DesignMatrixError(f"non-finite values in source {source!r}")
        return
    if request.column_kinds[source] != "categorical":
        raise DesignMatrixError(f"invalid column kind for source {source!r}")
    if source not in request.categorical_levels:
        raise DesignMatrixError(f"missing categorical levels for source {source!r}")
    levels = tuple(request.categorical_levels[source])
    level_keys = tuple(_canonical_scalar(level) for level in levels)
    observed_keys = tuple(_canonical_scalar(value) for value in raw)
    if not levels or len(set(level_keys)) != len(level_keys):
        raise DesignMatrixError(f"invalid categorical levels for source {source!r}")
    if set(level_keys) != set(observed_keys):
        raise DesignMatrixError(f"categorical level ledger mismatch for source {source!r}")


def reconstruct_nuisance_design(
    rows: pd.DataFrame,
    design: Design,
    request: FixedEffectReconstructionRequest,
) -> FittedDesignResult:
    """Reconstruct ``C`` only when every fixed-effect MVP fact is exact."""
    if not design.confirmed_by_human or not confidence_high(
        design, "analyst_adjusted_for"
    ) or design.analyst_adjusted_for is None:
        return _not_audited(
            "The fitted adjustment list was not ratified at high confidence.",
            "adjustment_not_ratified",
        )
    if (
        not request.rows_exact
        or not isinstance(request.row_ledger_identity, str)
        or not request.row_ledger_identity.strip()
    ):
        return _not_audited(
            "Exact fitted-row identity and order were not verified.",
            "rows_not_exact",
        )
    if request.operator_kind == "random_intercept_only":
        return _not_audited(
            "no verified conditioning operator found",
            "no_verified_conditioning_operator",
        )
    if request.operator_kind != "ordinary_fixed_effects":
        detail = request.unsupported_reason or "unsupported conditioning operator"
        return _not_audited(
            f"Column-space coverage was not audited: {detail}.",
            "unsupported_operator",
        )
    if request.unsupported_reason:
        return _not_audited(
            f"Column-space coverage was not audited: {request.unsupported_reason}.",
            "unsupported_request",
        )
    if request.weight_role is not None:
        return _not_audited(
            "A verified unweighted exposure geometry was unavailable because a weight role was present.",
            "weighted_geometry_unsupported",
        )
    if request.offset_role is not None:
        return _not_audited(
            "A verified ordinary exposure geometry was unavailable because an offset role was present.",
            "offset_geometry_unsupported",
        )
    if not isinstance(rows, pd.DataFrame):
        return _not_audited("Exact fitted rows were unavailable.", "rows_unavailable")

    adjusted = design.analyst_adjusted_for
    if not isinstance(adjusted, list) or not all(
        isinstance(source, str) and source for source in adjusted
    ):
        return _not_audited(
            "The ratified adjustment list contains an invalid exact column label.",
            "invalid_adjustment_label",
        )
    if len(set(adjusted)) != len(adjusted):
        return _not_audited(
            "The ratified adjustment list contains duplicate labels.",
            "duplicate_adjustment_label",
        )
    exposures = tuple(request.exposure_columns)
    if len(set(exposures)) != len(exposures):
        return _not_audited(
            "The exposure role ledger contains duplicate labels.",
            "duplicate_exposure_label",
        )

    for source in adjusted:
        if source not in rows.columns:
            return _not_audited(
                f"Requested adjustment column {source!r} is missing.",
                "missing_adjustment_column",
            )
        transform = request.transforms.get(source)
        if transform != "identity":
            shown = "missing" if transform is None else transform
            return _not_audited(
                f"Unsupported transform for {source!r}: {shown}.",
                "unsupported_transform",
            )
        if source not in request.column_kinds:
            return _not_audited(
                f"The exact column kind for {source!r} is missing.",
                "missing_column_kind",
            )

    nuisance_sources = tuple(source for source in adjusted if source not in exposures)
    excluded_sources = tuple(source for source in adjusted if source in exposures)
    try:
        for source in excluded_sources:
            _validate_excluded_source(rows, source, request)
        nuisance_kinds = {
            source: request.column_kinds[source] for source in nuisance_sources
        }
        nuisance_levels = {
            source: tuple(request.categorical_levels[source])
            for source in nuisance_sources
            if request.column_kinds[source] == "categorical"
            and source in request.categorical_levels
        }
        built = build_fixed_effect_matrix(
            rows,
            source_columns=nuisance_sources,
            column_kinds=nuisance_kinds,
            categorical_levels=nuisance_levels,
            intercept=request.intercept,
        )
    except (DesignMatrixError, TypeError, ValueError) as error:
        lowered = str(error).lower()
        if "missing value" in lowered or "non-finite" in lowered:
            reason = (
                "A requested value was missing or non-finite, and row dropping could not be verified."
            )
            machine_reason = "unverified_row_dropping"
        else:
            reason = f"The exact fixed-effect artifact could not be reconstructed: {error}."
            machine_reason = "design_matrix_unavailable"
        return _not_audited(reason, machine_reason)

    c = np.array(built.matrix, dtype=np.float64, order="C", copy=True)
    c.flags.writeable = False
    artifact = FittedDesignArtifact(
        c=c,
        c_column_ids=built.column_ids,
        c_source_columns=nuisance_sources,
        c_source_column_indices=built.source_column_indices,
        excluded_exposure_columns=excluded_sources,
        row_identity=built.row_identity,
        row_ledger_identity=request.row_ledger_identity,
        matrix_digest=_canonical_matrix_digest(
            c, policy_version=NUMERIC_POLICY_V1.version
        ),
    )
    return FittedDesignResult(
        state=CertificationState.CERTIFIED,
        reason="Exact ordinary fixed-effect nuisance geometry reconstructed.",
        machine_reason="exact_fixed_effect_geometry",
        artifact=artifact,
    )


def reconstruct_fixed_component_for_batch(
    rows: pd.DataFrame,
    design: Design,
    fitted_rows,
    batch: str,
) -> FittedDesignResult:
    """Reconstruct only independently ratified fixed facts beside a supported random intercept.

    The per-batch source list is provenance, never a span decision. The returned artifact is built
    from the existing analyst adjustment declaration and must still pass column-space certification.
    """
    declaration = design.fitted_design
    if declaration is None or not confidence_high(design, "fitted_design"):
        return _not_audited("The batch component ledger was not ratified.",
                            "batch_ledger_unratified")
    entry = declaration.batch_modeling.get(batch)
    if entry is None or entry.source_column != batch:
        return _not_audited("The batch component ledger was not ratified.",
                            "batch_ledger_unratified")
    if any(value != "high" for value in entry.field_confidence.values()):
        return _not_audited("The batch component ledger was not ratified at high confidence.",
                            "batch_ledger_unratified")
    if not entry.rows_exact or not getattr(fitted_rows, "exact", False):
        return _not_audited("The batch component does not cover exact fitted rows.",
                            "batch_rows_not_exact")
    if entry.row_ledger_identity != getattr(fitted_rows, "row_ledger_identity", None):
        return _not_audited("The batch component row identity is stale or mismatched.",
                            "batch_row_identity_mismatch")
    if entry.component_scope.contrast_name != design.name or (
        entry.component_scope.target_coefficient != design.target_coefficient
    ):
        return _not_audited("The batch component scope does not match this contrast.",
                            "batch_component_scope_mismatch")
    if entry.random_group_column != batch:
        return _not_audited("The random grouping column is not the declared batch.",
                            "random_group_column_mismatch")
    if entry.unsupported_components:
        return _not_audited("The batch component inventory contains unsupported structure.",
                            "unsupported_batch_component")
    if entry.fixed_source_columns is None:
        return _not_audited("The fixed-component source inventory is unresolved.",
                            "fixed_sources_unresolved")
    if entry.modeled_as not in ("random_intercept", "fixed_and_random_intercept"):
        return _not_audited("No ratified random-intercept component is in scope.",
                            "batch_component_not_in_scope")
    if declaration.unsupported_reason:
        return _not_audited("The whole fitted component inventory is incomplete.",
                            "unsupported_batch_component")
    for source in entry.fixed_source_columns:
        if source not in declaration.column_kinds or declaration.transforms.get(source) != "identity":
            return _not_audited("A fixed-component source cannot be reconstructed exactly.",
                                "fixed_source_map_unavailable")

    contrast_column, _, _ = design.contrast_column_and_levels()
    exposures = (contrast_column,) if isinstance(contrast_column, str) else ()
    request = FixedEffectReconstructionRequest(
        rows_exact=bool(declaration.rows_exact and fitted_rows.exact),
        row_ledger_identity=fitted_rows.row_ledger_identity,
        # This adapter reconstructs the independently inventoried fixed component; it does not
        # reinterpret the whole-fit operator enum used by the unchanged strong check.
        operator_kind="ordinary_fixed_effects",
        intercept=declaration.intercept,
        column_kinds=declaration.column_kinds,
        categorical_levels=declaration.categorical_levels,
        transforms=declaration.transforms,
        exposure_columns=exposures,
        rows_exact_basis=getattr(fitted_rows, "rows_exact_basis", RowsExactBasis.HUMAN_DECLARED),
        weight_role=declaration.weight_role,
        offset_role=declaration.offset_role,
    )
    return reconstruct_nuisance_design(rows, design, request)


def certify_identity_nuisance(
    reconstruction: FittedDesignResult,
    rows: pd.DataFrame,
    z_column: str,
) -> ColumnSpaceCertificate:
    """Certify identity ``H(Z)=[Z]`` against an exact reconstructed nuisance space."""
    if not reconstruction.exact:
        return ColumnSpaceCertificate(
            state=CertificationState.NOT_AUDITED,
            reason=reconstruction.reason,
            machine_reason=reconstruction.machine_reason,
        )
    artifact = reconstruction.artifact
    if not isinstance(rows, pd.DataFrame):
        return ColumnSpaceCertificate(
            state=CertificationState.NOT_AUDITED,
            reason="The fitted row identity could not be verified.",
            machine_reason="row_identity_unavailable",
        )
    try:
        rebuilt_identity = build_fixed_effect_matrix(
            rows,
            source_columns=(),
            column_kinds={},
            categorical_levels={},
            intercept=False,
        ).row_identity
    except DesignMatrixError:
        rebuilt_identity = None
    if rebuilt_identity != artifact.row_identity:
        return ColumnSpaceCertificate(
            state=CertificationState.NOT_AUDITED,
            reason="The fitted row identity or order does not match the reconstructed artifact.",
            machine_reason="row_identity_mismatch",
        )
    if not isinstance(z_column, str) or z_column not in rows.columns:
        return ColumnSpaceCertificate(
            state=CertificationState.NOT_AUDITED,
            reason="The identity candidate column is missing from the fitted rows.",
            machine_reason="missing_identity_candidate",
        )
    try:
        h = np.asarray(rows[z_column].to_numpy())[:, None]
        return certify_column_space(
            artifact.c,
            h,
            c_columns=artifact.c_column_ids,
            excluded_exposure_columns=artifact.excluded_exposure_columns,
            h_mapping=(f"{z_column}:identity",),
            row_ledger_identity=artifact.row_ledger_identity,
            exact=True,
        )
    except (TypeError, ValueError):
        return ColumnSpaceCertificate(
            state=CertificationState.NOT_AUDITED,
            reason="The identity candidate was not a finite continuous numeric column.",
            machine_reason="invalid_identity_candidate",
        )


def certificate_abstention_finding(
    check_id: str,
    certificate: ColumnSpaceCertificate | FittedDesignResult,
) -> "Finding":
    """Adapt only an audit-coverage abstention; geometry needs a consumer policy."""
    if certificate.state is not CertificationState.NOT_AUDITED:
        raise ValueError(
            "A certified or not-certified geometry outcome requires an independent consumer policy."
        )
    if certificate.machine_reason == "no_verified_conditioning_operator":
        verdict = "No verified conditioning operator found; column-space coverage was not checked."
    else:
        forbidden = (
            "omitted",
            "unadjusted",
            "biased",
            "confounded",
            "major",
            "blocker",
            "informational",
        )
        reason = certificate.reason
        if any(word in reason.lower() for word in forbidden):
            reason = "A required conditioning operator or exact artifact was unavailable."
        verdict = f"Column-space audit coverage is incomplete: {reason}"
    from sc_referee.checks.base import Finding

    return Finding(
        check_id,
        S.NOT_AUDITED,
        verdict,
        metrics={
            "column_space_state": CertificationState.NOT_AUDITED.value,
            "machine_reason": certificate.machine_reason,
        },
        coverage=S.NOT_RUN,
    )
