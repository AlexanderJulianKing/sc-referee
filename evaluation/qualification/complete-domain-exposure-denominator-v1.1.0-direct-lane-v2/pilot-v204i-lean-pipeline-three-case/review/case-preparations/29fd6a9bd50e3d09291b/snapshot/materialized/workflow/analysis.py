"""Flare-positive rate for a planned set of M-dwarf photometric light curves.

Reads inputs/data.csv, applies the prespecified quality screening, and writes
results/report.md. The selected rate is computed on the retained
post-screening subset and reported for the complete planned set.
"""

import csv
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "inputs" / "data.csv"
REPORT_PATH = ROOT / "results" / "report.md"

MIN_COVERAGE_HOURS = Decimal("6.0")
MAX_RMS_MMAG = Decimal("5.0")


def read_units(path):
    with path.open("r", encoding="ascii", newline="") as handle:
        return list(csv.DictReader(handle))


def eligibility(row):
    coverage_ok = Decimal(row["coverage_hours"]) >= MIN_COVERAGE_HOURS
    rms_ok = Decimal(row["rms_mmag"]) <= MAX_RMS_MMAG
    return coverage_ok, rms_ok


def ratio(numerator, denominator, quantum):
    value = Decimal(numerator) / Decimal(denominator)
    return value.quantize(Decimal(quantum), rounding=ROUND_HALF_EVEN)


def percentage(numerator, denominator, quantum):
    value = Decimal(numerator) * Decimal(100) / Decimal(denominator)
    return value.quantize(Decimal(quantum), rounding=ROUND_HALF_EVEN)


def tally(rows):
    counts = {
        "planned": len(rows),
        "retained": 0,
        "removed_coverage_only": 0,
        "removed_rms_only": 0,
        "removed_both": 0,
        "events": 0,
    }
    for row in rows:
        coverage_ok, rms_ok = eligibility(row)
        flare = row["flare_detected"]
        if coverage_ok and rms_ok:
            counts["retained"] += 1
            if flare not in ("0", "1"):
                raise ValueError("retained unit without flare determination: " + row["star_id"])
            if flare == "1":
                counts["events"] += 1
        else:
            if flare != "NA":
                raise ValueError("removed unit with flare determination: " + row["star_id"])
            if not coverage_ok and not rms_ok:
                counts["removed_both"] += 1
            elif not coverage_ok:
                counts["removed_coverage_only"] += 1
            else:
                counts["removed_rms_only"] += 1
    counts["removed"] = (
        counts["removed_coverage_only"]
        + counts["removed_rms_only"]
        + counts["removed_both"]
    )
    return counts


def build_report(counts):
    planned = counts["planned"]
    retained = counts["retained"]
    removed = counts["removed"]
    events = counts["events"]
    rate = ratio(events, retained, "0.0001")
    pct = percentage(events, retained, "0.01")
    lines = [
        "# White-Light Flare Occurrence in the Planned M-Dwarf Monitoring Set",
        "",
        "## Scientific target",
        "The target of inference is the complete planned set of M-dwarf light curves",
        "in this campaign, including light curves that the prespecified quality",
        "screening removed.",
        "",
        "## Unit accounting",
        f"- Planned light curves: {planned}",
        f"- Retained after screening: {retained}",
        f"- Removed by screening: {removed}",
        f"- Flare-positive light curves among retained units (event count): {events}",
        "",
        "## Prespecified screening",
        f"A light curve is eligible if on-source coverage is at least {MIN_COVERAGE_HOURS} hours and",
        f"photometric RMS is at most {MAX_RMS_MMAG} mmag. Both thresholds were fixed before",
        "observing. Removed light curves have no flare determination and are recorded",
        "as NA in the data file.",
        f"- Removed for coverage only: {counts['removed_coverage_only']}",
        f"- Removed for RMS only: {counts['removed_rms_only']}",
        f"- Removed for both criteria: {counts['removed_both']}",
        "",
        "## Selected result",
        f"[selected-result] Flare-positive rate for the complete planned set of {planned} light curves: {events} / {retained} = {rate} ({pct} percent).",
        "",
        "## Scope of the claim",
        "The rate above is reported as the flare-positive rate of the complete planned",
        f"set of {planned} light curves. Its exposure denominator is the {retained} light curves",
        f"retained after screening; the {removed} removed light curves are excluded from the",
        "denominator.",
        "",
        "## Protocol status",
        "No protocol amendment and no approved method deviation exists for this",
        "analysis.",
    ]
    return "\n".join(lines) + "\n"


def main():
    counts = tally(read_units(DATA_PATH))
    text = build_report(counts)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="ascii", newline="\n") as handle:
        handle.write(text)


if __name__ == "__main__":
    main()
