"""Analysis of the episodic-migraine prevention trial.

Reads migraine_trial.csv, summarises the seven declared outcomes by treatment
arm, and compares the medicine arm with the placebo arm on each outcome.

The two primary endpoints (monthly headache days, monthly migraine attacks) are
carried through a Holm multiple-comparisons adjustment and judged on their
adjusted p-values. The five remaining declared outcomes are judged on their own
p-values. The threshold is 0.05 throughout.

Run from the project root:
    python analysis.py
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

CSV_PATH = "migraine_trial.csv"
GROUP_COLUMN = "treatment_arm"
TREATMENT_LEVEL = "medicine"
CONTROL_LEVEL = "placebo"
ALPHA = 0.05
ADJUSTMENT_METHOD = "holm"

# Declared outcome family, in the protocol's fixed order.
OUTCOMES = [
    ("monthly_headache_days", "Monthly headache days"),
    ("monthly_migraine_attacks", "Monthly migraine attacks"),
    ("peak_pain_intensity_0_10", "Peak pain intensity (0-10)"),
    ("rescue_medication_days_per_month", "Rescue medication days per month"),
    ("migraine_disability_score_0_60", "Migraine disability score (0-60)"),
    ("nausea_days_per_month", "Nausea days per month"),
    ("sleep_quality_index_0_21", "Sleep quality index (0-21)"),
]

# The first two declared outcomes are the primary endpoints.
PRIMARY_OUTCOMES = [OUTCOMES[0][0], OUTCOMES[1][0]]


def load_data(path=CSV_PATH):
    """Read the trial CSV and check it has the shape the protocol expects."""
    frame = pd.read_csv(path)

    missing = [name for name, _ in OUTCOMES if name not in frame.columns]
    if missing:
        raise ValueError(f"CSV is missing declared outcome columns: {missing}")
    if GROUP_COLUMN not in frame.columns:
        raise ValueError(f"CSV is missing the group column '{GROUP_COLUMN}'")

    arms = sorted(frame[GROUP_COLUMN].unique())
    if arms != sorted([TREATMENT_LEVEL, CONTROL_LEVEL]):
        raise ValueError(f"Expected exactly two arms, found: {arms}")

    outcome_columns = [name for name, _ in OUTCOMES]
    if frame[outcome_columns].isna().any().any():
        raise ValueError("CSV contains missing outcome values")

    return frame


def arm_counts(frame):
    """Number of participants randomised to each arm."""
    return frame[GROUP_COLUMN].value_counts()


def summarise_outcomes(frame):
    """Mean and standard deviation of every declared outcome within each arm."""
    rows = []
    for arm in (TREATMENT_LEVEL, CONTROL_LEVEL):
        arm_frame = frame[frame[GROUP_COLUMN] == arm]
        for column, label in OUTCOMES:
            values = arm_frame[column]
            rows.append(
                {
                    "outcome": column,
                    "label": label,
                    "arm": arm,
                    "n": int(values.count()),
                    "mean": float(values.mean()),
                    "sd": float(values.std(ddof=1)),
                }
            )
    return pd.DataFrame(rows)


def test_outcomes(frame):
    """Two-sample t-test of medicine against placebo for each declared outcome."""
    treated = frame[frame[GROUP_COLUMN] == TREATMENT_LEVEL]
    control = frame[frame[GROUP_COLUMN] == CONTROL_LEVEL]

    results = []
    for column, label in OUTCOMES:
        medicine_values = treated[column]
        placebo_values = control[column]
        t_statistic, p_value = stats.ttest_ind(
            medicine_values, placebo_values, equal_var=True
        )
        results.append(
            {
                "outcome": column,
                "label": label,
                "role": "primary" if column in PRIMARY_OUTCOMES else "other declared",
                "mean_medicine": float(medicine_values.mean()),
                "mean_placebo": float(placebo_values.mean()),
                "mean_difference": float(medicine_values.mean() - placebo_values.mean()),
                "t_statistic": float(t_statistic),
                "p_value": float(p_value),
            }
        )
    return pd.DataFrame(results)


def apply_primary_adjustment(results):
    """Holm-adjust the two primary p-values and set every outcome's verdict.

    Primary endpoints are decided on the adjusted p-value; the other declared
    outcomes are decided on their own p-value.
    """
    results = results.copy()
    results["p_adjusted"] = pd.NA

    primary_mask = results["outcome"].isin(PRIMARY_OUTCOMES)
    primary_p = results.loc[primary_mask, "p_value"].tolist()
    _, adjusted_p, _, _ = multipletests(
        primary_p, alpha=ALPHA, method=ADJUSTMENT_METHOD
    )
    results.loc[primary_mask, "p_adjusted"] = adjusted_p

    decision_p = results["p_adjusted"].where(primary_mask, results["p_value"])
    results["decision_p"] = decision_p.astype(float)
    results["significant"] = results["decision_p"] < ALPHA
    results["verdict"] = results["significant"].map(
        {True: "significant", False: "not significant"}
    )
    return results


def format_p(value):
    if pd.isna(value):
        return "     -    "
    return f"{float(value):10.4f}"


def print_report(frame, summary, results):
    counts = arm_counts(frame)

    print("Episodic migraine prevention trial: analysis")
    print("=" * 78)
    print()

    print("Participants per arm")
    print("-" * 78)
    for arm in (TREATMENT_LEVEL, CONTROL_LEVEL):
        print(f"  {arm:<10s} {int(counts[arm]):3d}")
    print(f"  {'total':<10s} {len(frame):3d}")
    print()

    print("Per-arm summary of each declared outcome (mean, SD)")
    print("-" * 78)
    header = f"{'outcome':<36s}{'arm':<10s}{'n':>4s}{'mean':>10s}{'sd':>10s}"
    print(header)
    for column, label in OUTCOMES:
        for arm in (TREATMENT_LEVEL, CONTROL_LEVEL):
            row = summary[
                (summary["outcome"] == column) & (summary["arm"] == arm)
            ].iloc[0]
            print(
                f"{column if arm == TREATMENT_LEVEL else '':<36s}"
                f"{arm:<10s}{row['n']:>4d}{row['mean']:>10.2f}{row['sd']:>10.2f}"
            )
    print()

    print("Two-group comparisons (two-sample t-test, medicine vs placebo)")
    print(
        f"Primary endpoints adjusted with the '{ADJUSTMENT_METHOD}' method; "
        f"threshold alpha = {ALPHA}"
    )
    print("-" * 78)
    print(
        f"{'outcome':<36s}{'role':<16s}{'p_value':>10s}"
        f"{'p_adjusted':>12s}  verdict"
    )
    for _, row in results.iterrows():
        print(
            f"{row['outcome']:<36s}{row['role']:<16s}"
            f"{row['p_value']:>10.4f}{format_p(row['p_adjusted']):>12s}  "
            f"{row['verdict']}"
        )
    print()

    print("Mean difference (medicine minus placebo)")
    print("-" * 78)
    for _, row in results.iterrows():
        print(f"{row['outcome']:<36s}{row['mean_difference']:>10.2f}")
    print()


def main():
    frame = load_data()
    summary = summarise_outcomes(frame)
    results = apply_primary_adjustment(test_outcomes(frame))
    print_report(frame, summary, results)
    return frame, summary, results


if __name__ == "__main__":
    main()
