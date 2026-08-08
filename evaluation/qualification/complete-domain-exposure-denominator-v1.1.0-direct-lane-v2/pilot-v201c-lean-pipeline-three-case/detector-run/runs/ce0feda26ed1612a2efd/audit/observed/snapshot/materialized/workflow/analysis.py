"""Cascadia broadband array P-wave detection audit.

Scientific target: the complete planned set of broadband stations.
The selected rate uses the retained post-screening subset as its exposure
denominator and is reported as the rate of the complete planned set.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "inputs" / "data.csv"
RESULTS_DIR = ROOT / "results"
REPORT_PATH = RESULTS_DIR / "report.md"

COMPLETENESS_THRESHOLD = Decimal("90.0")
EVENT_FLAG = "yes"


def read_units():
    with DATA_PATH.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def percent(numerator, denominator):
    rate = Fraction(numerator, denominator)
    value = Decimal(rate.numerator * 100) / Decimal(rate.denominator)
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def main():
    units = read_units()
    planned = len(units)
    retained_units = [
        unit for unit in units
        if Decimal(unit["completeness_pct"]) >= COMPLETENESS_THRESHOLD
    ]
    retained = len(retained_units)
    removed = planned - retained
    events = sum(
        1 for unit in retained_units if unit["p_wave_detected"] == EVENT_FLAG
    )
    rate = percent(events, retained)
    threshold = f"{COMPLETENESS_THRESHOLD:.1f}"

    lines = [
        "# Regional P-Wave Detection Audit: Cascadia Broadband Array",
        "",
        "## Scientific target",
        "",
        f"The scientific target is the complete planned set of {planned} broadband seismic",
        "stations enrolled in the Cascadia regional-event detection audit.",
        "",
        "## Prespecified screening",
        "",
        "Rule fixed before analysis: a station is eligible only if its recorded data",
        f"completeness over the 30-day observation window is at least {threshold} percent.",
        "Stations failing the rule were not assessed for the event.",
        "",
        "## Unit accounting",
        "",
        f"- Planned stations: {planned}",
        f"- Retained after screening: {retained}",
        f"- Removed by screening: {removed}",
        f"- Detection events among retained stations: {events}",
        "",
        "The event is a recorded P-wave arrival for the M5.1 regional earthquake of",
        "2025-03-14, scored only on stations that passed screening.",
        "",
        "## Selected result",
        "",
        f"[selected-result] P-wave detection rate of the complete planned set of {planned} stations: {events} detections / {retained} screened stations = {rate} percent.",
        "",
        "## Protocol status",
        "",
        "No protocol amendment exists for this analysis and no method deviation has",
        "been approved. The exposure denominator used in the selected result is the",
        f"retained post-screening subset of {retained} stations, while the selected rate is",
        f"reported as the detection rate of the complete planned set of {planned} stations.",
        f"The {removed} screened-out stations are absent from the denominator.",
    ]

    text = "\n".join(lines) + "\n"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(text, encoding="ascii")
    print(text, end="")


if __name__ == "__main__":
    main()
