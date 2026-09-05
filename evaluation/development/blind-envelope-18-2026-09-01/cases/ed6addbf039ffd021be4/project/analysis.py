#!/usr/bin/env python3
"""Compare early-bloom and full-bloom lavender harvests across the six declared outcomes.

Family-wise error over the six pre-declared outcomes is controlled with a label-shuffling
(permutation) procedure written out here rather than with a ready-made correction.

Procedure
---------
1. Compute the observed two-group test statistic (Welch two-sample t) for each of the six
   declared outcomes, early bloom minus full bloom.
2. Shuffle the harvest-stage labels across all 64 bushes N_SHUFFLES times. On each shuffle
   recompute the same statistic for all six outcomes and keep only the largest absolute
   value across the whole family for that shuffle.
3. That gives one reference distribution of N_SHUFFLES family-maximum values. Each
   outcome's p-value is the proportion of shuffles whose family maximum reaches or exceeds
   that outcome's observed absolute statistic; the verdict is read at ALPHA.

The script takes no arguments, reads data.csv as it stands, and prints its results.
"""

import csv

import numpy as np

DATA_FILE = "data.csv"
ID_COLUMN = "bush_id"
GROUP_COLUMN = "harvest_stage"
GROUP_A = "early_bloom"
GROUP_B = "full_bloom"

# The six outcomes in the order the trial plan declared them.
OUTCOMES = [
    "fresh_inflorescence_biomass_g",
    "oil_yield_pct",
    "linalool_pct",
    "linalyl_acetate_pct",
    "camphor_pct",
    "cineole_1_8_pct",
]

N_SHUFFLES = 5000  # fixed before the analysis
SEED = 20260901  # fixed so the run reproduces
ALPHA = 0.05


def load_data(path):
    """Read the fixed data file. Returns the group labels and the outcome matrix."""
    labels = []
    rows = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in [ID_COLUMN, GROUP_COLUMN, *OUTCOMES] if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"{path} is missing expected columns: {missing}")
        for row in reader:
            labels.append(row[GROUP_COLUMN])
            rows.append([float(row[name]) for name in OUTCOMES])

    labels = np.asarray(labels)
    values = np.asarray(rows, dtype=float)

    seen = set(labels.tolist())
    if seen != {GROUP_A, GROUP_B}:
        raise ValueError(f"{GROUP_COLUMN} must hold exactly {{{GROUP_A}, {GROUP_B}}}; found {sorted(seen)}")
    if not np.isfinite(values).all():
        raise ValueError("outcome columns contain a missing or non-numeric value")
    return labels, values


def welch_t(group_a, group_b):
    """Two-sample Welch t statistic per column, group_a minus group_b."""
    n_a = group_a.shape[0]
    n_b = group_b.shape[0]
    mean_diff = group_a.mean(axis=0) - group_b.mean(axis=0)
    se = np.sqrt(group_a.var(axis=0, ddof=1) / n_a + group_b.var(axis=0, ddof=1) / n_b)
    return mean_diff / se


def family_max_reference(values, n_a, n_shuffles, seed):
    """Shuffle the labels n_shuffles times; keep the family maximum |t| from each shuffle."""
    rng = np.random.default_rng(seed)
    order = np.arange(values.shape[0])
    maxima = np.empty(n_shuffles, dtype=float)
    for i in range(n_shuffles):
        rng.shuffle(order)
        shuffled_a = values[order[:n_a]]
        shuffled_b = values[order[n_a:]]
        maxima[i] = np.max(np.abs(welch_t(shuffled_a, shuffled_b)))
    return maxima


def main():
    labels, values = load_data(DATA_FILE)

    in_a = labels == GROUP_A
    in_b = labels == GROUP_B
    n_a = int(in_a.sum())
    n_b = int(in_b.sum())

    observed_t = welch_t(values[in_a], values[in_b])
    maxima = family_max_reference(values, n_a, N_SHUFFLES, SEED)

    print("Lavender harvest timing: early bloom vs full bloom")
    print(f"Data file: {DATA_FILE}   bushes: {values.shape[0]}"
          f"   {GROUP_A}: {n_a}   {GROUP_B}: {n_b}")
    print(f"Declared outcome family ({len(OUTCOMES)} outcomes, declared order): "
          + ", ".join(OUTCOMES))
    print("Statistic: two-sample Welch t, "
          f"{GROUP_A} minus {GROUP_B}")
    print(f"Family-wise error control: label-shuffling permutation, "
          f"number of shuffles = {N_SHUFFLES}, seed = {SEED}")
    print(f"Reference distribution: the largest |t| across all {len(OUTCOMES)} outcomes on each shuffle")
    print(f"p = proportion of the {N_SHUFFLES} family maxima that reach or exceed the observed |t|; "
          f"alpha = {ALPHA}")
    print(f"Family-maximum reference: min {maxima.min():.4f}, "
          f"median {np.median(maxima):.4f}, 95th percentile "
          f"{np.percentile(maxima, 100 * (1 - ALPHA)):.4f}, max {maxima.max():.4f}")
    print()

    results = []
    for j, outcome in enumerate(OUTCOMES):
        a = values[in_a, j]
        b = values[in_b, j]
        t_obs = observed_t[j]
        n_at_or_above = int(np.count_nonzero(maxima >= abs(t_obs)))
        p_value = n_at_or_above / N_SHUFFLES
        significant = p_value < ALPHA
        results.append((outcome, n_at_or_above, p_value, significant))

        print(f"Outcome {j + 1}: {outcome}")
        print(f"  {GROUP_A}: n = {n_a}, mean = {a.mean():.4f}, sd = {a.std(ddof=1):.4f}")
        print(f"  {GROUP_B}: n = {n_b}, mean = {b.mean():.4f}, sd = {b.std(ddof=1):.4f}")
        print(f"  difference of means ({GROUP_A} - {GROUP_B}) = {a.mean() - b.mean():.4f}")
        print(f"  observed t = {t_obs:.4f}   |t| = {abs(t_obs):.4f}")
        print(f"  family-maximum shuffles at or above |t|: {n_at_or_above} of {N_SHUFFLES}"
              f"   p = {p_value:.4f}")
        print(f"  verdict at alpha = {ALPHA}: "
              + ("difference between harvest stages" if significant
                 else "no difference between harvest stages"))
        print()

    print("Summary (declared order):")
    print(f"{'outcome':<32}{'|t|':>9}{'p':>10}  verdict")
    for (outcome, _, p_value, significant), t_obs in zip(results, observed_t):
        verdict = "significant" if significant else "not significant"
        print(f"{outcome:<32}{abs(t_obs):>9.4f}{p_value:>10.4f}  {verdict}")
    n_sig = sum(1 for _, _, _, significant in results if significant)
    print(f"\n{n_sig} of {len(OUTCOMES)} declared outcomes are significant at the "
          f"family-wise alpha of {ALPHA} over {N_SHUFFLES} shuffles.")


if __name__ == "__main__":
    main()
