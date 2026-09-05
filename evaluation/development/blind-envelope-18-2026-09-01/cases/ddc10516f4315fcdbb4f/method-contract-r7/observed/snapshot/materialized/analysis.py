"""Compare improved biomass stove households with traditional open fire households.

Reads the fixed authored file ``data.csv`` and compares the two stove groups on
each of the five outcomes declared by the study protocol, in the declared order.
The script does not create, simulate, or modify any data.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "data.csv"
GROUP_COLUMN = "stove_type"
IMPROVED = "improved_biomass_stove"
TRADITIONAL = "traditional_open_fire"

# Per-outcome significance threshold fixed by the study protocol before any data
# were collected. It is used here exactly as the protocol gave it.
ALPHA = 0.01

# The five declared outcomes, in the order the protocol declared them.
OUTCOMES = [
    ("kitchen_pm25_ug_m3", "24-hour kitchen PM2.5 (ug/m3)"),
    ("kitchen_co_ppm", "24-hour kitchen carbon monoxide (ppm)"),
    ("fuelwood_use_kg_day", "Daily fuelwood use (kg/day)"),
    ("respiratory_symptom_score", "Cook's respiratory symptom score (0-12)"),
    ("cooking_time_min", "Daily cooking time (minutes)"),
]


def main():
    data = pd.read_csv(DATA_FILE)

    improved = data[data[GROUP_COLUMN] == IMPROVED]
    traditional = data[data[GROUP_COLUMN] == TRADITIONAL]

    print("Improved biomass stove vs traditional open fire")
    print("Rows read from {}: {}".format(DATA_FILE, len(data)))
    print("Protocol per-outcome significance threshold: {}".format(ALPHA))
    print("")

    for index, (column, label) in enumerate(OUTCOMES, start=1):
        a = improved[column].astype(float)
        b = traditional[column].astype(float)

        # Welch's two-sample t-test: a standard two-group comparison that does
        # not assume the two groups share a variance.
        t_statistic, p_value = stats.ttest_ind(a, b, equal_var=False)

        verdict = (
            "significant at the 0.01 protocol threshold"
            if p_value < ALPHA
            else "not significant at the 0.01 protocol threshold"
        )

        print("Outcome {}: {} [{}]".format(index, label, column))
        print(
            "  improved_biomass_stove: n = {}, mean = {:.3f}, sd = {:.3f}".format(
                a.size, a.mean(), a.std(ddof=1)
            )
        )
        print(
            "  traditional_open_fire:  n = {}, mean = {:.3f}, sd = {:.3f}".format(
                b.size, b.mean(), b.std(ddof=1)
            )
        )
        print("  difference (improved - traditional): {:.3f}".format(a.mean() - b.mean()))
        print("  Welch t = {:.3f}".format(t_statistic))
        print("  p-value = {:.6g}".format(p_value))
        print("  verdict: {}".format(verdict))
        print("")


if __name__ == "__main__":
    main()
