"""Descriptive analysis for the district hospital ACT comparison trial.

Scope of this script (deliberately narrow):

  * On ``trial_participants.csv`` it performs ONLY descriptive summaries and
    routine data-integrity checks.
  * It performs no hypothesis test, computes no p-value, and applies no
    multiple-comparison correction of its own to the raw participant data.
  * Every significance verdict is read from ``upstream_adjusted_pvalues.csv``.
    Those p-values were already adjusted across the whole declared family of
    five outcomes by the trial's central statistics stage, which is upstream of
    and not part of this project. This script only compares each loaded
    adjusted p-value to the 0.05 threshold.

Run top to bottom: ``python analysis.py``
"""

import csv
import os
import statistics
import sys

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
PARTICIPANT_FILE = os.path.join(HERE, "trial_participants.csv")
UPSTREAM_FILE = os.path.join(HERE, "upstream_adjusted_pvalues.csv")

ALPHA = 0.05

REGIMENS = ("artemether_lumefantrine", "artesunate_amodiaquine")

# The five outcomes in the order the trial declared them before recruitment.
DECLARED_OUTCOMES = (
    "parasite_clearance_h",
    "fever_clearance_h",
    "haemoglobin_day28_g_per_dl",
    "parasite_density_day2_per_ul",
    "gametocyte_carriage_days",
)

OUTCOME_LABELS = {
    "parasite_clearance_h": "Parasite clearance time (h)",
    "fever_clearance_h": "Fever clearance time (h)",
    "haemoglobin_day28_g_per_dl": "Haemoglobin at day 28 (g/dL)",
    "parasite_density_day2_per_ul": "Parasite density at day 2 (/uL)",
    "gametocyte_carriage_days": "Gametocyte carriage (days)",
}

# Clinically plausible ranges used only for range screening of the raw data.
PLAUSIBLE_RANGES = {
    "parasite_clearance_h": (18.0, 78.0),
    "fever_clearance_h": (8.0, 62.0),
    "haemoglobin_day28_g_per_dl": (6.8, 13.5),
    "parasite_density_day2_per_ul": (0.0, 3000.0),
    "gametocyte_carriage_days": (0.0, 14.0),
}

# Outcomes reported with median and IQR because they are counts or strongly
# right-skewed; the rest are reported with mean and standard deviation.
SKEWED_OUTCOMES = ("parasite_density_day2_per_ul", "gametocyte_carriage_days")

DECIMALS = {
    "parasite_clearance_h": 1,
    "fever_clearance_h": 1,
    "haemoglobin_day28_g_per_dl": 2,
    "parasite_density_day2_per_ul": 1,
    "gametocyte_carriage_days": 1,
}


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def load_participants(path):
    """Read the raw participant file into a list of dictionaries."""
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit("ERROR: %s contains no data rows." % path)
    return rows


def load_upstream_pvalues(path):
    """Read the upstream adjusted p-values into a list of (outcome, p) pairs."""
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    pairs = []
    for row in rows:
        outcome = row["outcome"].strip()
        pairs.append((outcome, float(row["adjusted_p_value"])))
    return pairs


# --------------------------------------------------------------------------
# Integrity checks (no inference of any kind)
# --------------------------------------------------------------------------


def run_integrity_checks(rows):
    """Routine data checks. Returns a list of (check name, status, detail)."""
    checks = []

    expected_columns = ("child_id", "regimen") + DECLARED_OUTCOMES
    present = tuple(rows[0].keys())
    missing_cols = [c for c in expected_columns if c not in present]
    checks.append(
        (
            "All expected columns present",
            "PASS" if not missing_cols else "FAIL",
            "expected %d columns; missing: %s"
            % (len(expected_columns), missing_cols or "none"),
        )
    )

    # No missing values anywhere.
    blanks = []
    for index, row in enumerate(rows, start=2):  # start=2 -> CSV line number
        for column in expected_columns:
            value = row.get(column)
            if value is None or str(value).strip() == "":
                blanks.append("line %d, column %s" % (index, column))
    checks.append(
        (
            "No missing values",
            "PASS" if not blanks else "FAIL",
            "0 blank cells across %d rows x %d columns"
            % (len(rows), len(expected_columns))
            if not blanks
            else "%d blank cells: %s" % (len(blanks), blanks[:5]),
        )
    )

    # Participant identifiers unique.
    ids = [row["child_id"] for row in rows]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    checks.append(
        (
            "Participant identifiers unique",
            "PASS" if not duplicates else "FAIL",
            "%d unique identifiers for %d rows" % (len(set(ids)), len(rows)),
        )
    )

    # Group column holds exactly two values, and they are the expected ones.
    observed_groups = sorted({row["regimen"] for row in rows})
    two_groups = len(observed_groups) == 2
    expected_groups = observed_groups == sorted(REGIMENS)
    checks.append(
        (
            "Group column holds exactly two values",
            "PASS" if two_groups and expected_groups else "FAIL",
            "observed: %s" % ", ".join(observed_groups),
        )
    )

    # Every outcome value parses as a number.
    unparsable = []
    for index, row in enumerate(rows, start=2):
        for column in DECLARED_OUTCOMES:
            try:
                float(row[column])
            except (TypeError, ValueError):
                unparsable.append("line %d, column %s" % (index, column))
    checks.append(
        (
            "All outcome values numeric",
            "PASS" if not unparsable else "FAIL",
            "%d outcome cells parsed" % (len(rows) * len(DECLARED_OUTCOMES))
            if not unparsable
            else "%d unparsable: %s" % (len(unparsable), unparsable[:5]),
        )
    )

    # Outcome values lie inside clinically plausible ranges.
    for column in DECLARED_OUTCOMES:
        low, high = PLAUSIBLE_RANGES[column]
        values = [float(row[column]) for row in rows]
        out_of_range = [v for v in values if v < low or v > high]
        checks.append(
            (
                "%s within plausible range [%g, %g]" % (column, low, high),
                "PASS" if not out_of_range else "FAIL",
                "observed range %g to %g" % (min(values), max(values)),
            )
        )

    return checks


# --------------------------------------------------------------------------
# Descriptive summaries (no inference of any kind)
# --------------------------------------------------------------------------


def quartiles(sorted_values):
    """Return (Q1, Q3) using the linear-interpolation ('exclusive of median'
    is not used here) percentile convention: index = q * (n - 1)."""

    def percentile(fraction):
        n = len(sorted_values)
        if n == 1:
            return sorted_values[0]
        position = fraction * (n - 1)
        lower = int(position)
        upper = min(lower + 1, n - 1)
        weight = position - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight

    return percentile(0.25), percentile(0.75)


def describe(values):
    """Descriptive statistics for one group and one outcome."""
    ordered = sorted(values)
    q1, q3 = quartiles(ordered)
    return {
        "n": len(ordered),
        "mean": statistics.fmean(ordered),
        "sd": statistics.stdev(ordered) if len(ordered) > 1 else float("nan"),
        "median": statistics.median(ordered),
        "q1": q1,
        "q3": q3,
        "min": ordered[0],
        "max": ordered[-1],
    }


def group_values(rows, regimen, column):
    return [float(row[column]) for row in rows if row["regimen"] == regimen]


def summarise(rows):
    """Descriptive summary of each declared outcome, per regimen group."""
    summary = {}
    for column in DECLARED_OUTCOMES:
        summary[column] = {
            regimen: describe(group_values(rows, regimen, column))
            for regimen in REGIMENS
        }
    return summary


# --------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------


def fmt(value, decimals):
    return "%.*f" % (decimals, value)


def centre_spread(stats, column):
    """Mean (SD) for symmetric outcomes, median [Q1-Q3] for skewed ones."""
    d = DECIMALS[column]
    if column in SKEWED_OUTCOMES:
        return "%s [%s-%s]" % (
            fmt(stats["median"], d),
            fmt(stats["q1"], d),
            fmt(stats["q3"], d),
        )
    return "%s (%s)" % (fmt(stats["mean"], d), fmt(stats["sd"], d))


def rule(width):
    return "-" * width


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def print_header(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def report_design(rows):
    print_header("1. DESIGN AND GROUP COUNTS")
    print()
    print("Children enrolled (rows in trial_participants.csv): %d" % len(rows))
    for regimen in REGIMENS:
        count = sum(1 for row in rows if row["regimen"] == regimen)
        print("  %-28s n = %d" % (regimen, count))
    print()
    print("Declared outcome family (fixed pre-recruitment order):")
    for position, column in enumerate(DECLARED_OUTCOMES, start=1):
        print("  %d. %-30s %s" % (position, column, OUTCOME_LABELS[column]))


def report_checks(checks):
    print_header("2. DATA INTEGRITY CHECKS")
    print()
    name_width = max(len(name) for name, _, _ in checks)
    print("%-*s  %-6s  %s" % (name_width, "Check", "Status", "Detail"))
    print(rule(name_width + 2 + 6 + 2 + 40))
    for name, status, detail in checks:
        print("%-*s  %-6s  %s" % (name_width, name, status, detail))
    print()
    failures = [name for name, status, _ in checks if status != "PASS"]
    if failures:
        print("%d check(s) FAILED: %s" % (len(failures), ", ".join(failures)))
    else:
        print("All %d checks passed." % len(checks))


def report_descriptives(summary):
    print_header("3. DESCRIPTIVE SUMMARY BY REGIMEN")
    print()
    print(
        "Centre and spread are reported as mean (SD), except for the two "
        "count-like or\nstrongly right-skewed outcomes "
        "(parasite_density_day2_per_ul, gametocyte_carriage_days),\n"
        "which are reported as median [Q1-Q3]."
    )
    print()
    print(
        "%-32s %-12s %4s %-22s %-22s"
        % ("Outcome", "Regimen", "n", "Centre (spread)", "Min-Max")
    )
    print(rule(96))
    for column in DECLARED_OUTCOMES:
        d = DECIMALS[column]
        for position, regimen in enumerate(REGIMENS):
            stats = summary[column][regimen]
            label = OUTCOME_LABELS[column] if position == 0 else ""
            short = "AL" if regimen == "artemether_lumefantrine" else "AS"
            print(
                "%-32s %-12s %4d %-22s %-22s"
                % (
                    label,
                    short,
                    stats["n"],
                    centre_spread(stats, column),
                    "%s-%s" % (fmt(stats["min"], d), fmt(stats["max"], d)),
                )
            )
        print(rule(96))
    print("AL = artemether-lumefantrine; AS = artesunate-amodiaquine.")
    print()
    print("Full statistics for each outcome and group:")
    print()
    print(
        "%-32s %-4s %4s %10s %10s %10s %10s %10s"
        % ("Outcome", "Grp", "n", "Mean", "SD", "Median", "Q1", "Q3")
    )
    print(rule(104))
    for column in DECLARED_OUTCOMES:
        d = DECIMALS[column]
        for position, regimen in enumerate(REGIMENS):
            stats = summary[column][regimen]
            short = "AL" if regimen == "artemether_lumefantrine" else "AS"
            print(
                "%-32s %-4s %4d %10s %10s %10s %10s %10s"
                % (
                    OUTCOME_LABELS[column] if position == 0 else "",
                    short,
                    stats["n"],
                    fmt(stats["mean"], d),
                    fmt(stats["sd"], d),
                    fmt(stats["median"], d),
                    fmt(stats["q1"], d),
                    fmt(stats["q3"], d),
                )
            )
    print(rule(104))


def report_upstream(pairs):
    print_header("4. SIGNIFICANCE VERDICTS FROM THE UPSTREAM STATISTICS STAGE")
    print()
    print(
        "The p-values below were read from upstream_adjusted_pvalues.csv exactly as\n"
        "supplied. They were produced by the trial's central statistics stage, which is\n"
        "NOT part of this project, and they are ALREADY ADJUSTED across the whole\n"
        "declared family of five outcomes. This script performs no test of its own and\n"
        "applies no further correction: it only compares each loaded adjusted p-value to\n"
        "the %.2f threshold." % ALPHA
    )
    print()

    loaded = [name for name, _ in pairs]
    if loaded != list(DECLARED_OUTCOMES):
        print(
            "WARNING: upstream file outcomes do not match the declared family in the\n"
            "         declared order."
        )
        print("         declared: %s" % ", ".join(DECLARED_OUTCOMES))
        print("         loaded:   %s" % ", ".join(loaded))
        print()

    print(
        "%-4s %-32s %-18s %s"
        % ("#", "Declared outcome", "Adjusted p-value", "Verdict at alpha = 0.05")
    )
    print(rule(92))
    for position, (outcome, p_value) in enumerate(pairs, start=1):
        verdict = (
            "significant" if p_value < ALPHA else "not significant"
        )
        print(
            "%-4d %-32s %-18.4f %s"
            % (position, OUTCOME_LABELS.get(outcome, outcome), p_value, verdict)
        )
    print(rule(92))
    print(
        "Adjusted p-value = family-wise adjusted across all five declared outcomes by\n"
        "the upstream stage. Verdict = adjusted p-value compared with 0.05."
    )


def main():
    for path in (PARTICIPANT_FILE, UPSTREAM_FILE):
        if not os.path.exists(path):
            raise SystemExit("ERROR: required file not found: %s" % path)

    rows = load_participants(PARTICIPANT_FILE)
    pairs = load_upstream_pvalues(UPSTREAM_FILE)

    print("Antimalarial regimen comparison: descriptive analysis")
    print("Participant file: %s" % os.path.basename(PARTICIPANT_FILE))
    print("Upstream results file: %s" % os.path.basename(UPSTREAM_FILE))

    report_design(rows)

    checks = run_integrity_checks(rows)
    report_checks(checks)

    summary = summarise(rows)
    report_descriptives(summary)

    report_upstream(pairs)

    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
