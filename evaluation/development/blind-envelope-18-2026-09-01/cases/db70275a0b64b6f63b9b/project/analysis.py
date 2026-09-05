"""Descriptive analysis of the rapeseed oil batch comparison.

This script reads the two authored data files that sit beside it:

  * ``data.csv``             - 72 production batches, one row per batch.
  * ``adjusted_pvalues.csv`` - the adjusted p-value the upstream pipeline
                               stage exported for each declared outcome.

The script summarises the raw file descriptively and runs routine data
checks only. It performs no significance test and computes no p-value of
its own. Every verdict reported below is read from ``adjusted_pvalues.csv``
and judged at the conventional 0.05 level.

Run with no arguments from the project root:  python3 analysis.py
"""

import csv
import statistics
import sys

DATA_FILE = "data.csv"
ADJUSTED_P_FILE = "adjusted_pvalues.csv"

ID_COLUMN = "batch_id"
GROUP_COLUMN = "region"
EXPECTED_GROUPS = ("lowland", "upland")

ALPHA = 0.05

# The six outcomes declared in advance by the quality plan, in the declared
# order, with the plausible range the plan states for each one.
DECLARED_OUTCOMES = [
    ("peroxide_value_meq_o2_kg", "Peroxide value (meq O2/kg)", 0.7, 4.8),
    ("free_fatty_acids_pct", "Free fatty acids (% oleic acid)", 0.15, 1.25),
    ("total_tocopherols_mg_kg", "Total tocopherols (mg/kg)", 340.0, 780.0),
    ("oxidative_stability_index_h", "Oxidative stability index (h)", 3.5, 12.5),
    ("chlorophyll_pigments_mg_kg", "Chlorophyll pigments (mg/kg)", 4.0, 27.0),
    ("erucic_acid_pct", "Erucic acid (% total fatty acids)", 0.03, 0.95),
]

OUTCOME_NAMES = [name for name, _label, _low, _high in DECLARED_OUTCOMES]


def read_rows(path):
    """Read a CSV file into a list of dictionaries, preserving the header."""
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise SystemExit("ERROR: %s has no header row." % path)
        return list(reader), list(reader.fieldnames)


def rule(title):
    print("")
    print("=" * 72)
    print(title)
    print("=" * 72)


def check_columns(header):
    """Confirm the expected columns are present, in the declared order."""
    expected = [ID_COLUMN, GROUP_COLUMN] + OUTCOME_NAMES
    missing = [column for column in expected if column not in header]
    extra = [column for column in header if column not in expected]
    print("Expected columns : %d" % len(expected))
    print("Columns found    : %d" % len(header))
    print("Missing columns  : %s" % (", ".join(missing) if missing else "none"))
    print("Unexpected cols  : %s" % (", ".join(extra) if extra else "none"))
    order_ok = header == expected
    print("Declared order   : %s" % ("as declared" if order_ok else "DIFFERS"))
    if missing:
        raise SystemExit("ERROR: data.csv is missing declared columns.")
    return not missing and not extra and order_ok


def check_missing_values(rows, header):
    """Count blank cells anywhere in the raw file."""
    blanks = {}
    for row in rows:
        for column in header:
            value = row.get(column)
            if value is None or str(value).strip() == "":
                blanks[column] = blanks.get(column, 0) + 1
    if blanks:
        for column, count in blanks.items():
            print("Missing values   : %-28s %d" % (column, count))
    else:
        print("Missing values   : none in any column")
    return not blanks


def check_identifiers(rows):
    ids = [row[ID_COLUMN] for row in rows]
    unique = len(set(ids))
    print("Batch identifiers: %d rows, %d unique" % (len(ids), unique))
    return unique == len(ids)


def check_groups(rows):
    """Report the group sizes and confirm exactly the two expected labels."""
    counts = {}
    for row in rows:
        counts[row[GROUP_COLUMN]] = counts.get(row[GROUP_COLUMN], 0) + 1
    labels = sorted(counts)
    print("Group labels     : %s" % ", ".join(labels))
    for label in labels:
        print("Group size       : %-28s n = %d" % (label, counts[label]))
    ok = labels == sorted(EXPECTED_GROUPS)
    if not ok:
        print("Group labels     : DIFFER from the expected two values")
    return counts, ok


def to_float(value, column, batch_id):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise SystemExit(
            "ERROR: non-numeric value %r in column %s for batch %s."
            % (value, column, batch_id)
        )


def check_ranges(rows):
    """Flag any value falling outside the plausible range for its outcome."""
    all_ok = True
    for column, label, low, high in DECLARED_OUTCOMES:
        values = [to_float(row[column], column, row[ID_COLUMN]) for row in rows]
        outside = [v for v in values if v < low or v > high]
        status = "ok" if not outside else "%d OUTSIDE" % len(outside)
        print(
            "Range check      : %-28s observed %.3f to %.3f, "
            "plausible %.3f to %.3f  [%s]"
            % (column, min(values), max(values), low, high, status)
        )
        if outside:
            all_ok = False
    return all_ok


def group_summary(rows, column):
    """Mean and sample standard deviation of one outcome, by group."""
    summary = {}
    for label in EXPECTED_GROUPS:
        values = [
            to_float(row[column], column, row[ID_COLUMN])
            for row in rows
            if row[GROUP_COLUMN] == label
        ]
        summary[label] = {
            "n": len(values),
            "mean": statistics.mean(values) if values else float("nan"),
            "sd": statistics.stdev(values) if len(values) > 1 else float("nan"),
        }
    return summary


def read_adjusted_pvalues(path):
    """Load the upstream export; no p-value is computed in this project."""
    rows, header = read_rows(path)
    for column in ("outcome", "adjusted_p_value"):
        if column not in header:
            raise SystemExit("ERROR: %s is missing the %s column." % (path, column))
    adjusted = {}
    order = []
    for row in rows:
        name = row["outcome"].strip()
        try:
            adjusted[name] = float(row["adjusted_p_value"])
        except (TypeError, ValueError):
            raise SystemExit(
                "ERROR: non-numeric adjusted p-value %r for outcome %s."
                % (row["adjusted_p_value"], name)
            )
        order.append(name)
    missing = [name for name in OUTCOME_NAMES if name not in adjusted]
    if missing:
        raise SystemExit(
            "ERROR: %s has no adjusted p-value for: %s" % (path, ", ".join(missing))
        )
    if order != OUTCOME_NAMES:
        print("NOTE: adjusted_pvalues.csv rows are not in the declared order.")
    return adjusted


def main():
    rows, header = read_rows(DATA_FILE)
    adjusted = read_adjusted_pvalues(ADJUSTED_P_FILE)

    rule("COLD-PRESSED RAPESEED OIL: LOWLAND VERSUS UPLAND GROWING REGION")
    print("Raw data file        : %s (%d data rows)" % (DATA_FILE, len(rows)))
    print("Adjusted p-values    : %s (%d outcomes)" % (ADJUSTED_P_FILE, len(adjusted)))
    print("Declared outcomes    : %d, judged at alpha = %.2f" % (len(DECLARED_OUTCOMES), ALPHA))
    print("Inference in script  : none; verdicts come from the upstream export")

    rule("ROUTINE DATA CHECKS ON data.csv")
    columns_ok = check_columns(header)
    identifiers_ok = check_identifiers(rows)
    complete = check_missing_values(rows, header)
    counts, groups_ok = check_groups(rows)
    ranges_ok = check_ranges(rows)
    checks_ok = columns_ok and identifiers_ok and complete and groups_ok and ranges_ok
    print("")
    print("All routine checks   : %s" % ("PASSED" if checks_ok else "SEE FLAGS ABOVE"))

    rule("DESCRIPTIVE SUMMARY AND ADJUSTED-P VERDICT, BY DECLARED OUTCOME")
    print(
        "%-30s %10s %10s %10s %10s %14s %s"
        % ("outcome", "lowland", "(sd)", "upland", "(sd)", "adjusted p", "verdict")
    )
    print("-" * 108)
    for column, label, _low, _high in DECLARED_OUTCOMES:
        summary = group_summary(rows, column)
        p_adjusted = adjusted[column]
        verdict = (
            "significant at 0.05"
            if p_adjusted < ALPHA
            else "not significant at 0.05"
        )
        print(
            "%-30s %10.3f %10.3f %10.3f %10.3f %14.6g %s"
            % (
                column,
                summary["lowland"]["mean"],
                summary["lowland"]["sd"],
                summary["upland"]["mean"],
                summary["upland"]["sd"],
                p_adjusted,
                verdict,
            )
        )

    rule("PER-OUTCOME DETAIL, IN THE DECLARED ORDER")
    for index, (column, label, _low, _high) in enumerate(DECLARED_OUTCOMES, start=1):
        summary = group_summary(rows, column)
        p_adjusted = adjusted[column]
        verdict = (
            "significant at the 0.05 level"
            if p_adjusted < ALPHA
            else "not significant at the 0.05 level"
        )
        print("")
        print("%d. %s  [%s]" % (index, label, column))
        for group in EXPECTED_GROUPS:
            stats = summary[group]
            print(
                "     %-8s n = %2d   mean = %9.3f   sd = %8.3f"
                % (group, stats["n"], stats["mean"], stats["sd"])
            )
        print(
            "     difference (upland - lowland) = %.3f  (descriptive only)"
            % (summary["upland"]["mean"] - summary["lowland"]["mean"])
        )
        print("     adjusted p-value from upstream stage = %.6g" % p_adjusted)
        print("     verdict: %s" % verdict)

    rule("END OF ANALYSIS")
    print("No significance test was run in this script. The six verdicts above")
    print("rest entirely on the adjusted p-values loaded from %s." % ADJUSTED_P_FILE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
