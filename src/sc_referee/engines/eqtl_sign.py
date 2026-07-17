"""Donor-level OLS sign recompute for the narrow eQTL orientation contract.

This engine returns arithmetic facts only. It does not decide Finding status or blocker entitlement.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import sparse, stats

from sc_referee.design import subset_mask
from sc_referee.engine import aggregate_to_pseudobulk


@dataclass(frozen=True)
class OrientationResolution:
    resolved: bool
    transform: str | None = None       # identity | complement
    source: str | None = None          # direct | exact_cohort_frequency | direct_and_frequency
    reason: str | None = None


@dataclass(frozen=True)
class EqtlSignResult:
    identified: bool
    reason: str | None
    sign: int | None
    slope: float | None
    se: float | None
    ci_low: float | None
    ci_high: float | None
    n_donors: int
    class_counts: dict
    raw_frequency: float | None
    transform: str


def resolve_orientation(design, raw_frequency: float) -> OrientationResolution:
    """Resolve raw dosage -> effect-allele dosage from ratified atomic facts.

    Direct and exact-cohort frequency footprints must agree when both are supplied. Population-panel
    frequency, MAF, and dosage mean alone never resolve orientation.
    """
    alleles = tuple(design.variant_alleles or ())
    effect = design.effect_allele
    if design.dosage_ploidy != 2:
        return OrientationResolution(False, reason="unsupported_ploidy")
    if len(alleles) != 2 or len(set(alleles)) != 2 or effect not in alleles:
        return OrientationResolution(False, reason="invalid_biallelic_contract")

    direct_transform = None
    counted = design.dosage_counts_allele
    if counted is not None:
        if counted not in alleles:
            return OrientationResolution(False, reason="dosage_allele_not_in_variant_alleles")
        direct_transform = "identity" if counted == effect else "complement"

    interval = design.effect_allele_frequency_interval
    scope = design.effect_allele_frequency_scope
    frequency_transform = None
    if interval is not None or scope is not None:
        if interval is None:
            return OrientationResolution(False, reason="frequency_interval_missing")
        if scope != "audited_donors":
            # An external panel is useful evidence, but population/sampling differences prevent proof.
            if direct_transform is None:
                return OrientationResolution(False, reason="frequency_scope_not_audited_donors")
        else:
            lo, hi = interval
            if not (0 <= lo <= hi <= 1):
                return OrientationResolution(False, reason="invalid_frequency_interval")
            raw_matches = bool(lo <= raw_frequency <= hi)
            complement_matches = bool(lo <= 1.0 - raw_frequency <= hi)
            if raw_matches == complement_matches:
                reason = ("frequency_orientation_ambiguous" if raw_matches
                          else "frequency_orientation_no_match")
                return OrientationResolution(False, reason=reason)
            frequency_transform = "identity" if raw_matches else "complement"

    if direct_transform is not None and frequency_transform is not None:
        if direct_transform != frequency_transform:
            return OrientationResolution(False, reason="orientation_footprints_conflict")
        return OrientationResolution(True, direct_transform, "direct_and_frequency")
    if direct_transform is not None:
        return OrientationResolution(True, direct_transform, "direct")
    if frequency_transform is not None:
        return OrientationResolution(True, frequency_transform, "exact_cohort_frequency")
    return OrientationResolution(False, reason="no_orientation_footprint")


def _failure(reason, *, transform, n=0, class_counts=None, raw_frequency=None) -> EqtlSignResult:
    return EqtlSignResult(
        identified=False, reason=reason, sign=None, slope=None, se=None, ci_low=None, ci_high=None,
        n_donors=n, class_counts=class_counts or {}, raw_frequency=raw_frequency, transform=transform,
    )


def recompute_eqtl_sign(bundle, design, *, transform: str) -> EqtlSignResult:
    """Aggregate raw counts by donor and fit the supported OLS-with-intercept sign estimand."""
    if transform not in ("identity", "complement"):
        return _failure("unsupported_orientation_transform", transform=transform)
    if bundle is None or getattr(bundle, "measure", None) is None:
        return _failure("bundle_missing", transform=transform)
    if bundle.measure.kind != "counts" or bundle.measure.counts is None:
        return _failure("raw_counts_unavailable", transform=transform)

    obs = bundle.observations
    keys = list(design.sample_unit or [])
    replicate = list(design.replicate_unit or [])
    if (not keys or not replicate or len(keys) != len(set(keys))
            or len(replicate) != len(set(replicate)) or set(keys) != set(replicate)):
        return _failure("sample_unit_is_not_the_ratified_donor_unit", transform=transform)
    required = [*keys, design.genotype_column]
    if any(c is None or c not in obs.columns for c in required):
        return _failure("donor_or_genotype_column_missing", transform=transform)
    if obs.columns.duplicated().any():
        return _failure("duplicate_observation_column_labels", transform=transform)

    raw_counts = bundle.measure.counts
    counts = sparse.csr_matrix(raw_counts) if sparse.issparse(raw_counts) else np.asarray(raw_counts)
    if getattr(counts, "ndim", 2) != 2 or counts.shape[0] != len(obs):
        return _failure("count_observation_alignment_invalid", transform=transform)
    values = counts.data if sparse.issparse(counts) else counts
    if (not np.issubdtype(counts.dtype, np.number) or not np.isfinite(values).all()
            or (values < 0).any() or not np.equal(values, np.floor(values)).all()):
        return _failure("count_matrix_is_not_finite_nonnegative_integers", transform=transform)
    features = list(bundle.measure.feature_index)
    if counts.shape[1] != len(features):
        return _failure("count_feature_alignment_invalid", transform=transform)
    if features.count(design.target_feature) != 1:
        return _failure("target_feature_not_unique_in_counts", transform=transform)

    mask = subset_mask(obs, design)
    scoped = obs if mask.all() else obs[mask]
    if scoped.empty:
        return _failure("confirmed_subset_is_empty", transform=transform)
    if scoped[keys].isna().any(axis=None):
        return _failure("missing_donor_key", transform=transform)
    dosage = scoped[design.genotype_column]
    if not pd.api.types.is_numeric_dtype(dosage.dtype) or pd.api.types.is_bool_dtype(dosage.dtype):
        return _failure("dosage_is_not_numeric", transform=transform)
    if dosage.isna().any() or not np.isfinite(dosage.to_numpy(dtype=float)).all():
        return _failure("dosage_missing_or_nonfinite", transform=transform)
    per_donor_nunique = scoped.groupby(keys, observed=True, sort=False, dropna=False)[
        design.genotype_column].nunique(dropna=False)
    if (per_donor_nunique != 1).any():
        return _failure("dosage_not_constant_within_donor", transform=transform)

    pb, meta = aggregate_to_pseudobulk(bundle, design)
    if meta.empty or design.genotype_column not in meta.columns:
        return _failure("donor_aggregation_empty", transform=transform)
    g = meta[design.genotype_column].to_numpy(dtype=float)
    if not np.isfinite(g).all() or not np.isin(g, (0.0, 1.0, 2.0)).all():
        return _failure("dosage_is_not_a_finite_0_1_2_hard_call", transform=transform)

    unique, counts_per_class = np.unique(g, return_counts=True)
    class_counts = {int(k): int(v) for k, v in zip(unique, counts_per_class)}
    raw_frequency = float(g.mean() / 2.0)
    n = len(g)
    if sum(v >= 3 for v in class_counts.values()) < 2:
        return _failure("fewer_than_3_donors_in_2_genotype_classes", transform=transform, n=n,
                        class_counts=class_counts, raw_frequency=raw_frequency)

    target_pos = features.index(design.target_feature)
    libraries = pb.to_numpy(dtype=float).sum(axis=1)
    target = pb.iloc[:, target_pos].to_numpy(dtype=float)
    if (libraries <= 0).any() or not np.isfinite(libraries).all():
        return _failure("nonpositive_or_nonfinite_library_size", transform=transform, n=n,
                        class_counts=class_counts, raw_frequency=raw_frequency)
    y = np.log2(target / libraries * 1e6 + 1.0)
    x = g if transform == "identity" else 2.0 - g
    if not np.isfinite(y).all() or np.var(x) <= 0 or np.var(y) <= 0:
        return _failure("genotype_or_outcome_has_no_variation", transform=transform, n=n,
                        class_counts=class_counts, raw_frequency=raw_frequency)

    x_centered = x - x.mean()
    y_centered = y - y.mean()
    sxx = float(x_centered @ x_centered)
    slope = float((x_centered @ y_centered) / sxx)
    intercept = float(y.mean() - slope * x.mean())
    residual = y - (intercept + slope * x)
    df = n - 2
    if df <= 0:
        return _failure("insufficient_ols_degrees_of_freedom", transform=transform, n=n,
                        class_counts=class_counts, raw_frequency=raw_frequency)
    se = float(np.sqrt(float(residual @ residual) / df / sxx))
    if not np.isfinite(slope) or not np.isfinite(se):
        return _failure("nonfinite_ols_slope_or_se", transform=transform, n=n,
                        class_counts=class_counts, raw_frequency=raw_frequency)
    critical = float(stats.t.ppf(0.975, df))
    ci_low, ci_high = slope - critical * se, slope + critical * se
    if not (ci_low > 0 or ci_high < 0):
        return EqtlSignResult(
            False, "slope_sign_not_identified", None, slope, se, ci_low, ci_high, n,
            class_counts, raw_frequency, transform,
        )
    sign = 1 if slope > 0 else -1
    return EqtlSignResult(
        True, None, sign, slope, se, ci_low, ci_high, n, class_counts, raw_frequency, transform,
    )
