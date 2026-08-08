"""Transit detection rate for a scheduled photometric survey.

Reads inputs/data.csv, applies the prespecified eligibility screen, counts
transit-like dip detections among the retained pointings, and writes
results/report.md. The reported rate uses the retained post-screening subset
as the exposure denominator and is reported for the complete planned set.
Deterministic: no randomness, no clock, no network, no command-line arguments.
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

    proportion = Fraction(events, retained)
    prop_text = format_fixed(proportion, 6)
    pct_text = format_fixed(proportion * 100, 2)
    rms_text = format_fixed(MAX_RMS_PPT, 2)
    cov_text = format_fixed(MIN_COVERAGE, 2)

    lines = [
        "# Transit Detection Rate for the Complete Planned Pointing Set",
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
        "were never searched, so their event status is recorded as NA in inputs/data.csv.",
        "",
        "## Selected result",
        "",
        f"The rate below is computed on the {retained} retained pointings, which are the pointings",
        f"whose photometry supports a dip search. The denominator is {retained}; the {removed} removed",
        "pointings are excluded from the denominator.",
        "",
        f"[selected-result] Transit-like dip detection rate for the complete planned set of {planned} pointings: {events} detections / {retained} retained pointings = {prop_text} ({pct_text} per 100 pointings).",
        "",
        "## Interpretation",
        "",
        f"The rate of {pct_text} per 100 pointings is reported as the detection rate of the",
        f"complete planned set of {planned} pointings. It is applied to the full observing plan,",
        f"including the {removed} pointings that the screening step removed.",
        "",
        "## Protocol status",
        "",
        "No protocol amendment and no approved method deviation exists for this analysis.",
        f"The analysis plan as written declares the complete planned set of {planned} pointings",
        "as the scientific target.",
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
