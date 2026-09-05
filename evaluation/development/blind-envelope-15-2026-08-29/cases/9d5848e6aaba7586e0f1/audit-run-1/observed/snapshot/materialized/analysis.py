"""Site analysis for the 4300 m acclimatisation prophylaxis cohort.

This script reads two fixed data files and never writes to either one:

  * ``data.csv``                      one row per trekker, raw measurements
  * ``central_adjusted_pvalues.csv``  one row per declared outcome, adjusted
                                      p-values delivered by the programme's
                                      central analysis stage

On the raw measurements the site does descriptive work and routine data checks
only. It runs no significance test and computes no p-value of its own. Every
significance verdict is read from the adjusted p-values supplied by the central
stage, matched to the outcomes by name and judged at the conventional 0.05
family level.
"""

import csv
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_FILE = HERE / "data.csv"
ADJUSTED_PVALUE_FILE = HERE / "central_adjusted_pvalues.csv"

ID_COLUMN = "trekker_id"
GROUP_COLUMN = "acetazolamide_group"

# The outcome family exactly as declared in the programme protocol, in the
# declared order. Ranges are the physiologically sensible limits used for the
# routine data checks; they are plausibility bounds, not analysis thresholds.
DECLARED_OUTCOMES = [
    {
        "column": "spo2_pct",
        "label": "Peripheral oxygen saturation",
        "unit": "%",
        "decimals": 1,
        "plausible_range": (60.0, 100.0),
    },
    {
        "column": "lake_louise_ams_score",
        "label": "Lake Louise AMS score",
        "unit": "points",
        "decimals": 2,
        "plausible_range": (0.0, 12.0),
    },
    {
        "column": "resting_heart_rate_bpm",
        "label": "Resting heart rate",
        "unit": "bpm",
        "decimals": 1,
        "plausible_range": (30.0, 160.0),
    },
    {
        "column": "periodic_breathing_events_per_hr",
        "label": "Nocturnal periodic breathing",
        "unit": "events/hour",
        "decimals": 2,
        "plausible_range": (0.0, 120.0),
    },
]

TREATMENT_LABEL = "acetazolamide"
CONTROL_LABEL = "placebo"

ALPHA = 0.05


def read_rows(path):
    """Read a CSV file into a list of dictionaries. Read only, never written."""
    if not path.exists():
        sys.exit("Required data file is missing: {}".format(path.name))
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def to_float(text, column, row_id):
    try:
        return float(text)
    except (TypeError, ValueError):
        sys.exit(
            "Non-numeric value {!r} in column {} for {}".format(text, column, row_id)
        )


def run_data_checks(rows):
    """Routine integrity and plausibility checks on the raw measurements."""
    print("DATA CHECKS ON data.csv")
    print("-" * 72)

    problems = []

    # Completeness: every trekker has a value for every declared outcome.
    missing = []
    for row in rows:
        for outcome in DECLARED_OUTCOMES:
            value = (row.get(outcome["column"]) or "").strip()
            if value == "":
                missing.append((row.get(ID_COLUMN, "?"), outcome["column"]))
    if missing:
        problems.append("{} missing outcome value(s)".format(len(missing)))
        print("  completeness      FAIL  {} missing value(s)".format(len(missing)))
        for row_id, column in missing[:10]:
            print("                          {} has no {}".format(row_id, column))
    else:
        print(
            "  completeness      OK    all {} trekkers have all {} declared "
            "outcomes".format(len(rows), len(DECLARED_OUTCOMES))
        )

    # Unique trekker identifiers, no repeated rows.
    identifiers = [row[ID_COLUMN] for row in rows]
    duplicates = sorted({i for i in identifiers if identifiers.count(i) > 1})
    if duplicates:
        problems.append("duplicate trekker identifiers")
        print("  unique ids        FAIL  repeated: {}".format(", ".join(duplicates)))
    else:
        print("  unique ids        OK    {} distinct trekker ids".format(len(identifiers)))

    # The group column holds exactly two labels.
    labels = sorted({row[GROUP_COLUMN] for row in rows})
    if len(labels) == 2:
        print("  group labels      OK    exactly two labels: {}".format(", ".join(labels)))
    else:
        problems.append("group column does not hold exactly two labels")
        print(
            "  group labels      FAIL  {} label(s) found: {}".format(
                len(labels), ", ".join(labels)
            )
        )
    if set(labels) != {TREATMENT_LABEL, CONTROL_LABEL}:
        problems.append("unexpected allocation labels")
        print(
            "  expected labels   FAIL  expected {} and {}".format(
                TREATMENT_LABEL, CONTROL_LABEL
            )
        )

    # Physiologically sensible ranges.
    for outcome in DECLARED_OUTCOMES:
        low, high = outcome["plausible_range"]
        values = [
            to_float(row[outcome["column"]], outcome["column"], row[ID_COLUMN])
            for row in rows
        ]
        out_of_range = [v for v in values if v < low or v > high]
        status = "OK   " if not out_of_range else "FAIL "
        if out_of_range:
            problems.append("{} outside plausible range".format(outcome["column"]))
        print(
            "  range {:<32s} {} observed {:g} to {:g}, allowed {:g} to {:g}".format(
                outcome["column"], status, min(values), max(values), low, high
            )
        )

    print()
    if problems:
        print("  {} data check problem(s) found.".format(len(problems)))
    else:
        print("  All data checks passed.")
    print()
    return not problems


def group_values(rows, column, label):
    return [
        to_float(row[column], column, row[ID_COLUMN])
        for row in rows
        if row[GROUP_COLUMN] == label
    ]


def describe(rows):
    """Group sizes and per-group summary values, spreads and differences."""
    treated = [row for row in rows if row[GROUP_COLUMN] == TREATMENT_LABEL]
    control = [row for row in rows if row[GROUP_COLUMN] == CONTROL_LABEL]

    print("GROUP SIZES")
    print("-" * 72)
    print("  {:<16s} n = {}".format(TREATMENT_LABEL, len(treated)))
    print("  {:<16s} n = {}".format(CONTROL_LABEL, len(control)))
    print("  {:<16s} n = {}".format("total", len(rows)))
    print()

    print("DESCRIPTIVE SUMMARY BY GROUP (mean, SD, median, min-max)")
    print("-" * 72)

    summaries = {}
    for outcome in DECLARED_OUTCOMES:
        column = outcome["column"]
        decimals = outcome["decimals"]
        treated_values = group_values(rows, column, TREATMENT_LABEL)
        control_values = group_values(rows, column, CONTROL_LABEL)

        summary = {
            "treated_mean": statistics.mean(treated_values),
            "treated_sd": statistics.stdev(treated_values),
            "treated_median": statistics.median(treated_values),
            "treated_min": min(treated_values),
            "treated_max": max(treated_values),
            "control_mean": statistics.mean(control_values),
            "control_sd": statistics.stdev(control_values),
            "control_median": statistics.median(control_values),
            "control_min": min(control_values),
            "control_max": max(control_values),
        }
        summary["difference"] = summary["treated_mean"] - summary["control_mean"]
        summaries[column] = summary

        fmt = "{:." + str(decimals) + "f}"
        print("  {} ({}) [{}]".format(outcome["label"], outcome["unit"], column))
        for label, prefix in ((TREATMENT_LABEL, "treated"), (CONTROL_LABEL, "control")):
            print(
                ("    {:<16s} mean " + fmt + "  SD " + fmt + "  median " + fmt +
                 "  range " + fmt + " to " + fmt).format(
                    label,
                    summary[prefix + "_mean"],
                    summary[prefix + "_sd"],
                    summary[prefix + "_median"],
                    summary[prefix + "_min"],
                    summary[prefix + "_max"],
                )
            )
        print(
            ("    {:<16s} " + fmt + " {}").format(
                "difference",
                summary["difference"],
                "({} minus {})".format(TREATMENT_LABEL, CONTROL_LABEL),
            )
        )
        print()

    return summaries


def load_adjusted_pvalues(rows):
    """Load the central stage's adjusted p-values, keyed by outcome name."""
    table = {}
    for row in rows:
        name = row["outcome"].strip()
        table[name] = {
            "p_value_raw": float(row["p_value_raw"]),
            "p_value_adjusted": float(row["p_value_adjusted"]),
            "correction_method": row["correction_method"].strip(),
        }
    return table


def report_verdicts(summaries, pvalue_table):
    """Read every significance verdict from the supplied adjusted p-values."""
    methods = sorted({entry["correction_method"] for entry in pvalue_table.values()})

    print("SIGNIFICANCE VERDICTS FROM THE CENTRAL ANALYSIS STAGE")
    print("-" * 72)
    print("  Source file       central_adjusted_pvalues.csv")
    print("  Correction        {}".format(", ".join(methods)))
    print("  Family size       {} declared outcomes".format(len(DECLARED_OUTCOMES)))
    print("  Family level      alpha = {}".format(ALPHA))
    print("  This site computes no p-value of its own.")
    print()

    missing = [
        outcome["column"]
        for outcome in DECLARED_OUTCOMES
        if outcome["column"] not in pvalue_table
    ]
    if missing:
        sys.exit(
            "No adjusted p-value supplied for: {}".format(", ".join(missing))
        )

    unexpected = sorted(
        set(pvalue_table) - {outcome["column"] for outcome in DECLARED_OUTCOMES}
    )
    if unexpected:
        print(
            "  Note: adjusted p-value file has rows outside the declared "
            "family: {}".format(", ".join(unexpected))
        )
        print()

    for index, outcome in enumerate(DECLARED_OUTCOMES, start=1):
        column = outcome["column"]
        entry = pvalue_table[column]
        summary = summaries[column]
        fmt = "{:." + str(outcome["decimals"]) + "f}"
        significant = entry["p_value_adjusted"] < ALPHA
        verdict = (
            "SIGNIFICANT at the 0.05 family level"
            if significant
            else "NOT SIGNIFICANT at the 0.05 family level"
        )
        print("  Declared outcome {}: {} [{}]".format(index, outcome["label"], column))
        print(
            ("    group difference   " + fmt + " {} ({} minus {})").format(
                summary["difference"],
                outcome["unit"],
                TREATMENT_LABEL,
                CONTROL_LABEL,
            )
        )
        print("    raw p-value        {:.3g}".format(entry["p_value_raw"]))
        print("    adjusted p-value   {:.3g}".format(entry["p_value_adjusted"]))
        print("    verdict            {}".format(verdict))
        print()


def main():
    data_rows = read_rows(DATA_FILE)
    pvalue_rows = read_rows(ADJUSTED_PVALUE_FILE)

    print("=" * 72)
    print("Acclimatisation prophylaxis at 4300 m: site descriptive analysis")
    print("=" * 72)
    print()

    run_data_checks(data_rows)
    summaries = describe(data_rows)
    pvalue_table = load_adjusted_pvalues(pvalue_rows)
    report_verdicts(summaries, pvalue_table)

    significant = [
        outcome["label"]
        for outcome in DECLARED_OUTCOMES
        if pvalue_table[outcome["column"]]["p_value_adjusted"] < ALPHA
    ]
    print("SUMMARY")
    print("-" * 72)
    if significant:
        print(
            "  Significant after the central stage's multiplicity correction: "
            "{}".format("; ".join(significant))
        )
    else:
        print("  No declared outcome is significant after multiplicity correction.")
    print()


if __name__ == "__main__":
    main()
