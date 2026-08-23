"""Nitrogen top-dressing schedule trial: split vs late.

The independent experimental unit is the paddy (see PROTOCOL.md). The nitrogen
schedule was applied to a whole paddy, and the six hills cut inside a paddy are
spatial subsamples of that one unit, not independent replicates.

So the inferential comparison is run on `paddy_harvest_summary.csv`, one row per
paddy, 18 observations total. `hill_harvest_raw.csv` is used only to describe the
data: how many hills were harvested, whether every paddy contributed six hills,
how the two files line up, and how much hill yields spread out. No inferential
test is run on the hill-level rows.
"""

import pandas as pd
from scipy import stats

RAW_FILE = "hill_harvest_raw.csv"
SUMMARY_FILE = "paddy_harvest_summary.csv"
SCHEDULES = ("split", "late")


def describe_raw(raw):
    """Descriptive-only checks on the hill-level field record."""
    print("=" * 70)
    print("PART 1  Hill-level field record (descriptive only)")
    print("=" * 70)
    print(f"File: {RAW_FILE}")
    print(f"Data rows (harvested hills): {len(raw)}")
    print(f"Distinct paddies: {raw['paddy_code'].nunique()}")

    hills_per_paddy = raw.groupby("paddy_code").size()
    print(
        "Hills per paddy: min "
        f"{hills_per_paddy.min()}, max {hills_per_paddy.max()}"
    )
    all_six = bool((hills_per_paddy == 6).all())
    print(f"Every paddy contributed exactly 6 hills: {all_six}")
    if not all_six:
        off = hills_per_paddy[hills_per_paddy != 6]
        print("  Paddies not at 6 hills:")
        for code, n in off.items():
            print(f"    {code}: {n}")

    # One schedule label per paddy.
    labels_per_paddy = raw.groupby("paddy_code")["nitrogen_schedule"].nunique()
    print(
        "Schedule label constant within every paddy: "
        f"{bool((labels_per_paddy == 1).all())}"
    )

    y = raw["hill_grain_yield_g"]
    print("\nSpread of hill grain yield (g), all 108 hills:")
    print(f"  mean   {y.mean():.2f}")
    print(f"  SD     {y.std(ddof=1):.2f}")
    print(f"  min    {y.min():.1f}")
    print(f"  Q1     {y.quantile(0.25):.2f}")
    print(f"  median {y.median():.2f}")
    print(f"  Q3     {y.quantile(0.75):.2f}")
    print(f"  max    {y.max():.1f}")

    print("\nSpread of hill grain yield (g) by schedule (descriptive only):")
    for sched in SCHEDULES:
        s = raw.loc[raw["nitrogen_schedule"] == sched, "hill_grain_yield_g"]
        print(
            f"  {sched:>5}: n={len(s)}  mean={s.mean():.2f}  "
            f"SD={s.std(ddof=1):.2f}  range {s.min():.1f}-{s.max():.1f}"
        )

    within = raw.groupby("paddy_code")["hill_grain_yield_g"].std(ddof=1)
    print(
        "\nWithin-paddy SD of hill yield (g): mean "
        f"{within.mean():.2f}, min {within.min():.2f}, max {within.max():.2f}"
    )
    return {
        "n_hills": len(raw),
        "n_paddies": int(raw["paddy_code"].nunique()),
        "all_six": all_six,
        "hills_min": int(hills_per_paddy.min()),
        "hills_max": int(hills_per_paddy.max()),
        "hill_mean": y.mean(),
        "hill_sd": y.std(ddof=1),
        "hill_min": y.min(),
        "hill_max": y.max(),
        "hill_q1": y.quantile(0.25),
        "hill_median": y.median(),
        "hill_q3": y.quantile(0.75),
        "within_sd_mean": within.mean(),
    }


def check_alignment(raw, summary):
    """Confirm the summary file really is the per-paddy mean of the raw file."""
    print("\n" + "=" * 70)
    print("PART 2  Agreement between the two files")
    print("=" * 70)

    recomputed = raw.groupby("paddy_code")["hill_grain_yield_g"].mean()
    merged = summary.set_index("paddy_code").join(
        recomputed.rename("recomputed_mean_g"), how="outer"
    )
    same_codes = bool(merged["mean_hill_yield_g"].notna().all()
                      and merged["recomputed_mean_g"].notna().all())
    print(f"Same 18 paddy codes in both files: {same_codes}")

    # Compare the stored value against the exact (unrounded) mean of the six
    # hills. A stored value rounded to one decimal place may sit up to 0.05 g
    # away from the exact mean, so 0.05 is the whole tolerance a correct
    # rounding can use, whichever way ties are broken.
    diff = (merged["mean_hill_yield_g"] - merged["recomputed_mean_g"]).abs()
    means_agree = bool((diff <= 0.05 + 1e-9).all())
    print(
        "Summary mean is the mean of that paddy's 6 hills rounded to 1 dp, "
        f"for all paddies: {means_agree} (largest gap {diff.max():.3f} g)"
    )
    if not means_agree:
        for code, g in diff[diff > 0.05 + 1e-9].items():
            print(
                f"    {code}: summary {merged.loc[code, 'mean_hill_yield_g']:.1f} g "
                f"vs exact mean {merged.loc[code, 'recomputed_mean_g']:.4f} g "
                f"(gap {g:.3f} g)"
            )

    # Exact .x5 ties, where half-up and half-to-even rounding disagree.
    ties = merged.index[
        ((merged["recomputed_mean_g"] * 100).round() % 10 == 5)
        & (((merged["recomputed_mean_g"] * 1000).round() % 10) == 0)
    ].tolist()
    if ties:
        print(
            "  Note: exact half-way mean(s) where the rounding rule matters: "
            + ", ".join(
                f"{c} (exact {merged.loc[c, 'recomputed_mean_g']:.2f} g, "
                f"stored {merged.loc[c, 'mean_hill_yield_g']:.1f} g)"
                for c in ties
            )
        )

    raw_labels = raw.groupby("paddy_code")["nitrogen_schedule"].first()
    labels = merged.join(raw_labels.rename("raw_schedule"))
    labels_agree = bool(
        (labels["nitrogen_schedule"] == labels["raw_schedule"]).all()
    )
    print(f"Schedule label agrees between files for every paddy: {labels_agree}")

    counts = raw.groupby("paddy_code").size().rename("raw_hill_count")
    hc = merged.join(counts)
    counts_agree = bool((hc["hills_sampled"] == hc["raw_hill_count"]).all())
    print(f"hills_sampled matches the raw row count for every paddy: {counts_agree}")
    return {
        "same_codes": same_codes,
        "means_agree": means_agree,
        "max_gap": diff.max(),
        "labels_agree": labels_agree,
        "counts_agree": counts_agree,
    }


def compare_schedules(summary):
    """The one inferential test, run on the per-paddy summary file."""
    print("\n" + "=" * 70)
    print("PART 3  Inferential comparison (paddy-level summary file)")
    print("=" * 70)
    print(f"File: {SUMMARY_FILE}")
    print(f"Rows used (paddies): {len(summary)}")

    groups = {}
    for sched in SCHEDULES:
        groups[sched] = summary.loc[
            summary["nitrogen_schedule"] == sched, "mean_hill_yield_g"
        ]

    for sched in SCHEDULES:
        g = groups[sched]
        print(
            f"  {sched:>5}: n={len(g)} paddies  mean={g.mean():.3f} g  "
            f"SD={g.std(ddof=1):.3f} g  range {g.min():.1f}-{g.max():.1f} g"
        )

    n_split, n_late = len(groups["split"]), len(groups["late"])
    print(f"  Total paddies analysed: {n_split + n_late}")

    diff = groups["late"].mean() - groups["split"].mean()
    print(f"\nDifference (late - split): {diff:.3f} g per hill")

    # Welch's two-sample t-test. Chosen because the two groups are independent
    # sets of paddies and Welch does not assume the group variances are equal;
    # it is the safe default here and stays valid if the variances happen to
    # match. The SDs above are visibly unequal, so pooling would be wrong.
    t_stat, p_val = stats.ttest_ind(
        groups["late"], groups["split"], equal_var=False
    )
    df = welch_df(groups["late"], groups["split"])
    print("\nWelch two-sample t-test (independent, two-sided):")
    print(f"  t = {t_stat:.4f}")
    print(f"  df = {df:.3f}")
    print(f"  p = {p_val:.6f}")

    # 95% CI for the difference in means, on the same Welch footing.
    se = (
        groups["late"].var(ddof=1) / n_late
        + groups["split"].var(ddof=1) / n_split
    ) ** 0.5
    crit = stats.t.ppf(0.975, df)
    lo, hi = diff - crit * se, diff + crit * se
    print(f"  95% CI for the difference: [{lo:.3f}, {hi:.3f}] g")

    return {
        "n_split": n_split,
        "n_late": n_late,
        "n_total": n_split + n_late,
        "mean_split": groups["split"].mean(),
        "mean_late": groups["late"].mean(),
        "sd_split": groups["split"].std(ddof=1),
        "sd_late": groups["late"].std(ddof=1),
        "min_split": groups["split"].min(),
        "max_split": groups["split"].max(),
        "min_late": groups["late"].min(),
        "max_late": groups["late"].max(),
        "diff": diff,
        "t": t_stat,
        "df": df,
        "p": p_val,
        "ci_lo": lo,
        "ci_hi": hi,
    }


def welch_df(a, b):
    """Welch-Satterthwaite degrees of freedom."""
    va, vb = a.var(ddof=1), b.var(ddof=1)
    na, nb = len(a), len(b)
    num = (va / na + vb / nb) ** 2
    den = (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    return num / den


def main():
    raw = pd.read_csv(RAW_FILE)
    summary = pd.read_csv(SUMMARY_FILE)

    describe_raw(raw)
    check_alignment(raw, summary)
    res = compare_schedules(summary)

    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    winner = "late" if res["diff"] > 0 else "split"
    verdict = "is" if res["p"] < 0.05 else "is not"
    print(
        f"Mean per-paddy hill yield was {res['diff']:.3f} g higher under the "
        f"{winner} schedule.\nAt the 5% level this difference {verdict} "
        f"statistically significant (p = {res['p']:.4f})."
    )


if __name__ == "__main__":
    main()
