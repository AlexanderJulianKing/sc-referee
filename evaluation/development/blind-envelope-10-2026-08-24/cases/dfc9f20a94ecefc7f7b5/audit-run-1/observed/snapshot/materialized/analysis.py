"""Harvest-timing comparison for dual-purpose industrial hemp.

Five outcomes were declared in the protocol, in this order:

    1. bast_fibre_yield_g
    2. tensile_strength_mpa
    3. stem_diameter_mm
    4. cbd_pct_dry
    5. stem_moisture_pct

Each outcome is compared between the two harvest timings with Welch's
two-sample t statistic.  Family-wise error is controlled by a label-shuffling
(max-T permutation) procedure written out by hand below: the harvest-timing
labels are permuted across all 96 plants, the statistic is recomputed for all
five outcomes on each permutation, and only the single largest absolute
statistic of the family is kept.  Every observed statistic is then referred to
that one reference distribution of family maxima.

Run from the project root:

    python analysis.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

DATA_FILE = "hemp_harvest_timing.csv"

GROUP_COLUMN = "harvest_group"
GROUP_A = "early_flower"
GROUP_B = "seed_mature"

# Declared outcome family, in protocol order.
OUTCOMES = [
    "bast_fibre_yield_g",
    "tensile_strength_mpa",
    "stem_diameter_mm",
    "cbd_pct_dry",
    "stem_moisture_pct",
]

N_SHUFFLES = 5000
RANDOM_SEED = 31415926
ALPHA = 0.05


# --------------------------------------------------------------------------
# Test statistic
# --------------------------------------------------------------------------


def welch_t(values_a: np.ndarray, values_b: np.ndarray) -> np.ndarray:
    """Welch's two-sample t statistic, group A minus group B.

    `values_a` and `values_b` have shape (..., n_a, n_outcomes) and
    (..., n_b, n_outcomes).  The statistic is computed along the
    second-to-last axis, so one call handles either a single data set or a
    whole stack of shuffled data sets.
    """
    n_a = values_a.shape[-2]
    n_b = values_b.shape[-2]

    mean_a = values_a.mean(axis=-2)
    mean_b = values_b.mean(axis=-2)

    # ddof=1: unbiased sample variance.
    var_a = values_a.var(axis=-2, ddof=1)
    var_b = values_b.var(axis=-2, ddof=1)

    standard_error = np.sqrt(var_a / n_a + var_b / n_b)
    return (mean_a - mean_b) / standard_error


# --------------------------------------------------------------------------
# Load and check the data
# --------------------------------------------------------------------------


def load_data() -> pd.DataFrame:
    frame = pd.read_csv(DATA_FILE)

    missing = [c for c in [GROUP_COLUMN, *OUTCOMES] if c not in frame.columns]
    if missing:
        raise ValueError(f"missing expected columns: {missing}")

    observed_groups = sorted(frame[GROUP_COLUMN].unique())
    if observed_groups != sorted([GROUP_A, GROUP_B]):
        raise ValueError(f"unexpected group labels: {observed_groups}")

    if frame[OUTCOMES].isna().to_numpy().any():
        raise ValueError("outcome columns contain empty cells")

    return frame


# --------------------------------------------------------------------------
# Main analysis
# --------------------------------------------------------------------------


def main() -> None:
    frame = load_data()

    n_plants = len(frame)
    is_group_a = (frame[GROUP_COLUMN] == GROUP_A).to_numpy()
    n_a = int(is_group_a.sum())
    n_b = n_plants - n_a

    # Outcome matrix, shape (n_plants, n_outcomes), columns in declared order.
    outcome_matrix = frame[OUTCOMES].to_numpy(dtype=float)

    # ---- observed statistics -------------------------------------------
    observed_t = welch_t(outcome_matrix[is_group_a], outcome_matrix[~is_group_a])

    # ---- group summaries ------------------------------------------------
    mean_a = outcome_matrix[is_group_a].mean(axis=0)
    sd_a = outcome_matrix[is_group_a].std(axis=0, ddof=1)
    mean_b = outcome_matrix[~is_group_a].mean(axis=0)
    sd_b = outcome_matrix[~is_group_a].std(axis=0, ddof=1)

    # ---- label shuffling ------------------------------------------------
    # A fixed seed makes the whole run reproducible.
    rng = np.random.default_rng(RANDOM_SEED)

    family_max = np.empty(N_SHUFFLES, dtype=float)
    for i in range(N_SHUFFLES):
        # Shuffle the harvest-timing labels across plants.  Equivalently,
        # permute the plant rows and hand the first n_a of them the
        # early_flower label.
        order = rng.permutation(n_plants)
        shuffled = outcome_matrix[order]
        shuffled_t = welch_t(shuffled[:n_a], shuffled[n_a:])
        # Keep only the single largest absolute statistic of the family.
        family_max[i] = np.abs(shuffled_t).max()

    # ---- p-values against the family-maximum distribution ---------------
    # Proportion of shuffles whose family maximum is at least as extreme as
    # the observed statistic for that outcome.
    exceed_counts = np.array(
        [int((family_max >= abs(t)).sum()) for t in observed_t]
    )
    p_values = exceed_counts / N_SHUFFLES
    verdicts = ["significant" if p < ALPHA else "not significant" for p in p_values]

    # ---- report ---------------------------------------------------------
    print("Harvest-timing comparison for dual-purpose industrial hemp")
    print("=" * 78)
    print(f"data file                : {DATA_FILE}")
    print(f"plants                   : {n_plants}")
    print(f"  {GROUP_A:<22}: {n_a}")
    print(f"  {GROUP_B:<22}: {n_b}")
    print(f"declared outcomes        : {len(OUTCOMES)}")
    print(f"test statistic           : Welch two-sample t ({GROUP_A} - {GROUP_B})")
    print(f"label shuffles           : {N_SHUFFLES}")
    print(f"random seed              : {RANDOM_SEED}")
    print(f"family-wise alpha        : {ALPHA}")
    print()

    print("Group summaries (mean, SD) and the difference in means")
    print("-" * 78)
    header = (
        f"{'outcome':<22}{GROUP_A + ' mean':>18}{'SD':>9}"
        f"{GROUP_B + ' mean':>18}{'SD':>9}{'diff':>10}"
    )
    print(header)
    for j, name in enumerate(OUTCOMES):
        print(
            f"{name:<22}{mean_a[j]:>18.3f}{sd_a[j]:>9.3f}"
            f"{mean_b[j]:>18.3f}{sd_b[j]:>9.3f}{mean_a[j] - mean_b[j]:>10.3f}"
        )
    print(f"(diff = {GROUP_A} mean minus {GROUP_B} mean)")
    print()

    print("Family-maximum reference distribution (5000 shuffles)")
    print("-" * 78)
    for q in (50, 90, 95, 99):
        print(f"  {q:>2}th percentile of max|t| : {np.percentile(family_max, q):.4f}")
    print(f"  maximum observed in shuffles: {family_max.max():.4f}")
    print()

    print("Declared outcomes, in protocol order")
    print("-" * 78)
    print(
        f"{'#':<3}{'outcome':<24}{'observed t':>12}{'shuffles>=':>12}"
        f"{'p (max-t)':>12}  verdict"
    )
    for j, name in enumerate(OUTCOMES):
        print(
            f"{j + 1:<3}{name:<24}{observed_t[j]:>12.4f}{exceed_counts[j]:>12d}"
            f"{p_values[j]:>12.4f}  {verdicts[j]}"
        )
    print(
        f"(shuffles>= counts, out of {N_SHUFFLES}, are the shuffles whose family "
        f"maximum reached the observed |t|;\n p is that count divided by "
        f"{N_SHUFFLES}, so the smallest non-zero p this run can resolve is "
        f"{1 / N_SHUFFLES:.4f})"
    )
    print()

    n_significant = sum(v == "significant" for v in verdicts)
    print(
        f"{n_significant} of {len(OUTCOMES)} declared outcomes reject at a "
        f"family-wise alpha of {ALPHA}."
    )


if __name__ == "__main__":
    main()
