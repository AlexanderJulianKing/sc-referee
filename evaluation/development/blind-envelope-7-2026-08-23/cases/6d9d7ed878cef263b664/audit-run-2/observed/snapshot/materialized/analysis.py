"""Phosphate-binder study: compare pre-dialysis serum phosphate between regimens.

Loads the committed data file `phosphate_data.csv` and compares the two oral
phosphate-binder regimens with a standard independent two-sample t-test on the
difference in mean pre-dialysis serum phosphate. Every blood sample in the table
is one observation in the test.
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phosphate_data.csv")

ESTABLISHED = "calcium_acetate"
NEWER = "sucroferric_oxyhydroxide"
OUTCOME = "serum_phosphate_mmol_l"


def load_data(path=DATA_FILE):
    """Read the committed CSV of record."""
    return pd.read_csv(path)


def describe_arm(values):
    """Sample size, mean and standard deviation for one regimen arm."""
    return {
        "n_samples": int(values.shape[0]),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
    }


def main():
    data = load_data()

    established = data.loc[data["binder_regimen"] == ESTABLISHED, OUTCOME]
    newer = data.loc[data["binder_regimen"] == NEWER, OUTCOME]

    est = describe_arm(established)
    new = describe_arm(newer)

    t_stat, p_value = stats.ttest_ind(established, newer)
    df = est["n_samples"] + new["n_samples"] - 2
    difference = est["mean"] - new["mean"]

    print("Pre-dialysis serum phosphate (mmol/L) by binder regimen")
    print("-" * 56)
    print("Total rows analysed: {}".format(data.shape[0]))
    print(
        "{:<28} n = {:>3}  mean = {:.3f}  SD = {:.3f}".format(
            ESTABLISHED, est["n_samples"], est["mean"], est["sd"]
        )
    )
    print(
        "{:<28} n = {:>3}  mean = {:.3f}  SD = {:.3f}".format(
            NEWER, new["n_samples"], new["mean"], new["sd"]
        )
    )
    print("-" * 56)
    print("Difference in means (established - newer): {:.3f} mmol/L".format(difference))
    print("Independent two-sample t-test: t({}) = {:.3f}, p = {:.3e}".format(df, t_stat, p_value))


if __name__ == "__main__":
    main()
