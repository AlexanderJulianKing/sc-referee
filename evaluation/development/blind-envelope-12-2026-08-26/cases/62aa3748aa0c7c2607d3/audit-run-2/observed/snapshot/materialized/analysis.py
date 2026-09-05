"""Analysis of the early mobilisation trial after elective heart valve surgery.

For each of the five outcomes declared in the protocol, the two mobilisation
schedules are compared with a two-group comparison of the patient values, and
the resulting p-value is compared with the significance threshold that the
protocol fixed before enrolment.

PROTOCOL_ALPHA below is that fixed protocol number, read off the protocol and
written here as a literal. This script does not derive it, adjust it, or alter
any p-value; it only compares each p-value with it.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "mobilisation_trial.csv"

# Significance threshold fixed in the protocol before any patient was enrolled.
PROTOCOL_ALPHA = 0.01

GROUP_COLUMN = "group"
STANDARD = "standard"
ACCELERATED = "accelerated"

# The five declared outcomes, in the order the protocol declared them.
OUTCOMES = [
    ("walk_distance_m", "Six-minute walk distance at discharge", "m"),
    ("length_of_stay_days", "Postoperative hospital length of stay", "days"),
    ("mip_cmh2o", "Maximal inspiratory pressure at discharge", "cmH2O"),
    ("pain_nrs", "Pain at rest on day of discharge", "NRS 0-10"),
    ("days_to_stairs", "Days from surgery to independent stair climbing", "days"),
]


def load_data(path=DATA_FILE):
    """Read the trial table and check the structure the protocol assumes."""
    data = pd.read_csv(path)

    expected = ["patient_id", GROUP_COLUMN] + [name for name, _, _ in OUTCOMES]
    if list(data.columns) != expected:
        raise ValueError(f"unexpected columns: {list(data.columns)}")

    if data["patient_id"].duplicated().any():
        raise ValueError("patient_id is not unique; one row per patient is assumed")

    groups = set(data[GROUP_COLUMN].unique())
    if groups != {STANDARD, ACCELERATED}:
        raise ValueError(f"unexpected schedule labels: {sorted(groups)}")

    outcome_columns = [name for name, _, _ in OUTCOMES]
    if data[outcome_columns].isna().any().any():
        raise ValueError("missing outcome values; every patient must have all five")

    return data


def compare_outcome(data, column):
    """Compare the two schedules on one outcome.

    Welch's two-sample t-test on the patient values, which does not assume the
    two schedules have equal variance. Returns the two group means, the mean
    difference (accelerated minus standard) and the two-sided p-value.
    """
    standard_values = data.loc[data[GROUP_COLUMN] == STANDARD, column]
    accelerated_values = data.loc[data[GROUP_COLUMN] == ACCELERATED, column]

    result = stats.ttest_ind(accelerated_values, standard_values, equal_var=False)

    return {
        "n_standard": int(standard_values.size),
        "n_accelerated": int(accelerated_values.size),
        "mean_standard": float(standard_values.mean()),
        "mean_accelerated": float(accelerated_values.mean()),
        "difference": float(accelerated_values.mean() - standard_values.mean()),
        "p_value": float(result.pvalue),
    }


def run_analysis(data):
    """Run all five declared comparisons, in the declared order."""
    rows = []
    for order, (column, label, unit) in enumerate(OUTCOMES, start=1):
        row = {"order": order, "outcome": column, "label": label, "unit": unit}
        row.update(compare_outcome(data, column))
        # The only use made of the protocol threshold: a comparison.
        row["significant"] = row["p_value"] < PROTOCOL_ALPHA
        rows.append(row)
    return pd.DataFrame(rows)


def format_p(p_value):
    return "<0.001" if p_value < 0.001 else f"{p_value:.3f}"


def print_results(results):
    print("Early mobilisation after elective heart valve surgery")
    print(f"Patients: {results.loc[0, 'n_standard'] + results.loc[0, 'n_accelerated']}"
          f" ({results.loc[0, 'n_standard']} standard,"
          f" {results.loc[0, 'n_accelerated']} accelerated)")
    print(f"Protocol significance threshold: p < {PROTOCOL_ALPHA}")
    print()

    header = (f"{'#':<2} {'Outcome (unit)':<56} {'Standard':>10} "
              f"{'Accelerated':>12} {'Diff':>9} {'p':>8}  Verdict")
    print(header)
    print("-" * len(header))

    for row in results.itertuples():
        verdict = "significant" if row.significant else "not significant"
        print(f"{row.order:<2} {row.label + ' (' + row.unit + ')':<56} "
              f"{row.mean_standard:>10.2f} {row.mean_accelerated:>12.2f} "
              f"{row.difference:>+9.2f} {format_p(row.p_value):>8}  {verdict}")

    print()
    print(f"Outcomes significant at the protocol threshold: "
          f"{int(results['significant'].sum())} of {len(results)}")


def main():
    data = load_data()
    results = run_analysis(data)
    print_results(results)
    return results


if __name__ == "__main__":
    main()
