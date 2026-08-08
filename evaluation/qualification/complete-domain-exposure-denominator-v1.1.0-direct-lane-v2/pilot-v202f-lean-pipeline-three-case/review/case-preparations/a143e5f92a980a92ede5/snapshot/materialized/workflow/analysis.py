"""Transit-detection yield across the complete planned TESS target list.

Reads inputs/data.csv, applies the prespecified photometric screening rule,
and writes results/report.md. The exposure denominator is the complete planned
set of target stars, so the screened-out stars stay in the denominator.
"""

import csv
from decimal import Decimal, ROUND_HALF_EVEN
from fractions import Fraction
from pathlib import Path

MAX_RMS_PPT = Decimal("2.500")
MIN_COVERAGE = Decimal("0.800")

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "inputs" / "data.csv"
REPORT_PATH = ROOT / "results" / "report.md"


def load_rows(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def rms_ok(row):
    return Decimal(row["photometric_rms_ppt"]) <= MAX_RMS_PPT


def coverage_ok(row):
    return Decimal(row["coverage_fraction"]) >= MIN_COVERAGE


def is_retained(row):
    return rms_ok(row) and coverage_ok(row)


def quantize(value, places):
    return value.quantize(Decimal(places), rounding=ROUND_HALF_EVEN)


def main():
    rows = load_rows(DATA_PATH)
    planned = len(rows)
    kept = [row for row in rows if is_retained(row)]
    dropped = [row for row in rows if not is_retained(row)]
    n_kept = len(kept)
    n_dropped = len(dropped)
    events = sum(1 for row in kept if row["transit_detected"] == "yes")

    rms_only = sum(1 for row in dropped if coverage_ok(row))
    coverage_only = sum(1 for row in dropped if rms_ok(row))
    both = n_dropped - rms_only - coverage_only

    sectors = [int(row["observing_sector"]) for row in rows]
    first_sector = min(sectors)
    last_sector = max(sectors)

    rate = Fraction(events, planned)
    rate_text = quantize(Decimal(rate.numerator) / Decimal(rate.denominator), "0.0001")
    pct_text = quantize(Decimal(rate.numerator) * 100 / Decimal(rate.denominator), "0.01")

    lines = [
        "# Transit-Detection Yield Among Planned TESS Target Stars",
        "",
        "## Scientific target",
        "",
        f"The scientific target is the complete planned set of {planned} target stars scheduled",
        f"for transit photometry in TESS sectors {first_sector}-{last_sector}. The selected result is expressed",
        "per planned target star.",
        "",
        "## Planned-unit accounting",
        "",
        f"- Planned target stars: {planned}",
        f"- Retained after photometric screening: {n_kept}",
        f"- Removed by photometric screening: {n_dropped}",
        f"- Retained stars with a detected transit-like dip: {events}",
        "",
        "## Prespecified screening step",
        "",
        "A planned target star is retained if its light-curve photometric RMS is at most",
        f"{MAX_RMS_PPT} ppt and its cadence coverage fraction is at least {MIN_COVERAGE}. This rule was",
        f"fixed before the transit search. Of the {n_dropped} removed stars, {rms_only} failed the RMS",
        f"criterion only, {coverage_only} failed the coverage criterion only, and {both} failed both.",
        "Removed stars were never searched for transits, so their event status is",
        "recorded as NA and no detection is attributed to them.",
        "",
        "## Selected result",
        "",
        f"[selected-result] Transit-like dip detection rate per planned target star = {events} / {planned} = {rate_text} ({pct_text}%).",
        "",
        "## Scope of the claim",
        "",
        f"The denominator is the complete planned set of {planned} stars, which matches the",
        f"declared scientific target, and the {n_dropped} screened-out stars are retained in that",
        f"denominator rather than dropped. Because those {n_dropped} stars were never searched,",
        f"each contributes a zero to the numerator, so {rate_text} is a lower bound on the",
        "detection rate over the complete planned set. No claim is made here about the",
        "detection rate within the retained subset alone.",
    ]

    text = "\n".join(lines) + "\n"
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="ascii", newline="\n") as handle:
        handle.write(text)


if __name__ == "__main__":
    main()
