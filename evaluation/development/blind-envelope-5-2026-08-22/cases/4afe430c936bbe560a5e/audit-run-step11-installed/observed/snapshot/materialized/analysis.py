"""Analysis for the drought-tolerant maize extension trial.

Reads maize_trial.csv, compares grain yield between the improved variety and the
local landrace with an independent two-sample test, and prints the results.

Design note. Each farm was allocated one seed type for its whole maize field and
was harvested and weighed once, so one row is one farm and one farm is one
independent unit. The rows and the independent units are therefore the same
thing, and every row is used directly in the test with no aggregation step. The
script checks that assumption against the file before testing.
"""

import math
import sys

import pandas as pd
from scipy import stats

DATA_FILE = "maize_trial.csv"
OUTCOME = "grain_yield_t_ha"
GROUP = "seed_type"
UNIT = "farm_id"
ALPHA = 0.05


def load_data(path):
    """Read the trial table and check the one-row-per-farm design."""
    df = pd.read_csv(path)

    expected = [UNIT, GROUP, "field_area_ha", "season_rainfall_mm", OUTCOME]
    if list(df.columns) != expected:
        sys.exit("Unexpected columns: %r" % (list(df.columns),))

    n_rows = len(df)
    n_farms = df[UNIT].nunique()
    if n_rows != n_farms:
        sys.exit(
            "Design check failed: %d rows but %d distinct farms. Each farm must "
            "appear exactly once for the rows to be the independent units."
            % (n_rows, n_farms)
        )

    # Each farm must sit in exactly one seed group.
    groups_per_farm = df.groupby(UNIT)[GROUP].nunique()
    if (groups_per_farm != 1).any():
        sys.exit("Design check failed: at least one farm has more than one seed type.")

    if df[OUTCOME].isna().any():
        sys.exit("Design check failed: missing yield values.")

    levels = sorted(df[GROUP].unique())
    if len(levels) != 2:
        sys.exit("Expected exactly two seed types, found: %r" % (levels,))

    return df, n_rows, n_farms, levels


def describe(values):
    """Mean, sample standard deviation, standard error, min and max."""
    n = len(values)
    mean = values.mean()
    sd = values.std(ddof=1)
    return {
        "n": n,
        "mean": mean,
        "sd": sd,
        "se": sd / math.sqrt(n),
        "min": values.min(),
        "max": values.max(),
    }


def main():
    df, n_rows, n_farms, levels = load_data(DATA_FILE)

    improved = df.loc[df[GROUP] == "improved", OUTCOME]
    landrace = df.loc[df[GROUP] == "landrace", OUTCOME]

    s_imp = describe(improved)
    s_lan = describe(landrace)

    # Welch's two-sample t-test: independent samples, no assumption that the two
    # groups share the same variance.
    t_stat, p_value = stats.ttest_ind(improved, landrace, equal_var=False)

    diff = s_imp["mean"] - s_lan["mean"]
    se_diff = math.sqrt(s_imp["se"] ** 2 + s_lan["se"] ** 2)
    # Welch-Satterthwaite degrees of freedom.
    dfree = (s_imp["se"] ** 2 + s_lan["se"] ** 2) ** 2 / (
        s_imp["se"] ** 4 / (s_imp["n"] - 1) + s_lan["se"] ** 4 / (s_lan["n"] - 1)
    )
    t_crit = stats.t.ppf(1 - ALPHA / 2, dfree)
    ci_low = diff - t_crit * se_diff
    ci_high = diff + t_crit * se_diff

    # Pooled standard deviation for a standardised effect size (Hedges-free
    # Cohen's d), reported as context for the size of the difference.
    sd_pooled = math.sqrt(
        ((s_imp["n"] - 1) * s_imp["sd"] ** 2 + (s_lan["n"] - 1) * s_lan["sd"] ** 2)
        / (s_imp["n"] + s_lan["n"] - 2)
    )
    cohens_d = diff / sd_pooled

    print("=" * 68)
    print("Improved drought-tolerant maize vs local landrace: grain yield")
    print("=" * 68)
    print()
    print("Data and units")
    print("-" * 68)
    print("Data file                  : %s" % DATA_FILE)
    print("Rows in file               : %d" % n_rows)
    print("Distinct farms             : %d" % n_farms)
    print("Rows per farm              : %.1f" % (n_rows / n_farms))
    print("Independent units (farms)  : %d" % n_farms)
    print("Seed types                 : %s" % ", ".join(levels))
    print("Outcome                    : %s (tonnes per hectare)" % OUTCOME)
    print()
    print("Every farm appears exactly once, so each row is one independent unit")
    print("and all %d rows enter the test directly." % n_rows)
    print()

    print("Group summaries")
    print("-" * 68)
    print(
        "%-10s %6s %8s %8s %8s %8s %8s"
        % ("group", "farms", "mean", "sd", "se", "min", "max")
    )
    for name, s in (("improved", s_imp), ("landrace", s_lan)):
        print(
            "%-10s %6d %8.3f %8.3f %8.3f %8.2f %8.2f"
            % (name, s["n"], s["mean"], s["sd"], s["se"], s["min"], s["max"])
        )
    print()

    print("Independent two-sample test (Welch's t-test)")
    print("-" * 68)
    print("Difference in means (improved - landrace) : %+.3f t/ha" % diff)
    print("Standard error of the difference          : %.3f t/ha" % se_diff)
    print("95%% confidence interval for difference    : %.3f to %.3f t/ha"
          % (ci_low, ci_high))
    print("t statistic                               : %.3f" % t_stat)
    print("Degrees of freedom (Welch)                : %.2f" % dfree)
    print("p-value (two-sided)                       : %.3e" % p_value)
    print("Cohen's d (pooled sd %.3f)                : %.2f" % (sd_pooled, cohens_d))
    print()

    print("Conclusion")
    print("-" * 68)
    if p_value < ALPHA:
        print(
            "At the %.0f%% level the difference is statistically significant "
            "(p = %.3e)." % (ALPHA * 100, p_value)
        )
        higher = "improved" if diff > 0 else "landrace"
        print(
            "Mean yield is higher on the %s farms by %.2f t/ha "
            "(95%% CI %.2f to %.2f)." % (higher, abs(diff), ci_low, ci_high)
        )
        print(
            "That is a %.1f%% increase over the landrace mean of %.2f t/ha."
            % (100 * diff / s_lan["mean"], s_lan["mean"])
        )
    else:
        print(
            "At the %.0f%% level the difference is not statistically significant "
            "(p = %.3f)." % (ALPHA * 100, p_value)
        )
        print(
            "The 95%% confidence interval (%.2f to %.2f t/ha) includes zero."
            % (ci_low, ci_high)
        )
    print()
    print(
        "This is a comparison between two groups of separate farms in one\n"
        "district and one season, so it speaks to that district and season."
    )
    print("=" * 68)


if __name__ == "__main__":
    main()
