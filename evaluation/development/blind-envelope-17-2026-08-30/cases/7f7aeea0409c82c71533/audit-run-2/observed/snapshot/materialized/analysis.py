"""Damselfly condition analysis: fish-free ponds versus fish-stocked ponds.

Reads `damselfly_condition.csv` and compares the two pond types on the five
outcomes declared in the field protocol, in the declared order. The five
outcomes are treated as ONE complete family: every p-value is adjusted together
in a single call, and every verdict is read from the adjusted p-value only.

Declared dependencies (third-party):
    pandas
    scipy
    pingouin        # specialist statistics package used for the family-wise
                    # multiple-comparison correction (pingouin.multicomp)

`pingouin` is deliberately used for the correction instead of the two
mainstream general-purpose libraries (scipy / statsmodels).
"""

import pandas as pd
from scipy import stats
from pingouin import multicomp

CSV_FILE = "damselfly_condition.csv"

GROUP_COLUMN = "pond_type"
GROUP_A = "fish_free"   # ponds holding no fish
GROUP_B = "fish"        # ponds stocked with fish

# The declared outcome family, in the order fixed by the field protocol.
DECLARED_OUTCOMES = [
    "body_length_mm",
    "hindwing_length_mm",
    "abdominal_fat_mg",
    "mite_count",
    "encapsulation_grey",
]

ALPHA = 0.05
CORRECTION_METHOD = "holm"  # Holm-Bonferroni: strong family-wise error control


def main():
    data = pd.read_csv(CSV_FILE)

    fish_free = data[data[GROUP_COLUMN] == GROUP_A]
    fish = data[data[GROUP_COLUMN] == GROUP_B]

    print("Damselfly condition: fish-free ponds vs fish-stocked ponds")
    print("Rows read: %d  (%s n=%d, %s n=%d)"
          % (len(data), GROUP_A, len(fish_free), GROUP_B, len(fish)))
    print("Declared outcome family (%d outcomes, one family):" % len(DECLARED_OUTCOMES))
    for name in DECLARED_OUTCOMES:
        print("  - %s" % name)
    print()

    # Two-group comparison on each declared outcome; p-values kept together in
    # the declared order.
    mean_a = []
    mean_b = []
    raw_pvals = []
    for outcome in DECLARED_OUTCOMES:
        a = fish_free[outcome]
        b = fish[outcome]
        result = stats.ttest_ind(a, b)
        mean_a.append(a.mean())
        mean_b.append(b.mean())
        raw_pvals.append(result.pvalue)

    # One adjustment over the COMPLETE family of five p-values, using the
    # specialist package pingouin.
    reject, adj_pvals = multicomp(raw_pvals, alpha=ALPHA, method=CORRECTION_METHOD)

    print("Multiple-comparison correction: pingouin.multicomp, method='%s', "
          "alpha=%.2f, applied to all %d p-values together."
          % (CORRECTION_METHOD, ALPHA, len(raw_pvals)))
    print("Verdicts are taken from the adjusted p-values only.")
    print()

    header = "%-20s %12s %12s %12s %12s %-16s" % (
        "outcome", "mean_fish_free", "mean_fish", "p_unadj", "p_adjusted", "verdict")
    print(header)
    print("-" * len(header))

    for i, outcome in enumerate(DECLARED_OUTCOMES):
        verdict = "significant" if bool(reject[i]) else "not significant"
        print("%-20s %12.3f %12.3f %12.4f %12.4f %-16s" % (
            outcome, mean_a[i], mean_b[i], raw_pvals[i], adj_pvals[i], verdict))

    print()
    print("Detail (adjusted p-values, declared order):")
    for i, outcome in enumerate(DECLARED_OUTCOMES):
        verdict = "significant" if bool(reject[i]) else "not significant"
        print("  %d. %s" % (i + 1, outcome))
        print("     mean %s = %.3f, mean %s = %.3f"
              % (GROUP_A, mean_a[i], GROUP_B, mean_b[i]))
        print("     unadjusted p = %.4f (reference only)" % raw_pvals[i])
        print("     adjusted p   = %.4f -> %s at alpha = %.2f"
              % (adj_pvals[i], verdict, ALPHA))


if __name__ == "__main__":
    main()
