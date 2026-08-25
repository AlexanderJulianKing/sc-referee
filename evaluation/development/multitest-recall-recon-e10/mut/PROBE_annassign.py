"""Annotated closed family declaration for the delta-1.1 recognizer gate."""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "chocolate_batches.csv"
GROUP_COLUMN = "conche_group"
GROUP_A = "conche_50c"
GROUP_B = "conche_65c"
ALPHA = 0.05

DECLARED_OUTCOMES: list[str] = [
    "particle_d90_um",
    "hardness_n",
    "melt_peak_c",
    "gloss_gu",
    "bitterness_score",
]


def load_data():
    frame = pd.read_csv(DATA_FILE)
    required = ["batch_id", GROUP_COLUMN] + DECLARED_OUTCOMES  # noqa: RUF005
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
    for outcome in DECLARED_OUTCOMES:
        values_a = frame.query("conche_group == 'conche_50c'")[outcome].to_numpy()
        values_b = frame.query("conche_group == 'conche_65c'")[outcome].to_numpy()
        result = stats.ttest_ind(values_a, values_b, equal_var=False)
        significant = result.pvalue < ALPHA
        print(outcome, result.pvalue, significant)


if __name__ == "__main__":
    main()
