"""Nitrate in drinking-water wells: agricultural vs forested catchments.

Two files are read:

  nitrate_monitoring_log.csv  raw log, one row per well-month (132 rows).
  well_nitrate_summary.csv    per-well summary, one row per well (22 rows).

The raw log is used for DESCRIPTIVE purposes only. The six monthly samples at a
well are repeated measurements of the same physical monitoring point, so they
are not independent observations; treating them as 132 independent data points
would be pseudoreplication and would understate the standard error.

The inferential two-group comparison is therefore run entirely on
well_nitrate_summary.csv, which carries exactly one value per well. The sample
size for the test is the number of WELLS per catchment type (11 and 11).
"""

from pathlib import Path

import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
RAW_PATH = HERE / "nitrate_monitoring_log.csv"
SUMMARY_PATH = HERE / "well_nitrate_summary.csv"

ALPHA = 0.05


def load_data():
    raw = pd.read_csv(RAW_PATH)
    summary = pd.read_csv(SUMMARY_PATH)
    return raw, summary


def describe_raw(raw):
    """Descriptive statistics from the raw monitoring log. No inference here."""
    lines = []
    lines.append("=" * 70)
    lines.append("1. DESCRIPTIVE SUMMARY OF THE RAW MONITORING LOG")
    lines.append("   (source: nitrate_monitoring_log.csv -- descriptive use only)")
    lines.append("=" * 70)

    n_rows = len(raw)
    n_wells = raw["well_id"].nunique()
    lines.append(f"Rows (well-month samples): {n_rows}")
    lines.append(f"Distinct wells (well_id):  {n_wells}")

    per_well = raw.groupby("well_id").size()
    lines.append(
        "Samples per well: min={0}, max={1}, all equal={2}".format(
            per_well.min(), per_well.max(), bool(per_well.nunique() == 1)
        )
    )

    months = sorted(raw["sample_month"].unique())
    lines.append(
        "Monitoring period: {0} to {1} ({2} monthly rounds)".format(
            months[0], months[-1], len(months)
        )
    )

    wells_by_group = raw.groupby("catchment_type")["well_id"].nunique()
    rows_by_group = raw.groupby("catchment_type").size()
    lines.append("")
    lines.append("Wells and rows by catchment type:")
    for group in sorted(wells_by_group.index):
        lines.append(
            "  {0:<13} wells={1:>3}  raw rows={2:>4}".format(
                group, wells_by_group[group], rows_by_group[group]
            )
        )

    lines.append("")
    lines.append("Sample-level nitrate_mg_per_l (descriptive only, n = samples):")
    desc = raw.groupby("catchment_type")["nitrate_mg_per_l"].agg(
        ["count", "mean", "std", "min", "max"]
    )
    for group in sorted(desc.index):
        row = desc.loc[group]
        lines.append(
            "  {0:<13} n={1:>4}  mean={2:6.3f}  sd={3:5.3f}  min={4:5.2f}  max={5:5.2f}".format(
                group,
                int(row["count"]),
                row["mean"],
                row["std"],
                row["min"],
                row["max"],
            )
        )

    lines.append("")
    lines.append("Other measured covariates (all samples pooled):")
    for col in ("water_temp_c", "well_depth_m"):
        lines.append(
            "  {0:<13} mean={1:6.2f}  min={2:5.1f}  max={3:5.1f}".format(
                col, raw[col].mean(), raw[col].min(), raw[col].max()
            )
        )

    lines.append("")
    lines.append("Missing values per column in the raw log:")
    for col, n_missing in raw.isna().sum().items():
        lines.append(f"  {col:<20} {int(n_missing)}")

    return "\n".join(lines), {
        "n_rows": n_rows,
        "n_wells": n_wells,
        "samples_per_well_min": int(per_well.min()),
        "samples_per_well_max": int(per_well.max()),
        "first_month": months[0],
        "last_month": months[-1],
        "n_months": len(months),
    }


def check_consistency(raw, summary):
    """Confirm the summary file is a faithful collapse of the raw log."""
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("2. CONSISTENCY CHECK BETWEEN THE TWO FILES")
    lines.append("=" * 70)

    recomputed = (
        raw.groupby("well_id")
        .agg(
            recomputed_mean=("nitrate_mg_per_l", "mean"),
            recomputed_n=("nitrate_mg_per_l", "size"),
            recomputed_catchment=("catchment_type", lambda s: s.iloc[0]),
        )
        .reset_index()
    )
    merged = summary.merge(recomputed, on="well_id", how="outer", indicator=True)

    same_wells = bool((merged["_merge"] == "both").all())
    mean_ok = bool(
        (merged["mean_nitrate_mg_per_l"] - merged["recomputed_mean"]).abs().max() <= 5e-4
    )
    n_ok = bool((merged["n_samples"] == merged["recomputed_n"]).all())
    group_ok = bool((merged["catchment_type"] == merged["recomputed_catchment"]).all())
    unique_ok = bool(summary["well_id"].is_unique)
    max_dev = float((merged["mean_nitrate_mg_per_l"] - merged["recomputed_mean"]).abs().max())

    lines.append(f"Same set of well_id in both files:              {same_wells}")
    lines.append(f"well_id unique in the summary file:             {unique_ok}")
    lines.append(f"catchment_type agrees for every well:           {group_ok}")
    lines.append(f"n_samples equals raw row count for every well:  {n_ok}")
    lines.append(
        "mean_nitrate_mg_per_l equals recomputed well mean: {0} (max abs deviation {1:.2e})".format(
            mean_ok, max_dev
        )
    )

    return "\n".join(lines), {
        "same_wells": same_wells,
        "unique_ok": unique_ok,
        "group_ok": group_ok,
        "n_ok": n_ok,
        "mean_ok": mean_ok,
        "max_dev": max_dev,
    }


def compare_groups(summary):
    """Independent two-sample comparison, one value per well."""
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("3. INFERENTIAL COMPARISON OF CATCHMENT TYPES")
    lines.append("   (source: well_nitrate_summary.csv -- one row per well)")
    lines.append("=" * 70)

    agri = summary.loc[
        summary["catchment_type"] == "agricultural", "mean_nitrate_mg_per_l"
    ].to_numpy()
    fore = summary.loc[
        summary["catchment_type"] == "forested", "mean_nitrate_mg_per_l"
    ].to_numpy()

    n_a, n_f = len(agri), len(fore)
    m_a, m_f = agri.mean(), fore.mean()
    s_a, s_f = agri.std(ddof=1), fore.std(ddof=1)

    lines.append("Unit of analysis: the well. Sample size = number of wells per group.")
    lines.append(
        "  agricultural: n_wells={0}  mean={1:.3f} mg/L  sd={2:.3f}  min={3:.3f}  max={4:.3f}".format(
            n_a, m_a, s_a, agri.min(), agri.max()
        )
    )
    lines.append(
        "  forested:     n_wells={0}  mean={1:.3f} mg/L  sd={2:.3f}  min={3:.3f}  max={4:.3f}".format(
            n_f, m_f, s_f, fore.min(), fore.max()
        )
    )

    diff = m_a - m_f
    lines.append(f"  difference in means (agricultural - forested): {diff:.3f} mg/L")

    # Group spreads differ by roughly a factor of two, so Welch's unequal-variance
    # two-sample t-test is the pre-specified primary test.
    t_stat, p_val = stats.ttest_ind(agri, fore, equal_var=False)
    se = (s_a**2 / n_a + s_f**2 / n_f) ** 0.5
    df = (s_a**2 / n_a + s_f**2 / n_f) ** 2 / (
        (s_a**2 / n_a) ** 2 / (n_a - 1) + (s_f**2 / n_f) ** 2 / (n_f - 1)
    )
    t_crit = stats.t.ppf(1 - ALPHA / 2, df)
    ci_low, ci_high = diff - t_crit * se, diff + t_crit * se

    lines.append("")
    lines.append("Primary test: Welch two-sample t-test (independent groups, two-sided)")
    lines.append(f"  t          = {t_stat:.4f}")
    lines.append(f"  df (Welch) = {df:.3f}")
    lines.append(f"  p-value    = {p_val:.6g}")
    lines.append(
        "  95% CI for the difference in means: [{0:.3f}, {1:.3f}] mg/L".format(ci_low, ci_high)
    )

    # Effect size (Hedges' g, pooled-SD standardised mean difference).
    sp = (((n_a - 1) * s_a**2 + (n_f - 1) * s_f**2) / (n_a + n_f - 2)) ** 0.5
    d = diff / sp
    dof_g = n_a + n_f - 2
    g = d * (1 - 3 / (4 * dof_g - 1))
    lines.append(f"  Cohen's d  = {d:.3f}   Hedges' g = {g:.3f}")

    # Distribution-free confirmation, since n is small in each group.
    u_stat, u_p = stats.mannwhitneyu(agri, fore, alternative="two-sided")
    lines.append("")
    lines.append("Supporting test: Mann-Whitney U (rank-based, no normality assumption)")
    lines.append(f"  U = {u_stat:.1f}   p-value = {u_p:.6g}")

    verdict = "reject" if p_val < ALPHA else "do not reject"
    lines.append("")
    lines.append(
        "At alpha = {0}, {1} the null hypothesis of equal mean nitrate between catchment types.".format(
            ALPHA, verdict
        )
    )

    return "\n".join(lines), {
        "n_a": n_a,
        "n_f": n_f,
        "m_a": m_a,
        "m_f": m_f,
        "s_a": s_a,
        "s_f": s_f,
        "min_a": float(agri.min()),
        "max_a": float(agri.max()),
        "min_f": float(fore.min()),
        "max_f": float(fore.max()),
        "diff": diff,
        "t_stat": t_stat,
        "df": df,
        "p_val": p_val,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "d": d,
        "g": g,
        "u_stat": u_stat,
        "u_p": u_p,
    }


def main():
    raw, summary = load_data()

    raw_text, _ = describe_raw(raw)
    print(raw_text)

    cons_text, _ = check_consistency(raw, summary)
    print(cons_text)

    test_text, _ = compare_groups(summary)
    print(test_text)


if __name__ == "__main__":
    main()
