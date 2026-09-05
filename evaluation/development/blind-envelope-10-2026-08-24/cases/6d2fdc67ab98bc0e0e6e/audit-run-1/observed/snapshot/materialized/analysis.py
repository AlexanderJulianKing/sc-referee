"""Descriptive analysis for the mid-lactation mineral supplement comparison.

This script does not run any significance test. It loads the subject-level table,
reports per-group counts, means and standard deviations for the five declared
outcomes, runs routine data quality checks, and then reads the upstream pipeline
results table. Every significance verdict is taken from the adjusted p-values
already written by the upstream stage, judged at alpha = 0.05. The upstream stage
adjusted all five declared outcomes together as one family, so no further
multiplicity adjustment is applied here.

Run from the project root:

    python analysis.py
"""

from pathlib import Path

import pandas as pd

SUBJECT_CSV = Path(__file__).resolve().parent / "camel_milk_outcomes.csv"
PIPELINE_CSV = Path(__file__).resolve().parent / "pipeline_family_results.csv"

ALPHA = 0.05

# The five outcomes in the order declared in the protocol.
OUTCOMES = [
    "milk_yield_l_per_day",
    "milk_fat_pct",
    "milk_protein_pct",
    "body_condition_score",
    "plasma_glucose_mmol_l",
]

OUTCOME_LABELS = {
    "milk_yield_l_per_day": "Daily milk yield (L/day)",
    "milk_fat_pct": "Milk fat (%)",
    "milk_protein_pct": "Milk protein (%)",
    "body_condition_score": "Body condition score (1-5)",
    "plasma_glucose_mmol_l": "Plasma glucose (mmol/L)",
}

# Plausible measurement ranges declared in the protocol, used for range checks only.
PLAUSIBLE_RANGES = {
    "milk_yield_l_per_day": (3.0, 12.0),
    "milk_fat_pct": (2.0, 4.5),
    "milk_protein_pct": (2.5, 4.0),
    "body_condition_score": (1.0, 5.0),
    "plasma_glucose_mmol_l": (3.5, 7.5),
}

GROUPS = ["mineral_standard", "mineral_enriched"]

EXPECTED_SUBJECT_COLUMNS = ["camel_id", "supplement_group"] + OUTCOMES
EXPECTED_ROWS = 96
EXPECTED_GROUP_SIZE = 48
FAMILY_SIZE = 5


def load_subject_table() -> pd.DataFrame:
    return pd.read_csv(SUBJECT_CSV)


def load_pipeline_table() -> pd.DataFrame:
    return pd.read_csv(PIPELINE_CSV)


def data_quality_checks(subjects: pd.DataFrame) -> list[tuple[str, bool, str]]:
    """Return a list of (check name, passed, detail) tuples. No inference here."""
    checks: list[tuple[str, bool, str]] = []

    n_rows = len(subjects)
    checks.append(
        (
            "Row count",
            n_rows == EXPECTED_ROWS,
            f"{n_rows} rows found, {EXPECTED_ROWS} expected",
        )
    )

    columns_ok = list(subjects.columns) == EXPECTED_SUBJECT_COLUMNS
    checks.append(
        (
            "Column names and order",
            columns_ok,
            "match the declared schema" if columns_ok else f"found {list(subjects.columns)}",
        )
    )

    n_ids = subjects["camel_id"].nunique()
    checks.append(
        (
            "Unique camel_id",
            n_ids == n_rows,
            f"{n_ids} distinct identifiers across {n_rows} rows",
        )
    )

    observed_groups = sorted(subjects["supplement_group"].unique())
    checks.append(
        (
            "Group labels",
            observed_groups == sorted(GROUPS),
            f"observed {observed_groups}",
        )
    )

    for group in GROUPS:
        size = int((subjects["supplement_group"] == group).sum())
        checks.append(
            (
                f"Group size: {group}",
                size == EXPECTED_GROUP_SIZE,
                f"{size} dams, {EXPECTED_GROUP_SIZE} expected",
            )
        )

    total_missing = int(subjects.isna().sum().sum())
    checks.append(
        (
            "Missing values",
            total_missing == 0,
            f"{total_missing} empty cells across all columns",
        )
    )

    for outcome in OUTCOMES:
        low, high = PLAUSIBLE_RANGES[outcome]
        values = subjects[outcome]
        n_out = int(((values < low) | (values > high)).sum())
        checks.append(
            (
                f"Range check: {outcome}",
                n_out == 0,
                f"observed {values.min():.2f} to {values.max():.2f}, "
                f"plausible range {low:.2f} to {high:.2f}, {n_out} outside",
            )
        )

    return checks


def pipeline_checks(pipeline: pd.DataFrame) -> list[tuple[str, bool, str]]:
    """Structural checks on the handed-over results table. No re-testing."""
    checks: list[tuple[str, bool, str]] = []

    n_rows = len(pipeline)
    checks.append(
        (
            "Pipeline row count",
            n_rows == FAMILY_SIZE,
            f"{n_rows} rows found, {FAMILY_SIZE} expected (one per declared outcome)",
        )
    )

    order_ok = list(pipeline["outcome_name"]) == OUTCOMES
    checks.append(
        (
            "Declared order preserved",
            order_ok,
            "rows follow the protocol's declared order"
            if order_ok
            else f"found {list(pipeline['outcome_name'])}",
        )
    )

    missing = int(pipeline.isna().sum().sum())
    checks.append(
        ("Pipeline missing values", missing == 0, f"{missing} empty cells"),
    )

    in_unit = bool(
        pipeline["raw_p_value"].between(0.0, 1.0).all()
        and pipeline["adjusted_p_value"].between(0.0, 1.0).all()
    )
    checks.append(
        ("P-values within [0, 1]", in_unit, "all raw and adjusted values in range"),
    )

    not_smaller = bool((pipeline["adjusted_p_value"] >= pipeline["raw_p_value"]).all())
    checks.append(
        (
            "Adjusted at least as large as raw",
            not_smaller,
            "adjusted p-value never below its raw p-value",
        )
    )

    return checks


def group_summary(subjects: pd.DataFrame) -> pd.DataFrame:
    """Count, mean and sample standard deviation per group for each outcome."""
    rows = []
    for outcome in OUTCOMES:
        for group in GROUPS:
            values = subjects.loc[subjects["supplement_group"] == group, outcome]
            rows.append(
                {
                    "outcome": outcome,
                    "supplement_group": group,
                    "n": int(values.count()),
                    "mean": float(values.mean()),
                    "sd": float(values.std(ddof=1)),
                }
            )
    return pd.DataFrame(rows)


def mean_differences(summary: pd.DataFrame) -> pd.DataFrame:
    """Descriptive enriched-minus-standard difference in group means.

    This is a plain difference of two reported means. It is not a test statistic
    and carries no p-value, confidence interval or verdict.
    """
    rows = []
    for outcome in OUTCOMES:
        block = summary[summary["outcome"] == outcome].set_index("supplement_group")
        rows.append(
            {
                "outcome": outcome,
                "mean_difference": float(
                    block.loc["mineral_enriched", "mean"]
                    - block.loc["mineral_standard", "mean"]
                ),
            }
        )
    return pd.DataFrame(rows)


def verdicts(pipeline: pd.DataFrame) -> pd.DataFrame:
    """Verdicts read off the upstream adjusted p-values at alpha = 0.05."""
    out = pipeline.copy()
    out["verdict"] = [
        "significant" if p < ALPHA else "not significant"
        for p in out["adjusted_p_value"]
    ]
    return out


def print_checks(title: str, checks: list[tuple[str, bool, str]]) -> None:
    print(title)
    print("-" * len(title))
    for name, passed, detail in checks:
        flag = "PASS" if passed else "FAIL"
        print(f"  [{flag}] {name}: {detail}")
    print()


def main() -> None:
    subjects = load_subject_table()
    pipeline = load_pipeline_table()

    print("Camel dairy mineral supplement comparison: descriptive analysis")
    print("=" * 62)
    print()
    print(f"Subject table:  {SUBJECT_CSV.name} ({len(subjects)} dams)")
    print(f"Pipeline table: {PIPELINE_CSV.name} ({len(pipeline)} declared outcomes)")
    print()

    print_checks("Data quality checks: subject table", data_quality_checks(subjects))
    print_checks("Structural checks: pipeline results table", pipeline_checks(pipeline))

    print("Descriptive summaries by group (mean, sample SD)")
    print("-" * 47)
    summary = group_summary(subjects)
    for outcome in OUTCOMES:
        print(f"  {OUTCOME_LABELS[outcome]}  [{outcome}]")
        block = summary[summary["outcome"] == outcome]
        for _, row in block.iterrows():
            print(
                f"    {row['supplement_group']:<18} "
                f"n = {int(row['n']):>2}   "
                f"mean = {row['mean']:.3f}   "
                f"SD = {row['sd']:.3f}"
            )
    print()

    print("Descriptive difference in group means (enriched minus standard)")
    print("-" * 62)
    print("Plain difference of the two means above; not a test statistic.")
    for _, row in mean_differences(summary).iterrows():
        print(f"  {row['outcome']:<24}{row['mean_difference']:>+9.3f}")
    print()

    print("Declared family of five: p-values as handed over by the upstream pipeline")
    print("-" * 72)
    print(
        "Multiplicity adjustment for all five declared outcomes was performed upstream."
    )
    print("No test is computed here; verdicts read the adjusted column at "
          f"alpha = {ALPHA}.")
    print()
    print(f"  {'outcome_name':<24}{'raw_p':>10}{'adjusted_p':>13}   verdict")
    results = verdicts(pipeline)
    for _, row in results.iterrows():
        print(
            f"  {row['outcome_name']:<24}"
            f"{row['raw_p_value']:>10.6f}"
            f"{row['adjusted_p_value']:>13.6f}   {row['verdict']}"
        )
    print()

    n_sig = int((results["verdict"] == "significant").sum())
    sig_names = list(results.loc[results["verdict"] == "significant", "outcome_name"])
    print(
        f"Outcomes significant at adjusted p < {ALPHA}: {n_sig} of {FAMILY_SIZE}"
        + (f" ({', '.join(sig_names)})" if sig_names else "")
    )


if __name__ == "__main__":
    main()
