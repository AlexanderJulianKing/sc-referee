import csv
from pathlib import Path


def exact_decimal(numerator, denominator):
    if denominator == 0:
        raise ValueError("A reported denominator is zero")
    whole, remainder = divmod(numerator, denominator)
    digits = []
    seen = set()
    while remainder:
        if remainder in seen:
            raise ValueError("A reported rate has a non-terminating decimal expansion")
        seen.add(remainder)
        remainder *= 10
        digit, remainder = divmod(remainder, denominator)
        digits.append(str(digit))
    if not digits:
        return str(whole)
    return str(whole) + "." + "".join(digits)


case_root = Path(__file__).resolve().parent.parent
with (case_root / "inputs" / "data.csv").open(newline="", encoding="ascii") as handle:
    rows = list(csv.DictReader(handle))

planned_rows = [row for row in rows if row["commissioned"] == "yes"]
planned = len(planned_rows)
complete_exposure = sum(row["calendar_exposure_complete"] == "yes" for row in planned_rows)
inspected_rows = [row for row in planned_rows if row["inspected"] == "yes"]
inspected = len(inspected_rows)
telemetry_complete = sum(row["telemetry_complete"] == "yes" for row in inspected_rows)
retained = sum(row["retained_after_screening"] == "yes" for row in planned_rows)
removed = sum(row["retained_after_screening"] == "no" for row in planned_rows)
events = sum(row["failure"] == "yes" for row in planned_rows)

if planned != retained + removed:
    raise ValueError("Screening accounting is incomplete")
if retained != telemetry_complete:
    raise ValueError("Retention and telemetry completion disagree")
if complete_exposure != planned:
    raise ValueError("Calendar exposure accounting is incomplete")

failure_rate = exact_decimal(events, planned)
failure_percent = exact_decimal(events * 100, planned)
quality_rate = exact_decimal(telemetry_complete, inspected)
quality_percent = exact_decimal(telemetry_complete * 100, inspected)

lines = [
    "# Instrument Study Report",
    "Planned commissioned slots: " + str(planned),
    "Complete calendar exposure accounting: " + str(complete_exposure) + "/" + str(planned) + " commissioned slots.",
    "Retained after telemetry screening: " + str(retained),
    "Removed by telemetry screening: " + str(removed),
    "Scientific failure events: " + str(events),
    "[selected-result] Complete-calendar failure intensity over all commissioned slots: "
    + str(events) + "/" + str(planned) + " = " + failure_rate + " (" + failure_percent + "%).",
    "Secondary quality value - telemetry completion among inspected slots: "
    + str(telemetry_complete) + "/" + str(inspected) + " = " + quality_rate + " (" + quality_percent + "%).",
    "The quality denominator is inspected slots; it does not define or enter the selected scientific endpoint.",
]
report = "\n".join(lines) + "\n"
(case_root / "results" / "report.md").write_text(report, encoding="ascii")
