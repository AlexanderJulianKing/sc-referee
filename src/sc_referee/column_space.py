"""Deterministic Euclidean column-space arithmetic for continuous values."""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from enum import Enum

import numpy as np


@dataclass(frozen=True)
class NumericPolicy:
    version: str
    tau: float
    epsilon: float
    precision: str
    norm_name: str
    rank_algorithm: str
    rank_cutoff_rule: str


NUMERIC_POLICY_V1 = NumericPolicy(
    version="column-space-numeric-v1",
    tau=1e-8,
    epsilon=1e-12,
    precision="float64",
    norm_name="frobenius",
    rank_algorithm="thin_svd_relative_cutoff",
    rank_cutoff_rule="max(n,p)*float64_eps*s_max; rank=sum(s>cutoff)",
)


@dataclass(frozen=True)
class Residualization:
    residual: np.ndarray
    n_rows: int
    c_columns: int
    value_columns: int
    rank_c: int
    rank_values: int
    policy_version: str


def _as_float64(value, *, name: str, dimensions: tuple[int, ...]) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim not in dimensions:
        expected = " or ".join(map(str, dimensions))
        raise ValueError(f"{name} must have {expected} dimensions")
    if array.dtype.kind in "bOcUSV" or np.issubdtype(array.dtype, np.complexfloating):
        raise ValueError(f"{name} must contain real numeric values, excluding booleans")
    if not np.issubdtype(array.dtype, np.number):
        raise ValueError(f"{name} must contain real numeric values")
    copied = np.array(array, dtype=np.float64, order="C", copy=True)
    if not np.isfinite(copied).all():
        raise ValueError(f"{name} must contain only finite values")
    return copied


def _svd_rank(
    matrix: np.ndarray, policy: NumericPolicy
) -> tuple[int, np.ndarray | None, float]:
    if matrix.shape[1] == 0:
        return 0, None, 0.0
    u, singular_values, _ = np.linalg.svd(matrix, full_matrices=False)
    if not np.isfinite(u).all() or not np.isfinite(singular_values).all():
        raise np.linalg.LinAlgError("SVD returned non-finite factors")
    if singular_values.size == 0 or singular_values[0] == 0.0:
        return 0, u, 0.0
    cutoff = (
        max(matrix.shape)
        * np.finfo(np.float64).eps
        * singular_values[0]
    )
    return int(np.sum(singular_values > cutoff)), u, float(cutoff)


def residualize(
    C, V, *, policy: NumericPolicy = NUMERIC_POLICY_V1
) -> Residualization:
    """Residualize a vector or matrix against ``col(C)`` under policy v1."""
    c = _as_float64(C, name="C", dimensions=(2,))
    values = _as_float64(V, name="V", dimensions=(1, 2))
    if c.shape[0] != values.shape[0]:
        raise ValueError("C and V must have identical row counts")

    was_vector = values.ndim == 1
    values_2d = values[:, None] if was_vector else values
    rank_c, u, _ = _svd_rank(c, policy)
    rank_values, _, _ = _svd_rank(values_2d, policy)
    if rank_c == 0:
        residual = values_2d.copy(order="C")
    else:
        u_rank = u[:, :rank_c]
        residual = values_2d - u_rank @ (u_rank.T @ values_2d)
    if was_vector:
        residual = residual[:, 0]

    return Residualization(
        residual=np.ascontiguousarray(residual, dtype=np.float64),
        n_rows=c.shape[0],
        c_columns=c.shape[1],
        value_columns=values_2d.shape[1],
        rank_c=rank_c,
        rank_values=rank_values,
        policy_version=policy.version,
    )


class CertificationState(str, Enum):
    CERTIFIED = "certified"
    NOT_CERTIFIED = "not_certified"
    NOT_AUDITED = "not_audited"


@dataclass(frozen=True)
class ColumnSpaceWitness:
    rho: float
    tau: float
    epsilon: float
    norm_name: str
    precision: str
    rank_algorithm: str
    rank_cutoff_rule: str
    c_rank_cutoff: float
    h_rank_cutoff: float
    residual_rank_cutoff: float
    c_shape: tuple[int, int]
    h_shape: tuple[int, int]
    residual_shape: tuple[int, int]
    rank_c: int
    rank_h: int
    rank_residual: int
    c_columns: tuple[str, ...]
    h_mapping: tuple[str, ...]
    excluded_exposure_columns: tuple[str, ...]
    row_ledger_identity: str
    c_digest: str
    h_digest: str
    residual_digest: str
    numeric_policy_version: str
    condition_number_c: float
    forward_error_bound: float
    ambiguity_boundary: float
    per_direction_residuals: tuple[float, ...]
    decision_rule_id: str
    decision_norm_name: str


@dataclass(frozen=True)
class ColumnSpaceCertificate:
    state: CertificationState
    reason: str
    machine_reason: str
    witness: ColumnSpaceWitness | None = None


def _frobenius_norm(matrix: np.ndarray) -> float:
    if matrix.size == 0:
        return 0.0
    scale = float(np.max(np.abs(matrix)))
    if scale == 0.0:
        return 0.0
    scaled = matrix / scale
    return float(scale * np.sqrt(np.sum(np.square(scaled), dtype=np.float64)))


def _unit_scale_columns(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Unit-normalize columns without ever squaring an unscaled input."""
    scaled = np.zeros_like(matrix)
    norms = np.zeros(matrix.shape[1], dtype=np.float64)
    for index in range(matrix.shape[1]):
        column = matrix[:, index]
        maximum = float(np.max(np.abs(column))) if column.size else 0.0
        if maximum == 0.0:
            continue
        bounded = column / maximum
        bounded_norm = float(np.sqrt(np.sum(np.square(bounded), dtype=np.float64)))
        if not np.isfinite(bounded_norm) or bounded_norm == 0.0:
            norms[index] = np.nan
            continue
        scaled[:, index] = bounded / bounded_norm
        # Only zero/nonzero status is needed downstream.  Keeping the bounded
        # norm avoids recreating an overflowing magnitude diagnostic.
        norms[index] = bounded_norm
    return scaled, norms


def _globally_scale(matrix: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return matrix.copy()
    maximum = float(np.max(np.abs(matrix)))
    return matrix.copy() if maximum == 0.0 else matrix / maximum


def _not_audited(reason: str, machine_reason: str) -> ColumnSpaceCertificate:
    return ColumnSpaceCertificate(
        state=CertificationState.NOT_AUDITED,
        reason=reason,
        machine_reason=machine_reason,
    )


def _canonical_matrix_digest(matrix: np.ndarray, *, policy_version: str) -> str:
    canonical = np.ascontiguousarray(matrix, dtype="<f8")
    digest = hashlib.sha256()
    digest.update(b"sc-referee-column-space-matrix-digest-v1\0")
    encoded_version = policy_version.encode("utf-8")
    digest.update(struct.pack("<Q", len(encoded_version)))
    digest.update(encoded_version)
    digest.update(struct.pack("<Q", canonical.ndim))
    for dimension in canonical.shape:
        digest.update(struct.pack("<Q", dimension))
    digest.update(canonical.tobytes(order="C"))
    return f"sha256:{digest.hexdigest()}"


def _certification_state_for_rho(
    rho: float, policy: NumericPolicy = NUMERIC_POLICY_V1
) -> CertificationState:
    return (
        CertificationState.CERTIFIED
        if rho <= policy.tau
        else CertificationState.NOT_CERTIFIED
    )


def certify_column_space(
    C,
    H,
    *,
    c_columns: tuple[str, ...],
    excluded_exposure_columns: tuple[str, ...],
    h_mapping: tuple[str, ...],
    row_ledger_identity: str,
    exact: bool,
    unsupported_reason: str | None = None,
    policy: NumericPolicy = NUMERIC_POLICY_V1,
) -> ColumnSpaceCertificate:
    """Certify whether ``col(H)`` lies in ``col(C)`` under a frozen policy.

    The decision statistic is the largest principal-direction residual after
    independently unit-scaling the input columns.  With

    ``b = 16 * max(C.shape) * eps64 * cond(C)``

    the decision rule is:

    * CERTIFIED only if ``rho <= tau`` and ``b <= tau``;
    * NOT_AUDITED if ``rho <= max(tau, 8*b)``;
    * NOT_CERTIFIED only if ``C`` is full column rank and
      ``rho > max(tau, 8*b)``;
    * NOT_AUDITED when ``C`` is rank-deficient and inclusion is not certified.

    Thus projection error on the scale of the conditioning-aware forward-error
    bound cannot create an accusation.  A direction discarded by ``C``'s SVD
    rank cutoff is numerically indistinguishable from an omitted direction, so
    a rank-deficient ``C`` can certify inclusion but cannot support an
    accusation.  The factor 16 covers the SVD, orthogonal projection, and
    residual norm roundoff; the additional factor 8 is a deliberately
    conservative ambiguity band.  Rank-cutoff dependence, degenerate H, and
    every non-finite decision quantity also abstain.
    """
    if unsupported_reason:
        return ColumnSpaceCertificate(
            state=CertificationState.NOT_AUDITED,
            reason=f"Column-space coverage was not audited: {unsupported_reason}.",
            machine_reason="unsupported_geometry",
        )
    if not exact:
        return ColumnSpaceCertificate(
            state=CertificationState.NOT_AUDITED,
            reason="Inexact fitted-design reconstruction; column-space coverage was not audited.",
            machine_reason="inexact_reconstruction",
        )

    try:
        c = _as_float64(C, name="C", dimensions=(2,))
        h = _as_float64(H, name="H", dimensions=(1, 2))
    except ValueError as error:
        if "finite" not in str(error):
            raise
        return _not_audited(
            "Non-finite column-space input; coverage was not audited.",
            "nonfinite_input",
        )
    if h.ndim == 1:
        h = h[:, None]
    canonical_c_columns = tuple(c_columns)
    canonical_h_mapping = tuple(h_mapping)
    canonical_excluded = tuple(excluded_exposure_columns)
    if len(canonical_c_columns) != c.shape[1]:
        raise ValueError("c_columns must identify every column of C")
    if len(canonical_h_mapping) != h.shape[1]:
        raise ValueError("h_mapping must identify every column of H")
    if not isinstance(row_ledger_identity, str) or not row_ledger_identity.strip():
        raise ValueError("row_ledger_identity must be non-empty")
    if c.shape[0] != h.shape[0]:
        raise ValueError("C and H must have identical row counts")
    if h.shape[1] == 0:
        return _not_audited(
            "Empty H(Z) contains no required direction; coverage was not audited.",
            "empty_h",
        )

    try:
        scaled_c, c_norms = _unit_scale_columns(c)
        scaled_h, h_norms = _unit_scale_columns(h)
        if not all(
            np.isfinite(quantity).all()
            for quantity in (scaled_c, c_norms, scaled_h, h_norms)
        ):
            return _not_audited(
                "Non-finite scaled column-space arithmetic; coverage was not audited.",
                "nonfinite_arithmetic",
            )
        if np.any(h_norms == 0.0):
            return _not_audited(
                "Degenerate H(Z) contains a zero required direction; coverage was not audited.",
                "degenerate_h",
            )

        rank_c, u_c, c_cutoff = _svd_rank(scaled_c, policy)
        rank_h, u_h, h_cutoff = _svd_rank(scaled_h, policy)
        unscaled_rank_c, _, _ = _svd_rank(_globally_scale(c), policy)
        if rank_h != h.shape[1]:
            return _not_audited(
                "Rank-deficient H(Z) does not identify every required direction; coverage was not audited.",
                "degenerate_h",
            )

        h_basis = u_h[:, :rank_h]
        if rank_c == 0:
            residual = h_basis.copy(order="C")
            singular_c = np.empty(0, dtype=np.float64)
            condition_number_c = 1.0
        else:
            c_basis = u_c[:, :rank_c]
            residual = h_basis - c_basis @ (c_basis.T @ h_basis)
            singular_c = np.linalg.svd(scaled_c, compute_uv=False)
            retained_c = singular_c[:rank_c]
            condition_number_c = float(retained_c[0] / retained_c[-1])

        residual = np.ascontiguousarray(residual, dtype=np.float64)
        per_direction = tuple(
            float(np.sqrt(np.sum(np.square(residual[:, index]), dtype=np.float64)))
            for index in range(residual.shape[1])
        )
        residual_singular = np.linalg.svd(residual, compute_uv=False)
        rho = float(residual_singular[0]) if residual_singular.size else 0.0
        rank_residual, _, residual_cutoff = _svd_rank(residual, policy)
        forward_error_bound = float(
            16.0
            * max(c.shape)
            * np.finfo(np.float64).eps
            * condition_number_c
        )
        ambiguity_boundary = float(max(policy.tau, 8.0 * forward_error_bound))
        decision_quantities = np.array(
            [
                condition_number_c,
                forward_error_bound,
                ambiguity_boundary,
                rho,
                c_cutoff,
                h_cutoff,
                residual_cutoff,
                *per_direction,
            ],
            dtype=np.float64,
        )
        if not (
            np.isfinite(residual).all()
            and np.isfinite(singular_c).all()
            and np.isfinite(residual_singular).all()
            and np.isfinite(decision_quantities).all()
        ):
            return _not_audited(
                "Non-finite column-space decision arithmetic; coverage was not audited.",
                "nonfinite_arithmetic",
            )
    except np.linalg.LinAlgError:
        return _not_audited(
            "SVD failed to converge; column-space coverage was not audited.",
            "svd_failure",
        )

    # A required column with no between-row variation is not a meaningful
    # adjustment direction.  Still allow a clearly omitted, non-degenerate
    # companion direction to produce NOT_CERTIFIED (case 3); degeneracy may
    # suppress a CLEAR, never a clear omission.
    constant_required_direction = any(
        _frobenius_norm(column - np.mean(column))
        <= 64.0 * np.finfo(np.float64).eps * max(1.0, _frobenius_norm(column))
        for column in scaled_h.T
    )
    if rank_c == c.shape[1] and rho > ambiguity_boundary:
        state = CertificationState.NOT_CERTIFIED
    elif constant_required_direction:
        state = CertificationState.NOT_AUDITED
    elif rho <= policy.tau and forward_error_bound <= policy.tau:
        state = CertificationState.CERTIFIED
    else:
        state = CertificationState.NOT_AUDITED

    witness = ColumnSpaceWitness(
        rho=rho,
        tau=policy.tau,
        epsilon=policy.epsilon,
        norm_name=policy.norm_name,
        precision=policy.precision,
        rank_algorithm=policy.rank_algorithm,
        rank_cutoff_rule=policy.rank_cutoff_rule,
        c_rank_cutoff=c_cutoff,
        h_rank_cutoff=h_cutoff,
        residual_rank_cutoff=residual_cutoff,
        c_shape=(c.shape[0], c.shape[1]),
        h_shape=(h.shape[0], h.shape[1]),
        residual_shape=(residual.shape[0], residual.shape[1]),
        rank_c=rank_c,
        rank_h=rank_h,
        rank_residual=rank_residual,
        c_columns=canonical_c_columns,
        h_mapping=canonical_h_mapping,
        excluded_exposure_columns=canonical_excluded,
        row_ledger_identity=row_ledger_identity,
        c_digest=_canonical_matrix_digest(c, policy_version=policy.version),
        h_digest=_canonical_matrix_digest(h, policy_version=policy.version),
        residual_digest=_canonical_matrix_digest(residual, policy_version=policy.version),
        numeric_policy_version=policy.version,
        condition_number_c=condition_number_c,
        forward_error_bound=forward_error_bound,
        ambiguity_boundary=ambiguity_boundary,
        per_direction_residuals=per_direction,
        decision_rule_id="principal-residual-cond-band-v1",
        decision_norm_name="maximum_principal_direction_residual_2_norm",
    )
    # A relative cutoff on the unscaled matrix can discard a genuine direction solely because
    # another column carries a large unit scale.  If unit-norm column scaling changes the SVD rank,
    # the span decision is cutoff-dependent: neither inclusion nor exclusion is certified.
    if unscaled_rank_c != rank_c:
        return ColumnSpaceCertificate(
            state=CertificationState.NOT_AUDITED,
            reason=("The column-space decision depends on a singular direction discarded by "
                    "the scale-derived rank cutoff; the span is numerically ambiguous."),
            machine_reason="ill_conditioned_span_ambiguous",
            witness=witness,
        )
    if rank_c < c.shape[1] and state is not CertificationState.CERTIFIED:
        return ColumnSpaceCertificate(
            state=CertificationState.NOT_AUDITED,
            reason=(
                "The fitted design is numerically rank-deficient, so a required "
                "direction may lie in a span discarded by the rank cutoff; "
                "column-space coverage was not audited."
            ),
            machine_reason="rank_deficient_ambiguous_span",
            witness=witness,
        )
    if state is CertificationState.NOT_AUDITED:
        machine_reason = (
            "degenerate_h" if constant_required_direction else "conditioning_ambiguous"
        )
        return ColumnSpaceCertificate(
            state=state,
            reason=(
                "Column-space coverage was not audited because the required basis is degenerate."
                if constant_required_direction
                else "The residual lies in the conditioning-aware ambiguity band; coverage was not audited."
            ),
            machine_reason=machine_reason,
            witness=witness,
        )
    relation = "lies in" if state is CertificationState.CERTIFIED else "lies outside"
    return ColumnSpaceCertificate(
        state=state,
        reason=f"H(Z) {relation} the verified nuisance column space under numeric policy v1.",
        machine_reason=state.value,
        witness=witness,
    )
