"""Analysis of the CKD sodium counselling trial.

Compares 24-hour ambulatory systolic blood pressure between the intensive dietary
sodium counselling arm and the usual dietary advice arm.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "ckd_sodium_trial_bp.csv"

OUTCOME = "systolic_bp_mmhg"
GROUP = "trial_arm"
USUAL = "usual_advice"
INTENSIVE = "intensive_counselling"


def load_data(path=DATA_FILE):
    """Read the trial data file."""
    return pd.read_csv(path)


def describe_arm(values):
    """Summarise one arm's blood pressure measurements."""
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
    }


def main():
    data = load_data()

    usual = data.loc[data[GROUP] == USUAL, OUTCOME]
    intensive = data.loc[data[GROUP] == INTENSIVE, OUTCOME]

    usual_stats = describe_arm(usual)
    intensive_stats = describe_arm(intensive)

    total_n = usual_stats["n"] + intensive_stats["n"]
    difference = intensive_stats["mean"] - usual_stats["mean"]

    t_statistic, p_value = stats.ttest_ind(intensive, usual)
    degrees_of_freedom = total_n - 2

    print("CKD sodium counselling trial: systolic blood pressure by trial arm")
    print("=" * 68)
    print(f"Data file: {DATA_FILE.name}")
    print(f"Total observations analysed: {total_n}")
    print()
    print(f"{'Arm':<26}{'n':>6}{'Mean (mmHg)':>16}{'SD (mmHg)':>14}")
    print("-" * 68)
    print(
        f"{'Usual advice':<26}{usual_stats['n']:>6}"
        f"{usual_stats['mean']:>16.2f}{usual_stats['sd']:>14.2f}"
    )
    print(
        f"{'Intensive counselling':<26}{intensive_stats['n']:>6}"
        f"{intensive_stats['mean']:>16.2f}{intensive_stats['sd']:>14.2f}"
    )
    print("-" * 68)
    print()
    print("Independent two-sample t-test (intensive counselling minus usual advice)")
    print(f"  Mean difference: {difference:.2f} mmHg")
    print(f"  t = {t_statistic:.4f}")
    print(f"  df = {degrees_of_freedom}")
    print(f"  p = {p_value:.6g}")
    print(f"  n = {total_n} observations "
          f"({intensive_stats['n']} intensive, {usual_stats['n']} usual advice)")


if __name__ == "__main__":
    main()
