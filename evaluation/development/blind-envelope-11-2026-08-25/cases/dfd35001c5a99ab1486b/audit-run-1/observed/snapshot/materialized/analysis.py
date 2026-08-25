"""Badger landscape study: analysis of five declared outcomes.

Reads badger_landscape_data.csv, summarises each declared outcome by landscape
group, and compares the two landscapes for each outcome with a standard
two-sample t-test against the conventional 0.05 threshold.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "badger_landscape_data.csv"

GROUP_COLUMN = "landscape_type"
GROUP_LEVELS = ("pasture", "arable")

# The five outcomes declared in the study plan, in the declared order.
DECLARED_OUTCOMES = [
    ("mean_nightly_distance_km", "Mean nightly distance travelled (km)"),
    ("home_range_95_kernel_ha", "Home range, 95% kernel (ha)"),
    ("body_condition_index", "Body condition index (unitless)"),
    ("mean_time_active_hours", "Mean time active per night (h)"),
    ("faecal_cortisol_ng_per_g", "Faecal cortisol metabolites (ng/g)"),
]

ALPHA = 0.05


def load_data(path=DATA_FILE):
    """Read the study data file and check its basic shape."""
    frame = pd.read_csv(path)

    missing = [
        column
        for column, _ in DECLARED_OUTCOMES
        if column not in frame.columns
    ]
    if missing:
        raise ValueError(f"data file is missing declared outcome columns: {missing}")
    if GROUP_COLUMN not in frame.columns:
        raise ValueError(f"data file is missing the group column {GROUP_COLUMN!r}")

    levels = tuple(sorted(frame[GROUP_COLUMN].unique()))
    if levels != tuple(sorted(GROUP_LEVELS)):
        raise ValueError(f"unexpected landscape levels: {levels}")

    return frame


def group_counts(frame):
    """Number of animals in each landscape group."""
    return {level: int((frame[GROUP_COLUMN] == level).sum()) for level in GROUP_LEVELS}


def group_summary(frame, column):
    """Per-group count, mean and spread (sample standard deviation)."""
    summary = {}
    for level in GROUP_LEVELS:
        values = frame.loc[frame[GROUP_COLUMN] == level, column].astype(float)
        summary[level] = {
            "n": int(values.count()),
            "mean": float(values.mean()),
            "sd": float(values.std(ddof=1)),
        }
    return summary


def compare_declared_outcomes(frame, outcomes, alpha=ALPHA):
    """Run the landscape comparison for every declared outcome.

    Takes the study data and the declared outcome list, performs one
    two-sample t-test per outcome, and hands back all of the collected
    results together as a list of dictionaries in the declared order.
    """
    results = []
    for order, (column, label) in enumerate(outcomes, start=1):
        pasture = frame.loc[frame[GROUP_COLUMN] == "pasture", column].astype(float)
        arable = frame.loc[frame[GROUP_COLUMN] == "arable", column].astype(float)

        t_statistic, p_value = stats.ttest_ind(pasture, arable, equal_var=True)

        results.append(
            {
                "order": order,
                "column": column,
                "label": label,
                "summary": group_summary(frame, column),
                "t": float(t_statistic),
                "p": float(p_value),
                "significant": bool(p_value < alpha),
            }
        )
    return results


def main():
    frame = load_data()

    print("Badger landscape study")
    print("=" * 62)
    print(f"Data file: {DATA_FILE.name}")
    print(f"Animals in file: {len(frame)}")

    counts = group_counts(frame)
    print("\nAnimals per landscape group")
    print("-" * 62)
    for level in GROUP_LEVELS:
        print(f"  {level:<10s} n = {counts[level]}")

    results = compare_declared_outcomes(frame, DECLARED_OUTCOMES)

    print("\nPer-group summaries (mean +/- SD)")
    print("-" * 62)
    for result in results:
        print(f"\nOutcome {result['order']}: {result['label']}")
        for level in GROUP_LEVELS:
            cell = result["summary"][level]
            print(
                f"  {level:<10s} n = {cell['n']:>2d}   "
                f"mean = {cell['mean']:.3f}   SD = {cell['sd']:.3f}"
            )

    print("\nTwo-sample t-tests, pasture vs arable (alpha = %.2f)" % ALPHA)
    print("-" * 62)
    for result in results:
        verdict = "SIGNIFICANT" if result["significant"] else "not significant"
        print(
            f"  Outcome {result['order']}: {result['label']}\n"
            f"      t = {result['t']:+.3f}   p = {result['p']:.4f}   -> {verdict}"
        )

    print("\nVerdicts in declared order")
    print("-" * 62)
    for result in results:
        direction = "differ" if result["significant"] else "do not differ"
        print(
            f"  {result['order']}. {result['column']}: the two landscapes "
            f"{direction} significantly (p = {result['p']:.4f})."
        )


if __name__ == "__main__":
    main()
