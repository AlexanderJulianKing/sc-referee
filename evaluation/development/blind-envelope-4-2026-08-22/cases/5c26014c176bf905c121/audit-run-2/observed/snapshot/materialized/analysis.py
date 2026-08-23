"""Stocking-density trial on Pacific oysters: does reduced density grow bigger shells?

Twenty-week grow-out trial on a single longline. Fourteen mesh baskets, seven at the farm's
standard stocking density and seven at a reduced density. Twelve oysters were lifted out of each
basket and measured for shell height, giving 168 measured animals.

Every measured oyster is one independent replicate, so the analysis compares the shell heights of
the 84 standard-density oysters against the 84 reduced-density oysters with an independent
two-sample t-test on the group means.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "oyster_shell_height.csv"


def load_measurements(path):
    """Read the measurement table, one row per measured oyster."""
    oysters = pd.read_csv(path)
    expected = ["basket_id", "density_group", "oyster_number", "shell_height_mm"]
    if list(oysters.columns) != expected:
        raise ValueError(f"unexpected columns: {list(oysters.columns)}")
    if oysters["shell_height_mm"].isna().any():
        raise ValueError("missing shell heights in the measurement table")
    return oysters


def main():
    oysters = load_measurements(DATA_FILE)

    # Split the measured animals by the stocking density their basket was run at.
    standard = oysters.loc[oysters["density_group"] == "standard", "shell_height_mm"]
    reduced = oysters.loc[oysters["density_group"] == "reduced", "shell_height_mm"]

    n_total = len(oysters)
    mean_standard = standard.mean()
    mean_reduced = reduced.mean()
    difference = mean_reduced - mean_standard

    # Independent two-sample t-test on the group means, using every measured oyster.
    t_stat, p_value = stats.ttest_ind(reduced, standard)
    df = len(reduced) + len(standard) - 2

    print("Pacific oyster stocking-density trial: shell height after 20 weeks")
    print("-" * 66)
    print(f"Oysters measured (total)      : {n_total}")
    print(f"Standard density: n = {len(standard)}, "
          f"mean = {mean_standard:.2f} mm, SD = {standard.std(ddof=1):.2f} mm")
    print(f"Reduced density : n = {len(reduced)}, "
          f"mean = {mean_reduced:.2f} mm, SD = {reduced.std(ddof=1):.2f} mm")
    print(f"Difference (reduced - standard): {difference:.2f} mm")
    print(f"Two-sample t-test             : t({df}) = {t_stat:.3f}, p = {p_value:.3e}")

    verdict = "increased" if difference > 0 and p_value < 0.05 else "did not increase"
    print(f"Conclusion                    : reduced stocking density {verdict} shell height.")


if __name__ == "__main__":
    main()
