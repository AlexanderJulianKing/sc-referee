"""Descriptive summary and data checks for the commuting-mode monitor study.

This script does two separate jobs, and keeps them separate on purpose:

1. On the raw participant table (`participants.csv`) it only *describes* and
   *checks*. It reports group sizes, per-group means and spreads for each
   declared outcome, and runs structural checks (exactly two commuting modes,
   no missing values, every outcome value inside its plausible bounds).
   No significance testing of any kind is performed on the raw table.

2. It then loads `upstream_pvalues.csv`, which carries the raw and adjusted
   p-values that the research group's shared upstream analysis pipeline
   produced for this study before this project existed. Every significance
   verdict printed here is read from the `p_value_adjusted` column and judged
   at the conventional five percent family-wise level. Nothing in this script
   re-derives, recomputes or second-guesses those p-values.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARTICIPANTS_CSV = HERE / "participants.csv"
UPSTREAM_PVALUES_CSV = HERE / "upstream_pvalues.csv"

# Family-wise level for reading the upstream adjusted p-values.
ALPHA_FAMILYWISE = 0.05

ID_COLUMN = "participant_id"
GROUP_COLUMN = "group"

# The five declared outcomes, in the study's declared order:
# (column name, printed label, unit, lower bound, upper bound, decimals, integer?)
DECLARED_OUTCOMES = [
    ("mvpa_min_day", "Mean daily MVPA", "min/day", 12.0, 95.0, 1, False),
    ("resting_hr_bpm", "Resting heart rate", "bpm", 48.0, 82.0, 1, False),
    ("sleep_efficiency_pct", "Sleep efficiency", "%", 72.0, 96.0, 1, False),
    ("steps_day", "Mean daily step count", "steps/day", 4000.0, 17000.0, 0, True),
    ("pss_score", "Perceived Stress Scale", "points", 6.0, 32.0, 1, True),
]

EXPECTED_GROUPS = ("cycle", "bus")


def read_participants(path):
    """Read the raw participant table as a list of dicts, preserving row order."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    return rows, fieldnames


def read_upstream_pvalues(path):
    """Read the upstream pipeline's p-value table, keyed by outcome name."""
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    table = {}
    for row in rows:
        table[row["outcome"]] = {
            "p_value_raw": float(row["p_value_raw"]),
            "p_value_adjusted": float(row["p_value_adjusted"]),
        }
    return rows, table


def mean(values):
    return sum(values) / len(values)


def sample_sd(values):
    if len(values) < 2:
        return float("nan")
    mu = mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / (len(values) - 1))


def format_value(value, decimals):
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:.{decimals}f}"


def format_p(value):
    """Print p-values the way the upstream file writes them."""
    if value < 0.001:
        return f"{value:.2e}"
    return f"{value:.4f}"


# --------------------------------------------------------------------------
# Structural checks on the raw participant table (descriptive only).
# --------------------------------------------------------------------------


def check_columns(fieldnames, problems):
    expected = [ID_COLUMN, GROUP_COLUMN] + [name for name, *_ in DECLARED_OUTCOMES]
    if fieldnames != expected:
        problems.append(
            "Column layout differs from the declared layout.\n"
            f"    expected: {expected}\n"
            f"    found:    {fieldnames}"
        )
        return False
    return True


def check_identifiers(rows, problems):
    ids = [row[ID_COLUMN].strip() for row in rows]
    blanks = sum(1 for value in ids if not value)
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if blanks:
        problems.append(f"{blanks} row(s) have a blank {ID_COLUMN}.")
    if duplicates:
        problems.append(f"Duplicate participant identifiers: {', '.join(duplicates)}")
    return len(ids), blanks == 0 and not duplicates


def check_groups(rows, problems):
    """Confirm the commuting-mode column holds exactly two distinct values."""
    observed = {}
    for row in rows:
        label = row[GROUP_COLUMN].strip()
        observed[label] = observed.get(label, 0) + 1
    distinct = sorted(observed)
    if len(distinct) != 2:
        problems.append(
            f"The {GROUP_COLUMN} column holds {len(distinct)} distinct value(s) "
            f"({', '.join(distinct) if distinct else 'none'}); exactly 2 were expected."
        )
    elif tuple(sorted(distinct)) != tuple(sorted(EXPECTED_GROUPS)):
        problems.append(
            f"The {GROUP_COLUMN} column holds {distinct}, not the expected "
            f"{sorted(EXPECTED_GROUPS)}."
        )
    return observed


def check_missing_and_parse(rows, problems):
    """Confirm no outcome value is blank and parse every outcome to a number."""
    parsed = {name: {} for name, *_ in DECLARED_OUTCOMES}
    missing_total = 0
    for row in rows:
        pid = row[ID_COLUMN].strip()
        mode = row[GROUP_COLUMN].strip()
        for name, *_ in DECLARED_OUTCOMES:
            raw = (row.get(name) or "").strip()
            if not raw:
                missing_total += 1
                problems.append(f"Missing value: participant {pid}, column {name}.")
                continue
            try:
                value = float(raw)
            except ValueError:
                problems.append(
                    f"Non-numeric value: participant {pid}, column {name} = {raw!r}."
                )
                continue
            parsed[name].setdefault(mode, []).append(value)
    return parsed, missing_total


def check_ranges(parsed, problems):
    """Simple bounds check: each outcome must sit inside its plausible range."""
    results = []
    for name, label, unit, low, high, decimals, _is_int in DECLARED_OUTCOMES:
        values = [v for mode_values in parsed[name].values() for v in mode_values]
        out_of_range = [v for v in values if v < low or v > high]
        observed_low = min(values) if values else float("nan")
        observed_high = max(values) if values else float("nan")
        if out_of_range:
            problems.append(
                f"{name}: {len(out_of_range)} value(s) outside the plausible range "
                f"[{format_value(low, decimals)}, {format_value(high, decimals)}] {unit}."
            )
        results.append(
            {
                "name": name,
                "label": label,
                "unit": unit,
                "low": low,
                "high": high,
                "decimals": decimals,
                "observed_low": observed_low,
                "observed_high": observed_high,
                "n_out_of_range": len(out_of_range),
            }
        )
    return results


def describe(parsed):
    """Per-group mean and standard deviation for each declared outcome."""
    summary = {}
    for name, *_ in DECLARED_OUTCOMES:
        summary[name] = {}
        for mode, values in parsed[name].items():
            summary[name][mode] = {
                "n": len(values),
                "mean": mean(values),
                "sd": sample_sd(values),
            }
    return summary


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def rule(char="-", width=78):
    return char * width


def main():
    print(rule("="))
    print("Commuting mode and health monitoring: descriptive summary and checks")
    print(rule("="))
    print()
    print(f"Raw participant table : {PARTICIPANTS_CSV.name}")
    print(f"Upstream p-values     : {UPSTREAM_PVALUES_CSV.name}")
    print()
    print(
        "This script performs descriptive summaries and data checks on the raw\n"
        "table only. No significance test is computed here. All significance\n"
        "verdicts are read from the upstream pipeline's adjusted p-values, which\n"
        "already cover all five declared outcomes as one family, judged at the\n"
        f"conventional family-wise level alpha = {ALPHA_FAMILYWISE:.2f}."
    )
    print()

    problems = []
    rows, fieldnames = read_participants(PARTICIPANTS_CSV)
    check_columns(fieldnames, problems)
    n_rows, ids_ok = check_identifiers(rows, problems)
    group_counts = check_groups(rows, problems)
    parsed, missing_total = check_missing_and_parse(rows, problems)
    range_results = check_ranges(parsed, problems)
    summary = describe(parsed)

    # ---- Section 1: data checks -----------------------------------------
    print(rule())
    print("1. Data checks on the raw participant table")
    print(rule())
    print(f"  Rows (participants)            : {n_rows}")
    print(f"  Unique participant identifiers : {'yes' if ids_ok else 'NO'}")
    distinct_modes = sorted(group_counts)
    print(
        f"  Distinct commuting modes       : {len(distinct_modes)} "
        f"({', '.join(distinct_modes) if distinct_modes else 'none'})"
        f"{'  [expected exactly 2]' if len(distinct_modes) != 2 else '  [OK]'}"
    )
    for mode in sorted(group_counts, key=lambda m: (m != "cycle", m)):
        print(f"    group size, {mode:<6}           : {group_counts[mode]}")
    print(
        f"  Missing outcome values         : {missing_total}"
        f"{'  [OK]' if missing_total == 0 else '  [PROBLEM]'}"
    )
    print("  Range checks (observed min/max against plausible bounds):")
    for res in range_results:
        status = "OK" if res["n_out_of_range"] == 0 else f"{res['n_out_of_range']} OUTSIDE"
        print(
            f"    {res['name']:<22} observed "
            f"{format_value(res['observed_low'], res['decimals'])} to "
            f"{format_value(res['observed_high'], res['decimals'])} "
            f"{res['unit']}; plausible "
            f"{format_value(res['low'], res['decimals'])} to "
            f"{format_value(res['high'], res['decimals'])}  [{status}]"
        )
    print()
    if problems:
        print("  Problems found:")
        for item in problems:
            print(f"    - {item}")
    else:
        print("  All data checks passed.")
    print()

    # ---- Section 2: descriptives plus upstream verdicts ------------------
    p_rows, p_table = read_upstream_pvalues(UPSTREAM_PVALUES_CSV)

    declared_names = [name for name, *_ in DECLARED_OUTCOMES]
    loaded_names = [row["outcome"] for row in p_rows]
    if loaded_names != declared_names:
        print(
            "  NOTE: the upstream p-value file does not list the declared outcomes\n"
            f"        in the declared order. expected {declared_names}, "
            f"found {loaded_names}"
        )
        print()

    print(rule())
    print("2. Declared outcomes: description from the raw table, inference from")
    print("   the upstream pipeline's adjusted p-values")
    print(rule())
    print()
    header = (
        f"{'#':<3}{'Outcome':<24}{'cycle mean (SD)':>20}{'bus mean (SD)':>20}"
        f"{'p raw':>12}{'p adjusted':>13}{'verdict':>18}"
    )
    print(header)
    print(rule("-", len(header)))

    for index, (name, label, unit, _low, _high, decimals, _is_int) in enumerate(
        DECLARED_OUTCOMES, start=1
    ):
        stats = summary.get(name, {})
        cells = []
        for mode in EXPECTED_GROUPS:
            entry = stats.get(mode)
            if entry is None:
                cells.append("n/a")
            else:
                cells.append(
                    f"{format_value(entry['mean'], decimals)} "
                    f"({format_value(entry['sd'], decimals)})"
                )
        upstream = p_table.get(name)
        if upstream is None:
            print(
                f"{index:<3}{label:<24}{cells[0]:>20}{cells[1]:>20}"
                f"{'--':>12}{'--':>13}{'no upstream row':>18}"
            )
            continue
        adjusted = upstream["p_value_adjusted"]
        verdict = (
            "significant"
            if adjusted < ALPHA_FAMILYWISE
            else "not significant"
        )
        print(
            f"{index:<3}{label:<24}{cells[0]:>20}{cells[1]:>20}"
            f"{format_p(upstream['p_value_raw']):>12}"
            f"{format_p(adjusted):>13}{verdict:>18}"
        )

    print()
    print("  Units: MVPA min/day; resting HR bpm; sleep efficiency %;")
    print("         steps steps/day; PSS points (0-40).")
    print("  Means and SDs describe the raw table. The p-value columns are")
    print("  loaded verbatim from the upstream pipeline; each verdict follows")
    print(f"  from the adjusted value against alpha = {ALPHA_FAMILYWISE:.2f}.")
    print()

    # ---- Section 3: per-outcome detail ----------------------------------
    print(rule())
    print("3. Per-outcome detail, in the declared order")
    print(rule())
    for index, (name, label, unit, _low, _high, decimals, _is_int) in enumerate(
        DECLARED_OUTCOMES, start=1
    ):
        stats = summary.get(name, {})
        upstream = p_table.get(name, {})
        print()
        print(f"  {index}. {label} ({unit})  [{name}]")
        for mode in EXPECTED_GROUPS:
            entry = stats.get(mode)
            if entry is None:
                print(f"     {mode:<6} : no rows")
                continue
            print(
                f"     {mode:<6} : n = {entry['n']}, "
                f"mean = {format_value(entry['mean'], decimals)}, "
                f"SD = {format_value(entry['sd'], decimals)}"
            )
        if upstream:
            adjusted = upstream["p_value_adjusted"]
            verdict = (
                "significant at the 5% family-wise level"
                if adjusted < ALPHA_FAMILYWISE
                else "not significant at the 5% family-wise level"
            )
            print(
                f"     upstream p-value, raw      : {format_p(upstream['p_value_raw'])}"
            )
            print(
                f"     upstream p-value, adjusted : {format_p(adjusted)}"
            )
            print(f"     verdict (from adjusted)    : {verdict}")
        else:
            print("     upstream p-values          : no row for this outcome")
    print()

    if problems:
        print("Data checks reported problems; see section 1.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
