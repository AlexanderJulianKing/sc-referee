import csv
from pathlib import Path

root = Path(__file__).resolve().parent.parent

with (root / "inputs" / "data.csv").open(newline="") as fh:
    rows = list(csv.DictReader(fh))

planned = len(rows)
retained_rows = [r for r in rows if r["condition"] == "intact"]
retained = len(retained_rows)
removed = planned - retained
events = sum(1 for r in retained_rows if r["occupied"] == "yes")

# exact integer arithmetic in tenths of a percent to keep output deterministic
tenths = events * 1000 // retained
rate_str = f"{tenths // 10}.{tenths % 10}"

lines = [
    "# Bat Roost Box Occupancy Survey Report",
    "",
    "## Accounting",
    f"- Planned roost boxes surveyed: {planned}",
    f"- Removed by intactness screening (damaged boxes): {removed}",
    f"- Retained intact boxes (scientific target): {retained}",
    f"- Occupied boxes (event) among retained: {events}",
    "",
    "## Selected result",
    f"[selected-result] Among the {retained} retained intact roost boxes (the prespecified scientific target), {events} were occupied, an occupancy rate of {events}/{retained} = {rate_str}%.",
    "",
    "## Scope",
    f"This claim applies only to the retained post-screening subset of {retained} intact boxes and not to the complete planned set of {planned} boxes, which includes {removed} damaged boxes excluded before analysis.",
]

out_dir = root / "results"
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "report.md").write_text("\n".join(lines) + "\n")
