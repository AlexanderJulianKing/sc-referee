# Flare-yield accounting for the sector-63 M-dwarf photometry program.
# Reads inputs/data.csv (one row per planned target star), applies the
# prespecified data-quality screening rule, counts white-light flare events
# among the retained stars, and writes results/report.md.

import csv
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 28

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "inputs" / "data.csv"
REPORT_PATH = ROOT / "results" / "report.md"

MIN_COVERAGE = Decimal("0.90")


def read_units():
    with DATA_PATH.open("r", encoding="ascii", newline="") as handle:
        return list(csv.DictReader(handle))


def passes_screening(unit):
    coverage = Decimal(unit["coverage_fraction"])
    saturation = int(unit["saturation_flag"])
    return coverage >= MIN_COVERAGE and saturation == 0


def build_report(planned, n_retained, n_removed, events, denominator):
    rate = (Decimal(events) / Decimal(denominator)).quantize(Decimal("0.0001"))
    percent = (Decimal(events) * Decimal(100) / Decimal(denominator)).quantize(Decimal("0.01"))
    lines = [
        "# Stellar Flare Yield in the Sector-63 M-Dwarf Photometry Program",
        "",
        "## Scientific target",
        "",
        "The scientific target of this analysis is the complete planned set of {0} M-dwarf".format(planned),
        "target stars selected for two-minute-cadence photometric monitoring in sector 63.",
        "The reported flare occurrence rate is stated as applying to that complete planned",
        "set of {0} target stars.".format(planned),
        "",
        "## Prespecified screening",
        "",
        "Screening rule, fixed before data inspection: a planned target star is retained",
        "only if its photometric coverage fraction is at least {0} and its saturation".format(MIN_COVERAGE),
        "flag is 0.",
        "",
        "## Accounting",
        "",
        "- Planned target stars: {0}".format(planned),
        "- Retained after screening: {0}".format(n_retained),
        "- Removed by screening: {0}".format(n_removed),
        "- Stars with at least one detected white-light flare (events, among retained): {0}".format(events),
        "",
        "## Selected result",
        "",
        "[selected-result] White-light flare occurrence rate for the complete planned set of {0} target stars: {1} ({2}%), computed as {3} flaring stars / {4} exposure units.".format(planned, rate, percent, events, denominator),
        "",
        "## Protocol status",
        "",
        "No protocol amendment and no approved method deviation exists for this analysis.",
    ]
    return "\n".join(lines) + "\n"


def main():
    units = read_units()
    planned = len(units)
    retained = [u for u in units if passes_screening(u)]
    removed = [u for u in units if not passes_screening(u)]
    n_retained = len(retained)
    n_removed = len(removed)
    events = sum(1 for u in retained if u["flare_detected"] == "yes")
    denominator = n_retained
    text = build_report(planned, n_retained, n_removed, events, denominator)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="ascii", newline="\n") as handle:
        handle.write(text)
    print(text, end="")


if __name__ == "__main__":
    main()
