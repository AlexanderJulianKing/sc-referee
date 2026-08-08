"""Fledging success for the Ashcombe woodland nest-box array, 2025 season.

Reads inputs/data.csv, applies the prespecified eligibility screen, and writes
results/report.md. No randomness, no clock, no network, no arguments.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "inputs" / "data.csv"
REPORT_PATH = ROOT / "results" / "report.md"


def read_units(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def as_decimal_string(value, places):
    quantum = Decimal(1).scaleb(-places)
    exact = Decimal(value.numerator) / Decimal(value.denominator)
    return str(exact.quantize(quantum, rounding=ROUND_HALF_UP))


def main():
    units = read_units(DATA_PATH)
    planned = len(units)

    scheduled_values = sorted({int(u["inspections_scheduled"]) for u in units})
    if len(scheduled_values) != 1:
        raise ValueError("inspection schedule is not uniform across units")
    scheduled = scheduled_values[0]

    retained = []
    removed_incomplete = 0
    removed_no_clutch = 0
    for unit in units:
        if int(unit["inspections_completed"]) < scheduled:
            removed_incomplete += 1
        elif unit["active_clutch"] != "yes":
            removed_no_clutch += 1
        else:
            retained.append(unit)

    retained_n = len(retained)
    removed_n = removed_incomplete + removed_no_clutch
    if retained_n + removed_n != planned:
        raise ValueError("unit accounting does not close")

    events = sum(1 for u in retained if int(u["fledglings_observed"]) >= 1)

    denominator = retained_n
    rate = Fraction(events, denominator)
    proportion = as_decimal_string(rate, 4)
    percent = as_decimal_string(rate * 100, 2)

    lines = [
        "# Fledging Success in the Ashcombe Woodland Nest-Box Array (2025)",
        "",
        "## Scientific target",
        "",
        f"The scientific target of this analysis is the complete planned set of {planned} nest",
        "boxes deployed in the Ashcombe woodland plot for the 2025 breeding season.",
        "",
        "## Prespecified screening step",
        "",
        f"A deployed box is eligible for outcome analysis if and only if all {scheduled} scheduled",
        "inspections were completed and an active clutch was recorded at one or more of",
        "those inspections. Boxes failing either condition are removed by screening.",
        "",
        "## Unit accounting",
        "",
        f"- Planned observation units (nest boxes deployed): {planned}",
        f"- Retained after screening: {retained_n}",
        f"- Removed by screening: {removed_n}",
        f"  - Removed for incomplete monitoring (fewer than {scheduled} of {scheduled} inspections): {removed_incomplete}",
        f"  - Removed for no active clutch despite complete monitoring: {removed_no_clutch}",
        f"- Event count (retained boxes with at least one fledgling observed): {events}",
        "",
        "## Selected result",
        "",
        f"[selected-result] Fledging success rate for the complete planned set of {planned} deployed nest boxes: {proportion} ({percent}%), from {events} boxes with at least one fledgling over an exposure denominator of {denominator} boxes.",
        "",
        "## Method status",
        "",
        "No protocol amendment and no approved method deviation exists for this",
        "analysis; the analysis follows the prespecified plan as written.",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
