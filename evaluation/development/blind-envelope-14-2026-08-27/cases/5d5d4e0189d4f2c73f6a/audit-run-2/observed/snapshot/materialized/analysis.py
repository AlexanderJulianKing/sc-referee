"""Analysis of the night wrist splinting trial in carpal tunnel syndrome.

Reads carpal_tunnel_splint_trial.csv and compares the night_splint arm with the
no_splint arm on each of the five outcomes declared by the protocol, in the
declared order. Each comparison is a two-sample Welch t-test and reports the two
group means, the difference between them, and the p-value.

The protocol fixed the per-outcome significance threshold in advance. That fixed
threshold is held below as a single constant and every verdict is a direct
comparison of the outcome's p-value against it.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

# Pre-specified per-outcome significance threshold, fixed by the protocol before
# recruitment. Used exactly as given; nothing in this script alters it.
SIGNIFICANCE_THRESHOLD = 0.01

DATA_FILE = Path(__file__).resolve().parent / "carpal_tunnel_splint_trial.csv"

GROUP_COLUMN = "allocation"
SPLINT_GROUP = "night_splint"
CONTROL_GROUP = "no_splint"

# The five outcomes declared by the protocol, in the declared order.
DECLARED_OUTCOMES = [
    ("symptom_severity_score", "Symptom severity score (1-5)"),
    ("functional_status_score", "Functional status score (1-5)"),
    ("night_awakenings_per_week", "Night awakenings per week (0-7)"),
    ("two_point_discrimination_mm", "Two-point discrimination (mm)"),
    ("distal_motor_latency_ms", "Distal motor latency (ms)"),
]


def load_data(path):
    """Load the trial data and check the basic shape the protocol assumes."""
    data = pd.read_csv(path)

    required = [GROUP_COLUMN] + [name for name, _ in DECLARED_OUTCOMES]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError("missing columns in the data file: " + ", ".join(missing))

    groups = sorted(data[GROUP_COLUMN].unique())
    if groups != sorted([SPLINT_GROUP, CONTROL_GROUP]):
        raise ValueError("unexpected allocation values: " + ", ".join(groups))

    blank_counts = data[required].isna().sum()
    blanks = blank_counts[blank_counts > 0]
    if not blanks.empty:
        raise ValueError("blank cells found in: " + ", ".join(blanks.index))

    return data


def compare_outcome(data, column):
    """Compare the two allocation groups on one outcome."""
    splint_values = data.loc[data[GROUP_COLUMN] == SPLINT_GROUP, column]
    control_values = data.loc[data[GROUP_COLUMN] == CONTROL_GROUP, column]

    # Welch's two-sample t-test: two independent groups, no assumption that the
    # two group variances are equal.
    result = stats.ttest_ind(splint_values, control_values, equal_var=False)

    splint_mean = float(splint_values.mean())
    control_mean = float(control_values.mean())

    return {
        "column": column,
        "n_splint": int(splint_values.size),
        "n_control": int(control_values.size),
        "mean_splint": splint_mean,
        "mean_control": control_mean,
        "difference": splint_mean - control_mean,
        "p_value": float(result.pvalue),
    }


def format_p_value(p_value):
    if p_value < 0.001:
        return "<0.001"
    return "{:.4f}".format(p_value)


def main():
    data = load_data(DATA_FILE)

    n_splint = int((data[GROUP_COLUMN] == SPLINT_GROUP).sum())
    n_control = int((data[GROUP_COLUMN] == CONTROL_GROUP).sum())

    print("Night wrist splinting in mild to moderate carpal tunnel syndrome")
    print("Data file: {}".format(DATA_FILE.name))
    print("Participants: {} total ({} {}, {} {})".format(
        len(data), n_splint, SPLINT_GROUP, n_control, CONTROL_GROUP))
    print("Test: two-sample Welch t-test, {} minus {}".format(
        SPLINT_GROUP, CONTROL_GROUP))
    print("Pre-specified per-outcome significance threshold: p < {}".format(
        SIGNIFICANCE_THRESHOLD))
    print()

    header = "{:<32} {:>12} {:>12} {:>12} {:>10}  {}".format(
        "Outcome (declared order)", "night_splint", "no_splint",
        "difference", "p-value", "verdict")
    print(header)
    print("-" * len(header))

    results = []
    for column, label in DECLARED_OUTCOMES:
        result = compare_outcome(data, column)
        result["label"] = label

        # The only rule applied to any p-value in this script.
        result["significant"] = result["p_value"] < SIGNIFICANCE_THRESHOLD
        verdict = "significant" if result["significant"] else "not significant"

        print("{:<32} {:>12.3f} {:>12.3f} {:>12.3f} {:>10}  {}".format(
            label,
            result["mean_splint"],
            result["mean_control"],
            result["difference"],
            format_p_value(result["p_value"]),
            verdict,
        ))
        results.append(result)

    print()
    significant = [r["label"] for r in results if r["significant"]]
    if significant:
        print("Outcomes meeting the p < {} threshold: {}".format(
            SIGNIFICANCE_THRESHOLD, "; ".join(significant)))
    else:
        print("No outcome met the p < {} threshold.".format(SIGNIFICANCE_THRESHOLD))


if __name__ == "__main__":
    main()
