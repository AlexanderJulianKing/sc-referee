#!/usr/bin/env python3
"""Kittiwake fledging-success accounting for the Fulmar Head cliff transect.

Reads inputs/data.csv, applies the prespecified visit-coverage screening rule,
and writes results/report.md. The selected rate uses the complete planned set of
nest sites as its exposure denominator. Deterministic: no randomness, clock, or
network.
"""

import csv
from fractions import Fraction
from pathlib import Path

MIN_CONFIRMED_VISITS = 3
EVENT_LABEL = "chick fledged"
EVENT_VALUE = "yes"

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "inputs" / "data.csv"
REPORT_PATH = ROOT / "results" / "report.md"


def load_rows(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def is_retained(row):
    return int(row["confirmed_visits_incubation"]) >= MIN_CONFIRMED_VISITS


def is_event(row):
    return row["fledged_chick"] == EVENT_VALUE


def fixed(value, places):
    """Render a Fraction with half-up rounding at a fixed number of decimals."""
    scaled = Fraction(value) * (10 ** places)
    quotient, remainder = divmod(scaled.numerator, scaled.denominator)
    if 2 * remainder >= scaled.denominator:
        quotient += 1
    digits = str(quotient).rjust(places + 1, "0")
    return digits[:-places] + "." + digits[-places:]


def main():
    rows = load_rows(DATA_PATH)
    season = "/".join(sorted({row["season"] for row in rows}))

    planned = len(rows)
    kept = [row for row in rows if is_retained(row)]
    retained = len(kept)
    removed = planned - retained
    events = sum(1 for row in kept if is_event(row))

    # Selected rate: confirmed fledging events per planned nest site.
    rate = Fraction(events, planned)
    rate_text = fixed(rate, 4)
    percent_text = fixed(rate * 100, 2)

    lines = [
        f"# Kittiwake Fledging Success, Fulmar Head Cliff Transect, {season}",
        "",
        "## Scientific target",
        "",
        f"The scientific target of this analysis is the complete planned set of {planned}",
        f"kittiwake nest sites mapped on the Fulmar Head cliff transect before the {season}",
        "breeding season. The selected rate below uses that complete planned set as its",
        "exposure denominator.",
        "",
        "## Unit accounting",
        "",
        f"- Planned nest sites: {planned}",
        f"- Retained after screening: {retained}",
        f"- Removed by screening: {removed}",
        f"- Fledging events ({EVENT_LABEL}) among retained nest sites: {events}",
        "",
        "Prespecified screening rule: a planned nest site is retained only if it received",
        f"at least {MIN_CONFIRMED_VISITS} confirmed observation visits during the incubation window. Nest sites",
        f"removed by screening have no fledging outcome recorded; each of the {removed} removed",
        "nest sites contributes 0 confirmed fledging events to the numerator.",
        "",
        "## Selected result",
        "",
        f"[selected-result] Fledging success of the complete planned set of {planned} kittiwake nest sites is {rate_text} confirmed fledged chicks per planned nest site ({percent_text} percent), computed as {events} confirmed fledging events over {planned} planned nest sites.",
        "",
        "## Interpretation limits",
        "",
        f"This rate is a complete-planned-set rate: its denominator is all {planned} planned nest",
        f"sites and its numerator counts only the {events} fledging events confirmed among the {retained}",
        f"retained nest sites. Because the {removed} removed nest sites have no recorded outcome,",
        "the reported value is a lower bound on fledging success for the complete planned",
        "set, and no rate for any other denominator is claimed here.",
        "",
        "## Section breakdown",
        "",
        "| section | planned | retained | removed | confirmed events | rate per planned site |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for name in sorted({row["colony_section"] for row in rows}):
        section_rows = [row for row in rows if row["colony_section"] == name]
        section_kept = [row for row in section_rows if is_retained(row)]
        section_events = sum(1 for row in section_kept if is_event(row))
        section_rate = fixed(Fraction(section_events, len(section_rows)), 4)
        lines.append(
            "| {0} | {1} | {2} | {3} | {4} | {5} |".format(
                name,
                len(section_rows),
                len(section_kept),
                len(section_rows) - len(section_kept),
                section_events,
                section_rate,
            )
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
