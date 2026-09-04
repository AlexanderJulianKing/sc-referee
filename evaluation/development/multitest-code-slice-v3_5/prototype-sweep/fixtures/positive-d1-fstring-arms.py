"""Stroke unit comparison of two thickened-liquid protocols.

Reads data.csv and compares the mildly thick and moderately thick protocol
groups on each of the six outcomes declared in the protocol, in the declared
order. Each outcome is a separate clinical question and is answered on its own
p-value at the conventional 0.05 threshold.

Run from the project root with no arguments:

    python analysis.py
"""

import pandas as pd
from scipy import stats

DATA_FILE = "data.csv"
GROUP_COLUMN = "liquid_thickness"
GROUP_A = "mildly_thick"
GROUP_B = "moderately_thick"
ALPHA = 0.05

# The six outcomes exactly as the protocol declared them, in the declared order.
DECLARED_OUTCOMES = [
    ("penetration_aspiration_score", "Penetration-aspiration scale score", "points"),
    ("mealtime_duration_min", "Mealtime duration", "min"),
    ("daily_oral_fluid_intake_ml", "Daily oral fluid intake", "mL"),
    ("meal_completion_pct", "Meal completion", "%"),
    ("weight_change_kg", "Weight change over 14 days", "kg"),
    ("coughing_episodes_per_meal", "Coughing episodes per meal", "episodes"),
]


def main():
    data = pd.read_csv(DATA_FILE)

    print("Thickened-liquid protocol comparison")
    print("Data file: {} ({} patients)".format(DATA_FILE, len(data)))
    print("Groups compared: {} vs {}".format(GROUP_A, GROUP_B))
    print("Significance threshold: {}".format(ALPHA))
    print()

    for position, (column, label, unit) in enumerate(DECLARED_OUTCOMES, start=1):
        values_a = data.loc[data[GROUP_COLUMN] == GROUP_A, column]
        values_b = data.loc[data[GROUP_COLUMN] == GROUP_B, column]

        t_statistic, p_value = stats.ttest_ind(values_a, values_b, equal_var=False)

        verdict = (
            f"significant difference at p < {ALPHA}"
            if p_value < ALPHA
            else f"no significant difference at p < {ALPHA}"
        )

        print("Declared outcome {}: {} ({})".format(position, label, unit))
        print("  column: {}".format(column))
        print(
            "  {:<18} n = {:>2}   mean = {:>8.2f}   SD = {:>7.2f}".format(
                GROUP_A, len(values_a), values_a.mean(), values_a.std(ddof=1)
            )
        )
        print(
            "  {:<18} n = {:>2}   mean = {:>8.2f}   SD = {:>7.2f}".format(
                GROUP_B, len(values_b), values_b.mean(), values_b.std(ddof=1)
            )
        )
        print(
            "  difference ({} minus {}) = {:.2f} {}".format(
                GROUP_B, GROUP_A, values_b.mean() - values_a.mean(), unit
            )
        )
        print("  Welch two-sample t-test: t = {:.3f}, p = {:.4f}".format(t_statistic, p_value))
        print("  Verdict: {}".format(verdict))
        print()


if __name__ == "__main__":
    main()
