"""Marram grass cover on fenced and unfenced coastal sand dunes.

Question: does excluding rabbits change percentage cover of marram grass on
mobile sand dunes?

The survey placed six 1 m quadrats along a fixed seaward-toe-to-crest line on
each of ten dunes: five fenced against rabbits for three years, five left
unfenced. Each quadrat is a percentage cover reading of the dune system, and
all sixty quadrat rows enter the comparison.

Reads marram_cover.csv (read-only; this script never writes to it) and prints
every number quoted in report.md.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA = Path(__file__).resolve().parent / "marram_cover.csv"


def main() -> None:
    df = pd.read_csv(DATA)

    print("=" * 62)
    print("MARRAM COVER AND RABBIT EXCLUSION ON COASTAL SAND DUNES")
    print("=" * 62)

    # ---- Data as read -------------------------------------------------
    print("\n[1] DATA AS READ")
    print(f"    file                : {DATA.name}")
    print(f"    rows (quadrats)     : {len(df)}")
    print(f"    columns             : {', '.join(df.columns)}")
    print(f"    dunes surveyed      : {df['dune_name'].nunique()}")
    print(f"    quadrats per dune   : {df.groupby('dune_name').size().unique().tolist()}")
    print(f"    quadrat_number range: {df['quadrat_number'].min()} to {df['quadrat_number'].max()}")
    print(f"    cover range (%)     : {df['marram_cover_pct'].min()} to {df['marram_cover_pct'].max()}")
    print(f"    missing values      : {int(df.isna().sum().sum())}")

    treatments = sorted(df["rabbit_exclusion"].unique())
    print(f"    treatment levels    : {', '.join(treatments)}")

    # ---- Descriptive summary by treatment -----------------------------
    print("\n[2] COVER BY TREATMENT (all quadrat rows)")
    header = f"    {'group':<10}{'n':>5}{'mean':>9}{'sd':>8}{'median':>9}{'min':>6}{'max':>6}"
    print(header)
    print("    " + "-" * (len(header) - 4))
    summary = {}
    for level in treatments:
        cover = df.loc[df["rabbit_exclusion"] == level, "marram_cover_pct"]
        summary[level] = cover
        print(
            f"    {level:<10}{len(cover):>5}{cover.mean():>9.2f}{cover.std(ddof=1):>8.2f}"
            f"{cover.median():>9.1f}{cover.min():>6.0f}{cover.max():>6.0f}"
        )

    # ---- Independent two-sample comparison of means -------------------
    fenced = summary["fenced"]
    unfenced = summary["unfenced"]

    n_total = len(df)
    mean_f = fenced.mean()
    mean_u = unfenced.mean()
    diff = mean_f - mean_u

    t_stat, p_value = stats.ttest_ind(fenced, unfenced, equal_var=True)
    df_resid = len(fenced) + len(unfenced) - 2

    # Pooled SD and 95% CI for the difference in means.
    sp2 = (
        (len(fenced) - 1) * fenced.var(ddof=1) + (len(unfenced) - 1) * unfenced.var(ddof=1)
    ) / df_resid
    se_diff = (sp2 * (1 / len(fenced) + 1 / len(unfenced))) ** 0.5
    tcrit = stats.t.ppf(0.975, df_resid)
    ci_low, ci_high = diff - tcrit * se_diff, diff + tcrit * se_diff
    cohen_d = diff / sp2**0.5

    print("\n[3] INDEPENDENT TWO-SAMPLE t-TEST (Student, equal variances)")
    print("    comparison          : fenced minus unfenced, marram_cover_pct")
    print(f"    total quadrats (n)  : {n_total}")
    print(f"    n fenced            : {len(fenced)}")
    print(f"    n unfenced          : {len(unfenced)}")
    print(f"    mean fenced (%)     : {mean_f:.2f}")
    print(f"    mean unfenced (%)   : {mean_u:.2f}")
    print(f"    difference (pp)     : {diff:.2f}")
    print(f"    pooled SD (pp)      : {sp2 ** 0.5:.2f}")
    print(f"    SE of difference    : {se_diff:.3f}")
    print(f"    95% CI of difference: {ci_low:.2f} to {ci_high:.2f}")
    print(f"    t statistic         : {t_stat:.3f}")
    print(f"    degrees of freedom  : {df_resid}")
    print(f"    p-value             : {p_value:.6g}")
    print(f"    Cohen's d           : {cohen_d:.2f}")

    direction = "more" if diff > 0 else "less"
    verdict = "yes" if (p_value < 0.05 and diff > 0) else "no"
    print("\n[4] CONCLUSION")
    print(f"    Did rabbit exclusion increase marram cover at alpha = 0.05? {verdict}")
    print(
        f"    Fenced dunes carry {abs(diff):.2f} percentage points {direction} marram\n"
        f"    cover than unfenced dunes (t = {t_stat:.3f}, df = {df_resid}, "
        f"p = {p_value:.6g})."
    )


if __name__ == "__main__":
    main()
