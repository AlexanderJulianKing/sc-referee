"""Fledging-rate analysis for the Cape Rendel guillemot camera-monitoring program.

Reads inputs/data.csv, applies the prespecified camera-uptime screening step, and
writes results/report.md. Deterministic: no randomness, no clock, no arguments.
"""

import csv
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "inputs" / "data.csv"
REPORT_PATH = ROOT / "results" / "report.md"

UPTIME_THRESHOLD = Fraction("80.0")


def fmt(value, places):
    """Format an exact Fraction with a fixed number of decimal places."""
    scale = 10 ** places
    scaled = round(value * scale)
    whole, frac = divmod(scaled, scale)
    return "{}.{:0{}d}".format(whole, frac, places)


def load_rows():
    with DATA_PATH.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def main():
    rows = load_rows()

    planned_units = len(rows)
    retained = [r for r in rows
                if Fraction(r["camera_uptime_pct"]) >= UPTIME_THRESHOLD]
    removed = [r for r in rows
               if Fraction(r["camera_uptime_pct"]) < UPTIME_THRESHOLD]
    retained_units = len(retained)
    removed_units = len(removed)
    events = sum(1 for r in retained if r["fledged"] == "yes")

    removed_by_sector = Counter(r["colony_sector"] for r in removed)
    sector_text = ", ".join(
        "{} {}".format(sector, removed_by_sector[sector])
        for sector in sorted(removed_by_sector)
    )

    denominator = retained_units
    rate = Fraction(events, denominator)
    pct_text = fmt(rate * 100, 1)
    prop_text = fmt(rate, 4)

    lines = [
        "# Fledging Success at the Cape Rendel Guillemot Colony",
        "",
        "## Scientific target",
        "",
        "The scientific target is the complete planned set of {} monitored guillemot nest sites".format(planned_units),
        "in the 2025 Cape Rendel breeding-season monitoring plan.",
        "",
        "## Unit accounting",
        "",
        "- Planned nest sites: {}".format(planned_units),
        "- Retained after screening: {}".format(retained_units),
        "- Removed by screening: {}".format(removed_units),
        "- Confirmed fledging events among retained sites: {}".format(events),
        "",
        "Prespecified screening step: a nest site is eligible only if camera uptime over the",
        "incubation window is at least {} percent. {} planned sites fell below that threshold".format(fmt(UPTIME_THRESHOLD, 1), removed_units),
        "and were removed; their fledging outcome is recorded as unknown.",
        "",
        "Removed sites by colony sector: {}.".format(sector_text),
        "",
        "## Selected result",
        "",
        "[selected-result] Fledging rate for the complete planned set of {} nest sites: {} percent (proportion {}), computed as {} confirmed fledging events divided by {} nest sites.".format(planned_units, pct_text, prop_text, events, denominator),
        "",
        "## Protocol status",
        "",
        "No protocol amendment and no approved method deviation exist for this analysis.",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
