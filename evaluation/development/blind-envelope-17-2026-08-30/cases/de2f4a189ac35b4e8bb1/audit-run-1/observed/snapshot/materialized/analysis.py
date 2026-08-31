"""Glasshouse applicator exposure study: family screen and per-outcome analysis.

The monitoring plan declares five outcomes as one family and protects that
family with a single overall screen that must pass before any individual
outcome is examined.  The screen is a gate, not a test: it is worked out with
plain arithmetic on the measured columns, with no statistical routine and no
p-value.  Only if the screen passes are the five per-outcome comparisons run.
"""

import numpy as np
import pandas as pd
from scipy import stats

DATA_FILE = "exposure_data.csv"

GROUP_COLUMN = "application_method"
GROUP_A = "knapsack"
GROUP_B = "trolley"

# The declared outcome family, in the fixed order of the monitoring plan.
OUTCOMES = [
    "urinary_dap_ug_per_g_creatinine",
    "cholinesterase_pct_baseline",
    "dermal_deposition_ug_per_hand",
    "inhalation_pad_ug",
    "symptom_score_0_20",
]

# Cut-off fixed in the monitoring plan before the data were seen.
SCREEN_CUTOFF = 0.30

ALPHA = 0.05


def main():
    data = pd.read_csv(DATA_FILE)

    group_a = data[data[GROUP_COLUMN] == GROUP_A]
    group_b = data[data[GROUP_COLUMN] == GROUP_B]

    n_a = len(group_a)
    n_b = len(group_b)

    print("Glasshouse applicator exposure study")
    print("=" * 72)
    print("Workers: {} total, {} {}, {} {}".format(
        len(data), n_a, GROUP_A, n_b, GROUP_B))
    print("Declared outcome family ({} outcomes): {}".format(
        len(OUTCOMES), ", ".join(OUTCOMES)))
    print()

    # ------------------------------------------------------------------
    # FAMILY SCREEN
    # Elementary array arithmetic only: group means, within-group standard
    # deviations, differences, absolute values and an average.  No
    # statistical routine, no p-value.
    # ------------------------------------------------------------------
    print("FAMILY SCREEN")
    print("-" * 72)

    absolute_standardised_differences = []

    for outcome in OUTCOMES:
        values_a = group_a[outcome].to_numpy(dtype=float)
        values_b = group_b[outcome].to_numpy(dtype=float)

        mean_a = values_a.mean()
        mean_b = values_b.mean()

        sd_a = values_a.std(ddof=1)
        sd_b = values_b.std(ddof=1)

        pooled_sd = np.sqrt(
            ((n_a - 1) * sd_a ** 2 + (n_b - 1) * sd_b ** 2) / (n_a + n_b - 2)
        )

        standardised_difference = (mean_a - mean_b) / pooled_sd
        absolute_standardised_differences.append(np.abs(standardised_difference))

        print("  {:<34s} mean {} = {:8.3f}   mean {} = {:8.3f}   "
              "pooled SD = {:8.3f}   |std diff| = {:.4f}".format(
                  outcome, GROUP_A, mean_a, GROUP_B, mean_b,
                  pooled_sd, np.abs(standardised_difference)))

    screening_quantity = np.mean(np.array(absolute_standardised_differences))

    print()
    print("  Screening quantity (mean absolute standardised difference "
          "across the 5 outcomes): {:.4f}".format(screening_quantity))
    print("  Pre-fixed cut-off: {:.2f}".format(SCREEN_CUTOFF))
    print()

    # ------------------------------------------------------------------
    # GATE
    # ------------------------------------------------------------------
    if screening_quantity >= SCREEN_CUTOFF:
        print("SCREEN PASSED: {:.4f} >= {:.2f}. The outcome family is opened.".format(
            screening_quantity, SCREEN_CUTOFF))
        print()
        print("PER-OUTCOME COMPARISONS (declared order)")
        print("-" * 72)

        for index, outcome in enumerate(OUTCOMES, start=1):
            values_a = group_a[outcome].to_numpy(dtype=float)
            values_b = group_b[outcome].to_numpy(dtype=float)

            mean_a = values_a.mean()
            mean_b = values_b.mean()

            t_statistic, p_value = stats.ttest_ind(values_a, values_b)

            verdict = ("significant at 0.05" if p_value < ALPHA
                       else "not significant at 0.05")

            print("  {}. {}".format(index, outcome))
            print("     mean {} = {:.3f}   mean {} = {:.3f}   "
                  "difference = {:.3f}".format(
                      GROUP_A, mean_a, GROUP_B, mean_b, mean_a - mean_b))
            print("     two-sample t-test: t = {:.4f}   p = {:.6g}   "
                  "verdict: {}".format(t_statistic, p_value, verdict))
            print()
    else:
        print("SCREEN FAILED: {:.4f} < {:.2f}. The outcome family stays closed.".format(
            screening_quantity, SCREEN_CUTOFF))
        print()
        print("No per-outcome comparison was run and none is reported.")


if __name__ == "__main__":
    main()
