import csv
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

rows = []
with (ROOT / "inputs" / "data.csv").open(newline="") as f:
    for row in csv.DictReader(f):
        rows.append(row)

planned = len(rows)
retained_rows = [r for r in rows if int(r["hydroperiod_days"]) >= 30]
retained = len(retained_rows)
removed = planned - retained
events = sum(1 for r in retained_rows if r["egg_mass_present"] == "yes")

pct = Fraction(events, retained) * 100
pct_str = f"{pct.numerator / pct.denominator:.1f}"

lines = [
    "# Wood Frog Egg Mass Survey: Vernal Pool Cohort Report",
    "",
    "## Study design and accounting",
    "",
    f"- Planned observation units: {planned} vernal pools",
    f"- Retained after hydroperiod screening (>= 30 days): {retained} pools",
    f"- Removed by screening (< 30 days): {removed} pools",
    f"- Event count (wood frog egg masses detected among retained pools): {events}",
    "",
    "## Target population",
    "",
    "The scientific target of this analysis is defined explicitly and only as the",
    f"retained post-screening subset: the {retained} vernal pools with a measured hydroperiod",
    "of at least 30 days. All claims below apply to that retained subset alone and",
    f"must not be extrapolated to the complete planned set of {planned} pools, which includes",
    f"{removed} short-hydroperiod pools excluded by the prespecified screening step.",
    "",
    f"[selected-result] Among the {retained} retained vernal pools (hydroperiod >= 30 days), wood frog egg masses were detected in {events} pools, a detection rate of {events}/{retained} = {pct_str}% of the retained subset.",
    "",
    "## Consistency check",
    "",
    f"Planned ({planned}) = retained ({retained}) + removed ({removed}); events ({events}) are counted only within the retained subset.",
]

out_dir = ROOT / "results"
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
