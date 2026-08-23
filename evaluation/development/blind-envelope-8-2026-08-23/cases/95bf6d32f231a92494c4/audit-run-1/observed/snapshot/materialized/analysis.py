"""Compare marketable cranberry yield between wet- and dry-harvested bogs.

Study design
------------
Twenty-four production bogs each took part once. Twelve bogs were wet-harvested
by flooding and twelve were dry-harvested with mechanical pickers. The
cooperative recorded a single marketable yield figure per bog for the season, so
the table holds exactly one row per bog and the bog is the independent unit.
Because one row is one bog, a row-level independent two-sample comparison of
`marketable_yield_bbl_per_acre` between the two levels of `harvest_method` is the
correct inferential test: there is no repeated measurement or nesting inside a
bog that would need pooling first.

Primary test
------------
Welch's independent two-sample t-test (two-sided) on the 24 bog-level yields.
Welch is used rather than the equal-variance (Student) form because it does not
assume the two methods share a variance; the Student and rank-based results are
reported alongside it as sensitivity checks only.

Run with: /usr/local/bin/python3 analysis.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "cranberry_harvest.csv"
OUTCOME = "marketable_yield_bbl_per_acre"
GROUP = "harvest_method"
UNIT = "bog_id"
ALPHA = 0.05


def load_data(path):
    """Read the frozen CSV. This script never writes to it."""
    return pd.read_csv(path, dtype={UNIT: str, GROUP: str, "cultivar": str})


def check_design(df):
    """Confirm the one-row-per-bog design the inferential test relies on.

    If this ever fails, the row-level t-test below would be treating repeated
    measurements as independent, so the script stops rather than reporting a
    number that is not supported by the table.
    """
    n_rows = len(df)
    n_units = df[UNIT].nunique()
    rows_per_unit = df.groupby(UNIT).size()
    counts = df[GROUP].value_counts().sort_index()

    lines = [
        f"rows in file:              {n_rows}",
        f"distinct {UNIT} values:     {n_units}",
        f"max rows per {UNIT}:        {int(rows_per_unit.max())}",
        f"missing {OUTCOME}: {int(df[OUTCOME].isna().sum())}",
    ]
    for level, count in counts.items():
        n_bogs = df.loc[df[GROUP] == level, UNIT].nunique()
        lines.append(f"harvest_method '{level}': {count} rows, {n_bogs} bogs")

    if n_rows != n_units:
        raise ValueError(
            f"{n_rows} rows but only {n_units} distinct {UNIT} values: a bog "
            "appears more than once, so rows are not independent units."
        )
    if sorted(counts.index) != ["dry", "wet"]:
        raise ValueError(f"expected exactly the levels dry and wet, found {list(counts.index)}")
    if df[OUTCOME].isna().any():
        raise ValueError("missing outcome values; the test below assumes complete yields")

    return "\n".join(lines)


def describe(values):
    return {
        "n": int(values.size),
        "mean": float(np.mean(values)),
        "sd": float(np.std(values, ddof=1)),
        "min": float(np.min(values)),
        "median": float(np.median(values)),
        "max": float(np.max(values)),
    }


def main():
    df = load_data(DATA_FILE)

    print("=" * 72)
    print("CRANBERRY HARVEST METHOD COMPARISON")
    print("=" * 72)
    print()
    print("Design checks (one row per bog)")
    print("-" * 72)
    print(check_design(df))
    print()

    dry = df.loc[df[GROUP] == "dry", OUTCOME].to_numpy()
    wet = df.loc[df[GROUP] == "wet", OUTCOME].to_numpy()

    print("Marketable yield (barrels per acre) by harvest method")
    print("-" * 72)
    print(f"{'method':>8} {'n bogs':>7} {'mean':>8} {'sd':>8} {'min':>8} {'median':>8} {'max':>8}")
    stats_by_group = {}
    for label, values in (("dry", dry), ("wet", wet)):
        s = describe(values)
        stats_by_group[label] = s
        print(
            f"{label:>8} {s['n']:>7d} {s['mean']:>8.2f} {s['sd']:>8.2f} "
            f"{s['min']:>8.1f} {s['median']:>8.2f} {s['max']:>8.1f}"
        )
    print()

    diff = stats_by_group["wet"]["mean"] - stats_by_group["dry"]["mean"]

    # ---- Primary test: Welch's two-sample t-test on the 24 bog-level values ----
    t_stat, p_value = stats.ttest_ind(wet, dry, equal_var=False)
    n_wet, n_dry = wet.size, dry.size
    var_wet, var_dry = np.var(wet, ddof=1), np.var(dry, ddof=1)
    se = np.sqrt(var_wet / n_wet + var_dry / n_dry)
    welch_df = (var_wet / n_wet + var_dry / n_dry) ** 2 / (
        (var_wet / n_wet) ** 2 / (n_wet - 1) + (var_dry / n_dry) ** 2 / (n_dry - 1)
    )
    t_crit = stats.t.ppf(1 - ALPHA / 2, welch_df)
    ci_low, ci_high = diff - t_crit * se, diff + t_crit * se

    # Hedges' g: standardised mean difference with the small-sample correction.
    pooled_sd = np.sqrt(
        ((n_wet - 1) * var_wet + (n_dry - 1) * var_dry) / (n_wet + n_dry - 2)
    )
    cohens_d = diff / pooled_sd
    hedges_g = cohens_d * (1 - 3 / (4 * (n_wet + n_dry) - 9))

    print("PRIMARY TEST - Welch's independent two-sample t-test (two-sided)")
    print("-" * 72)
    print(f"unit of analysis:            one production bog (one row)")
    print(f"n bogs, wet:                 {n_wet}")
    print(f"n bogs, dry:                 {n_dry}")
    print(f"mean yield, wet:             {stats_by_group['wet']['mean']:.2f} bbl/acre")
    print(f"mean yield, dry:             {stats_by_group['dry']['mean']:.2f} bbl/acre")
    print(f"difference (wet - dry):      {diff:.2f} bbl/acre")
    print(f"standard error of difference:{se:9.2f}")
    print(f"t statistic:                 {t_stat:.4f}")
    print(f"degrees of freedom (Welch):  {welch_df:.2f}")
    print(f"p-value:                     {p_value:.4f}")
    print(f"95% CI for the difference:   [{ci_low:.2f}, {ci_high:.2f}] bbl/acre")
    print(f"Hedges' g:                   {hedges_g:.3f}")
    print(f"decision at alpha = {ALPHA}:    "
          f"{'reject' if p_value < ALPHA else 'do not reject'} the null of equal means")
    print()

    # ---- Sensitivity checks. Reported for transparency, not as the decision. ----
    t_student, p_student = stats.ttest_ind(wet, dry, equal_var=True)
    u_stat, p_mw = stats.mannwhitneyu(wet, dry, alternative="two-sided")
    lev_stat, p_levene = stats.levene(wet, dry, center="median")
    sw_wet = stats.shapiro(wet)
    sw_dry = stats.shapiro(dry)

    print("Sensitivity checks (secondary; the Welch test above is the decision)")
    print("-" * 72)
    print(f"Student t-test (equal variance):  t = {t_student:.4f}, p = {p_student:.4f}")
    print(f"Mann-Whitney U (rank-based):      U = {u_stat:.1f}, p = {p_mw:.4f}")
    print(f"Levene equal-variance test:       W = {lev_stat:.4f}, p = {p_levene:.4f}")
    print(f"Shapiro-Wilk normality, wet:      W = {sw_wet.statistic:.4f}, p = {sw_wet.pvalue:.4f}")
    print(f"Shapiro-Wilk normality, dry:      W = {sw_dry.statistic:.4f}, p = {sw_dry.pvalue:.4f}")
    print()
    print("Note: bog area, cultivar, planting age, and harvest date are recorded in")
    print("the file but are not used in this comparison. The protocol asks only for a")
    print("two-group comparison of yield, and no adjusted model was planned in advance.")
    print("=" * 72)


if __name__ == "__main__":
    main()
