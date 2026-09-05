"""Analysis of the cloudy pear juice processing trial.

Forty-four bottles from one pressed batch were split between thermal
pasteurisation and high-pressure processing, stored 28 days in the dark at
4 degrees Celsius, then opened once and measured. A bottle is the unit of the
study and appears exactly once in the data file.

The trial declared four quality outcomes, each as its own acceptance question
for the new process. Each declared outcome is therefore compared on its own
terms with a standard two-group comparison of the bottle values and judged at
the conventional five percent threshold. No multiple-comparison adjustment is
applied: every outcome carries its own verdict at that threshold.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "juice_quality.csv"

GROUP_COLUMN = "group"
THERMAL = "thermal_pasteurisation"
HIGH_PRESSURE = "high_pressure_processing"

ALPHA = 0.05

# The four quality outcomes, in the order the trial declared them.
DECLARED_OUTCOMES = [
    ("ascorbic_acid_mg_100ml", "Ascorbic acid", "mg/100 mL"),
    ("cloud_stability_pct", "Cloud stability", "% of initial turbidity"),
    ("browning_index", "Browning index", "absorbance at 420 nm"),
    ("plate_count_log_cfu", "Total aerobic plate count", "log10 CFU/mL"),
]


def load_data(path=DATA_FILE):
    """Read the bottle table and check the shape the trial described."""
    data = pd.read_csv(path)

    expected_columns = ["bottle_id", GROUP_COLUMN] + [
        column for column, _, _ in DECLARED_OUTCOMES
    ]
    missing = [column for column in expected_columns if column not in data.columns]
    if missing:
        raise ValueError(f"missing expected column(s): {', '.join(missing)}")

    if data["bottle_id"].duplicated().any():
        raise ValueError("bottle_id values are not unique; one row per bottle expected")

    observed_groups = set(data[GROUP_COLUMN].unique())
    if observed_groups != {THERMAL, HIGH_PRESSURE}:
        raise ValueError(f"unexpected treatment labels: {sorted(observed_groups)}")

    outcome_columns = [column for column, _, _ in DECLARED_OUTCOMES]
    if data[outcome_columns].isna().any().any():
        raise ValueError("outcome columns contain blanks; every bottle must be measured")

    return data


def compare_outcome(data, column):
    """Compare the two treatments on one outcome with a two-sample t-test."""
    thermal_values = data.loc[data[GROUP_COLUMN] == THERMAL, column]
    high_pressure_values = data.loc[data[GROUP_COLUMN] == HIGH_PRESSURE, column]

    result = stats.ttest_ind(thermal_values, high_pressure_values)

    return {
        "column": column,
        "n_thermal": int(thermal_values.size),
        "n_high_pressure": int(high_pressure_values.size),
        "mean_thermal": float(thermal_values.mean()),
        "mean_high_pressure": float(high_pressure_values.mean()),
        "sd_thermal": float(thermal_values.std(ddof=1)),
        "sd_high_pressure": float(high_pressure_values.std(ddof=1)),
        # Difference is high-pressure processing minus thermal pasteurisation.
        "difference": float(high_pressure_values.mean() - thermal_values.mean()),
        "t_statistic": float(result.statistic),
        "p_value": float(result.pvalue),
    }


def main():
    data = load_data()

    print("Cloudy pear juice processing trial")
    print(f"Bottles: {len(data)} "
          f"({(data[GROUP_COLUMN] == THERMAL).sum()} thermal pasteurisation, "
          f"{(data[GROUP_COLUMN] == HIGH_PRESSURE).sum()} high-pressure processing)")
    print("One bottle per row; each bottle measured once after 28 days at 4 C.")
    print(f"Each declared outcome judged on its own at alpha = {ALPHA:.2f}; "
          "no multiple-comparison adjustment applied.")
    print()

    # One repeated pass over the declared outcome list, reporting as it goes.
    for column, label, unit in DECLARED_OUTCOMES:
        result = compare_outcome(data, column)
        verdict = (
            "significant" if result["p_value"] < ALPHA else "not significant"
        )

        print(f"{label} ({unit}) [{column}]")
        print(f"  thermal pasteurisation   mean = {result['mean_thermal']:.3f} "
              f"(SD {result['sd_thermal']:.3f}, n = {result['n_thermal']})")
        print(f"  high-pressure processing mean = {result['mean_high_pressure']:.3f} "
              f"(SD {result['sd_high_pressure']:.3f}, n = {result['n_high_pressure']})")
        print(f"  difference (high pressure - thermal) = {result['difference']:+.3f}")
        print(f"  t = {result['t_statistic']:.3f}, p = {result['p_value']:.4g} "
              f"-> {verdict} at the {ALPHA:.0%} threshold")
        print()


if __name__ == "__main__":
    main()
