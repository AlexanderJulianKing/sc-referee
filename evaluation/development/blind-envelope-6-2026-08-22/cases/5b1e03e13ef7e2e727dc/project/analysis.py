"""Bifidobacterium relative abundance in breastfed and formula-fed infants.

Reads the sequenced stool samples, summarises Bifidobacterium relative abundance in
each feeding group, and compares the two groups with a two-sample t-test with
unequal variances (Welch). Every stool sample row enters the comparison, and the
sample size reported for each group is the total number of stool samples collected
in that group.

Run:  python3 analysis.py
"""

import math
import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "bifidobacterium_samples.csv")

GROUPS = ("breastfed", "formula")
OUTCOME = "bifidobacterium_pct"
ALPHA = 0.05


def load_samples(path):
    """Load the stool sample table and check the columns the analysis needs."""
    data = pd.read_csv(path)
    required = ["infant_id", "feeding_group", "age_weeks", "sample_id", OUTCOME]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError("missing columns in %s: %s" % (path, ", ".join(missing)))
    observed = set(data["feeding_group"].unique())
    if observed != set(GROUPS):
        raise ValueError("expected feeding groups %s, found %s"
                         % (sorted(GROUPS), sorted(observed)))
    return data


def summarise_group(values):
    """Descriptive statistics for the stool samples of one feeding group."""
    return {
        "n_samples": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "sem": float(values.std(ddof=1) / math.sqrt(values.size)),
        "median": float(values.median()),
        "q1": float(values.quantile(0.25)),
        "q3": float(values.quantile(0.75)),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
    }


def summarise_by_age(data):
    """Mean relative abundance at each scheduled visit, by feeding group."""
    table = data.pivot_table(index="age_weeks", columns="feeding_group",
                             values=OUTCOME, aggfunc="mean")
    return table.reindex(columns=list(GROUPS))


def compare_groups(first, second):
    """Two-sample t-test with unequal variances, plus effect size and interval."""
    result = stats.ttest_ind(first, second, equal_var=False)

    n1, n2 = first.size, second.size
    v1, v2 = first.var(ddof=1), second.var(ddof=1)
    standard_error = math.sqrt(v1 / n1 + v2 / n2)
    welch_df = (v1 / n1 + v2 / n2) ** 2 / (
        (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    )
    difference = float(first.mean() - second.mean())
    critical = stats.t.ppf(1 - ALPHA / 2, welch_df)
    pooled_sd = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))

    return {
        "n1": int(n1),
        "n2": int(n2),
        "difference": difference,
        "standard_error": float(standard_error),
        "t": float(result.statistic),
        "df": float(welch_df),
        "p": float(result.pvalue),
        "ci_low": difference - critical * standard_error,
        "ci_high": difference + critical * standard_error,
        "cohens_d": difference / pooled_sd,
    }


def format_p(value):
    return "< 0.001" if value < 0.001 else "%.4f" % value


def main():
    data = load_samples(DATA_FILE)

    print("Bifidobacterium relative abundance by feeding regimen")
    print("=" * 62)
    print("Stool samples read: %d" % len(data))
    print("Infants enrolled:   %d" % data["infant_id"].nunique())
    print("Visit ages (weeks): %s"
          % ", ".join(str(age) for age in sorted(data["age_weeks"].unique())))
    print()

    summaries = {}
    print("Group summaries (%s, percent of sequencing reads)" % OUTCOME)
    print("-" * 62)
    header = ("%-11s %8s %8s %8s %8s %8s %8s"
              % ("group", "n", "mean", "SD", "median", "min", "max"))
    print(header)
    for group in GROUPS:
        values = data.loc[data["feeding_group"] == group, OUTCOME]
        summary = summarise_group(values)
        summaries[group] = summary
        print("%-11s %8d %8.2f %8.2f %8.2f %8.2f %8.2f"
              % (group, summary["n_samples"], summary["mean"], summary["sd"],
                 summary["median"], summary["minimum"], summary["maximum"]))
    print()
    for group in GROUPS:
        summary = summaries[group]
        print("%s: IQR %.2f to %.2f, SEM %.2f, samples from %d infants"
              % (group, summary["q1"], summary["q3"], summary["sem"],
                 data.loc[data["feeding_group"] == group, "infant_id"].nunique()))
    print()

    print("Mean abundance by visit age (percent)")
    print("-" * 62)
    by_age = summarise_by_age(data)
    print("%-12s %12s %12s %12s" % ("age_weeks", "breastfed", "formula", "difference"))
    for age, row in by_age.iterrows():
        print("%-12d %12.2f %12.2f %12.2f"
              % (age, row["breastfed"], row["formula"],
                 row["breastfed"] - row["formula"]))
    print()

    breastfed = data.loc[data["feeding_group"] == "breastfed", OUTCOME]
    formula = data.loc[data["feeding_group"] == "formula", OUTCOME]
    test = compare_groups(breastfed, formula)

    print("Two-sample t-test with unequal variances (Welch)")
    print("-" * 62)
    print("Stool samples compared: breastfed n = %d, formula n = %d"
          % (test["n1"], test["n2"]))
    print("Mean difference (breastfed - formula): %.2f percentage points"
          % test["difference"])
    print("95%% CI: %.2f to %.2f" % (test["ci_low"], test["ci_high"]))
    print("Standard error: %.3f" % test["standard_error"])
    print("t = %.3f, df = %.2f, p = %s"
          % (test["t"], test["df"], format_p(test["p"])))
    print("Cohen's d: %.2f" % test["cohens_d"])
    print()

    verdict = "is" if test["p"] < ALPHA else "is not"
    print("At the %.2f level the difference between feeding regimens %s "
          "statistically significant." % (ALPHA, verdict))


if __name__ == "__main__":
    main()
