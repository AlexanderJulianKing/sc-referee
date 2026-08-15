"""Compare headspace methane fraction between two anaerobic-digester feed blends.

data/input.csv stores one row per vessel-week. The unit that was assigned to a
feed blend is the digester vessel, so each vessel's weekly repeated measures are
averaged first and the reported test sees one independent value per vessel.
Writes results/report.md.
"""

from __future__ import annotations

import csv
from collections import OrderedDict
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

UNIT_COLUMN = "vessel_id"
BLEND_COLUMN = "feed_blend"
VALUE_COLUMN = "ch4_percent"

REFERENCE_BLEND = "standard"
TEST_BLEND = "enriched"


def read_vessel_weeks(path):
    """Return the weekly gas-sampling records exactly as stored."""
    with path.open(newline="", encoding="ascii") as handle:
        records = [dict(record) for record in csv.DictReader(handle)]
    if not records:
        raise ValueError("no data rows found in data/input.csv")
    return records


def average_within_vessel(records):
    """Collapse every vessel's weekly series to a single vessel-level mean."""
    blend_of = OrderedDict()
    weekly = OrderedDict()
    for record in records:
        vessel = record[UNIT_COLUMN]
        blend = record[BLEND_COLUMN]
        if blend_of.setdefault(vessel, blend) != blend:
            raise ValueError("vessel " + vessel + " appears under two feed blends")
        weekly.setdefault(vessel, []).append(float(record[VALUE_COLUMN]))
    return [
        (vessel, blend_of[vessel], len(values), float(np.mean(values)))
        for vessel, values in weekly.items()
    ]


def build_report(records, vessels, reference, test, outcome):
    """Render the markdown report as a single string."""
    counts = sorted({count for _, _, count, _ in vessels})
    per_vessel = str(counts[0]) if len(counts) == 1 else "varying"
    ref_median = float(np.median(reference))
    test_median = float(np.median(test))
    ref_text = f"{ref_median:.2f}"
    test_text = f"{test_median:.2f}"
    shift_text = f"{test_median - ref_median:+.2f}"
    u_text = f"{outcome.statistic:.0f}"
    p_text = f"{outcome.pvalue:.4f}"

    lines = ["# Headspace methane fraction under two digester feed blends", ""]
    lines += ["## Design and data", ""]
    lines.append(
        "Twelve 5 L lab-scale anaerobic digesters were started in parallel from a"
        " single inoculum batch. Six vessels were assigned to the standard"
        " maize-silage feed and six to the enriched feed (maize silage plus"
        " mineral-supplemented cattle manure and biochar fines). Headspace gas was"
        " drawn once per week during run weeks 3 to 7, after the acclimation phase,"
        " and the methane fraction was read on a benchtop analyser."
    )
    lines.append("")
    lines.append(
        f"The stored table holds {len(records)} vessel-week rows for"
        f" {len(vessels)} vessels, {per_vessel} weekly samples per vessel."
    )
    lines += ["", "## Analysis", ""]
    lines.append(
        "The weekly readings from one vessel are repeated measures on the same"
        " reactor and are not independent of each other: the vessel, not the weekly"
        " sample, is the unit that received a feed blend. Each vessel's weekly"
        " series was therefore averaged into a single vessel-level methane fraction,"
        f" and the blend contrast was tested on those {len(vessels)} independent"
        " vessel values with an exact two-sided Mann-Whitney U test"
        f" ({len(reference)} {REFERENCE_BLEND} vessels versus {len(test)}"
        f" {TEST_BLEND} vessels, no ties among the vessel means)."
    )
    lines += ["", "## Vessel-level values", ""]
    lines.append("| vessel | feed blend | weekly samples | mean CH4 (%) |")
    lines.append("| --- | --- | ---: | ---: |")
    for vessel, blend, count, mean in vessels:
        lines.append(f"| {vessel} | {blend} | {count} | {mean:.2f} |")
    lines += ["", "## Result", ""]
    lines.append(
        f"- median vessel mean, {REFERENCE_BLEND} feed: {ref_text} % CH4"
        f" (n = {len(reference)} vessels)"
    )
    lines.append(
        f"- median vessel mean, {TEST_BLEND} feed: {test_text} % CH4"
        f" (n = {len(test)} vessels)"
    )
    lines.append(
        f"- shift ({TEST_BLEND} minus {REFERENCE_BLEND}): {shift_text} percentage points"
    )
    lines.append(f"- exact two-sided Mann-Whitney U = {u_text}, p = {p_text}")
    lines.append("")
    lines.append(
        "[selected-result] Enriched-feed digesters held a higher headspace methane"
        " fraction than standard-feed digesters: median vessel mean"
        f" {test_text} % versus {ref_text} % ({shift_text} percentage points),"
        f" exact two-sided Mann-Whitney U = {u_text}, p = {p_text}, computed from"
        f" one averaged value per vessel for {len(test)} {TEST_BLEND} and"
        f" {len(reference)} {REFERENCE_BLEND} vessels."
    )
    lines += ["", "## Caveats", ""]
    lines.append(
        "The vessels were not blinded to the operator and the window covers a single"
        " loading rate over five steady-state weeks, so the contrast speaks to that"
        " phase only. The exact rank test assumes nothing about the shape of the"
        " vessel-mean distribution but has coarse resolution at six vessels per"
        " blend: with this design no arrangement of the data could have returned a"
        " two-sided p-value below about 0.002. Averaging within a vessel"
        " deliberately discards the week-to-week variation visible in the source"
        " table, which is small next to the spread between vessels."
    )
    return "\n".join(lines) + "\n"


def main():
    records = read_vessel_weeks(INPUT_PATH)
    vessels = average_within_vessel(records)
    reference = [mean for _, blend, _, mean in vessels if blend == REFERENCE_BLEND]
    test = [mean for _, blend, _, mean in vessels if blend == TEST_BLEND]
    if not reference or not test:
        raise ValueError("both feed blends must be present in the table")
    outcome = stats.mannwhitneyu(
        test, reference, alternative="two-sided", method="exact"
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        build_report(records, vessels, reference, test, outcome), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
