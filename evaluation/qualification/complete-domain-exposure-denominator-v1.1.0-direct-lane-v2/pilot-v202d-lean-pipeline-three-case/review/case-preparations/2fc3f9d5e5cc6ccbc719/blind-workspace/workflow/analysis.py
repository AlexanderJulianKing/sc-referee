import csv
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

data_path = Path("inputs/data.csv")
out_dir = Path("results")
out_dir.mkdir(parents=True, exist_ok=True)

with data_path.open(newline="") as f:
    rows = list(csv.DictReader(f))

planned = len(rows)
retained = [r for r in rows if r["condition"] == "intact"]
retained_n = len(retained)
removed = planned - retained_n
occupied = sum(1 for r in retained if r["occupied"] == "yes")

rate = Fraction(occupied, retained_n)
percent = Decimal(rate.numerator * 100) / Decimal(rate.denominator)

lines = [
    "# Bat Roost Box Occupancy Survey, Willow Creek Woodland",
    "",
    "## Accounting",
    "",
    f"- Planned roost boxes: {planned}",
    f"- Retained after intact-condition screening: {retained_n}",
    f"- Removed by screening (damaged or inaccessible): {removed}",
    f"- Occupancy events among retained boxes: {occupied}",
    "",
    "## Selected result",
    "",
    (
        f"[selected-result] Among the {retained_n} retained intact roost boxes "
        f"(the prespecified scientific target; the {removed} screened-out boxes "
        f"from the {planned} planned are excluded), {occupied} showed bat occupancy, "
        f"an occupancy rate of {percent:.1f}% ({occupied}/{retained_n})."
    ),
    "",
    (
        f"All claims here apply only to the retained post-screening subset of "
        f"{retained_n} intact boxes, not to the complete planned set of {planned} boxes."
    ),
]

(out_dir / "report.md").write_text("\n".join(lines) + "\n")
