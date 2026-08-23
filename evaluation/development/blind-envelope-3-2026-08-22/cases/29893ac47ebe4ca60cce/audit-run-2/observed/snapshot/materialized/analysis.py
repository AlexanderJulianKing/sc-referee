"""Shading and algal chlorophyll-a in intertidal rock pools.

Reads the field data, summarises chlorophyll-a for the shaded and uncovered
groups, and tests the treatment effect with an independent two-sample
t-test. Every measurement row in the table enters the test as one
observation.

Run:  /usr/local/bin/python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "rockpool_chlorophyll.csv")

RESPONSE = "chlorophyll_ug_cm2"
GROUP = "treatment"


def load_data(path):
    """Read the comma-separated field data file."""
    df = pd.read_csv(path)
    return df


def describe_group(values):
    """Mean, standard deviation, standard error, range and count."""
    n = int(values.count())
    return {
        "n": n,
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "se": float(values.std(ddof=1) / (n ** 0.5)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def main():
    df = load_data(DATA_FILE)

    n_total = int(len(df))
    shaded = df.loc[df[GROUP] == "shaded", RESPONSE]
    uncovered = df.loc[df[GROUP] == "uncovered", RESPONSE]

    s_stats = describe_group(shaded)
    u_stats = describe_group(uncovered)

    # Independent two-sample t-test. Each measurement row is one observation.
    t_stat, p_value = stats.ttest_ind(shaded, uncovered, equal_var=True)
    df_resid = s_stats["n"] + u_stats["n"] - 2
    difference = s_stats["mean"] - u_stats["mean"]

    # Pooled standard deviation and Cohen's d for the effect size.
    pooled_var = (((s_stats["n"] - 1) * s_stats["sd"] ** 2 +
                   (u_stats["n"] - 1) * u_stats["sd"] ** 2) / df_resid)
    pooled_sd = pooled_var ** 0.5
    cohens_d = difference / pooled_sd

    # 95% confidence interval on the difference in means.
    se_diff = pooled_sd * ((1.0 / s_stats["n"] + 1.0 / u_stats["n"]) ** 0.5)
    t_crit = stats.t.ppf(0.975, df_resid)
    ci_low = difference - t_crit * se_diff
    ci_high = difference + t_crit * se_diff

    print("=" * 66)
    print("Shading and algal chlorophyll-a in intertidal rock pools")
    print("=" * 66)
    print("Data file          : %s" % os.path.basename(DATA_FILE))
    print("Sample size (n)    : %d measurement rows analysed" % n_total)
    print("Columns            : %s" % ", ".join(df.columns))
    print("Missing values     : %d" % int(df.isna().sum().sum()))
    print("Rock pools sampled : %d" % int(df["pool_id"].nunique()))
    print("Pool surface area  : %.2f to %.2f m2"
          % (df["surface_area_m2"].min(), df["surface_area_m2"].max()))
    print()

    print("-" * 66)
    print("Group summaries (chlorophyll-a, ug/cm2)")
    print("-" * 66)
    print("%-12s %5s %8s %8s %8s %8s %8s"
          % ("group", "n", "mean", "sd", "se", "min", "max"))
    for label, st in (("shaded", s_stats), ("uncovered", u_stats)):
        print("%-12s %5d %8.2f %8.2f %8.2f %8.2f %8.2f"
              % (label, st["n"], st["mean"], st["sd"], st["se"],
                 st["min"], st["max"]))
    print()

    print("-" * 66)
    print("Independent two-sample t-test (shaded vs uncovered)")
    print("-" * 66)
    print("Observations entered : %d (one per measurement row)" % n_total)
    print("Difference in means  : %.2f ug/cm2 (shaded minus uncovered)"
          % difference)
    print("95%% CI on difference : %.2f to %.2f ug/cm2" % (ci_low, ci_high))
    print("Pooled SD            : %.2f ug/cm2" % pooled_sd)
    print("Cohen's d            : %.2f" % cohens_d)
    print("t                    : %.3f" % t_stat)
    print("degrees of freedom   : %d" % df_resid)
    print("p-value              : %.3e" % p_value)
    print()

    if p_value < 0.05:
        direction = "lower" if difference < 0 else "higher"
        print("Chlorophyll-a was significantly %s in shaded pools "
              "(p < 0.05)." % direction)
    else:
        print("No significant difference between shaded and uncovered pools "
              "(p >= 0.05).")
    print("=" * 66)


if __name__ == "__main__":
    main()
