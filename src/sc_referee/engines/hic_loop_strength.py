"""Arithmetic-only recompute for one exact Hi-C loop-strength estimator contract."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

MIN_BACKGROUND_PAIRS = 50  # conservative coverage floor, not a theorem


@dataclass(frozen=True)
class HiCLoopStrengthResult:
    identified: bool
    reason: str | None
    recomputed_delta: float | None
    condition_means: dict
    sample_strengths: tuple[dict, ...]
    background_pairs: int
    distance_bp: int | None
    samples_per_condition: dict
    contacts_digest: str | None = None
    bins_digest: str | None = None


def _failure(reason, *, background_pairs=0, distance_bp=None, samples=None, bundle=None):
    hic = getattr(bundle, "hic", None)
    return HiCLoopStrengthResult(
        False, reason, None, {}, tuple(samples or ()), background_pairs, distance_bp, {},
        getattr(hic, "contacts_digest", None), getattr(hic, "bins_digest", None),
    )


def _canonical_pair(left, right):
    if not isinstance(left, str) or not isinstance(right, str) or left == right:
        raise ValueError("bin ids must be distinct strings")
    return (left, right) if left < right else (right, left)


def recompute_hic_loop_strength(bundle, design) -> HiCLoopStrengthResult:
    hic = getattr(bundle, "hic", None)
    contacts = getattr(hic, "contacts", None)
    bins = getattr(hic, "bins", None)
    if not isinstance(contacts, pd.DataFrame) or not isinstance(bins, pd.DataFrame):
        return _failure("contacts_or_bins_missing", bundle=bundle)
    if contacts.columns.duplicated().any() or bins.columns.duplicated().any():
        return _failure("duplicate_contact_or_bin_column_labels", bundle=bundle)
    contact_required = [*list(design.replicate_unit or []), design.condition,
                        "bin_i", "bin_j", "observed_count"]
    bin_required = ["bin_id", "chrom", "start", "masked"]
    if any(c is None or c not in contacts.columns for c in contact_required):
        return _failure("required_contact_column_missing", bundle=bundle)
    if any(c not in bins.columns for c in bin_required):
        return _failure("required_bin_column_missing", bundle=bundle)
    replicate = list(design.replicate_unit or [])
    if not replicate or len(replicate) != len(set(replicate)):
        return _failure("replicate_key_missing_or_duplicated", bundle=bundle)

    resolution = design.hic_resolution_bp
    view_start, view_end = design.hic_background_view_start, design.hic_background_view_end
    if (isinstance(resolution, bool) or not isinstance(resolution, int) or resolution <= 0
            or isinstance(view_start, bool) or not isinstance(view_start, int)
            or isinstance(view_end, bool) or not isinstance(view_end, int)
            or view_start < 0 or view_end <= view_start or (view_end - view_start) % resolution):
        return _failure("invalid_resolution_or_background_view", bundle=bundle)
    if bins["bin_id"].isna().any() or bins["bin_id"].duplicated().any():
        return _failure("bin_ids_missing_or_duplicated", bundle=bundle)
    if not bins["bin_id"].map(lambda x: isinstance(x, str)).all():
        return _failure("bin_ids_are_not_strings", bundle=bundle)
    if (not pd.api.types.is_integer_dtype(bins["start"].dtype)
            or bins["start"].isna().any() or (bins["start"] < 0).any()):
        return _failure("bin_starts_are_not_nonnegative_integers", bundle=bundle)
    if not pd.api.types.is_bool_dtype(bins["masked"].dtype):
        return _failure("masked_column_is_not_boolean", bundle=bundle)

    indexed = bins.set_index("bin_id", drop=False)
    target_i, target_j = design.hic_target_bin_i, design.hic_target_bin_j
    if target_i not in indexed.index or target_j not in indexed.index or target_i == target_j:
        return _failure("target_bins_missing_or_degenerate", bundle=bundle)
    left, right = indexed.loc[target_i], indexed.loc[target_j]
    if left["chrom"] != right["chrom"]:
        return _failure("trans_target_is_unsupported", bundle=bundle)
    if bool(left["masked"]) or bool(right["masked"]):
        return _failure("target_bin_is_masked", bundle=bundle)
    target_chrom = left["chrom"]
    distance_bp = abs(int(left["start"]) - int(right["start"]))
    if distance_bp <= 0 or distance_bp % resolution:
        return _failure("target_distance_not_on_resolution_grid", distance_bp=distance_bp, bundle=bundle)
    view = bins[(bins["chrom"] == target_chrom)
                & (bins["start"] >= view_start) & (bins["start"] < view_end)].copy()
    expected_starts = list(range(view_start, view_end, resolution))
    if (view["start"].duplicated().any() or sorted(view["start"].tolist()) != expected_starts):
        return _failure("background_bin_view_is_not_a_complete_grid", distance_bp=distance_bp,
                        bundle=bundle)
    by_start = {int(row.start): row for row in view.itertuples(index=False)}
    all_pairs = []
    for start in expected_starts:
        other = start + distance_bp
        if other in by_start:
            all_pairs.append(_canonical_pair(by_start[start].bin_id, by_start[other].bin_id))
    target_pair = _canonical_pair(target_i, target_j)
    if target_pair not in all_pairs:
        return _failure("target_not_in_ratified_background_view", distance_bp=distance_bp, bundle=bundle)
    mask_by_id = dict(zip(view["bin_id"], view["masked"]))
    background = [pair for pair in all_pairs
                  if pair != target_pair and not mask_by_id[pair[0]] and not mask_by_id[pair[1]]]
    if len(background) < MIN_BACKGROUND_PAIRS:
        return _failure("fewer_than_50_eligible_background_pairs", background_pairs=len(background),
                        distance_bp=distance_bp, bundle=bundle)

    if contacts[contact_required].isna().any(axis=None):
        return _failure("missing_contact_identity_or_count", background_pairs=len(background),
                        distance_bp=distance_bp, bundle=bundle)
    counts = contacts["observed_count"]
    if (pd.api.types.is_bool_dtype(counts.dtype) or not pd.api.types.is_numeric_dtype(counts.dtype)
            or not np.isfinite(counts.to_numpy(dtype=float)).all() or (counts < 0).any()
            or not np.equal(counts.to_numpy(dtype=float), np.floor(counts.to_numpy(dtype=float))).all()):
        return _failure("observed_counts_not_finite_nonnegative_integers",
                        background_pairs=len(background), distance_bp=distance_bp, bundle=bundle)
    known_bins = set(bins["bin_id"])
    if not set(contacts["bin_i"]).union(contacts["bin_j"]) <= known_bins:
        return _failure("contact_references_unknown_bin", background_pairs=len(background),
                        distance_bp=distance_bp, bundle=bundle)
    try:
        relation = contacts.copy()
        relation["_pair"] = [_canonical_pair(a, b)
                             for a, b in zip(relation["bin_i"], relation["bin_j"])]
    except (TypeError, ValueError):
        return _failure("invalid_contact_bin_pair", background_pairs=len(background),
                        distance_bp=distance_bp, bundle=bundle)
    reference, test = design.reference, design.test
    if reference == test:
        return _failure("reference_and_test_are_not_distinct", background_pairs=len(background),
                        distance_bp=distance_bp, bundle=bundle)
    relation = relation[(relation[design.condition] == reference)
                        | (relation[design.condition] == test)]
    sample_columns = [*replicate, design.condition]
    if relation.empty:
        return _failure("no_contacts_in_confirmed_arms", background_pairs=len(background),
                        distance_bp=distance_bp, bundle=bundle)
    required_pairs = set(all_pairs)
    sample_strengths = []
    seen_conditions = []
    grouper = sample_columns[0] if len(sample_columns) == 1 else sample_columns
    for sample_key, sample in relation.groupby(grouper, observed=True, sort=False, dropna=False):
        if sample["_pair"].duplicated().any():
            return _failure("duplicate_unordered_contact_pixel", background_pairs=len(background),
                            distance_bp=distance_bp, bundle=bundle)
        pair_counts = dict(zip(sample["_pair"], sample["observed_count"]))
        if not required_pairs <= set(pair_counts):
            return _failure("dense_zero_inclusive_distance_stratum_incomplete",
                            background_pairs=len(background), distance_bp=distance_bp, bundle=bundle)
        observed = float(pair_counts[target_pair])
        expected = float(sum(int(pair_counts[pair]) for pair in background) / len(background))
        if not np.isfinite(observed) or not np.isfinite(expected) or observed <= 0 or expected <= 0:
            return _failure("observed_or_expected_not_positive", background_pairs=len(background),
                            distance_bp=distance_bp, bundle=bundle)
        condition = sample.iloc[0][design.condition]
        strength = float(np.log2(observed / expected))
        sample_strengths.append({
            "sample": sample_key if isinstance(sample_key, tuple) else (sample_key,),
            "condition": condition,
            "observed": observed,
            "expected": expected,
            "log2_oe": strength,
        })
        seen_conditions.append(condition)
    per_condition = {}
    sample_counts = {}
    for condition in (reference, test):
        values = [row["log2_oe"] for row in sample_strengths if row["condition"] == condition]
        if not values:
            return _failure("one_or_both_conditions_have_no_replicates",
                            background_pairs=len(background), distance_bp=distance_bp,
                            samples=sample_strengths, bundle=bundle)
        per_condition[condition] = float(np.mean(values))
        sample_counts[condition] = len(values)
    delta = float(per_condition[test] - per_condition[reference])
    return HiCLoopStrengthResult(
        True, None, delta, per_condition, tuple(sample_strengths), len(background), distance_bp,
        sample_counts, hic.contacts_digest, hic.bins_digest,
    )
