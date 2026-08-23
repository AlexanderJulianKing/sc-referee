"""Harbour seal pup rehabilitation study: diet comparison.

Question: does the high-fat fish-oil supplemented diet produce heavier pups than
the centre's standard diet?

The analysis is an independent two-sample comparison of mean body mass between
the two diet groups, run across every weighing row in the table.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "seal_pup_masses.csv"


def load_data(path=DATA_FILE):
    """Read the weekly weighing table."""
    data = pd.read_csv(path)
    expected = ["pup_tag", "diet_group", "week_in_care", "body_mass_kg"]
    if list(data.columns) != expected:
        raise ValueError(f"unexpected columns: {list(data.columns)}")
    return data


def compare_diets(data):
    """Independent two-sample t-test on body mass, one observation per weighing."""
    standard = data.loc[data["diet_group"] == "standard", "body_mass_kg"]
    supplemented = data.loc[data["diet_group"] == "supplemented", "body_mass_kg"]

    result = stats.ttest_ind(supplemented, standard)

    return {
        "n_records_total": int(len(data)),
        "n_records_standard": int(len(standard)),
        "n_records_supplemented": int(len(supplemented)),
        "mean_standard": float(standard.mean()),
        "mean_supplemented": float(supplemented.mean()),
        "sd_standard": float(standard.std(ddof=1)),
        "sd_supplemented": float(supplemented.std(ddof=1)),
        "mean_difference": float(supplemented.mean() - standard.mean()),
        "t_statistic": float(result.statistic),
        "df": int(len(standard) + len(supplemented) - 2),
        "p_value": float(result.pvalue),
    }


def main():
    data = load_data()
    res = compare_diets(data)

    print("Harbour seal pup diet comparison")
    print("=" * 40)
    print(f"Total weight records analysed: {res['n_records_total']}")
    print(f"  standard diet:     {res['n_records_standard']} records")
    print(f"  supplemented diet: {res['n_records_supplemented']} records")
    print()
    print(f"Mean mass, standard diet:     {res['mean_standard']:.2f} kg "
          f"(SD {res['sd_standard']:.2f})")
    print(f"Mean mass, supplemented diet: {res['mean_supplemented']:.2f} kg "
          f"(SD {res['sd_supplemented']:.2f})")
    print(f"Difference (supplemented - standard): {res['mean_difference']:.2f} kg")
    print()
    print(f"Two-sample t-test: t({res['df']}) = {res['t_statistic']:.3f}, "
          f"p = {res['p_value']:.3g}")
    print()
    print("Mean mass by diet group and week in care (kg):")
    weekly = (data.pivot_table(index="week_in_care", columns="diet_group",
                               values="body_mass_kg", aggfunc="mean")
              .round(2))
    print(weekly.to_string())

    return res


if __name__ == "__main__":
    main()
