"""Transport stress in horses: serum cortisol in transported versus stay-at-home animals.

Reads cortisol_transport.csv and compares serum cortisol between the two transport
conditions with an independent two-sample t-test. Every cortisol reading in the table
is entered into the test as an individual observation.
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cortisol_transport.csv")


def load_data(path=DATA_FILE):
    """Read the assay table."""
    return pd.read_csv(path)


def describe_group(values):
    """Return the descriptive statistics reported for one transport condition."""
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "sem": float(values.std(ddof=1) / (values.size ** 0.5)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def main():
    data = load_data()

    transported = data.loc[data["transport_condition"] == "transported", "cortisol_nmol_l"]
    stayed = data.loc[data["transport_condition"] == "stayed", "cortisol_nmol_l"]

    n_total = int(data.shape[0])
    desc_transported = describe_group(transported)
    desc_stayed = describe_group(stayed)

    t_stat, p_value = stats.ttest_ind(transported, stayed)
    df = desc_transported["n"] + desc_stayed["n"] - 2
    difference = desc_transported["mean"] - desc_stayed["mean"]

    pooled_sd = (
        ((desc_transported["n"] - 1) * desc_transported["sd"] ** 2
         + (desc_stayed["n"] - 1) * desc_stayed["sd"] ** 2) / df
    ) ** 0.5
    se_diff = pooled_sd * (1.0 / desc_transported["n"] + 1.0 / desc_stayed["n"]) ** 0.5
    t_crit = stats.t.ppf(0.975, df)
    ci_low = difference - t_crit * se_diff
    ci_high = difference + t_crit * se_diff
    cohens_d = difference / pooled_sd

    ages = data.drop_duplicates("horse_id")["age_years"]

    print("Serum cortisol and road transport in horses")
    print("=" * 55)
    print("Data file: {}".format(os.path.basename(DATA_FILE)))
    print("Cortisol readings analysed (n): {}".format(n_total))
    print("Horses in the study: {}".format(data["horse_id"].nunique()))
    print("Age of horses (years): mean {:.1f}, range {} to {}".format(
        ages.mean(), int(ages.min()), int(ages.max())))
    print()

    print("Group summaries (serum cortisol, nmol/L)")
    print("-" * 55)
    header = "{:<14}{:>6}{:>10}{:>10}{:>9}{:>9}{:>9}".format(
        "group", "n", "mean", "sd", "sem", "min", "max")
    print(header)
    for label, desc in (("transported", desc_transported), ("stayed", desc_stayed)):
        print("{:<14}{:>6d}{:>10.2f}{:>10.2f}{:>9.2f}{:>9.1f}{:>9.1f}".format(
            label, desc["n"], desc["mean"], desc["sd"], desc["sem"],
            desc["min"], desc["max"]))
    print()

    print("Independent two-sample t-test (transported vs stayed)")
    print("-" * 55)
    print("Mean difference (transported - stayed): {:.2f} nmol/L".format(difference))
    print("95% confidence interval: {:.2f} to {:.2f} nmol/L".format(ci_low, ci_high))
    print("Pooled SD: {:.2f} nmol/L".format(pooled_sd))
    print("t({}) = {:.3f}".format(df, t_stat))
    print("p = {:.3e}".format(p_value))
    print("Cohen's d = {:.2f}".format(cohens_d))
    print("Total observations entered into the test: {}".format(n_total))


if __name__ == "__main__":
    main()
