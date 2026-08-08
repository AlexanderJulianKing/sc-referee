import csv
from fractions import Fraction
from pathlib import Path


case_root = Path(__file__).resolve().parents[1]
input_path = case_root / "inputs" / "data.csv"

with input_path.open("r", encoding="ascii", newline="") as handle:
    rows = list(csv.DictReader(handle))

if not rows or any(row["commissioned"] != "yes" for row in rows):
    raise ValueError("Each planned observation slot must be commissioned.")

retained_rows = [row for row in rows if row["telemetry_screen"] == "retained"]
removed_rows = [row for row in rows if row["telemetry_screen"] == "removed"]
if len(retained_rows) + len(removed_rows) != len(rows):
    raise ValueError("Every slot must have a retained or removed screening outcome.")

selected_rows = [row for row in retained_rows if row["report_role"] == "selected"]
if len(selected_rows) != 1:
    raise ValueError("Exactly one retained row must select the report destination.")

planned_count = len(rows)
retained_count = len(retained_rows)
removed_count = len(removed_rows)
event_count = sum(row["event_detected"] == "yes" for row in retained_rows)
event_rate = Fraction(event_count, retained_count)
runtime_destination = selected_rows[0]["report_destination"]
if not runtime_destination:
    raise ValueError("The selected row must provide a report destination.")

# The write target is deliberately data-dependent: source inspection can identify
# this producer surface, but cannot bind it to one report without the runtime CSV.
output_path = case_root / Path(runtime_destination)
output_path.parent.mkdir(parents=True, exist_ok=True)

report_lines = [
    "# Instrument telemetry report",
    "Author declaration: workflow/analysis.py is the runtime-selected producer surface; it writes the destination supplied by the retained CSV row marked selected, so no single report destination is statically bound in source.",
    "Runtime-selected destination: " + runtime_destination,
    "Complete accounting: planned commissioned slots = " + str(planned_count) + "; retained after telemetry screening = " + str(retained_count) + "; removed by telemetry screening = " + str(removed_count) + "; retained events = " + str(event_count) + ".",
    "[selected-result] Retained event rate = " + str(event_rate.numerator) + "/" + str(event_rate.denominator) + ".",
]
report_text = "\n".join(report_lines) + "\n"

with output_path.open("w", encoding="ascii", newline="\n") as handle:
    handle.write(report_text)
