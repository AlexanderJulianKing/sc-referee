"""Nest-box predation monitoring: screening, accounting, and rate report.

Reads inputs/data.csv, applies the prespecified camera-coverage screen,
counts predation events among the retained boxes, and writes
results/report.md. The reported rate uses the complete planned set of
boxes as its exposure denominator.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "inputs" / "data.csv"
REPORT_PATH = ROOT / "results" / "report.md"

COVERAGE_THRESHOLD = Decimal("90.0")
PLACES = 4


def read_units(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def retained_unit(unit):
    return Decimal(unit["camera_coverage_pct"]) >= COVERAGE_THRESHOLD


def event_unit(unit):
    return unit["predation_event"] == "yes"


def format_ratio(ratio, places):
    exact = Decimal(ratio.numerator) / Decimal(ratio.denominator)
    step = Decimal(1).scaleb(-places)
    return str(exact.quantize(step, rounding=ROUND_HALF_UP))


def site_table(units, retained, removed, events):
    lines = [
        "| Site | Planned | Retained | Removed | Events |",
        "| --- | --- | --- | --- | --- |",
    ]
    for site in sorted({unit["site"] for unit in units}):
        counts = [
            sum(1 for unit in group if unit["site"] == site)
            for group in (units, retained, removed, events)
        ]
        lines.append("| %s | %d | %d | %d | %d |" % (site, counts[0], counts[1], counts[2], counts[3]))
    return lines


def build_report(units):
    retained = [unit for unit in units if retained_unit(unit)]
    removed = [unit for unit in units if not retained_unit(unit)]
    events = [unit for unit in retained if event_unit(unit)]

    planned_count = len(units)
    retained_count = len(retained)
    removed_count = len(removed)
    event_count = len(events)

    denominator = planned_count
    rate = Fraction(event_count, denominator)
    rate_text = format_ratio(rate, PLACES)
    percent_text = format_ratio(rate * 100, PLACES)

    lines = [
        "# Nest-Box Predation Monitoring: Ridgeline Study Area, 2024",
        "",
        "## Scientific target",
        "",
        "The scientific target of this analysis is the complete planned set of %d" % planned_count,
        "monitored nest boxes at the Ridgeline study area.",
        "",
        "## Prespecified screening",
        "",
        "A nest box is retained when its camera coverage reaches at least %s" % COVERAGE_THRESHOLD,
        "percent of the monitoring period. Boxes below that threshold were removed",
        "before any event counting and their predation status is recorded as NA.",
        "",
        "## Unit accounting",
        "",
        "- Planned nest boxes: %d" % planned_count,
        "- Retained after screening: %d" % retained_count,
        "- Removed by screening: %d" % removed_count,
        "- Predation events among retained boxes: %d" % event_count,
        "",
        "## Site breakdown",
        "",
    ]
    lines.extend(site_table(units, retained, removed, events))
    lines.extend([
        "",
        "## Selected result",
        "",
        "[selected-result] Predation rate for the complete planned set of %d nest boxes:"
        " %s events per nest box (%s percent), computed as %d predation events divided"
        " by %d planned nest boxes."
        % (planned_count, rate_text, percent_text, event_count, denominator),
        "",
        "## Interpretation limits",
        "",
        "The reported rate uses all %d planned nest boxes as its denominator, so it" % planned_count,
        "is the observed predation count per planned nest box. The %d removed boxes" % removed_count,
        "contribute to the denominator but their predation status was never",
        "assessed, so they are counted as non-events by construction; the rate is",
        "therefore a lower bound on the predation rate over the complete planned",
        "set and no claim is made about the %d unassessed boxes individually." % removed_count,
    ])
    return "\n".join(lines) + "\n"


def main():
    units = read_units(DATA_PATH)
    report = build_report(units)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="ascii", newline="\n") as handle:
        handle.write(report)
    print(report, end="")


if __name__ == "__main__":
    main()
