"""Greenhouse tomato mycorrhiza trial: inoculated vs. control marketable yield.

One row of `greenhouse_tomato_yield.csv` is one whole tomato plant. Each plant grew
alone in its own pot, was assigned to a treatment at transplanting, and was harvested
once at the end of the season. The plant is therefore both the treated unit and the
measured unit: rows, measurements, and experimental units are the same 48 plants.

Because every plant contributes exactly one independent value of `marketable_yield_g`,
the two groups are compared with an independent two-sample t-test on the per-plant
yields. Welch's form is used, so the test does not assume the two groups share a
variance. No aggregation or nesting is needed: there is nothing below the plant to
average over and nothing above it that plants share.

Run with:  python3 analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "greenhouse_tomato_yield.csv"

ID_COL = "plant_id"
GROUP_COL = "treatment"
OUTCOME_COL = "marketable_yield_g"
CONTROL = "control"
INOCULATED = "inoculated"

EXPECTED_PLANTS = 48


def load_data(path):
    """Read the trial data, one row per plant."""
    return pd.read_csv(path)


def check_one_row_per_plant(df):
    """Confirm every plant identifier appears exactly once.

    This is the check that the analysis unit and the row are the same thing. If any
    plant_id appeared twice, the rows would no longer be independent plants and an
    independent two-sample test would not be the right comparison.

    Returns True when the check passes.
    """
    counts = df[ID_COL].value_counts()
    repeated = counts[counts > 1]
    n_rows = len(df)
    n_unique = df[ID_COL].nunique()

    print("Unit-of-analysis check: does every plant appear exactly once?")
    print(f"  rows in file                 : {n_rows}")
    print(f"  distinct {ID_COL} values     : {n_unique}")
    print(f"  identifiers appearing twice+ : {len(repeated)}")
    if not repeated.empty:
        for plant_id, count in repeated.items():
            print(f"    {plant_id}: {count} rows")

    passed = repeated.empty and n_rows == n_unique == EXPECTED_PLANTS
    if passed:
        print(
            f"  RESULT: PASS - {n_rows} rows, {n_unique} distinct plants, "
            "one row per plant, no plant measured twice."
        )
        print(
            "  The row and the experimental unit are the same, so each row is one "
            "independent observation."
        )
    else:
        print(
            f"  RESULT: FAIL - expected {EXPECTED_PLANTS} rows each with a distinct "
            f"{ID_COL}; got {n_rows} rows and {n_unique} distinct identifiers."
        )
    return passed


def describe_group(values):
    """Sample size, mean, and sample standard deviation (n - 1 denominator)."""
    return len(values), values.mean(), values.std(ddof=1)


def main():
    df = load_data(DATA_FILE)

    print("=" * 72)
    print("Greenhouse tomato trial: mycorrhizal inoculation and marketable yield")
    print("=" * 72)
    print(f"Data file: {DATA_FILE.name}")
    print(f"Columns  : {', '.join(df.columns)}")
    print()
    print("One row = one whole plant, harvested once at the end of the season.")
    print()

    check_passed = check_one_row_per_plant(df)
    print()

    groups = sorted(df[GROUP_COL].unique())
    print(f"Treatment groups found: {groups}")
    print()

    control = df.loc[df[GROUP_COL] == CONTROL, OUTCOME_COL]
    inoculated = df.loc[df[GROUP_COL] == INOCULATED, OUTCOME_COL]

    n_ctl, mean_ctl, sd_ctl = describe_group(control)
    n_ino, mean_ino, sd_ino = describe_group(inoculated)
    n_total = n_ctl + n_ino

    print("Sample size (number of plants; each plant gives one yield value)")
    print(f"  control     : n = {n_ctl} plants")
    print(f"  inoculated  : n = {n_ino} plants")
    print(f"  total       : n = {n_total} plants")
    print()

    print(f"Outcome: {OUTCOME_COL} (cumulative marketable fresh mass per plant, g)")
    print(f"  control     mean = {mean_ctl:8.1f} g   SD = {sd_ctl:7.1f} g")
    print(f"  inoculated  mean = {mean_ino:8.1f} g   SD = {sd_ino:7.1f} g")
    print()

    diff = mean_ino - mean_ctl
    pct = 100.0 * diff / mean_ctl
    print("Difference in means (inoculated minus control)")
    print(f"  difference  = {diff:.1f} g  ({pct:+.1f}% of the control mean)")
    print()

    # Independent two-sample t-test on per-plant yields, Welch (unequal variances).
    result = stats.ttest_ind(inoculated, control, equal_var=False)
    t_stat = float(result.statistic)
    p_value = float(result.pvalue)

    # Welch-Satterthwaite degrees of freedom, computed here so the script does not
    # depend on the scipy version exposing them on the result object.
    var_ino = sd_ino**2 / n_ino
    var_ctl = sd_ctl**2 / n_ctl
    df_welch = (var_ino + var_ctl) ** 2 / (
        var_ino**2 / (n_ino - 1) + var_ctl**2 / (n_ctl - 1)
    )

    # 95% confidence interval for the difference, on the same Welch footing.
    se_diff = (var_ino + var_ctl) ** 0.5
    t_crit = stats.t.ppf(0.975, df_welch)
    ci_low = diff - t_crit * se_diff
    ci_high = diff + t_crit * se_diff

    print("Independent two-sample t-test (Welch, unequal variances not assumed equal)")
    print(f"  comparison  : {INOCULATED} vs {CONTROL}, one yield value per plant")
    print(f"  t           = {t_stat:.4f}")
    print(f"  df (Welch)  = {df_welch:.2f}")
    print(f"  p-value     = {p_value:.6f}")
    print(f"  95% CI for the difference = [{ci_low:.1f}, {ci_high:.1f}] g")
    print()

    # Student's pooled-variance t-test, reported alongside for completeness.
    pooled = stats.ttest_ind(inoculated, control, equal_var=True)
    print("Same comparison with the pooled-variance (Student) t-test, for reference")
    print(f"  t = {float(pooled.statistic):.4f}   df = {n_total - 2}   "
          f"p = {float(pooled.pvalue):.6f}")
    print()

    print("-" * 72)
    print("Summary")
    print(f"  unit-of-analysis check : {'PASS' if check_passed else 'FAIL'}")
    print(f"  plants per group       : {n_ctl} control, {n_ino} inoculated "
          f"({n_total} total)")
    print(f"  control mean (SD)      : {mean_ctl:.1f} g ({sd_ctl:.1f} g)")
    print(f"  inoculated mean (SD)   : {mean_ino:.1f} g ({sd_ino:.1f} g)")
    print(f"  difference in means    : {diff:.1f} g")
    print(f"  p-value (Welch t-test) : {p_value:.6f}")
    print("-" * 72)


if __name__ == "__main__":
    main()
