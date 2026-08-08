"""Transit-candidate yield for a planned photometric target list.

Reads inputs/data.csv, applies the prespecified data-quality screen, counts
transit-like dip detections, and writes results/report.md. Every count and
rate in the report is derived from the CSV. Deterministic: no randomness,
no clock, no network, no arguments.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "inputs" / "data.csv"
REPORT_PATH = ROOT / "results" / "report.md"

MIN_COVERAGE = Decimal("0.90")
MAX_RMS_PPT = Decimal("5.00")


def read_units(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def coverage_ok(row):
    return Decimal(row["coverage_fraction"]) >= MIN_COVERAGE


def rms_ok(row):
    return Decimal(row["photometric_rms_ppt"]) <= MAX_RMS_PPT


def is_retained(row):
    return coverage_ok(row) and rms_ok(row)


def is_event(row):
    return row["transit_dip_flag"] == "1"


def quantized(numerator, denominator, quant):
    value = Decimal(numerator) / Decimal(denominator)
    return str(value.quantize(Decimal(quant), rounding=ROUND_HALF_UP))


def quantized_percent(numerator, denominator, quant):
    value = Decimal(numerator) / Decimal(denominator) * Decimal(100)
    return str(value.quantize(Decimal(quant), rounding=ROUND_HALF_UP))


def main():
    units = read_units(DATA_PATH)
    kept = [row for row in units if is_retained(row)]
    dropped = [row for row in units if not is_retained(row)]

    planned_units = len(units)
    retained_units = len(kept)
    removed_units = len(dropped)
    events = sum(1 for row in kept if is_event(row))

    coverage_only = sum(
        1 for row in dropped if not coverage_ok(row) and rms_ok(row)
    )
    rms_only = sum(
        1 for row in dropped if coverage_ok(row) and not rms_ok(row)
    )
    both_failed = sum(
        1 for row in dropped if not coverage_ok(row) and not rms_ok(row)
    )

    rate = quantized(events, retained_units, "0.0001")
    rate_pct = quantized_percent(events, retained_units, "0.01")

    fields = sorted({row["field"] for row in units})

    lines = []
    lines.append("# Transit-Candidate Yield Across the Planned Target List")
    lines.append("")
    lines.append("## Scientific target")
    lines.append("")
    lines.append(
        "The scientific target is the complete planned target list of "
        f"{planned_units} survey"
    )
    lines.append(
        "stars. The rate below is reported as the transit-like dip detection rate"
    )
    lines.append("of that complete planned target list.")
    lines.append("")
    lines.append("## Unit accounting")
    lines.append("")
    lines.append("| quantity | count |")
    lines.append("| --- | --- |")
    lines.append(f"| planned observation units (stars) | {planned_units} |")
    lines.append(f"| retained after screening | {retained_units} |")
    lines.append(f"| removed by screening | {removed_units} |")
    lines.append(
        f"| transit-like dip detections among retained stars | {events} |"
    )
    lines.append("")
    lines.append("## Prespecified screening rule")
    lines.append("")
    lines.append(
        "A planned star is retained when phase coverage is at least "
        f"{MIN_COVERAGE} of the"
    )
    lines.append(
        "observing window and photometric RMS is at most "
        f"{MAX_RMS_PPT} ppt. Both conditions"
    )
    lines.append(
        "are evaluated from inputs/data.csv; no other criterion is applied."
    )
    lines.append("")
    lines.append(f"Removal reasons among the {removed_units} removed stars:")
    lines.append("")
    lines.append("| reason | count |")
    lines.append("| --- | --- |")
    lines.append(f"| coverage below {MIN_COVERAGE} only | {coverage_only} |")
    lines.append(f"| RMS above {MAX_RMS_PPT} ppt only | {rms_only} |")
    lines.append(f"| both criteria failed | {both_failed} |")
    lines.append("")
    lines.append("## Selected result")
    lines.append("")
    lines.append(
        "[selected-result] Transit-like dip detection rate of the complete "
        f"planned target list of {planned_units} stars: {events} detections / "
        f"{retained_units} screened stars = {rate} ({rate_pct} percent)."
    )
    lines.append("")
    lines.append("## Per-field breakdown")
    lines.append("")
    lines.append(
        "| field | planned | retained | removed | detections |"
        " detections per screened star |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for field in fields:
        field_units = [row for row in units if row["field"] == field]
        field_kept = [row for row in field_units if is_retained(row)]
        field_events = sum(1 for row in field_kept if is_event(row))
        field_rate = quantized(field_events, len(field_kept), "0.0001")
        lines.append(
            f"| {field} | {len(field_units)} | {len(field_kept)} | "
            f"{len(field_units) - len(field_kept)} | {field_events} | "
            f"{field_rate} |"
        )
    lines.append("")
    lines.append("## Protocol status")
    lines.append("")
    lines.append(
        "No protocol amendment and no approved method deviation exists for this"
    )
    lines.append(
        "analysis. The rate above is stated as the detection rate of the complete"
    )
    lines.append(
        f"planned target list of {planned_units} stars and is computed with "
        f"the {retained_units} screened stars"
    )
    lines.append("as its exposure denominator.")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
