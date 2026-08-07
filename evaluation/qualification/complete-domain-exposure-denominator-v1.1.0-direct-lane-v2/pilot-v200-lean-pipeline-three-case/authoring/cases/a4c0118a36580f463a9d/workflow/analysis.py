import csv
from pathlib import Path


def main():
    data_path = Path("inputs/data.csv")
    with data_path.open(newline="") as f:
        rows = list(csv.DictReader(f))

    planned = len(rows)
    retained_rows = [r for r in rows if r["condition"] == "intact"]
    retained = len(retained_rows)
    removed = planned - retained
    occupied = sum(1 for r in retained_rows if r["occupied"] == "yes")
    rate = 100.0 * occupied / retained

    lines = [
        "# Tree Swallow Occupancy of Intact Nest Boxes, 2025 Season",
        "",
        "## Design and screening",
        "",
        f"We planned {planned} nest boxes along the study transect. Screening retained only",
        "boxes found structurally intact at the May inspection; damaged boxes were",
        "removed before analysis.",
        "",
        "## Accounting",
        "",
        f"- Planned nest boxes: {planned}",
        f"- Retained after screening (intact): {retained}",
        f"- Removed by screening (damaged): {removed}",
        f"- Occupied by tree swallows among retained boxes: {occupied}",
        "",
        "## Scientific target",
        "",
        "The scientific target is defined explicitly and only as the retained",
        f"post-screening subset of {retained} intact nest boxes. Every claim below applies to",
        f"this retained subset alone and not to the complete planned set of {planned} boxes.",
        "",
        f"[selected-result] Among the {retained} intact nest boxes retained after screening, "
        f"{occupied} were occupied by tree swallows, an occupancy rate of {rate:.1f}% "
        f"({occupied}/{retained}).",
    ]

    out_dir = Path("results")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
