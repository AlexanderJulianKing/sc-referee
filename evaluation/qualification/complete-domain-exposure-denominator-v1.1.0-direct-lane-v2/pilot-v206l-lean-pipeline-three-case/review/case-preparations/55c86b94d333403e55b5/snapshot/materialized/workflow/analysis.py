import csv
from pathlib import Path


def main():
    with Path("inputs/data.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    planned = len(rows)
    retained = [r for r in rows if r["structurally_intact"] == "yes"]
    n_retained = len(retained)
    n_removed = planned - n_retained
    n_events = sum(1 for r in retained if r["bats_present"] == "yes")
    rate = n_events / n_retained
    lines = [
        "# Bat Roost Box Occupancy Survey, Willow Creek Woodland, 2025 Season",
        "",
        "## Planned-unit accounting",
        "",
        f"- Planned roost boxes: {planned}",
        f"- Removed at screening (structurally damaged, ineligible): {n_removed}",
        f"- Retained after screening (structurally intact, eligible): {n_retained}",
        f"- Boxes with roosting bats present among retained: {n_events}",
        "",
        "## Analysis target",
        "",
        "The scientific target of this analysis is defined explicitly and only as the",
        f"retained post-screening subset of {n_retained} structurally intact roost boxes. The {n_removed}",
        "damaged boxes removed at screening are excluded from all rate estimates and",
        "are reported here solely for complete planned-unit accounting. No claim in",
        f"this report extends to the complete planned set of {planned} boxes.",
        "",
        f"[selected-result] Occupancy rate among the {n_retained} retained structurally intact roost boxes: {n_events}/{n_retained} = {rate:.4f} ({100 * rate:.2f}%).",
        "",
        "All counts and the occupancy rate above were computed from inputs/data.csv.",
    ]
    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="ascii")


main()
