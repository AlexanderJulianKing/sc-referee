"""Green roofs and building microclimate.

Fifty flat-roofed municipal buildings logged over one summer, 25 with extensive
green roof retrofits and 25 with conventional membrane roofs. One row per
building, five season-summary outcomes.
"""

import pandas as pd
from scipy import stats

DATA = "data.csv"
LEVEL = 0.05

# Verdict wording is looked up rather than written out at each outcome, so the
# same words always follow from the same comparison.
VERDICTS = ("no significant difference", "significant difference")

OUTCOMES = [
    ("peak_roof_temp_c", "peak roof surface temp (C)"),
    ("cooling_kwh_m2", "summer cooling energy (kWh/m2)"),
    ("indoor_temp_range_c", "daily indoor temp swing (C)"),
    ("runoff_coefficient", "stormwater runoff coefficient"),
    ("maintenance_hours", "annual maintenance (hours)"),
]


def main():
    df = pd.read_csv(DATA)
    conventional = df[df["roof_type"] == "conventional"]
    green = df[df["roof_type"] == "green"]

    print("Green roof retrofits versus conventional membrane roofs")
    print("n conventional = %d, n green = %d" % (len(conventional), len(green)))
    print("Significance level: %.2f" % LEVEL)
    print()

    header = "%-30s %14s %10s %10s %26s" % (
        "outcome", "conventional", "green", "p", "verdict")
    print(header)
    print("-" * len(header))

    for col, label in OUTCOMES:
        a = conventional[col].to_numpy()
        b = green[col].to_numpy()
        # Welch t-test: the two roof populations differ in more than the mean and
        # equal variance is not a safe assumption.
        test = stats.ttest_ind(a, b, equal_var=False)
        verdict = VERDICTS[int(test.pvalue < LEVEL)]
        print(f"{label:-30s} {a.mean():14.2f} {b.mean():10.2f} {test.pvalue:10.4g} {verdict:26s}")


if __name__ == "__main__":
    main()
