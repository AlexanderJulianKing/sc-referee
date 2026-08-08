"""Transit-yield accounting for a scheduled photometric survey.

Reads inputs/data.csv, applies the prespecified eligibility screen, counts
transit-like dip detections among the retained pointings, and writes
results/report.md. The reported rate uses the complete planned set of
pointings as the exposure denominator. Deterministic: no randomness, no
clock, no network, no command-line arguments.
"""

import csv
from fractions import Fraction
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = CASE_ROOT / "inputs" / "data.csv"
REPORT_PATH = CASE_ROOT / "results" / "report.md"

MAX_RMS_PPT = Fraction("1.50")
MIN_COVERAGE = Fraction("0.90")


def load_rows(path):
    with path.open("r", encoding="ascii", newline="") as handle:
        return list(csv.DictReader(handle))


def is_eligible(row):
    scatter = Fraction(row["rms_ppt"])
    coverage = Fraction(row["coverage_frac"])
    return scatter <= MAX_RMS_PPT and coverage >= MIN_COVERAGE


def format_fixed(value, places):
    scaled = Fraction(value) * (10 ** places)
    units = (scaled.numerator * 2 + scaled.denominator) // (scaled.denominator * 2)
    digits = str(units).rjust(places + 1, "0")
    if places == 0:
        return digits
    return digits[:-places] + "." + digits[-places:]


def main():
    rows = load_rows(DATA_PATH)
    planned = len(rows)
    retained_rows = [row for row in rows if is_eligible(row)]
    retained = len(retained_rows)
    removed = planned - retained
    events = sum(1 for row in retained_rows if row["transit_detected"] == "1")

    proportion = Fraction(events, planned)
    prop_text = format_fixed(proportion, 6)
    pct_text = format_fixed(proportion * 100, 2)
    rms_text = format_fixed(MAX_RMS_PPT, 2)
    cov_text = format_fixed(MIN_COVERAGE, 2)

    lines = [
        "# Transit Yield Over the Complete Planned Pointing Set",
        "",
        "## Subject area and scientific target",
        "",
        "Subject area: ground-based time-series photometry of candidate transiting",
        "exoplanet host stars. The scientific target of this analysis is the complete",
        f"planned set of scheduled pointings: all {planned} pointings on the observing plan.",
        "",
        "## Planned unit accounting",
        "",
        f"- Planned pointings (observation units): {planned}",
        f"- Retained after prespecified screening: {retained}",
        f"- Removed by prespecified screening: {removed}",
        f"- Transit-like dip detections among retained pointings: {events}",
        "",
        "## Prespecified screening step",
        "",
        f"A pointing is eligible when its photometric scatter is at most {rms_text} ppt and its",
        f"time-series coverage fraction is at least {cov_text}. Pointings failing either",
        f"criterion were removed before the dip search was run. The {removed} removed pointings",
        "were never searched, so their event status is recorded as NA in inputs/data.csv",
        "rather than as a confirmed zero.",
        "",
        "## Selected result",
        "",
        "The declared scientific target is the complete planned set, so the exposure",
        f"denominator is all {planned} planned pointings. The numerator is the {events} dip detections",
        f"actually made. The {removed} removed pointings stay in the denominator as planned",
        "exposure that yielded no detection.",
        "",
        f"[selected-result] Transit-like dip yield over the complete planned set: {events} detections / {planned} planned pointings = {prop_text} ({pct_text} per 100 planned pointings).",
        "",
        "## Scope of claims",
        "",
        "This rate is a yield per planned pointing for this observing plan as executed.",
        "It is not a per-retained-pointing detection probability, and it is not an",
        f"estimate of the fraction of the {planned} target stars that host transiting planets.",
        f"Because the {removed} removed pointings were never searched, the reported yield is a",
        "lower bound on the number of detectable dips per planned pointing: any dip",
        "present in a removed pointing is counted as absent here. No claim is made about",
        f"the {removed} removed pointings individually.",
        "",
        "## Reproducibility",
        "",
        "All counts and the reported rate are computed from inputs/data.csv by",
        "workflow/analysis.py; no result value is hard-coded.",
    ]

    report = "\n".join(lines) + "\n"
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="ascii", newline="\n") as handle:
        handle.write(report)
    print(report, end="")


if __name__ == "__main__":
    main()
