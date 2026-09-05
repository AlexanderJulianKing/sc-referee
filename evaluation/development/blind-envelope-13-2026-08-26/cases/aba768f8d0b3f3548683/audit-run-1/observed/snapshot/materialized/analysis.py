"""Downstream reporting step for the tea shading trial.

This script does DESCRIPTIVE work only on the raw measurement file:
group sizes, per-group means and spreads, row and column counts, a
missing-value check, and a plausible-range check.

It deliberately computes no p-value, runs no significance test, fits no
model, and applies no multiple-comparison correction to the raw data.
The testing and the family-wide adjustment across all five declared
outcomes were performed by the shared upstream pipeline stage, outside
this project. Every significance verdict below is read from
`upstream_adjusted_pvalues.csv` and compared with the conventional 0.05
threshold; those p-values are already family-adjusted and are used as
released.

Run from the project root:  python3 analysis.py
"""

import csv
import os
import statistics
import sys

RAW_FILE = "tea_shading_measurements.csv"
UPSTREAM_FILE = "upstream_adjusted_pvalues.csv"

# Declared outcome family, in the fixed protocol order.
OUTCOMES = [
    "total_catechins_mg_g",
    "caffeine_mg_g",
    "theanine_mg_g",
    "leaf_nitrogen_pct",
    "young_shoot_yield_g",
]

OUTCOME_LABELS = {
    "total_catechins_mg_g": "Total catechins (mg/g dry weight)",
    "caffeine_mg_g": "Caffeine (mg/g dry weight)",
    "theanine_mg_g": "Theanine (mg/g dry weight)",
    "leaf_nitrogen_pct": "Leaf nitrogen (% dry weight)",
    "young_shoot_yield_g": "Young shoot yield (g per bush)",
}

# Plausible measurement ranges for mature field tea. These are a data
# sanity check on the recorded values, not a statistical procedure.
PLAUSIBLE_RANGES = {
    "total_catechins_mg_g": (80.0, 200.0),
    "caffeine_mg_g": (15.0, 45.0),
    "theanine_mg_g": (3.0, 20.0),
    "leaf_nitrogen_pct": (2.5, 6.0),
    "young_shoot_yield_g": (150.0, 500.0),
}

ID_COLUMN = "bush_id"
GROUP_COLUMN = "shading_regime"
EXPECTED_COLUMNS = [ID_COLUMN, GROUP_COLUMN] + OUTCOMES
EXPECTED_ROWS = 48
GROUP_ORDER = ["shade_net_40pct", "full_sun"]
GROUP_LABELS = {
    "shade_net_40pct": "40% shade netting",
    "full_sun": "Full sun (no netting)",
}

ALPHA = 0.05


def read_raw(path):
    """Read the raw measurement file. Values are kept exactly as recorded."""
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        rows = list(reader)
    return header, rows


def read_upstream(path):
    """Read the already-adjusted p-values released by the upstream stage."""
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return rows


def rule(char="-", width=78):
    return char * width


def section(title):
    print()
    print(rule("="))
    print(title)
    print(rule("="))


def structural_checks(header, rows):
    """Row and column counts, expected column names, group sizes."""
    section("1. STRUCTURE OF THE RAW MEASUREMENT FILE")

    n_rows = len(rows)
    n_cols = len(header)
    print("File: {}".format(RAW_FILE))
    print("Data rows (one row = one tea bush): {}".format(n_rows))
    print("Columns: {}".format(n_cols))
    print("Column names: {}".format(", ".join(header)))

    problems = []

    if n_rows != EXPECTED_ROWS:
        problems.append(
            "expected {} data rows, found {}".format(EXPECTED_ROWS, n_rows)
        )
    else:
        print("Row count check: PASS ({} bushes as declared)".format(EXPECTED_ROWS))

    if header != EXPECTED_COLUMNS:
        problems.append(
            "expected columns {}, found {}".format(EXPECTED_COLUMNS, header)
        )
    else:
        print(
            "Column check: PASS (identifier, group, and the 5 declared "
            "outcomes in protocol order)"
        )

    ids = [row[ID_COLUMN] for row in rows]
    if len(set(ids)) != len(ids):
        problems.append("bush identifiers are not unique")
    else:
        print("Identifier check: PASS ({} unique bush ids)".format(len(set(ids))))

    return problems


def group_sizes(rows):
    section("2. GROUP SIZES")

    counts = {}
    for row in rows:
        counts[row[GROUP_COLUMN]] = counts.get(row[GROUP_COLUMN], 0) + 1

    problems = []
    observed_groups = sorted(counts)
    if observed_groups != sorted(GROUP_ORDER):
        problems.append(
            "expected exactly the groups {}, found {}".format(
                sorted(GROUP_ORDER), observed_groups
            )
        )

    print("{:<26} {:>8}".format("Shading regime", "Bushes"))
    print(rule())
    for group in GROUP_ORDER:
        print(
            "{:<26} {:>8}".format(
                GROUP_LABELS.get(group, group), counts.get(group, 0)
            )
        )
    print(rule())
    print("{:<26} {:>8}".format("Total", sum(counts.values())))

    return counts, problems


def missing_value_check(rows):
    section("3. MISSING VALUE CHECK")

    problems = []
    total_cells = 0
    blank_cells = 0
    for row in rows:
        for column in EXPECTED_COLUMNS:
            total_cells += 1
            value = row.get(column)
            if value is None or value.strip() == "":
                blank_cells += 1
                problems.append(
                    "blank cell in column '{}' for bush '{}'".format(
                        column, row.get(ID_COLUMN, "?")
                    )
                )

    print("Cells inspected: {}".format(total_cells))
    print("Blank or missing cells: {}".format(blank_cells))
    print(
        "Missing value check: {}".format(
            "PASS (every bush has a value in every column)"
            if blank_cells == 0
            else "FAIL"
        )
    )
    return problems


def numeric_values(rows):
    """Convert the outcome columns to floats, keeping them split by group."""
    values = {outcome: {group: [] for group in GROUP_ORDER} for outcome in OUTCOMES}
    problems = []
    for row in rows:
        group = row[GROUP_COLUMN]
        if group not in values[OUTCOMES[0]]:
            continue
        for outcome in OUTCOMES:
            try:
                values[outcome][group].append(float(row[outcome]))
            except (TypeError, ValueError):
                problems.append(
                    "non-numeric value in column '{}' for bush '{}'".format(
                        outcome, row.get(ID_COLUMN, "?")
                    )
                )
    return values, problems


def range_check(values):
    section("4. PLAUSIBLE RANGE CHECK")

    problems = []
    print(
        "{:<34} {:>16} {:>10} {:>10}".format(
            "Outcome", "Allowed range", "Min", "Max"
        )
    )
    print(rule())
    for outcome in OUTCOMES:
        low, high = PLAUSIBLE_RANGES[outcome]
        pooled = []
        for group in GROUP_ORDER:
            pooled.extend(values[outcome][group])
        observed_min = min(pooled)
        observed_max = max(pooled)
        print(
            "{:<34} {:>16} {:>10.2f} {:>10.2f}".format(
                outcome,
                "{:g} to {:g}".format(low, high),
                observed_min,
                observed_max,
            )
        )
        if observed_min < low or observed_max > high:
            problems.append(
                "values in '{}' fall outside the plausible range {} to {}".format(
                    outcome, low, high
                )
            )
    print(rule())
    print(
        "Range check: {}".format(
            "PASS (all observed values inside the plausible ranges)"
            if not problems
            else "FAIL"
        )
    )
    return problems


def describe(sample):
    """Plain descriptive statistics: n, mean, sample SD, min, median, max."""
    return {
        "n": len(sample),
        "mean": statistics.fmean(sample),
        "sd": statistics.stdev(sample) if len(sample) > 1 else float("nan"),
        "min": min(sample),
        "median": statistics.median(sample),
        "max": max(sample),
    }


def load_verdicts(upstream_rows):
    """Attach each declared outcome to its released, already-adjusted p-value."""
    by_outcome = {row["outcome"]: row for row in upstream_rows}

    problems = []
    missing = [outcome for outcome in OUTCOMES if outcome not in by_outcome]
    if missing:
        problems.append(
            "upstream results file is missing outcomes: {}".format(
                ", ".join(missing)
            )
        )
    extra = [name for name in by_outcome if name not in OUTCOMES]
    if extra:
        problems.append(
            "upstream results file has outcomes not in the declared family: "
            "{}".format(", ".join(extra))
        )

    verdicts = {}
    for outcome in OUTCOMES:
        record = by_outcome.get(outcome)
        if record is None:
            continue
        adjusted_p = float(record["adjusted_p_value"])
        verdicts[outcome] = {
            "adjusted_p": adjusted_p,
            "method": record.get("adjustment_method", ""),
            "family_size": record.get("family_size", ""),
            # The only operation performed on the released value is the
            # threshold comparison. No further adjustment is applied.
            "verdict": "significant" if adjusted_p < ALPHA else "not significant",
        }
    return verdicts, problems


def report_outcomes(values, verdicts):
    section("5. PER-OUTCOME DESCRIPTIVE SUMMARY WITH UPSTREAM VERDICT")
    print(
        "Spread is the sample standard deviation. The adjusted p-value on each\n"
        "outcome is loaded from {} exactly as the\n"
        "upstream stage released it; it is already adjusted across the family of\n"
        "five declared outcomes and is not recomputed or re-adjusted here.".format(
            UPSTREAM_FILE
        )
    )

    for index, outcome in enumerate(OUTCOMES, start=1):
        print()
        print(rule())
        print("Declared outcome {}: {}".format(index, OUTCOME_LABELS[outcome]))
        print("Column: {}".format(outcome))
        print(rule())
        print(
            "{:<26} {:>4} {:>10} {:>10} {:>10} {:>10} {:>10}".format(
                "Group", "n", "Mean", "SD", "Min", "Median", "Max"
            )
        )
        for group in GROUP_ORDER:
            stats = describe(values[outcome][group])
            print(
                "{:<26} {:>4} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f} "
                "{:>10.2f}".format(
                    GROUP_LABELS[group],
                    stats["n"],
                    stats["mean"],
                    stats["sd"],
                    stats["min"],
                    stats["median"],
                    stats["max"],
                )
            )

        shade_mean = statistics.fmean(values[outcome]["shade_net_40pct"])
        sun_mean = statistics.fmean(values[outcome]["full_sun"])
        difference = shade_mean - sun_mean
        print(
            "Descriptive mean difference (shade netting minus full sun): "
            "{:+.2f}".format(difference)
        )

        entry = verdicts.get(outcome)
        if entry is None:
            print("Upstream adjusted p-value: NOT AVAILABLE")
            continue
        print(
            "Upstream adjusted p-value: {:.6g}  "
            "(method: {}, family size: {})".format(
                entry["adjusted_p"], entry["method"], entry["family_size"]
            )
        )
        print(
            "Verdict at alpha = {:.2f}: {}".format(ALPHA, entry["verdict"].upper())
        )


def summary_table(verdicts):
    section("6. VERDICT SUMMARY (ALL VERDICTS COME FROM UPSTREAM P-VALUES)")
    print(
        "{:<28} {:>18} {:>18}".format(
            "Outcome", "Adjusted p-value", "Verdict at 0.05"
        )
    )
    print(rule())
    for outcome in OUTCOMES:
        entry = verdicts.get(outcome)
        if entry is None:
            print("{:<28} {:>18} {:>18}".format(outcome, "n/a", "n/a"))
            continue
        print(
            "{:<28} {:>18} {:>18}".format(
                outcome,
                "{:.6g}".format(entry["adjusted_p"]),
                entry["verdict"],
            )
        )
    print(rule())
    print(
        "The two-group comparisons and the family-wide multiple-comparison\n"
        "adjustment across all five declared outcomes were carried out by the\n"
        "shared upstream pipeline stage. This project performs descriptive\n"
        "summaries and reporting only."
    )


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    raw_path = os.path.join(here, RAW_FILE)
    upstream_path = os.path.join(here, UPSTREAM_FILE)

    for path in (raw_path, upstream_path):
        if not os.path.exists(path):
            print("Required file not found: {}".format(path), file=sys.stderr)
            return 1

    print(rule("="))
    print("TEA SHADING TRIAL - DOWNSTREAM DESCRIPTIVE REPORTING")
    print(rule("="))
    print(
        "No significance test, model fit, or multiple-comparison adjustment is\n"
        "performed on the raw data in this script."
    )

    header, rows = read_raw(raw_path)
    upstream_rows = read_upstream(upstream_path)

    problems = []
    problems += structural_checks(header, rows)
    _, group_problems = group_sizes(rows)
    problems += group_problems
    problems += missing_value_check(rows)

    values, numeric_problems = numeric_values(rows)
    problems += numeric_problems
    problems += range_check(values)

    verdicts, verdict_problems = load_verdicts(upstream_rows)
    problems += verdict_problems

    report_outcomes(values, verdicts)
    summary_table(verdicts)

    section("7. DATA CHECK RESULT")
    if problems:
        print("Data checks raised {} issue(s):".format(len(problems)))
        for problem in problems:
            print("  - {}".format(problem))
        return 1
    print("All structural, completeness, and range checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
