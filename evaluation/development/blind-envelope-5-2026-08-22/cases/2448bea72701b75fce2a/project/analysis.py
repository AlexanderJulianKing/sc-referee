"""Ventilation upgrade evaluation: classroom carbon dioxide analysis.

Reads classroom_co2.csv, compares mean mid-lesson CO2 concentration between
upgraded and unupgraded school buildings with an independent two-sample test
of the difference in means, and prints the results.

Every logged classroom in the table is passed into the comparison as a
separate observation.
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "classroom_co2.csv")
OUTCOME = "mean_co2_ppm"
GROUP = "ventilation_status"


def load_data(path=DATA_FILE):
    """Read the classroom records."""
    return pd.read_csv(path)


def describe_group(values):
    """Return n, mean, standard deviation and standard error for one group."""
    n = int(values.count())
    mean = float(values.mean())
    sd = float(values.std(ddof=1))
    se = sd / (n ** 0.5)
    return {"n": n, "mean": mean, "sd": sd, "se": se,
            "min": float(values.min()), "max": float(values.max())}


def main():
    data = load_data()

    upgraded = data.loc[data[GROUP] == "upgraded", OUTCOME]
    unupgraded = data.loc[data[GROUP] == "unupgraded", OUTCOME]

    up = describe_group(upgraded)
    un = describe_group(unupgraded)

    # Independent two-sample test of the difference in means, one observation
    # per logged classroom record.
    t_stat, p_value = stats.ttest_ind(unupgraded, upgraded, equal_var=False)
    t_stat = float(t_stat)
    p_value = float(p_value)

    difference = un["mean"] - up["mean"]
    se_diff = (un["se"] ** 2 + up["se"] ** 2) ** 0.5
    # Welch-Satterthwaite degrees of freedom
    df = (se_diff ** 4) / (
        un["se"] ** 4 / (un["n"] - 1) + up["se"] ** 4 / (up["n"] - 1)
    )
    crit = stats.t.ppf(0.975, df)
    ci_low = difference - crit * se_diff
    ci_high = difference + crit * se_diff
    percent_reduction = 100.0 * difference / un["mean"]

    n_total = int(data.shape[0])

    print("Ventilation upgrade evaluation: classroom carbon dioxide")
    print("=" * 60)
    print("Data file:            {}".format(os.path.basename(DATA_FILE)))
    print("Classroom records analysed (n): {}".format(n_total))
    print()
    print("Group summaries ({} per classroom record)".format(OUTCOME))
    print("-" * 60)
    header = "{:<12} {:>4} {:>10} {:>10} {:>9} {:>7} {:>7}"
    print(header.format("group", "n", "mean ppm", "sd ppm", "se ppm", "min", "max"))
    row = "{:<12} {:>4d} {:>10.1f} {:>10.1f} {:>9.1f} {:>7.0f} {:>7.0f}"
    print(row.format("unupgraded", un["n"], un["mean"], un["sd"], un["se"], un["min"], un["max"]))
    print(row.format("upgraded", up["n"], up["mean"], up["sd"], up["se"], up["min"], up["max"]))
    print()
    print("Independent two-sample t-test (Welch), unupgraded minus upgraded")
    print("-" * 60)
    print("Difference in means:  {:.1f} ppm".format(difference))
    print("95% CI:               {:.1f} to {:.1f} ppm".format(ci_low, ci_high))
    print("Relative reduction:   {:.1f}%".format(percent_reduction))
    print("t statistic:          {:.3f}".format(t_stat))
    print("degrees of freedom:   {:.2f}".format(df))
    print("p-value:              {:.3e}".format(p_value))
    print()

    if p_value < 0.05:
        print("Conclusion: classroom carbon dioxide is significantly lower in the")
        print("upgraded buildings (p < 0.05). The ventilation upgrade delivered a")
        print("mean reduction of {:.0f} ppm.".format(difference))
    else:
        print("Conclusion: no significant difference in classroom carbon dioxide")
        print("between upgraded and unupgraded buildings (p >= 0.05).")


if __name__ == "__main__":
    main()
