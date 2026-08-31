"""Vanilla pod curing study: descriptive summaries, data checks, and loaded verdicts.

This script performs NO statistical testing and computes NO p-value. The family-wise
adjustment across the five declared outcomes was carried out by the upstream laboratory
pipeline stage that wrote `adjusted_pvalues.csv`. Here we only:

  1. read the raw pod-level CSV and produce per-group descriptive summaries and routine
     data checks;
  2. read the already-adjusted p-values and report, for each declared outcome, the group
     means, the loaded adjusted p-value, and its significant / not-significant verdict at
     the conventional 0.05 threshold.
"""

import csv
import statistics
import sys

RAW_CSV = "vanilla_curing_pods.csv"
ADJUSTED_CSV = "adjusted_pvalues.csv"

ID_COLUMN = "pod_id"
GROUP_COLUMN = "curing_method"

# Declared outcome family, in the order fixed in the study plan before curing began.
OUTCOMES = [
    "vanillin_g_per_100g",
    "moisture_pct",
    "p_hydroxybenzaldehyde_mg_per_100g",
    "bend_force_n",
    "surface_lightness_l_star",
]

# Expected groups and sizes.
GROUPS = ["traditional", "oven_assisted"]
EXPECTED_GROUP_SIZE = 36

# Physically sensible ranges for each outcome (inclusive bounds).
PLAUSIBLE_RANGES = {
    "vanillin_g_per_100g": (0.0, 10.0),
    "moisture_pct": (0.0, 100.0),
    "p_hydroxybenzaldehyde_mg_per_100g": (0.0, 1000.0),
    "bend_force_n": (0.0, 50.0),
    "surface_lightness_l_star": (0.0, 100.0),
}

ALPHA = 0.05


def read_raw(path):
    """Read the raw pod-level CSV into a list of dicts, keeping cells as read."""
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames
        rows = list(reader)
    return header, rows


def read_adjusted(path):
    """Read the upstream pipeline's adjusted p-value file, in file order."""
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    return [(row["outcome"], float(row["adjusted_p_value"])) for row in rows]


def run_checks(header, rows):
    """Routine data checks. Returns a list of (check description, passed, detail)."""
    checks = []

    expected_header = [ID_COLUMN, GROUP_COLUMN] + OUTCOMES
    checks.append(
        (
            "raw CSV header matches the declared column layout",
            header == expected_header,
            "found: " + ", ".join(header),
        )
    )

    checks.append(
        (
            "total pod count is %d" % (len(GROUPS) * EXPECTED_GROUP_SIZE),
            len(rows) == len(GROUPS) * EXPECTED_GROUP_SIZE,
            "found %d rows" % len(rows),
        )
    )

    pod_ids = [row[ID_COLUMN] for row in rows]
    checks.append(
        (
            "pod identifiers are unique",
            len(set(pod_ids)) == len(pod_ids),
            "%d unique of %d" % (len(set(pod_ids)), len(pod_ids)),
        )
    )

    observed_groups = sorted(set(row[GROUP_COLUMN] for row in rows))
    checks.append(
        (
            "exactly the two expected curing methods are present",
            observed_groups == sorted(GROUPS),
            "found: " + ", ".join(observed_groups),
        )
    )

    for group in GROUPS:
        count = sum(1 for row in rows if row[GROUP_COLUMN] == group)
        checks.append(
            (
                "group '%s' has %d pods" % (group, EXPECTED_GROUP_SIZE),
                count == EXPECTED_GROUP_SIZE,
                "found %d" % count,
            )
        )

    missing = []
    for row in rows:
        for column in expected_header:
            value = row.get(column)
            if value is None or value.strip() == "":
                missing.append("%s / %s" % (row.get(ID_COLUMN, "?"), column))
    checks.append(
        (
            "no missing cells anywhere in the raw file",
            not missing,
            "missing: " + (", ".join(missing) if missing else "none"),
        )
    )

    non_numeric = []
    out_of_range = []
    for row in rows:
        for outcome in OUTCOMES:
            try:
                value = float(row[outcome])
            except (TypeError, ValueError):
                non_numeric.append("%s / %s" % (row[ID_COLUMN], outcome))
                continue
            low, high = PLAUSIBLE_RANGES[outcome]
            if not (low <= value <= high):
                out_of_range.append(
                    "%s / %s = %s" % (row[ID_COLUMN], outcome, row[outcome])
                )
    checks.append(
        (
            "every outcome cell parses as a number",
            not non_numeric,
            "non-numeric: " + (", ".join(non_numeric) if non_numeric else "none"),
        )
    )
    checks.append(
        (
            "every outcome value sits inside its physically sensible range",
            not out_of_range,
            "out of range: " + (", ".join(out_of_range) if out_of_range else "none"),
        )
    )

    return checks


def summarise(rows):
    """Per group and per outcome: n, mean, standard deviation, minimum, maximum."""
    summary = {}
    for group in GROUPS:
        group_rows = [row for row in rows if row[GROUP_COLUMN] == group]
        summary[group] = {}
        for outcome in OUTCOMES:
            values = [float(row[outcome]) for row in group_rows]
            summary[group][outcome] = {
                "n": len(values),
                "mean": statistics.mean(values),
                "sd": statistics.stdev(values) if len(values) > 1 else float("nan"),
                "min": min(values),
                "max": max(values),
            }
    return summary


def main():
    header, rows = read_raw(RAW_CSV)

    print("=" * 78)
    print("VANILLA POD CURING STUDY - DESCRIPTIVE SUMMARY AND DATA CHECKS")
    print("=" * 78)
    print("Raw data file      : %s (%d pods)" % (RAW_CSV, len(rows)))
    print("Adjusted p-values  : %s (written by the upstream pipeline stage)" % ADJUSTED_CSV)
    print("This script runs no statistical test and computes no p-value.")
    print()

    print("-" * 78)
    print("DATA CHECKS")
    print("-" * 78)
    checks = run_checks(header, rows)
    for description, passed, detail in checks:
        print("[%s] %s" % ("PASS" if passed else "FAIL", description))
        if not passed:
            print("        %s" % detail)
    failed = [c for c in checks if not c[1]]
    print()
    print("%d of %d checks passed." % (len(checks) - len(failed), len(checks)))
    print()

    if failed:
        print("Data checks failed; stopping before the summary.")
        return 1

    summary = summarise(rows)

    print("-" * 78)
    print("DESCRIPTIVE SUMMARIES BY GROUP AND OUTCOME")
    print("-" * 78)
    print(
        "%-34s %-14s %3s %10s %9s %9s %9s"
        % ("outcome", "group", "n", "mean", "sd", "min", "max")
    )
    for outcome in OUTCOMES:
        for group in GROUPS:
            stats = summary[group][outcome]
            print(
                "%-34s %-14s %3d %10.3f %9.3f %9.2f %9.2f"
                % (
                    outcome,
                    group,
                    stats["n"],
                    stats["mean"],
                    stats["sd"],
                    stats["min"],
                    stats["max"],
                )
            )
    print()

    adjusted = read_adjusted(ADJUSTED_CSV)
    adjusted_names = [name for name, _ in adjusted]
    if adjusted_names != OUTCOMES:
        print("Adjusted p-value file does not match the declared outcome family.")
        print("  expected: " + ", ".join(OUTCOMES))
        print("  found   : " + ", ".join(adjusted_names))
        return 1
    adjusted_lookup = dict(adjusted)

    print("-" * 78)
    print("VERDICTS FROM THE UPSTREAM-ADJUSTED P-VALUES (threshold %.2f)" % ALPHA)
    print("-" * 78)
    print(
        "The five outcomes were declared as one family. The family-wise adjustment across"
    )
    print(
        "all five was performed by the pipeline stage that wrote %s;" % ADJUSTED_CSV
    )
    print("the values below are read from that file, not recomputed here.")
    print()
    for outcome in OUTCOMES:
        adjusted_p = adjusted_lookup[outcome]
        verdict = "significant" if adjusted_p < ALPHA else "not significant"
        print(outcome)
        print(
            "    mean, traditional   : %.3f" % summary["traditional"][outcome]["mean"]
        )
        print(
            "    mean, oven_assisted : %.3f" % summary["oven_assisted"][outcome]["mean"]
        )
        print(
            "    difference (oven - traditional): %+.3f"
            % (
                summary["oven_assisted"][outcome]["mean"]
                - summary["traditional"][outcome]["mean"]
            )
        )
        print("    adjusted p-value    : %s" % format_p(adjusted_p))
        print("    verdict             : %s at the %.2f level" % (verdict, ALPHA))
        print()

    return 0


def format_p(value):
    """Print an adjusted p-value the way the upstream file carries it."""
    if value < 0.001:
        return "%.3g" % value
    return "%.4f" % value


if __name__ == "__main__":
    sys.exit(main())
