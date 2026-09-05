"""Analysis of the pig slurry store cover trial.

Run from the project root:

    python analysis.py

The script has two stages. Stage 1 computes one overall screening quantity from
all five declared outcome columns at once, using only basic numerical array
operations. Stage 2 runs the per-outcome two-group comparisons, but only if the
Stage 1 screen passes. If the screen does not pass, no per-outcome comparison is
run or reported.
"""

import csv
import os

import numpy as np
from scipy import stats

DATA_FILE = "slurry_store_measurements.csv"

GROUP_COLUMN = "cover_treatment"
GROUP_A = "floating_cover"
GROUP_B = "uncovered"

# The five outcomes in the order declared in the monitoring plan.
OUTCOMES = [
    ("methane_flux_g_per_m2_per_day", "mean methane flux", "g CH4 / m2 / day"),
    ("ammonia_flux_gn_per_m2_per_day", "mean ammonia flux", "g N / m2 / day"),
    (
        "nitrous_oxide_flux_mgn_per_m2_per_day",
        "mean nitrous oxide flux",
        "mg N / m2 / day",
    ),
    ("slurry_ph_ph_units", "end-of-storage slurry pH", "pH units"),
    ("slurry_dry_matter_percent", "end-of-storage dry matter", "percent by mass"),
]

# --------------------------------------------------------------------------
# Fixed decision constants. Both are set here, ahead of any computation on the
# data, and neither is adjusted after the screening quantity is known.
#
# SCREEN_THRESHOLD is the pass threshold for the Stage 1 screening quantity.
# The quantity is the Euclidean length of the vector of five between-group
# differences in standardised outcome means. With 20 stores per group, each such
# difference has a standard deviation of sqrt(1/20 + 1/20) = 0.3162 when the two
# groups do not differ, so the squared length of the five-component vector has
# an expected value of 5 * 0.1 = 0.5 in that case. The threshold 1.05 is the
# corresponding upper 5 per cent point, sqrt(0.1 * 11.07), taken from the
# chi-square distribution on five degrees of freedom as a fixed constant.
SCREEN_THRESHOLD = 1.05

# ALPHA is the conventional significance threshold for the Stage 2 per-outcome
# verdicts.
ALPHA = 0.05
# --------------------------------------------------------------------------


def load_data(path):
    """Read the CSV into a group label array and a 40 x 5 outcome matrix."""
    groups = []
    rows = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for record in reader:
            groups.append(record[GROUP_COLUMN])
            rows.append([float(record[name]) for name, _, _ in OUTCOMES])
    return np.array(groups), np.array(rows, dtype=float)


def screening_quantity(values, mask_a, mask_b):
    """Return the overall screening quantity and its five components.

    Each outcome column is standardised over all stores to zero mean and unit
    standard deviation. The mean standardised value is then taken within each
    group, and the five between-group differences are combined into a single
    number by taking the Euclidean length of that five-component vector. Only
    basic array arithmetic is used: no statistical test routine, no p-value and
    no model fitting.
    """
    column_means = values.mean(axis=0)
    column_sds = values.std(axis=0, ddof=1)
    standardised = (values - column_means) / column_sds

    mean_a = standardised[mask_a].mean(axis=0)
    mean_b = standardised[mask_b].mean(axis=0)
    differences = mean_a - mean_b

    overall = float(np.sqrt(np.sum(differences**2)))
    return overall, differences


def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
    groups, values = load_data(path)

    mask_a = groups == GROUP_A
    mask_b = groups == GROUP_B

    print("=" * 72)
    print("SLURRY STORE COVER TRIAL")
    print("=" * 72)
    print(f"Data file           : {DATA_FILE}")
    print(f"Stores              : {values.shape[0]}")
    print(f"  {GROUP_A:<18}: {int(mask_a.sum())}")
    print(f"  {GROUP_B:<18}: {int(mask_b.sum())}")
    print(f"Declared outcomes   : {len(OUTCOMES)}")
    print()

    # ---------------------------------------------------------------- Stage 1
    print("=" * 72)
    print("STAGE 1 - OVERALL SCREEN (runs always)")
    print("=" * 72)
    print(
        "Quantity: Euclidean length of the five between-group differences in\n"
        "standardised outcome means (floating_cover minus uncovered).\n"
        "Computed with basic array arithmetic only; no test, p-value or model."
    )
    print()

    overall, differences = screening_quantity(values, mask_a, mask_b)

    print("Component differences in standardised means:")
    for (name, label, _unit), difference in zip(OUTCOMES, differences):
        print(f"  {label:<26} ({name:<38}) {difference:+.4f}")
    print()

    passed = overall >= SCREEN_THRESHOLD

    print(f"Overall screening quantity : {overall:.4f}")
    print(f"Fixed pass threshold       : {SCREEN_THRESHOLD:.4f}")
    print(f"Screen outcome             : {'PASS' if passed else 'FAIL'}")
    print()

    # ---------------------------------------------------------------- Stage 2
    if not passed:
        print("=" * 72)
        print("BRANCH TAKEN: SCREEN DID NOT PASS")
        print("=" * 72)
        print(
            f"The overall screening quantity {overall:.4f} is below the fixed\n"
            f"threshold {SCREEN_THRESHOLD:.4f}. Per the analysis plan, no per-outcome\n"
            "comparison is run and none is reported. Inference stops here."
        )
        print()
        print("Per-outcome comparisons run    : 0 of 5")
        print("Per-outcome results reported   : none")
        print("=" * 72)
        return

    print("=" * 72)
    print("BRANCH TAKEN: SCREEN PASSED - STAGE 2 PER-OUTCOME COMPARISONS")
    print("=" * 72)
    print(
        "All five declared outcomes are compared between the two groups with the\n"
        "same test: a two-sample Welch t-test (two-sided, unequal variances).\n"
        f"Verdicts use the conventional threshold alpha = {ALPHA}."
    )
    print()

    header = (
        f"{'#':<3}{'outcome':<40}{'mean ' + GROUP_A:>22}"
        f"{'mean ' + GROUP_B:>18}{'diff':>10}{'t':>9}{'p':>10}  verdict"
    )
    print(header)
    print("-" * len(header))

    for index, (name, label, unit) in enumerate(OUTCOMES, start=1):
        column = values[:, index - 1]
        sample_a = column[mask_a]
        sample_b = column[mask_b]
        t_statistic, p_value = stats.ttest_ind(sample_a, sample_b, equal_var=False)
        difference = sample_a.mean() - sample_b.mean()
        verdict = "significant" if p_value < ALPHA else "not significant"
        print(
            f"{index:<3}{name:<40}{sample_a.mean():>22.4f}"
            f"{sample_b.mean():>18.4f}{difference:>10.4f}"
            f"{t_statistic:>9.3f}{p_value:>10.4f}  {verdict}"
        )

    print()
    print("Units, in outcome order:")
    for index, (_name, label, unit) in enumerate(OUTCOMES, start=1):
        print(f"  {index}. {label}: {unit}")
    print()
    print("Per-outcome comparisons run    : 5 of 5")
    print("=" * 72)


if __name__ == "__main__":
    main()
