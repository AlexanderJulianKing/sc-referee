"""On-farm sugar beet seed treatment trial: analysis.

Compares clean root yield (t/ha) between fields drilled with standard
fungicide-treated seed and fields drilled with seed carrying an added
biological coating.

Design note that fixes the analysis: the field is the experimental unit.
Each of the 34 commercial fields sits on a different farm, was drilled with
exactly one seed treatment, and was harvested whole, so it contributes exactly
one delivered clean root yield figure. Rows and fields are one to one, so each
row is one independent observation and the two groups are independent of one
another. That makes the standard independent two-sample t-test the appropriate
comparison; nothing here is nested, paired or repeated.

Reads the committed CSV. Does not generate data.
"""

import os

import pandas as pd
from scipy import stats

CSV_NAME = "sugar_beet_field_yields.csv"
OUTCOME = "clean_root_yield_t_ha"
GROUP = "seed_treatment"
UNIT = "field_id"
LEVELS = ["standard", "biological"]


def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_NAME)
    frame = pd.read_csv(path)

    # Guard the design assumption: one row per field, no field appears twice.
    n_rows = len(frame)
    n_units = frame[UNIT].nunique()
    if n_rows != n_units:
        raise ValueError(
            "expected one row per field, got {} rows and {} distinct {} values".format(
                n_rows, n_units, UNIT
            )
        )
    if frame[OUTCOME].isna().any() or frame[GROUP].isna().any():
        raise ValueError("missing values in the outcome or the group column")

    observed_levels = sorted(frame[GROUP].unique())
    if observed_levels != sorted(LEVELS):
        raise ValueError("unexpected {} levels: {}".format(GROUP, observed_levels))

    return frame


def describe(frame):
    """Group size, mean and sample standard deviation of yield."""
    table = (
        frame.groupby(GROUP)[OUTCOME]
        .agg(fields="size", mean="mean", sd=lambda s: s.std(ddof=1),
             minimum="min", maximum="max")
        .reindex(LEVELS)
    )
    return table


def main():
    frame = load_data()
    summary = describe(frame)

    standard = frame.loc[frame[GROUP] == "standard", OUTCOME].to_numpy()
    biological = frame.loc[frame[GROUP] == "biological", OUTCOME].to_numpy()

    n_standard = standard.size
    n_biological = biological.size

    # Standard independent two-sample t-test (Student, pooled variance).
    # One observation per field; the two groups contain different fields.
    result = stats.ttest_ind(biological, standard, equal_var=True)
    t_stat = float(result.statistic)
    p_value = float(result.pvalue)
    df = n_standard + n_biological - 2

    diff = float(biological.mean() - standard.mean())

    # 95% confidence interval for the difference in means, pooled SD.
    var_pooled = (
        (n_biological - 1) * biological.var(ddof=1)
        + (n_standard - 1) * standard.var(ddof=1)
    ) / df
    se_diff = (var_pooled * (1.0 / n_biological + 1.0 / n_standard)) ** 0.5
    t_crit = float(stats.t.ppf(0.975, df))
    ci_low = diff - t_crit * se_diff
    ci_high = diff + t_crit * se_diff

    # Welch's version, reported only as a robustness check on the equal-variance
    # assumption. The Student test above is the headline result.
    welch = stats.ttest_ind(biological, standard, equal_var=False)
    v_bio = biological.var(ddof=1) / n_biological
    v_std = standard.var(ddof=1) / n_standard
    welch_df = (v_bio + v_std) ** 2 / (
        v_bio ** 2 / (n_biological - 1) + v_std ** 2 / (n_standard - 1)
    )

    print("On-farm sugar beet seed treatment trial")
    print("=" * 55)
    print("Experimental unit: field (one row per field, one yield per field)")
    print("Fields in file: {}   distinct field_id values: {}".format(
        len(frame), frame[UNIT].nunique()))
    print("Field area (ha): min {:.1f}, max {:.1f}, mean {:.1f}".format(
        frame["field_area_ha"].min(),
        frame["field_area_ha"].max(),
        frame["field_area_ha"].mean(),
    ))
    print()
    print("Clean root yield by seed treatment (t/ha)")
    print("-" * 55)
    for level in LEVELS:
        row = summary.loc[level]
        print(
            "{:<12} n = {:>2} fields   mean {:6.2f}   sd {:5.2f}   "
            "range {:.1f} to {:.1f}".format(
                level, int(row["fields"]), row["mean"], row["sd"],
                row["minimum"], row["maximum"],
            )
        )
    print()
    print("Independent two-sample t-test (Student, pooled variance)")
    print("-" * 55)
    print("Comparison        : biological minus standard")
    print("Sample size       : {} fields vs {} fields".format(
        n_biological, n_standard))
    print("Difference in means: {:+.2f} t/ha".format(diff))
    print("95% CI            : {:.2f} to {:.2f} t/ha".format(ci_low, ci_high))
    print("t({})            : {:.4f}".format(df, t_stat))
    print("p-value           : {:.4f}".format(p_value))
    print()
    print("Robustness check (Welch, unequal variances allowed)")
    print("-" * 55)
    print("t = {:.4f}, df = {:.2f}, p = {:.4f}".format(
        float(welch.statistic),
        float(welch_df),
        float(welch.pvalue),
    ))


if __name__ == "__main__":
    main()
