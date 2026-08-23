"""Wing centroid size of adult female Drosophila melanogaster on two larval diets.

Reads wing_size.csv and compares wing_centroid_size_mm between the standard-diet
flies and the high-sugar-diet flies with a single independent two-sample t-test
(Welch), taking each measured fly in the table as one observation.

Run with: /usr/local/bin/python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wing_size.csv")

OUTCOME = "wing_centroid_size_mm"
GROUP = "diet"
REFERENCE = "standard"
TREATMENT = "high_sugar"


def load_data(path=DATA_FILE):
    """Read the measured-fly table."""
    return pd.read_csv(path)


def describe_group(values):
    """Sample size, mean and standard deviation for one group of measured flies."""
    return {
        "n_flies": int(values.count()),
        "mean_mm": float(values.mean()),
        "sd_mm": float(values.std(ddof=1)),
    }


def welch_degrees_of_freedom(a, b):
    """Welch-Satterthwaite degrees of freedom for two independent samples."""
    va, vb = a.var(ddof=1) / a.count(), b.var(ddof=1) / b.count()
    return float((va + vb) ** 2 / (va ** 2 / (a.count() - 1) + vb ** 2 / (b.count() - 1)))


def main():
    data = load_data()

    standard = data.loc[data[GROUP] == REFERENCE, OUTCOME]
    high_sugar = data.loc[data[GROUP] == TREATMENT, OUTCOME]

    standard_stats = describe_group(standard)
    high_sugar_stats = describe_group(high_sugar)

    difference_mm = high_sugar_stats["mean_mm"] - standard_stats["mean_mm"]

    t_statistic, p_value = stats.ttest_ind(high_sugar, standard, equal_var=False)
    welch_df = welch_degrees_of_freedom(high_sugar, standard)

    total_flies = standard_stats["n_flies"] + high_sugar_stats["n_flies"]

    print("Wing centroid size by larval diet")
    print("=" * 52)
    print("Data file: {}".format(os.path.basename(DATA_FILE)))
    print("Outcome:   {} (mm), one value per measured fly".format(OUTCOME))
    print("Test:      independent two-sample t-test (Welch), measured flies")
    print("")
    print("{:<12} {:>10} {:>12} {:>12}".format("group", "n_flies", "mean_mm", "sd_mm"))
    print("-" * 52)
    print(
        "{:<12} {:>10d} {:>12.3f} {:>12.3f}".format(
            REFERENCE,
            standard_stats["n_flies"],
            standard_stats["mean_mm"],
            standard_stats["sd_mm"],
        )
    )
    print(
        "{:<12} {:>10d} {:>12.3f} {:>12.3f}".format(
            TREATMENT,
            high_sugar_stats["n_flies"],
            high_sugar_stats["mean_mm"],
            high_sugar_stats["sd_mm"],
        )
    )
    print("-" * 52)
    print("Total measured flies:        {:d}".format(total_flies))
    print(
        "Difference in means (mm):    {:+.3f}  ({} minus {})".format(
            difference_mm, TREATMENT, REFERENCE
        )
    )
    print("t statistic:                 {:.3f}".format(float(t_statistic)))
    print("Degrees of freedom (Welch):  {:.2f}".format(welch_df))
    print("p-value:                     {:.3e}".format(float(p_value)))


if __name__ == "__main__":
    main()
