"""Hop cone alpha-acid analysis.

Compares alpha-acid content of hop cones between the farm's standard nitrogen
top-dressing rate and the reduced rate under test.

Every assayed cone in `hop_cone_alpha_acids.csv` enters the comparison as its own
observation, so the comparison is run over all 120 rows of the table with an
independent two-sample t-test.

Run with:  python3 analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "hop_cone_alpha_acids.csv"

OUTCOME = "alpha_acid_percent"
GROUP = "nitrogen_rate"
STANDARD = "standard"
REDUCED = "reduced"


def load_data(path=DATA_FILE):
    """Read the cone-level table."""
    return pd.read_csv(path)


def describe_group(values):
    """Mean, standard deviation and count for one group of cone measurements."""
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def compare_groups(data):
    """Independent two-sample t-test over every row of the table."""
    standard = data.loc[data[GROUP] == STANDARD, OUTCOME]
    reduced = data.loc[data[GROUP] == REDUCED, OUTCOME]

    result = stats.ttest_ind(standard, reduced, equal_var=True)

    n_standard = standard.size
    n_reduced = reduced.size
    df = n_standard + n_reduced - 2

    # Pooled standard deviation, for the difference interval and the effect size.
    pooled_var = (
        (n_standard - 1) * standard.var(ddof=1) + (n_reduced - 1) * reduced.var(ddof=1)
    ) / df
    pooled_sd = pooled_var ** 0.5
    se_diff = pooled_sd * ((1.0 / n_standard + 1.0 / n_reduced) ** 0.5)

    difference = float(standard.mean() - reduced.mean())
    t_crit = stats.t.ppf(0.975, df)

    return {
        "standard": describe_group(standard),
        "reduced": describe_group(reduced),
        "n_total": int(data.shape[0]),
        "difference": difference,
        "se_diff": float(se_diff),
        "ci_low": float(difference - t_crit * se_diff),
        "ci_high": float(difference + t_crit * se_diff),
        "t": float(result.statistic),
        "df": int(df),
        "p": float(result.pvalue),
        "cohens_d": float(difference / pooled_sd),
    }


def main():
    data = load_data()
    out = compare_groups(data)

    print("Hop cone alpha-acid content: standard vs reduced nitrogen")
    print("=" * 58)
    print(f"Rows analysed (total sample size): {out['n_total']}")
    print()
    for label, key in ((STANDARD, "standard"), (REDUCED, "reduced")):
        g = out[key]
        print(
            f"  {label:<9} n = {g['n']:>3}   mean = {g['mean']:.2f}%   "
            f"SD = {g['sd']:.2f}   range = {g['min']:.2f}-{g['max']:.2f}"
        )
    print()
    print("Independent two-sample t-test (equal variances)")
    print(f"  difference in means (standard - reduced) = {out['difference']:.2f} pp")
    print(f"  95% CI = [{out['ci_low']:.2f}, {out['ci_high']:.2f}] pp")
    print(f"  SE of the difference = {out['se_diff']:.3f} pp")
    print(f"  t({out['df']}) = {out['t']:.3f}")
    print(f"  p = {out['p']:.3g}")
    print(f"  Cohen's d = {out['cohens_d']:.3f}")


if __name__ == "__main__":
    main()
