"""Bone-density supplement study: analysis script.

Study design
------------
Thirty post-menopausal women each completed one of two twelve-month supplement
regimes (combined vitamin D + calcium, or vitamin D alone). Each woman had ONE
lumbar spine scan, read at four vertebral levels (L1-L4). The independent
experimental unit is therefore the WOMAN, not the vertebral level: the four
readings from one spine are four looks at the same woman, not four independent
observations.

Consequences for this script
----------------------------
* The regime comparison is run on ``patient_summary.csv`` only, so each woman
  enters it exactly once. n = 30 women, 15 per regime.
* ``vertebral_level_readings.csv`` is used only for descriptive counts (how many
  readings were taken, how many levels each woman had) and for checking that the
  two files agree numerically. No group comparison is run on it.

Run with:  python3 analysis.py
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
LEVEL_FILE = os.path.join(HERE, "vertebral_level_readings.csv")
SUMMARY_FILE = os.path.join(HERE, "patient_summary.csv")

REGIMES = ["vitamin_d_calcium", "vitamin_d_only"]
ALPHA = 0.05


def rule(title=""):
    print("\n" + "=" * 72)
    if title:
        print(title)
        print("=" * 72)


def load_data():
    levels = pd.read_csv(LEVEL_FILE)
    summary = pd.read_csv(SUMMARY_FILE)
    return levels, summary


def describe_level_file(levels):
    """Descriptive counts only. No group comparison is performed here."""
    rule("1. Vertebral-level file: descriptive counts only")
    print("File: vertebral_level_readings.csv")
    print("Columns: " + ", ".join(levels.columns))
    print("One row = one vertebral level of one woman's scan.")
    print("Total vertebral-level readings: %d" % len(levels))
    print("Distinct women (patient_ref): %d" % levels["patient_ref"].nunique())
    print("Distinct vertebral levels: %s"
          % ", ".join(sorted(levels["vertebral_level"].unique())))

    per_woman = levels.groupby("patient_ref").size()
    print("Readings per woman: min %d, max %d (every woman has %s)"
          % (per_woman.min(), per_woman.max(),
             "the same number" if per_woman.nunique() == 1 else "differing numbers"))

    print("\nReadings per regime (readings, not women):")
    for regime in REGIMES:
        block = levels[levels["supplement_regime"] == regime]
        print("  %-18s %3d readings from %2d women"
              % (regime, len(block), block["patient_ref"].nunique()))

    print("\nReadings per vertebral level (pooled across both regimes,"
          " descriptive only):")
    for level in sorted(levels["vertebral_level"].unique()):
        block = levels[levels["vertebral_level"] == level]
        print("  %-3s n=%3d  mean %.4f  SD %.4f g/cm^2"
              % (level, len(block), block["bmd_g_per_cm2"].mean(),
                 block["bmd_g_per_cm2"].std(ddof=1)))

    print("\nOverall reading range: %.3f to %.3f g/cm^2"
          % (levels["bmd_g_per_cm2"].min(), levels["bmd_g_per_cm2"].max()))
    print("Missing values in level file: %d" % int(levels.isna().sum().sum()))


def check_files_agree(levels, summary):
    """Confirm the summary file is the faithful per-woman collapse of the level file."""
    rule("2. Consistency check between the two files")
    recomputed = (levels.groupby(["patient_ref", "supplement_regime"])["bmd_g_per_cm2"]
                        .agg(["mean", "size"])
                        .reset_index()
                        .rename(columns={"mean": "recomputed_mean",
                                         "size": "recomputed_n"}))
    merged = summary.merge(recomputed, on=["patient_ref", "supplement_regime"],
                           how="outer", indicator=True)

    unmatched = int((merged["_merge"] != "both").sum())
    max_mean_diff = float((merged["mean_bmd_g_per_cm2"]
                           - merged["recomputed_mean"]).abs().max())
    n_mismatch = int((merged["n_levels"] != merged["recomputed_n"]).sum())

    print("Women in summary file: %d" % len(summary))
    print("Women present in one file but not the other: %d" % unmatched)
    # The stored means are given to 4 dp, so a faithful collapse can differ from
    # the freshly recomputed mean by at most half a unit in the last place,
    # i.e. 0.00005 g/cm^2. Anything larger would mean the files disagree.
    tol = 5e-5 + 1e-9
    print("Largest gap between the stored per-woman mean and the mean recomputed")
    print("  from the level file: %.6f g/cm^2 (rounding to 4 dp allows up to %.5f)"
          % (max_mean_diff, 5e-5))
    print("Women whose n_levels disagrees with the level-file row count: %d" % n_mismatch)
    print("Duplicate patient_ref values in summary file: %d"
          % int(summary["patient_ref"].duplicated().sum()))
    print("Missing values in summary file: %d" % int(summary.isna().sum().sum()))
    print("Files agree numerically: %s"
          % ("yes" if (unmatched == 0 and n_mismatch == 0
                       and max_mean_diff <= tol) else "NO - investigate"))


def group_comparison(summary):
    """The one and only inferential comparison, run at the level of the woman."""
    rule("3. Regime comparison - per-woman summary file only (n = 30 women)")
    print("File: patient_summary.csv")
    print("Columns: " + ", ".join(summary.columns))
    print("One row = one woman. Each woman enters this comparison exactly once.")

    counts = summary["supplement_regime"].value_counts()
    print("\nSample size: %d women (%s)"
          % (len(summary),
             ", ".join("%d %s" % (counts[r], r) for r in REGIMES)))

    a = summary.loc[summary["supplement_regime"] == REGIMES[0],
                    "mean_bmd_g_per_cm2"].to_numpy()
    b = summary.loc[summary["supplement_regime"] == REGIMES[1],
                    "mean_bmd_g_per_cm2"].to_numpy()

    print("\nPer-woman mean aBMD by regime (g/cm^2):")
    print("  %-18s %-8s %-8s %-8s %-8s %-8s"
          % ("regime", "n", "mean", "SD", "min", "max"))
    for name, arr in zip(REGIMES, (a, b)):
        print("  %-18s %-8d %-8.4f %-8.4f %-8.4f %-8.4f"
              % (name, len(arr), arr.mean(), arr.std(ddof=1), arr.min(), arr.max()))

    # Welch two-sample t-test: does not assume equal variances.
    t_stat, p_val = stats.ttest_ind(a, b, equal_var=False)

    n1, n2 = len(a), len(b)
    v1, v2 = a.var(ddof=1), b.var(ddof=1)
    se = np.sqrt(v1 / n1 + v2 / n2)
    df = (v1 / n1 + v2 / n2) ** 2 / ((v1 / n1) ** 2 / (n1 - 1)
                                     + (v2 / n2) ** 2 / (n2 - 1))
    diff = a.mean() - b.mean()
    t_crit = stats.t.ppf(1 - ALPHA / 2, df)
    ci_low, ci_high = diff - t_crit * se, diff + t_crit * se

    # Hedges' g (bias-corrected standardised difference).
    sp = np.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    cohens_d = diff / sp
    hedges_g = cohens_d * (1 - 3 / (4 * (n1 + n2) - 9))

    print("\nPrimary test: Welch two-sample t-test on the per-woman means")
    print("  difference (%s minus %s): %+.4f g/cm^2" % (REGIMES[0], REGIMES[1], diff))
    print("  95%% CI for the difference: %+.4f to %+.4f g/cm^2" % (ci_low, ci_high))
    print("  t = %.3f, df = %.2f, p = %.4f" % (t_stat, df, p_val))
    print("  Hedges' g = %.3f" % hedges_g)

    print("\nAssumption checks and sensitivity (same n = 30 women)")
    for name, arr in zip(REGIMES, (a, b)):
        w_stat, w_p = stats.shapiro(arr)
        print("  Shapiro-Wilk normality, %-18s W = %.3f, p = %.4f"
              % (name, w_stat, w_p))
    lev_stat, lev_p = stats.levene(a, b, center="median")
    print("  Levene equal-variance test: W = %.3f, p = %.4f" % (lev_stat, lev_p))
    u_stat, u_p = stats.mannwhitneyu(a, b, alternative="two-sided")
    print("  Mann-Whitney U (rank-based sensitivity check): U = %.1f, p = %.4f"
          % (u_stat, u_p))

    return {"diff": diff, "ci_low": ci_low, "ci_high": ci_high, "t": t_stat,
            "df": df, "p": p_val, "g": hedges_g, "u_p": u_p,
            "mean_a": a.mean(), "sd_a": a.std(ddof=1),
            "mean_b": b.mean(), "sd_b": b.std(ddof=1),
            "n_a": n1, "n_b": n2}


def main():
    levels, summary = load_data()
    describe_level_file(levels)
    check_files_agree(levels, summary)
    res = group_comparison(summary)

    rule("4. Conclusion in one line")
    verdict = "is" if res["p"] < ALPHA else "is not"
    print("Comparing %d women (%d vs %d), the combined vitamin D + calcium regime"
          % (res["n_a"] + res["n_b"], res["n_a"], res["n_b"]))
    print("averaged %+.4f g/cm^2 (95%% CI %+.4f to %+.4f, p = %.4f), which %s"
          % (res["diff"], res["ci_low"], res["ci_high"], res["p"], verdict))
    print("statistically significant at the %.0f%% level." % (100 * ALPHA))
    print("\nNote: the 120 vertebral-level readings were used for counts and file")
    print("checks only. They are 4 looks at each of 30 spines, not 120 independent")
    print("observations, so no group test was run on them.")


if __name__ == "__main__":
    main()
