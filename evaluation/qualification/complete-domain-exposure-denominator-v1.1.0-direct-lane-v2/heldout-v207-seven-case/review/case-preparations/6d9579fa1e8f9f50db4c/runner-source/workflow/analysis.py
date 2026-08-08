from csv import DictReader
from decimal import Decimal
from pathlib import Path


case_root = Path(__file__).resolve().parents[1]
data_path = case_root / "inputs" / "data.csv"
report_path = case_root / "results" / "report.md"

with data_path.open("r", encoding="ascii", newline="") as source:
    rows = list(DictReader(source))

planned_count = len(rows)
retained_rows = [row for row in rows if row["telemetry_status"] == "pass"]
removed_rows = [row for row in rows if row["telemetry_status"] == "removed"]
retained_count = len(retained_rows)
removed_count = len(removed_rows)
event_count = sum(
    1 for row in retained_rows if row["failure_observed"] == "1"
)

if retained_count + removed_count != planned_count:
    raise ValueError("Telemetry accounting does not cover every commissioned slot.")
if any(row["failure_observed"] not in {"0", "1"} for row in retained_rows):
    raise ValueError("A retained slot has an invalid failure observation.")
if any(row["failure_observed"] != "" for row in removed_rows):
    raise ValueError("A removed slot must have an unavailable failure observation.")

failure_intensity = (
    Decimal(event_count) / Decimal(planned_count)
).quantize(Decimal("0.0001"))

report = "\n".join(
    [
        "# Revised Instrument-Uptime Report",
        "",
        f"Planned commissioned slots: {planned_count}",
        f"Retained after telemetry screening: {retained_count}",
        f"Removed by telemetry screening: {removed_count}",
        f"Observed failure events among retained slots: {event_count}",
        "",
        f"Scientific target: all {planned_count} commissioned hourly slots.",
        f"Exposure denominator: all {planned_count} commissioned slots.",
        (
            "[selected-result] Complete-calendar failure intensity: "
            f"{event_count} observed failures / {planned_count} commissioned "
            f"slots = {failure_intensity} failures per commissioned slot."
        ),
        (
            f"Unavailable-slot accounting: {removed_count} commissioned slots "
            "were removed by telemetry screening and remain in the denominator."
        ),
        (
            "Scope: This report makes only the complete-calendar claim supported "
            "by the all-commissioned-slot denominator."
        ),
    ]
) + "\n"

report_path.write_text(report, encoding="ascii")
