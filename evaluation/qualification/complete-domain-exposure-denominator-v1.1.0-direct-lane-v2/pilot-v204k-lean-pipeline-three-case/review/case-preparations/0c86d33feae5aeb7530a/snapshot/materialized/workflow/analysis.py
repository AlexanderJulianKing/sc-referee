import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

with (ROOT / "inputs" / "data.csv").open(newline="") as fh:
    rows = list(csv.DictReader(fh))

planned = len(rows)
retained_rows = [r for r in rows if r["monitoring_complete"] == "yes"]
retained = len(retained_rows)
removed = planned - retained
events = sum(1 for r in retained_rows if r["owl_pair_present"] == "yes")
rate_pct = 100 * events / retained

lines = [
    "# Barn Owl Nest Box Occupancy Report",
    "",
    "## Study design",
    "",
    f"Planned observation units: {planned} wooden nest boxes installed along a single",
    "farmland survey transect in spring 2026. A prespecified screening step",
    "retained only boxes with a complete weekly monitoring record for the full",
    "season; boxes with an incomplete record were removed before analysis.",
    "",
    "## Accounting",
    "",
    f"- Planned nest boxes: {planned}",
    f"- Retained after screening (complete monitoring record): {retained}",
    f"- Removed by screening (incomplete monitoring record): {removed}",
    f"- Occupancy events (barn owl pair present) among retained boxes: {events}",
    "",
    "## Selected result",
    "",
    f"[selected-result] Among the {retained} retained nest boxes, {events} showed barn owl occupancy: {events}/{retained} = {rate_pct:.2f}% of the retained post-screening subset.",
    "",
    "## Scope note",
    "",
    "The scientific target of this analysis is exclusively the retained subset of",
    f"{retained} nest boxes that passed screening. No occupancy claim is made about",
    f"the {removed} removed boxes or about the complete planned set of {planned} boxes.",
]

out_dir = ROOT / "results"
out_dir.mkdir(parents=True, exist_ok=True)
with (out_dir / "report.md").open("w", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")
