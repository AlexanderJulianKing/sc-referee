"""Compare week-6 microcolony mass between the two pollen diets.

One row of microcolony_growth.csv is one whole microcolony weighed once, so the
rows that go into the test are the colonies themselves.
"""

import os

import pandas as pd
from scipy import stats

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "microcolony_growth.csv")


def main() -> None:
    df = pd.read_csv(CSV_PATH)

    # Each colony must appear exactly once; if it does not, the rows are not colonies.
    duplicated = df["hive_label"].duplicated()
    if duplicated.any():
        raise ValueError(
            "duplicated hive_label values: " + ", ".join(sorted(df.loc[duplicated, "hive_label"]))
        )

    n_rows = len(df)
    n_colonies = df["hive_label"].nunique()
    print(f"rows in file:      {n_rows}")
    print(f"unique colonies:   {n_colonies}")
    print(f"one row per colony: {n_rows == n_colonies}")

    # Split the single mass measurement per colony by diet treatment.
    mono = df.loc[df["pollen_diet"] == "monofloral", "final_colony_mass_g"]
    mixed = df.loc[df["pollen_diet"] == "mixed", "final_colony_mass_g"]

    for name, group in (("monofloral", mono), ("mixed", mixed)):
        print(
            f"{name:>11}: n = {len(group)} colonies, "
            f"mean = {group.mean():.2f} g, sd = {group.std(ddof=1):.2f} g"
        )

    # Two-sample t-test on colony-level masses (Student's, equal variances assumed).
    t_stat, p_value = stats.ttest_ind(mono, mixed)
    print(f"t statistic: {t_stat:.4f}")
    print(f"p-value:     {p_value:.4f}")


if __name__ == "__main__":
    main()
