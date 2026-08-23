"""Butterfly abundance on farmland under two management regimes.

Reads the two data files, runs the two-group comparison on the per-route
summary file, and prints the results.

Design note
-----------
The independent experimental unit is the route, not the route-week. Each route
was walked 18 times by the same recorder, so the 396 weekly rows are repeated
measures of only 22 independent units. The inferential test is therefore run on
the 22 rows of route_summary.csv, and the sample size is the number of routes.
The weekly file is used for description only; no test is run on the weekly rows.
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
WEEKLY_PATH = os.path.join(HERE, "weekly_counts.csv")
SUMMARY_PATH = os.path.join(HERE, "route_summary.csv")

GROUPS = ("wildflower_margin", "conventional")


def load_data():
    weekly = pd.read_csv(WEEKLY_PATH)
    summary = pd.read_csv(SUMMARY_PATH)
    return weekly, summary


def describe_weekly(weekly):
    """Descriptive counts from the weekly file. No inference here."""
    print("=" * 70)
    print("1. DESCRIPTION OF THE WEEKLY FILE (weekly_counts.csv)")
    print("=" * 70)
    print(f"Weekly rows (route-weeks):      {len(weekly)}")
    print(f"Distinct routes:                {weekly['route_code'].nunique()}")
    print(f"Distinct survey weeks:          {weekly['survey_week'].nunique()}"
          f" (week {int(weekly['survey_week'].min())}"
          f" to week {int(weekly['survey_week'].max())})")

    walks_per_route = weekly.groupby("route_code").size()
    print(f"Walks per route:                min {int(walks_per_route.min())},"
          f" max {int(walks_per_route.max())}")
    print(f"Missing values anywhere:        {int(weekly.isna().sum().sum())}")

    print("\nRoutes per management regime (from the weekly file):")
    for grp in GROUPS:
        n_routes = weekly.loc[weekly["management"] == grp, "route_code"].nunique()
        n_rows = int((weekly["management"] == grp).sum())
        print(f"  {grp:<20s} {n_routes} routes, {n_rows} weekly rows")

    print("\nWeekly butterfly counts (descriptive, route-weeks are not independent):")
    for grp in GROUPS:
        counts = weekly.loc[weekly["management"] == grp, "butterfly_count"]
        print(f"  {grp:<20s} range {int(counts.min())} to {int(counts.max())},"
              f" median {counts.median():.1f}, mean {counts.mean():.2f}")
    allc = weekly["butterfly_count"]
    print(f"  {'all routes':<20s} range {int(allc.min())} to {int(allc.max())},"
          f" median {allc.median():.1f}, mean {allc.mean():.2f}")

    print("\nAir temperature at the start of the walk (degrees C):")
    temp = weekly["air_temp_c"]
    print(f"  range {temp.min():.1f} to {temp.max():.1f}, mean {temp.mean():.2f}")

    peak_week = (weekly.groupby("survey_week")["butterfly_count"]
                 .mean().idxmax())
    print(f"\nSurvey week with the highest mean count across all routes: week {int(peak_week)}")
    print()


def check_files_agree(weekly, summary):
    """Confirm the per-route file matches what the weekly file implies."""
    print("=" * 70)
    print("2. AGREEMENT BETWEEN THE TWO FILES")
    print("=" * 70)

    recomputed = (weekly.groupby(["route_code", "management"])["butterfly_count"]
                  .agg(weeks_surveyed="size", mean_weekly_count="mean")
                  .reset_index())
    recomputed["mean_weekly_count"] = recomputed["mean_weekly_count"].round(2)

    merged = summary.merge(recomputed, on=["route_code", "management"],
                           how="outer", suffixes=("_file", "_recomputed"),
                           indicator=True)

    unmatched = int((merged["_merge"] != "both").sum())
    weeks_ok = bool((merged["weeks_surveyed_file"]
                     == merged["weeks_surveyed_recomputed"]).all())
    max_mean_diff = float((merged["mean_weekly_count_file"]
                           - merged["mean_weekly_count_recomputed"]).abs().max())

    print(f"Routes in the per-route file:   {len(summary)}")
    print(f"Route codes unmatched across the two files: {unmatched}")
    print(f"weeks_surveyed agrees for every route:      {weeks_ok}")
    print(f"Largest gap in mean_weekly_count:           {max_mean_diff:.4f}")
    print()


def two_group_test(summary):
    """Independent two-sample comparison on the 22 per-route rows."""
    print("=" * 70)
    print("3. TWO-GROUP COMPARISON (per-route file, 22 routes)")
    print("=" * 70)

    groups = {g: summary.loc[summary["management"] == g,
                             "mean_weekly_count"].to_numpy()
              for g in GROUPS}

    print("Per-route mean weekly count, by management regime:")
    for grp in GROUPS:
        vals = groups[grp]
        print(f"  {grp:<20s} n = {len(vals):2d} routes,"
              f" mean {vals.mean():.2f},"
              f" SD {vals.std(ddof=1):.2f},"
              f" median {np.median(vals):.2f},"
              f" range {vals.min():.2f} to {vals.max():.2f}")

    wf, conv = groups["wildflower_margin"], groups["conventional"]
    n1, n2 = len(wf), len(conv)
    total_n = n1 + n2
    diff = wf.mean() - conv.mean()

    print(f"\nSample size for the test: {total_n} routes"
          f" ({n1} wildflower-margin, {n2} conventional)")
    print(f"Difference in group means (wildflower_margin - conventional):"
          f" {diff:.2f} butterflies per walk")
    print(f"Ratio of group means: {wf.mean() / conv.mean():.2f}x")

    # Assumption checks, reported rather than used to switch tests silently.
    lev_stat, lev_p = stats.levene(wf, conv, center="mean")
    sw_wf = stats.shapiro(wf)
    sw_conv = stats.shapiro(conv)
    print("\nAssumption checks:")
    print(f"  Levene equal-variance test:   W = {lev_stat:.3f}, p = {lev_p:.4f}")
    print(f"  Shapiro-Wilk, wildflower:     W = {sw_wf.statistic:.3f},"
          f" p = {sw_wf.pvalue:.4f}")
    print(f"  Shapiro-Wilk, conventional:   W = {sw_conv.statistic:.3f},"
          f" p = {sw_conv.pvalue:.4f}")

    # Primary test: Welch's independent two-sample t-test. Welch is used as the
    # default because it does not assume the two groups share a variance, and it
    # is chosen ahead of the data rather than on the basis of the Levene result.
    welch = stats.ttest_ind(wf, conv, equal_var=False)
    se = np.sqrt(wf.var(ddof=1) / n1 + conv.var(ddof=1) / n2)
    dfw = se**4 / ((wf.var(ddof=1) / n1) ** 2 / (n1 - 1)
                   + (conv.var(ddof=1) / n2) ** 2 / (n2 - 1))
    tcrit = stats.t.ppf(0.975, dfw)
    ci_low, ci_high = diff - tcrit * se, diff + tcrit * se

    print("\nPRIMARY TEST -- Welch's independent two-sample t-test")
    print("  (unit of analysis: the route; one value per route)")
    print(f"  t = {welch.statistic:.3f}, df = {dfw:.2f}, p = {welch.pvalue:.3e}")
    print(f"  95% CI for the difference in means:"
          f" {ci_low:.2f} to {ci_high:.2f} butterflies per walk")

    # Effect size (Hedges' g, small-sample corrected Cohen's d).
    sp = np.sqrt(((n1 - 1) * wf.var(ddof=1) + (n2 - 1) * conv.var(ddof=1))
                 / (total_n - 2))
    d = diff / sp
    g = d * (1 - 3 / (4 * (total_n - 2) - 1))
    print(f"  Cohen's d = {d:.2f}; Hedges' g = {g:.2f}")

    # Supporting tests, reported for completeness. The conclusion does not
    # depend on which of the three is read.
    student = stats.ttest_ind(wf, conv, equal_var=True)
    mwu = stats.mannwhitneyu(wf, conv, alternative="two-sided")
    print("\nSUPPORTING TESTS (reported for completeness, not selected on the data)")
    print(f"  Student's t-test (equal variance): t = {student.statistic:.3f},"
          f" df = {total_n - 2}, p = {student.pvalue:.3e}")
    print(f"  Mann-Whitney U (rank based):       U = {mwu.statistic:.1f},"
          f" p = {mwu.pvalue:.3e}")
    print()

    return {
        "n_wf": n1, "n_conv": n2, "total_n": total_n,
        "mean_wf": wf.mean(), "mean_conv": conv.mean(),
        "sd_wf": wf.std(ddof=1), "sd_conv": conv.std(ddof=1),
        "diff": diff, "welch_t": welch.statistic, "welch_df": dfw,
        "welch_p": welch.pvalue, "ci_low": ci_low, "ci_high": ci_high,
        "hedges_g": g,
    }


def main():
    weekly, summary = load_data()
    describe_weekly(weekly)
    check_files_agree(weekly, summary)
    res = two_group_test(summary)

    print("=" * 70)
    print("4. HEADLINE RESULT")
    print("=" * 70)
    print(f"Wildflower-margin routes averaged {res['mean_wf']:.2f} butterflies per walk"
          f" and conventional routes {res['mean_conv']:.2f},")
    print(f"a difference of {res['diff']:.2f} (95% CI {res['ci_low']:.2f} to"
          f" {res['ci_high']:.2f}); Welch t({res['welch_df']:.2f}) ="
          f" {res['welch_t']:.3f}, p = {res['welch_p']:.3e},")
    print(f"Hedges' g = {res['hedges_g']:.2f}, n = {res['total_n']} routes.")
    print("This is an observational comparison of existing farms, not a randomised trial.")


if __name__ == "__main__":
    main()
