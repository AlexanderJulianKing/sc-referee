"""Two-dressing comparison for chronic venous leg ulcers.

Compares a standard foam dressing against an alginate dressing on the six
outcomes declared by the protocol, using an independent two-sample t-test for
each outcome at the conventional 0.05 threshold.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "venous_ulcer_dressings.csv"

GROUP_COLUMN = "dressing_group"
GROUP_FOAM = "dressing_foam"
GROUP_ALGINATE = "dressing_alginate"

ALPHA = 0.05

# The six outcomes in the order the protocol declared them.
DECLARED_OUTCOMES = [
    "area_reduction_pct",
    "pain_vas_mm",
    "exudate_score",
    "periwound_erythema_mm",
    "days_to_half_healing",
    "wound_qol_score",
]


def load_data():
    """Read the patient-level CSV and split it into the two dressing arms."""
    frame = pd.read_csv(DATA_FILE)
    return frame


def main():
    frame = load_data()

    print("Venous leg ulcer dressing comparison")
    print("=" * 78)
    print(f"Data file: {DATA_FILE.name}")
    print(f"Patients: {len(frame)} rows, one row per patient")
    print(f"  arms: {GROUP_FOAM} vs {GROUP_ALGINATE}")
    print(f"Missing cells in the file: {int(frame.isna().sum().sum())}")
    print()

    # All six per-outcome results are built in one pass over the declared
    # outcome list, in the declared order, into a single collection.
    results = {}
    for column in DECLARED_OUTCOMES:
        foam_values = frame.loc[frame[GROUP_COLUMN] == GROUP_FOAM, column].to_numpy()
        alginate_values = frame.loc[frame[GROUP_COLUMN] == GROUP_ALGINATE, column].to_numpy()
        test = stats.ttest_ind(foam_values, alginate_values)
        results[column] = {
            "foam_mean": float(foam_values.mean()),
            "foam_sd": float(foam_values.std(ddof=1)),
            "alginate_mean": float(alginate_values.mean()),
            "alginate_sd": float(alginate_values.std(ddof=1)),
            "difference": float(foam_values.mean() - alginate_values.mean()),
            "t_statistic": float(test.statistic),
            "p_value": float(test.pvalue),
        }

    print("Group summaries (mean and standard deviation)")
    print("-" * 78)
    header = f"{'Outcome':<40}{'Foam':>18}{'Alginate':>18}"
    print(header)
    for column in DECLARED_OUTCOMES:
        entry = results[column]
        foam_cell = f"{entry['foam_mean']:.2f} ({entry['foam_sd']:.2f})"
        alginate_cell = f"{entry['alginate_mean']:.2f} ({entry['alginate_sd']:.2f})"
        print(f"{column:<40}{foam_cell:>18}{alginate_cell:>18}")
    print()

    print(f"Per-outcome tests (independent two-sample t-test, alpha = {ALPHA})")
    print("-" * 78)
    print(f"{'#':<3}{'Outcome':<40}{'diff':>10}{'t':>9}{'p':>12}  verdict")
    for column in DECLARED_OUTCOMES:
        entry = results[column]
        significant_flag = entry["p_value"] < 0.05
        print(
            f"{column:<40}"
            f"{entry['difference']:>10.2f}"
            f"{entry['t_statistic']:>9.3f}"
            f"{entry['p_value']:>12.4f}  {significant_flag}"
        )
    print()

    return results


if __name__ == "__main__":
    main()
