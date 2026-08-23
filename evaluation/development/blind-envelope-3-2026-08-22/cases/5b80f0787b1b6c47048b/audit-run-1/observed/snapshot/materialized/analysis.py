"""Pre-lambing mineral drench trial: analysis of total weaned lamb weight per ewe.

One row of `ewe_weaning_weights.csv` is one ewe, recorded once at weaning. The ewe is the
unit that was assigned to a treatment group, so the row and the experimental unit are the
same thing and the two groups are independent sets of animals. The comparison below is
therefore an independent two-sample comparison carried out at the level of the rows in the
file, with no clustering or repeated measurement to account for.

Run:  python3 analysis.py
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "ewe_weaning_weights.csv")

OUTCOME = "total_weaned_lamb_weight_kg"
GROUP = "treatment"
UNIT = "ewe_id"
LEVELS = ("drenched", "undrenched")


def load_data(path):
    """Read the data file and check the structure the analysis assumes."""
    df = pd.read_csv(path)

    expected = [UNIT, GROUP, "lambs_weaned", "ewe_age_years",
                "body_condition_score", OUTCOME]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError("missing expected column(s): %s" % ", ".join(missing))

    if df[expected].isna().any().any():
        raise ValueError("data file contains missing values")

    # One row per ewe. If an identifier ever repeated, the rows would no longer be
    # independent and a plain two-sample test would not be the right analysis.
    if df[UNIT].duplicated().any():
        raise ValueError("ewe_id is repeated; rows are not one per ewe")

    # Each ewe sits in exactly one treatment group.
    per_ewe_groups = df.groupby(UNIT)[GROUP].nunique()
    if (per_ewe_groups > 1).any():
        raise ValueError("an ewe appears under more than one treatment")

    observed_levels = sorted(df[GROUP].unique())
    if observed_levels != sorted(LEVELS):
        raise ValueError("unexpected treatment levels: %s" % observed_levels)

    return df


def describe(values):
    """Sample size, mean, standard deviation and range for one group of ewes."""
    return {
        "n": int(values.size),
        "mean": float(np.mean(values)),
        "sd": float(np.std(values, ddof=1)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def main():
    df = load_data(DATA_FILE)

    print("Pre-lambing mineral drench trial")
    print("=" * 64)
    print("Data file          : %s" % os.path.basename(DATA_FILE))
    print("Rows in file       : %d" % len(df))
    print("Distinct ewes      : %d" % df[UNIT].nunique())
    print("Rows per ewe       : %d (one record per ewe, taken at weaning)"
          % df[UNIT].value_counts().max())
    print("Experimental unit  : the ewe, identified by %s" % UNIT)
    print()

    drenched = df.loc[df[GROUP] == "drenched", OUTCOME].to_numpy(dtype=float)
    undrenched = df.loc[df[GROUP] == "undrenched", OUTCOME].to_numpy(dtype=float)

    stats_by_group = {"drenched": describe(drenched),
                      "undrenched": describe(undrenched)}

    print("Total weaned lamb weight (kg) by group")
    print("-" * 64)
    print("%-12s %5s %9s %9s %9s %9s" % ("group", "ewes", "mean", "sd", "min", "max"))
    for level in LEVELS:
        s = stats_by_group[level]
        print("%-12s %5d %9.2f %9.2f %9.1f %9.1f"
              % (level, s["n"], s["mean"], s["sd"], s["min"], s["max"]))
    print()

    # Group composition, reported for background only. The pre-specified comparison
    # below is the unadjusted two-group comparison; nothing here is adjusted for.
    print("Group composition (background only, not adjusted for)")
    print("-" * 64)
    for level in LEVELS:
        sub = df[df[GROUP] == level]
        twins = int((sub["lambs_weaned"] == 2).sum())
        print("%-12s twins %2d, singles %2d, mean age %.1f y, mean BCS %.2f"
              % (level, twins, len(sub) - twins,
                 sub["ewe_age_years"].mean(), sub["body_condition_score"].mean()))
    print()

    # Independent two-sample t-test. Welch's version is used as the primary test
    # because it does not assume the two groups share a variance; the equal-variance
    # version is printed alongside it as a check.
    welch = stats.ttest_ind(drenched, undrenched, equal_var=False)
    student = stats.ttest_ind(drenched, undrenched, equal_var=True)

    diff = stats_by_group["drenched"]["mean"] - stats_by_group["undrenched"]["mean"]

    n1, n2 = drenched.size, undrenched.size
    v1, v2 = np.var(drenched, ddof=1), np.var(undrenched, ddof=1)
    se_welch = np.sqrt(v1 / n1 + v2 / n2)
    df_welch = (v1 / n1 + v2 / n2) ** 2 / (
        (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
    tcrit = stats.t.ppf(0.975, df_welch)
    ci_low, ci_high = diff - tcrit * se_welch, diff + tcrit * se_welch

    # Pooled standard deviation, for a standardised effect size.
    sd_pooled = np.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))

    print("Independent two-sample comparison (drenched minus undrenched)")
    print("-" * 64)
    print("Ewes compared          : %d drenched vs %d undrenched" % (n1, n2))
    print("Difference in means    : %+.2f kg" % diff)
    print("Standard error         : %.2f kg" % se_welch)
    print("95%% confidence interval: %.2f to %.2f kg" % (ci_low, ci_high))
    print("Welch t                : %.3f on %.1f df" % (welch.statistic, df_welch))
    print("Welch p-value          : %.4f" % welch.pvalue)
    print("Equal-variance t       : %.3f on %d df, p = %.4f"
          % (student.statistic, n1 + n2 - 2, student.pvalue))
    print("Cohen's d              : %.3f" % (diff / sd_pooled))
    print()

    # Assumption checks reported for transparency; they do not change the test used.
    print("Assumption checks")
    print("-" * 64)
    for level, values in (("drenched", drenched), ("undrenched", undrenched)):
        w_stat, w_p = stats.shapiro(values)
        print("Shapiro-Wilk, %-11s W = %.3f, p = %.3f" % (level + ":", w_stat, w_p))
    lev_stat, lev_p = stats.levene(drenched, undrenched, center="median")
    print("Levene equal variance : W = %.3f, p = %.3f" % (lev_stat, lev_p))
    mw = stats.mannwhitneyu(drenched, undrenched, alternative="two-sided")
    print("Mann-Whitney U (check): U = %.1f, p = %.4f" % (mw.statistic, mw.pvalue))
    print()

    verdict = "is" if welch.pvalue < 0.05 else "is not"
    print("At the 5%% level the difference in total weaned lamb weight %s "
          "statistically significant." % verdict)


if __name__ == "__main__":
    main()
