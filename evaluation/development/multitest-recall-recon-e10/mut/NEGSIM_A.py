"""Conching temperature and dark chocolate quality: per-outcome group comparison.

Reads chocolate_batches.csv (one row per production batch) and compares the two
conching groups, conche_50c and conche_65c, on each of the five quality outcomes
declared in the protocol, in the declared order.

For each declared outcome the script reports the mean and standard deviation in
each group and a Welch two-sample t test for independent samples, with a
significant-or-not verdict at the conventional 0.05 threshold.
"""

from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = Path(__file__).resolve().parent / "chocolate_batches.csv"

GROUP_COLUMN = "conche_group"
GROUP_A = "conche_50c"
GROUP_B = "conche_65c"

ALPHA = 0.05

# The five quality outcomes declared in the protocol, in their declared order.
DECLARED_OUTCOMES = [
    "particle_d90_um",
    "hardness_n",
    "melt_peak_c",
    "gloss_gu",
    "bitterness_score",
]



def load_data():
    """Load the batch table and check the structure the protocol assumes."""
    frame = pd.read_csv(DATA_FILE)

    required = ["batch_id", GROUP_COLUMN] + DECLARED_OUTCOMES
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"missing expected columns: {missing}")

    groups_present = sorted(frame[GROUP_COLUMN].unique())
    if groups_present != sorted([GROUP_A, GROUP_B]):
        raise ValueError(f"unexpected group labels: {groups_present}")

    if frame[required].isna().any().any():
        raise ValueError("unexpected missing values in the analysis columns")

    if frame["batch_id"].duplicated().any():
        raise ValueError("duplicate batch_id values")

    return frame


def main():
    frame = load_data()

    print("Conching temperature and dark chocolate quality")
    print("=" * 78)

    p_values = []
    for outcome in DECLARED_OUTCOMES:
        values_a = frame.loc[frame[GROUP_COLUMN] == GROUP_A, outcome].to_numpy()
        values_b = frame.loc[frame[GROUP_COLUMN] == GROUP_B, outcome].to_numpy()
        result = stats.ttest_ind(values_a, values_b, equal_var=False)
        p_values.append(float(result.pvalue))

    reject, p_adjusted, _, _ = multipletests(p_values, alpha=0.05, method="holm")

    for position in range(len(DECLARED_OUTCOMES)):
        print(f"{DECLARED_OUTCOMES[position]}: p_adj = {p_adjusted[position]:.4f} reject = {reject[position]}")


if __name__ == "__main__":
    main()
