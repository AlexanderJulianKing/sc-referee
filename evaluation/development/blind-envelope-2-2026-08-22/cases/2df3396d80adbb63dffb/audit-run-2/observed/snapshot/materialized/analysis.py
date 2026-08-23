"""Milk yield analysis: conventional soybean meal vs treated canola.

Reads milk_yield.csv and compares daily milk yield (kg) between the two total
mixed ration formulations with a single independent two-sample t-test. Each
test-day record in the table is one observation in that comparison.
"""

import os

import pandas as pd
from scipy import stats

CSV_NAME = "milk_yield.csv"
OUTCOME = "milk_yield_kg"
GROUP = "ration"
CONTROL = "conventional_soybean_meal"
TREATED = "treated_canola"


def load_data():
    """Read the test-day records from the CSV next to this script."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_NAME)
    return pd.read_csv(path)


def main():
    data = load_data()

    control = data.loc[data[GROUP] == CONTROL, OUTCOME]
    treated = data.loc[data[GROUP] == TREATED, OUTCOME]

    n_control = len(control)
    n_treated = len(treated)
    n_total = n_control + n_treated

    mean_control = control.mean()
    mean_treated = treated.mean()
    sd_control = control.std(ddof=1)
    sd_treated = treated.std(ddof=1)
    difference = mean_treated - mean_control

    result = stats.ttest_ind(treated, control)

    print("Daily milk yield by ration")
    print("Comparison: independent two-sample t-test on test-day records")
    print("")
    print("Sample size")
    print("  {:<28s} n = {:d} test-day records".format(CONTROL, n_control))
    print("  {:<28s} n = {:d} test-day records".format(TREATED, n_treated))
    print("  {:<28s} n = {:d} test-day records".format("total", n_total))
    print("")
    print("Group summaries (kg/d)")
    print("  {:<28s} mean = {:.2f}  SD = {:.2f}".format(
        CONTROL, mean_control, sd_control))
    print("  {:<28s} mean = {:.2f}  SD = {:.2f}".format(
        TREATED, mean_treated, sd_treated))
    print("")
    print("Difference in means (treated_canola - conventional_soybean_meal)")
    print("  {:+.2f} kg/d".format(difference))
    print("")
    print("Test statistic")
    print("  t = {:.4f}".format(result.statistic))
    print("  df = {:d}".format(n_total - 2))
    print("  p = {:.6f}".format(result.pvalue))


if __name__ == "__main__":
    main()
