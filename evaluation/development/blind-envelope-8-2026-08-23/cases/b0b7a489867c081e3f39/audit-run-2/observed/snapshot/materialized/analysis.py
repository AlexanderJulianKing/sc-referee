"""Seagrass exclusion-zone survey: compare maximum leaf length between zones.

Reads seagrass_survey.csv and compares leaf_length_cm between the protected
zone (inside the boat-mooring exclusion zone) and the open zone (adjacent water
open to mooring) with an independent two-sample t-test applied to every row of
the table. Each sampled dive point is one observation entering the comparison.

Run:  python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "seagrass_survey.csv")

RESPONSE = "leaf_length_cm"
GROUP = "zone"
PROTECTED = "protected"
OPEN = "open"


def load_data(path=DATA_PATH):
    """Load the survey table and check the columns the analysis needs."""
    frame = pd.read_csv(path)

    expected = [
        "meadow_id",
        "zone",
        "point_number",
        "leaf_length_cm",
        "depth_m",
        "sediment_type",
    ]
    missing = [name for name in expected if name not in frame.columns]
    if missing:
        raise ValueError("missing column(s) in %s: %s" % (path, ", ".join(missing)))

    levels = set(frame[GROUP].unique())
    if levels != {PROTECTED, OPEN}:
        raise ValueError("zone must hold exactly 'protected' and 'open'; got %s" % sorted(levels))

    if frame[RESPONSE].isna().any() or frame[GROUP].isna().any():
        raise ValueError("missing values in the analysis columns")

    return frame


def describe_group(values):
    """Row count, mean and standard deviation for one zone."""
    return {
        "n": int(values.size),
        "mean_cm": float(values.mean()),
        "sd_cm": float(values.std(ddof=1)),
        "min_cm": float(values.min()),
        "max_cm": float(values.max()),
    }


def compare_zones(frame):
    """Independent two-sample t-test on every row of the table."""
    protected = frame.loc[frame[GROUP] == PROTECTED, RESPONSE]
    open_zone = frame.loc[frame[GROUP] == OPEN, RESPONSE]

    # Student's independent two-sample t-test, equal variances assumed.
    statistic, p_value = stats.ttest_ind(protected, open_zone, equal_var=True)

    protected_stats = describe_group(protected)
    open_stats = describe_group(open_zone)

    n_protected = protected_stats["n"]
    n_open = open_stats["n"]
    df = n_protected + n_open - 2

    # Pooled standard deviation and Cohen's d for the effect size.
    pooled_var = (
        (n_protected - 1) * protected_stats["sd_cm"] ** 2
        + (n_open - 1) * open_stats["sd_cm"] ** 2
    ) / df
    pooled_sd = pooled_var ** 0.5
    difference = protected_stats["mean_cm"] - open_stats["mean_cm"]
    cohens_d = difference / pooled_sd

    # 95 percent confidence interval for the difference in means.
    standard_error = pooled_sd * (1.0 / n_protected + 1.0 / n_open) ** 0.5
    t_critical = stats.t.ppf(0.975, df)
    ci_low = difference - t_critical * standard_error
    ci_high = difference + t_critical * standard_error

    return {
        "n_total": int(frame.shape[0]),
        "protected": protected_stats,
        "open": open_stats,
        "difference_cm": float(difference),
        "t_statistic": float(statistic),
        "df": int(df),
        "p_value": float(p_value),
        "pooled_sd_cm": float(pooled_sd),
        "cohens_d": float(cohens_d),
        "ci95_low_cm": float(ci_low),
        "ci95_high_cm": float(ci_high),
    }


def format_p(p_value):
    if p_value < 1e-4:
        return "%.3e" % p_value
    return "%.6f" % p_value


def main():
    frame = load_data()
    result = compare_zones(frame)

    print("Seagrass maximum leaf length: protected zone vs open zone")
    print("=" * 62)
    print("Rows entering the comparison (n): %d" % result["n_total"])
    print("")
    print("%-12s %5s %10s %10s %10s %10s" % ("zone", "n", "mean_cm", "sd_cm", "min_cm", "max_cm"))
    for label, key in ((PROTECTED, "protected"), (OPEN, "open")):
        group = result[key]
        print(
            "%-12s %5d %10.2f %10.2f %10.2f %10.2f"
            % (label, group["n"], group["mean_cm"], group["sd_cm"], group["min_cm"], group["max_cm"])
        )
    print("")
    print("Difference (protected - open): %.2f cm" % result["difference_cm"])
    print(
        "95%% CI for the difference: %.2f to %.2f cm"
        % (result["ci95_low_cm"], result["ci95_high_cm"])
    )
    print("Independent two-sample t-test (equal variances):")
    print("  t(%d) = %.4f" % (result["df"], result["t_statistic"]))
    print("  p = %s" % format_p(result["p_value"]))
    print("  Cohen's d = %.3f (pooled sd = %.2f cm)" % (result["cohens_d"], result["pooled_sd_cm"]))
    print("")
    verdict = "significant" if result["p_value"] < 0.05 else "not significant"
    print("At alpha = 0.05 the zone difference is %s." % verdict)

    return result


if __name__ == "__main__":
    main()
