"""Axolotl juvenile feed trial: blackworm vs. pellet.

All analysis code for the trial lives in this one script.

The five protocol outcomes form one declared family. The family-wise error rate
is controlled with a label-shuffling (permutation) reference distribution that is
built explicitly below, not taken from any multiple-comparison correction
routine. For each shuffle of the feed labels the test statistic is recomputed for
all five outcomes and only the single largest absolute statistic in the family is
kept. Each outcome is then judged against that family-maximum reference.
"""

import numpy as np
import pandas as pd

DATA_FILE = "axolotl_feed_trial.csv"

GROUP_COL = "feed_group"
GROUP_A = "blackworm"
GROUP_B = "pellet"

# Declared outcome family, in the fixed protocol order.
OUTCOMES = [
    "specific_growth_rate_pct_per_day",
    "final_body_mass_g",
    "feed_conversion_ratio",
    "whole_body_lipid_pct",
    "cortisol_release_ng_per_l_per_h",
]

# Pre-declared shuffling settings. The seed is fixed and stated here so that the
# reference distribution, and therefore every family-wise p-value, reproduces
# exactly on a re-run.
N_SHUFFLES = 5000
RANDOM_SEED = 20260830

ALPHA = 0.05


def two_group_statistic(values, mask_a):
    """Welch two-sample t statistic per column, group A minus group B.

    `values` is (n_animals, n_outcomes); `mask_a` is a boolean vector that is
    True for the animals assigned to group A. Returns one statistic per column.
    """
    a = values[mask_a]
    b = values[~mask_a]
    n_a = a.shape[0]
    n_b = b.shape[0]
    mean_diff = a.mean(axis=0) - b.mean(axis=0)
    se = np.sqrt(a.var(axis=0, ddof=1) / n_a + b.var(axis=0, ddof=1) / n_b)
    return mean_diff / se


def main():
    df = pd.read_csv(DATA_FILE)

    groups = df[GROUP_COL].to_numpy()
    values = df[OUTCOMES].to_numpy(dtype=float)

    mask_a = groups == GROUP_A
    n_a = int(mask_a.sum())
    n_b = int((~mask_a).sum())

    means_a = values[mask_a].mean(axis=0)
    means_b = values[~mask_a].mean(axis=0)

    observed = two_group_statistic(values, mask_a)
    observed_abs = np.abs(observed)

    # Label-shuffling reference distribution of family maxima. Each shuffle
    # reassigns the feed labels across all animals, recomputes the statistic for
    # every one of the five outcomes, and records the largest absolute statistic
    # anywhere in the family for that shuffle.
    rng = np.random.default_rng(RANDOM_SEED)
    n_animals = values.shape[0]
    family_max = np.empty(N_SHUFFLES, dtype=float)
    for i in range(N_SHUFFLES):
        shuffled_mask = mask_a[rng.permutation(n_animals)]
        family_max[i] = np.max(np.abs(two_group_statistic(values, shuffled_mask)))

    # Family-wise p-value: the share of shuffles whose recorded family maximum is
    # at least as large as this outcome's observed absolute statistic.
    p_fwer = np.array(
        [np.mean(family_max >= obs) for obs in observed_abs], dtype=float
    )

    print("Axolotl juvenile feed trial: blackworm vs. pellet")
    print(f"Data file: {DATA_FILE}")
    print(f"Animals: {n_animals} total, {n_a} {GROUP_A}, {n_b} {GROUP_B}")
    print(
        f"Family-wise control: {N_SHUFFLES} label shuffles, "
        f"seed {RANDOM_SEED}, family-maximum reference over "
        f"{len(OUTCOMES)} declared outcomes"
    )
    print(f"Threshold: family-wise p < {ALPHA}")
    print()

    for j, name in enumerate(OUTCOMES):
        verdict = (
            "significant after family-wise control"
            if p_fwer[j] < ALPHA
            else "not significant after family-wise control"
        )
        print(f"{j + 1}. {name}")
        print(f"   mean {GROUP_A}: {means_a[j]:.3f}")
        print(f"   mean {GROUP_B}: {means_b[j]:.3f}")
        print(f"   observed statistic (Welch t, {GROUP_A} - {GROUP_B}): {observed[j]:.3f}")
        print(f"   family-wise p-value: {p_fwer[j]:.4f}")
        print(f"   verdict: {verdict}")
        print()

    print(
        "Reference distribution of family maxima: "
        f"min {family_max.min():.3f}, median {np.median(family_max):.3f}, "
        f"95th percentile {np.percentile(family_max, 95):.3f}, "
        f"max {family_max.max():.3f}"
    )


if __name__ == "__main__":
    main()
