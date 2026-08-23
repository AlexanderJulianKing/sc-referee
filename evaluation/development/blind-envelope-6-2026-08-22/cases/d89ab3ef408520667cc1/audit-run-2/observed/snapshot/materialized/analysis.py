"""Salt-in-moisture comparison of two starter cultures in a semi-hard raw-milk cheese.

Reads the titration measurement file, summarises salt-in-moisture for each starter
culture, and compares the two cultures with an independent two-sample t-test. Every
titration measurement is treated as one observation of salt-in-moisture, so the
sample size for each culture is the total number of titration measurements made on
that culture's vats.
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = "salt_in_moisture.csv"

VALUE_COLUMN = "SaltInMoisturePct"
GROUP_COLUMN = "CultureType"

TRADITIONAL = "Traditional"
COMMERCIAL = "Commercial"

ALPHA = 0.05


def load_measurements(path):
    """Read the titration measurements and check the expected columns are present."""
    frame = pd.read_csv(path, parse_dates=["MakeDate"])

    expected = [
        "VatCode",
        "CultureType",
        "MakeDate",
        "ReplicateNo",
        "SaltInMoisturePct",
    ]
    missing = [column for column in expected if column not in frame.columns]
    if missing:
        raise ValueError("missing columns in {}: {}".format(path, ", ".join(missing)))

    if frame[VALUE_COLUMN].isna().any():
        raise ValueError("missing salt-in-moisture values in {}".format(path))

    return frame


def summarise(frame):
    """Descriptive statistics of salt-in-moisture for each starter culture."""
    summary = (
        frame.groupby(GROUP_COLUMN)[VALUE_COLUMN]
        .agg(
            n_measurements="count",
            mean="mean",
            sd="std",
            minimum="min",
            maximum="max",
        )
        .reindex([TRADITIONAL, COMMERCIAL])
    )
    summary["sem"] = summary["sd"] / (summary["n_measurements"] ** 0.5)
    return summary


def compare_cultures(frame):
    """Independent two-sample t-test on the titration measurements."""
    traditional = frame.loc[frame[GROUP_COLUMN] == TRADITIONAL, VALUE_COLUMN]
    commercial = frame.loc[frame[GROUP_COLUMN] == COMMERCIAL, VALUE_COLUMN]

    result = stats.ttest_ind(commercial, traditional, equal_var=True)

    n_traditional = int(traditional.size)
    n_commercial = int(commercial.size)
    df = n_traditional + n_commercial - 2

    difference = float(commercial.mean() - traditional.mean())

    # Pooled standard deviation, for the standard error and the confidence interval.
    pooled_variance = (
        (n_traditional - 1) * traditional.var(ddof=1)
        + (n_commercial - 1) * commercial.var(ddof=1)
    ) / df
    pooled_sd = float(pooled_variance ** 0.5)
    standard_error = pooled_sd * ((1.0 / n_traditional + 1.0 / n_commercial) ** 0.5)

    critical = float(stats.t.ppf(1 - ALPHA / 2, df))
    ci_low = difference - critical * standard_error
    ci_high = difference + critical * standard_error

    cohens_d = difference / pooled_sd

    return {
        "n_traditional": n_traditional,
        "n_commercial": n_commercial,
        "mean_traditional": float(traditional.mean()),
        "mean_commercial": float(commercial.mean()),
        "difference": difference,
        "pooled_sd": pooled_sd,
        "standard_error": float(standard_error),
        "df": df,
        "t_statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "cohens_d": float(cohens_d),
    }


def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
    frame = load_measurements(path)

    print("Salt-in-moisture in a semi-hard raw-milk cheese: two starter cultures")
    print("=" * 72)
    print("Titration measurements read: {}".format(len(frame)))
    print(
        "Make dates: {} to {}".format(
            frame["MakeDate"].min().date(), frame["MakeDate"].max().date()
        )
    )
    print()

    summary = summarise(frame)
    print("Salt-in-moisture (percent) by starter culture")
    print("-" * 72)
    print(
        "{:<14}{:>6}{:>9}{:>9}{:>9}{:>9}{:>9}".format(
            "Culture", "n", "mean", "SD", "SEM", "min", "max"
        )
    )
    for culture, row in summary.iterrows():
        print(
            "{:<14}{:>6d}{:>9.3f}{:>9.3f}{:>9.3f}{:>9.2f}{:>9.2f}".format(
                culture,
                int(row["n_measurements"]),
                row["mean"],
                row["sd"],
                row["sem"],
                row["minimum"],
                row["maximum"],
            )
        )
    print()

    test = compare_cultures(frame)
    print("Independent two-sample t-test (Commercial minus Traditional)")
    print("-" * 72)
    print(
        "n per culture:            Traditional {}, Commercial {}".format(
            test["n_traditional"], test["n_commercial"]
        )
    )
    print("Mean Traditional:         {:.3f} percent".format(test["mean_traditional"]))
    print("Mean Commercial:          {:.3f} percent".format(test["mean_commercial"]))
    print(
        "Difference in means:      {:+.3f} percentage points".format(test["difference"])
    )
    print("Pooled SD:                {:.3f} percentage points".format(test["pooled_sd"]))
    print(
        "Standard error of diff:   {:.3f} percentage points".format(
            test["standard_error"]
        )
    )
    print(
        "95% CI for difference:    {:+.3f} to {:+.3f} percentage points".format(
            test["ci_low"], test["ci_high"]
        )
    )
    print("t({}) = {:.3f}".format(test["df"], test["t_statistic"]))
    print("p = {:.3e}".format(test["p_value"]))
    print("Cohen's d:                {:.3f}".format(test["cohens_d"]))
    print()

    verdict = "reject" if test["p_value"] < ALPHA else "do not reject"
    print(
        "At alpha = {:.2f} we {} the null hypothesis of equal mean "
        "salt-in-moisture.".format(ALPHA, verdict)
    )


if __name__ == "__main__":
    main()
