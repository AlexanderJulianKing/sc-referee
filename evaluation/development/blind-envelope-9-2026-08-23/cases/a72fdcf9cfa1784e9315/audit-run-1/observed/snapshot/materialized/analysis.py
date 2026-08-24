"""Estuarine benthic survey: polychaete counts inside and outside the dredge
spoil disposal footprint.

Reads `benthic_grabs.csv` and compares `polychaete_count` between the two
levels of `station_group` (`footprint` and `reference`) with an independent
two-sample t-test. Every grab row in the table enters the comparison as its own
observation, so the comparison runs on all 80 rows.

Run:  python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = "benthic_grabs.csv"
OUTCOME = "polychaete_count"
GROUP = "station_group"
FOOTPRINT = "footprint"
REFERENCE = "reference"


def load_data():
    """Load the grab table."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
    return pd.read_csv(path)


def describe_group(values):
    """Mean, standard deviation, count and range for one group of grabs."""
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "min": int(values.min()),
        "max": int(values.max()),
    }


def main():
    data = load_data()

    footprint = data.loc[data[GROUP] == FOOTPRINT, OUTCOME]
    reference = data.loc[data[GROUP] == REFERENCE, OUTCOME]

    footprint_stats = describe_group(footprint)
    reference_stats = describe_group(reference)

    # Independent two-sample t-test on every row of the table.
    result = stats.ttest_ind(reference, footprint, equal_var=True)

    n_total = int(data.shape[0])
    n_f = footprint_stats["n"]
    n_r = reference_stats["n"]
    df = n_f + n_r - 2

    difference = reference_stats["mean"] - footprint_stats["mean"]

    # Pooled standard deviation, for the confidence interval and effect size.
    pooled_var = (
        (n_f - 1) * footprint_stats["sd"] ** 2 + (n_r - 1) * reference_stats["sd"] ** 2
    ) / df
    pooled_sd = pooled_var ** 0.5
    se = pooled_sd * (1.0 / n_f + 1.0 / n_r) ** 0.5
    t_crit = stats.t.ppf(0.975, df)
    ci_low = difference - t_crit * se
    ci_high = difference + t_crit * se
    cohens_d = difference / pooled_sd

    print("Estuarine benthic survey: polychaete counts per 0.1 m^2 grab")
    print("=" * 62)
    print(f"Rows in table (observations in the test): {n_total}")
    print()
    print(f"{'group':<12}{'n':>5}{'mean':>10}{'sd':>10}{'min':>7}{'max':>7}")
    for name, s in ((FOOTPRINT, footprint_stats), (REFERENCE, reference_stats)):
        print(
            f"{name:<12}{s['n']:>5}{s['mean']:>10.2f}{s['sd']:>10.2f}"
            f"{s['min']:>7}{s['max']:>7}"
        )
    print()
    print("Independent two-sample t-test (reference - footprint), equal variances")
    print(f"  mean difference : {difference:.2f} worms per grab")
    print(f"  95% CI          : {ci_low:.2f} to {ci_high:.2f}")
    print(f"  t({df})         : {result.statistic:.3f}")
    print(f"  p-value         : {result.pvalue:.3e}")
    print(f"  Cohen's d       : {cohens_d:.3f}")


if __name__ == "__main__":
    main()
