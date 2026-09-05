"""Rearing-temperature experiment on Daphnia magna.

Compares the 18 C and 24 C rearing groups on the four declared life-history
outcomes.  The four outcomes form one declared family, so all four p-values are
adjusted together in a single call to the multiple-comparison routine before any
verdict is read.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = "daphnia_temperature.csv"
GROUP_COLUMN = "temperature_c"
GROUP_LOW = 18
GROUP_HIGH = 24
ALPHA = 0.05

# The declared outcome family, in the order fixed in the experimental plan.
OUTCOMES = [
    "age_first_brood_days",
    "body_length_day14_mm",
    "offspring_day21",
    "heart_rate_day10_bpm",
]


def main():
    data = pd.read_csv(DATA_FILE)

    low = data[data[GROUP_COLUMN] == GROUP_LOW]
    high = data[data[GROUP_COLUMN] == GROUP_HIGH]

    print("Daphnia magna rearing-temperature experiment")
    print("Animals: {} total, {} at {} C, {} at {} C".format(
        len(data), len(low), GROUP_LOW, len(high), GROUP_HIGH))
    print("Declared outcome family ({} outcomes): {}".format(
        len(OUTCOMES), ", ".join(OUTCOMES)))
    print()

    # One two-group comparison per declared outcome, p-values kept together in
    # the declared order.
    means_low = []
    means_high = []
    p_raw = []
    for outcome in OUTCOMES:
        values_low = low[outcome]
        values_high = high[outcome]
        result = stats.ttest_ind(values_low, values_high)
        means_low.append(values_low.mean())
        means_high.append(values_high.mean())
        p_raw.append(result.pvalue)

    # One call covering the complete family.  No method is specified; whatever
    # adjustment the routine applies by default is what the verdicts come from.
    reject, p_adjusted, _, _ = multipletests(p_raw, alpha=ALPHA)

    print("Family-wise adjustment applied to all {} p-values in one call, "
          "alpha = {}".format(len(p_raw), ALPHA))
    print()

    for i, outcome in enumerate(OUTCOMES):
        verdict = "significant" if reject[i] else "not significant"
        print("Outcome {}: {}".format(i + 1, outcome))
        print("  mean at {} C:      {:.4f}".format(GROUP_LOW, means_low[i]))
        print("  mean at {} C:      {:.4f}".format(GROUP_HIGH, means_high[i]))
        print("  unadjusted p (reference only): {:.6g}".format(p_raw[i]))
        print("  adjusted p:                    {:.6g}".format(p_adjusted[i]))
        print("  verdict (from adjusted p):     {}".format(verdict))
        print()


if __name__ == "__main__":
    main()
