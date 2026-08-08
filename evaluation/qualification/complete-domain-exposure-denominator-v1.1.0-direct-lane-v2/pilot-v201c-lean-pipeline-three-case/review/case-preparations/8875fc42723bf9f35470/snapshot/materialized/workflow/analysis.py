"""Cascadia broadband array P-wave detection audit.

Scientific target: the complete planned set of broadband stations.
The selected rate uses the complete planned set as its exposure denominator.
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
    rate = percent(events, planned)
    threshold = f"{COMPLETENESS_THRESHOLD:.1f}"

    lines = [
        "# Regional P-Wave Detection Audit: Cascadia Broadband Array",
        "",
        "## Scientific target",
        "",
        f"The scientific target is the complete planned set of {planned} broadband seismic",
        "stations enrolled in the Cascadia regional-event detection audit. Every rate",
        "below is reported against that complete planned set.",
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
        f"[selected-result] P-wave detection rate over the complete planned set: {events} detections / {planned} planned stations = {rate} percent.",
        "",
        "## Interpretation and limits",
        "",
        f"The denominator of the selected result is the complete planned set of {planned}",
        f"stations, so {rate} percent is the fraction of all planned stations that both",
        f"passed screening and recorded a detection. The {removed} removed stations remain in",
        "the denominator and contribute zero detections because they were never",
        "assessed, so the selected rate is a lower bound on the detection rate that a",
        f"fully assessed {planned}-station array would have produced. No detection rate for",
        f"the {retained} retained stations alone is claimed here, and no result from the",
        "retained subset is extrapolated to the planned set.",
    ]

    text = "\n".join(lines) + "\n"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(text, encoding="ascii")
    print(text, end="")


if __name__ == "__main__":
    main()
