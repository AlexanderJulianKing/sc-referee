"""Storage atmosphere comparison for seed potato firmness.

Reads storage_firmness.csv, compares tuber firmness (newtons) between the two
storage atmospheres with an independent two-sample t-test, and prints the
results.
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage_firmness.csv")

CONVENTIONAL = "conventional_air"
LOW_OXYGEN = "low_oxygen_ca"


def load_data(path):
    """Read the bin-visit table."""
    return pd.read_csv(path)


def describe_group(values):
    """Mean, standard deviation and record count for one group's firmness."""
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def main():
    data = load_data(DATA_FILE)

    conventional = data.loc[data["atmosphere"] == CONVENTIONAL, "firmness_newton"]
    low_oxygen = data.loc[data["atmosphere"] == LOW_OXYGEN, "firmness_newton"]

    conv = describe_group(conventional)
    lowo = describe_group(low_oxygen)
    total_n = conv["n"] + lowo["n"]

    # Independent two-sample t-test on the difference in mean firmness.
    # Every firmness record in the table enters the comparison as its own
    # observation.
    t_stat, p_value = stats.ttest_ind(low_oxygen, conventional)
    difference = lowo["mean"] - conv["mean"]

    print("Seed potato storage atmosphere comparison")
    print("=" * 44)
    print("Outcome: tuber firmness (newtons)")
    print("Firmness records analysed: {}".format(total_n))
    print("")

    print("Group summaries")
    print("-" * 44)
    header = "{:<20} {:>4} {:>8} {:>8} {:>14}"
    row = "{:<20} {:>4} {:>8.2f} {:>8.2f} {:>14}"
    print(header.format("atmosphere", "n", "mean", "sd", "range"))
    print(
        row.format(
            CONVENTIONAL,
            conv["n"],
            conv["mean"],
            conv["sd"],
            "{:.1f}-{:.1f}".format(conv["min"], conv["max"]),
        )
    )
    print(
        row.format(
            LOW_OXYGEN,
            lowo["n"],
            lowo["mean"],
            lowo["sd"],
            "{:.1f}-{:.1f}".format(lowo["min"], lowo["max"]),
        )
    )
    print("")

    print("Independent two-sample t-test")
    print("-" * 44)
    print("Difference in means (low_oxygen_ca - conventional_air): {:.2f} N".format(difference))
    print("t = {:.3f}".format(t_stat))
    print("degrees of freedom = {}".format(total_n - 2))
    print("p = {:.4e}".format(p_value))
    print("")

    if p_value < 0.05:
        higher = LOW_OXYGEN if difference > 0 else CONVENTIONAL
        print(
            "Conclusion: the two atmospheres differ significantly in mean tuber "
            "firmness (p < 0.05); firmness is higher under {}.".format(higher)
        )
    else:
        print(
            "Conclusion: no significant difference in mean tuber firmness "
            "between the two atmospheres (p >= 0.05)."
        )


if __name__ == "__main__":
    main()
