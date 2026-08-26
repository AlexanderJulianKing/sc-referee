"""Enrichment programme comparison for captive Asian elephants.

Compares two enrichment programmes (scatter feeding vs fixed station) across the
six outcomes declared in PROTOCOL.md, and controls the family-wise error rate
over that family of six with a label-shuffling (permutation) procedure written
out here rather than with any packaged multiple-comparison correction.

Run from the project root:

    python3 analysis.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Fixed analysis constants, declared in advance.
# ---------------------------------------------------------------------------

DATA_FILE = Path(__file__).resolve().parent / "elephant_enrichment_welfare.csv"

GROUP_COLUMN = "enrichment_group"
GROUP_A = "scatter_feeding"
GROUP_B = "fixed_station"

# The six protocol outcomes, in the declared order. They form one family.
OUTCOMES = [
    "stereotypic_behaviour_pct",
    "daily_walking_distance_km",
    "night_recumbent_rest_min",
    "faecal_glucocorticoid_metabolites_ng_per_g",
    "feeding_bout_duration_min",
    "social_proximity_pct",
]

# Number of label shuffles, fixed in advance (not tuned after seeing results).
N_SHUFFLES = 5000

# Fixed seed so the run reproduces exactly.
RANDOM_SEED = 20260826

# Conventional family-wise error level.
FWER_ALPHA = 0.05


# ---------------------------------------------------------------------------
# Test statistic: two-sample t statistic, the same test for every outcome.
# ---------------------------------------------------------------------------


def two_sample_t(values, in_group_a):
    """Two-sample (pooled-variance) t statistic for group A minus group B.

    ``values`` has shape (n_animals, n_outcomes); ``in_group_a`` is a boolean
    mask of length n_animals. Returns one t statistic per outcome.
    """
    a = values[in_group_a, :]
    b = values[~in_group_a, :]
    n_a = a.shape[0]
    n_b = b.shape[0]
    # ddof=1 gives the usual unbiased sample variance.
    var_a = a.var(axis=0, ddof=1)
    var_b = b.var(axis=0, ddof=1)
    pooled_var = ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)
    standard_error = np.sqrt(pooled_var * (1.0 / n_a + 1.0 / n_b))
    return (a.mean(axis=0) - b.mean(axis=0)) / standard_error


def main():
    frame = pd.read_csv(DATA_FILE)

    observed_groups = frame[GROUP_COLUMN].to_numpy()
    distinct = sorted(set(observed_groups))
    if distinct != sorted([GROUP_A, GROUP_B]):
        raise ValueError(f"expected exactly the two groups {GROUP_A!r} and {GROUP_B!r}, found {distinct}")

    missing = [c for c in OUTCOMES if c not in frame.columns]
    if missing:
        raise ValueError(f"missing declared outcome columns: {missing}")
    if frame[OUTCOMES].isna().any().any():
        raise ValueError("declared outcome columns contain blank cells")

    values = frame[OUTCOMES].to_numpy(dtype=float)
    in_group_a = observed_groups == GROUP_A
    n_animals = values.shape[0]
    n_a = int(in_group_a.sum())
    n_b = n_animals - n_a

    # --- Step 1: observed statistics for the whole declared family. ---------
    observed_t = two_sample_t(values, in_group_a)

    # --- Step 2: reference distribution of the family maximum. -------------
    # On each shuffle the group labels are permuted across all animals (the
    # group sizes are held at their real values), all six statistics are
    # recomputed, and only the single largest absolute statistic across the
    # family is kept. That is the null distribution of the family maximum.
    rng = np.random.default_rng(RANDOM_SEED)
    family_max = np.empty(N_SHUFFLES, dtype=float)
    base_mask = np.zeros(n_animals, dtype=bool)
    base_mask[:n_a] = True
    for i in range(N_SHUFFLES):
        shuffled_mask = rng.permutation(base_mask)
        family_max[i] = np.max(np.abs(two_sample_t(values, shuffled_mask)))

    # --- Step 3: judge each outcome against the family maximum. ------------
    # Critical value: the (1 - alpha) quantile of the family-maximum
    # distribution. Any outcome whose absolute observed statistic reaches it is
    # significant at the 0.05 family-wise level.
    critical_value = float(np.quantile(family_max, 1.0 - FWER_ALPHA))

    # Family-wise adjusted p-value for each outcome: the share of shuffles
    # whose family maximum is at least as large as this outcome's observed
    # absolute statistic. The +1 in numerator and denominator keeps the value
    # strictly positive and the test valid at finite shuffle counts. No verdict
    # anywhere in this script uses an unadjusted per-outcome p-value.
    adjusted_p = np.array(
        [
            (1.0 + np.sum(family_max >= abs(t))) / (1.0 + N_SHUFFLES)
            for t in observed_t
        ]
    )

    # --- Report ------------------------------------------------------------
    print("Enrichment programme comparison for captive Asian elephants")
    print("=" * 78)
    print(f"Data file            : {DATA_FILE.name}")
    print(f"Elephants            : {n_animals} ({GROUP_A}: {n_a}, {GROUP_B}: {n_b})")
    print(f"Declared outcomes    : {len(OUTCOMES)} (one family)")
    print("Test statistic       : two-sample pooled-variance t "
          f"({GROUP_A} minus {GROUP_B}), same test for every outcome")
    print(f"Label shuffles       : {N_SHUFFLES} (fixed in advance)")
    print(f"Random seed          : {RANDOM_SEED}")
    print(f"Family-wise level    : {FWER_ALPHA}")
    print()
    print("Group means")
    print("-" * 78)
    print(f"{'outcome':<42}{GROUP_A:>16}{GROUP_B:>16}")
    for j, name in enumerate(OUTCOMES):
        mean_a = values[in_group_a, j].mean()
        mean_b = values[~in_group_a, j].mean()
        print(f"{name:<42}{mean_a:>16.3f}{mean_b:>16.3f}")
    print()
    print("Family-maximum reference distribution (null distribution of the")
    print("largest absolute t across all six outcomes)")
    print("-" * 78)
    print(f"shuffles                                : {N_SHUFFLES}")
    print(f"minimum family maximum                  : {family_max.min():.3f}")
    print(f"median family maximum                   : {np.median(family_max):.3f}")
    print(f"maximum family maximum                  : {family_max.max():.3f}")
    print(f"critical value ({1 - FWER_ALPHA:.2f} quantile)         : {critical_value:.3f}")
    print()
    print("Per-outcome results, judged against the family maximum")
    print("-" * 78)
    header = (
        f"{'outcome':<42}{'obs t':>9}{'crit':>8}{'adj p':>9}{'verdict':>10}"
    )
    print(header)
    for j, name in enumerate(OUTCOMES):
        t_value = observed_t[j]
        significant = abs(t_value) >= critical_value
        verdict = "SIG" if significant else "not sig"
        print(
            f"{name:<42}{t_value:>9.3f}{critical_value:>8.3f}"
            f"{adjusted_p[j]:>9.4f}{verdict:>10}"
        )
    print()
    print("Standing of each observed statistic in the reference distribution")
    print("-" * 78)
    for j, name in enumerate(OUTCOMES):
        t_value = observed_t[j]
        share_below = float(np.mean(family_max < abs(t_value)))
        print(
            f"{name:<42} |t| = {abs(t_value):>6.3f} exceeds "
            f"{share_below * 100:>6.2f}% of the {N_SHUFFLES} family maxima"
        )
    print()
    n_sig = int(np.sum(np.abs(observed_t) >= critical_value))
    print(
        f"{n_sig} of {len(OUTCOMES)} declared outcomes reach the "
        f"{FWER_ALPHA} family-wise threshold."
    )


if __name__ == "__main__":
    main()
