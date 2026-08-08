import csv
from pathlib import Path

root = Path(__file__).resolve().parent.parent

rows = []
with (root / "inputs" / "data.csv").open(newline="") as f:
    for row in csv.DictReader(f):
        rows.append(row)

planned = len(rows)
retained = [r for r in rows if r["box_condition"] == "intact"]
removed = planned - len(retained)
events = sum(1 for r in retained if r["occupied"] == "yes")
rate_pct = 100.0 * events / len(retained)

lines = [
    "# Tree Swallow Occupancy in Intact Nest Boxes",
    "",
    "## Study accounting",
    "",
    f"- Planned nest boxes surveyed: {planned}",
    f"- Retained after intactness screening (intact boxes): {len(retained)}",
    f"- Removed at screening (damaged boxes): {removed}",
    f"- Occupancy events among retained boxes: {events}",
    "",
    "## Selected result",
    "",
    f"[selected-result] Among the {len(retained)} intact nest boxes retained after screening, {events} were occupied by tree swallows, an occupancy rate of {rate_pct:.1f}% ({events}/{len(retained)}).",
    "",
    "## Scope",
    "",
    "The scientific target of this analysis is exclusively the retained post-screening",
    f"subset of {len(retained)} intact nest boxes. The occupancy rate applies only to this retained",
    f"subset and must not be read as a rate over the complete planned set of {planned} boxes,",
    f"of which {removed} damaged boxes were removed at the prespecified screening step.",
]

out_dir = root / "results"
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "report.md").write_text("\n".join(lines) + "\n")
