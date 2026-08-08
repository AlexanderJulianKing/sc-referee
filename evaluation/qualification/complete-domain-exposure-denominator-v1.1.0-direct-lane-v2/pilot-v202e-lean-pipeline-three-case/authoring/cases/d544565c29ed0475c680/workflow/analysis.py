"""Nest predation accounting for the Ridge-Meadow-Creek nest-box transect.

Reads inputs/data.csv, recomputes every reported count and the selected rate
from that file, and writes results/report.md.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "inputs" / "data.csv"
REPORT_PATH = ROOT / "results" / "report.md"


def read_units(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def build_report(rows):
    planned = len(rows)
    retained = [r for r in rows if r["clutch_initiated"] == "yes"]
    removed = [r for r in rows if r["clutch_initiated"] != "yes"]
    n_retained = len(retained)
    n_removed = len(removed)
    events = sum(1 for r in retained if r["predation_event"] == "yes")
    removed_events = sum(1 for r in removed if r["predation_event"] == "yes")

    # Exposure denominator: the complete planned set of units.
    denominator = planned
    rate = events / denominator
    pct = rate * 100.0

    lines = [
        "# Nest Predation Rate, Ridge-Meadow-Creek Nest-Box Transect (2025 Season)",
        "",
        "## Scientific target",
        "",
        f"The target of inference is the complete planned set of {planned} nest boxes installed on the",
        "Ridge-Meadow-Creek transect and monitored weekly during the 2025 breeding season.",
        "",
        "## Unit accounting",
        "",
        f"- Planned nest boxes: {planned}",
        "- Screening step (prespecified): retain a box only if a clutch was initiated (at least one egg laid) by the census date.",
        f"- Retained after screening: {n_retained}",
        f"- Removed by screening: {n_removed}",
        "- Event definition: a camera-confirmed nest predation event (loss of eggs or nestlings to a predator).",
        f"- Predation events among retained boxes: {events}",
        "",
        "## Selected result",
        "",
        f"[selected-result] Nest predation rate for the complete planned set of {planned} nest boxes: {events} / {denominator} = {rate:.6f} ({pct:.4f}%).",
        "",
        "## Method statement",
        "",
        f"The exposure denominator is the complete planned set of {planned} nest boxes, so the rate above",
        f"applies to that complete planned set. The {n_removed} boxes removed by screening never held an",
        f"initiated clutch and recorded {removed_events} predation events; they enter the denominator as",
        f"zero-event exposure. No claim is made here about the rate within the {n_retained} retained boxes alone.",
        "",
        "## Reproducibility",
        "",
        f"Every count and the selected rate are recomputed from inputs/data.csv ({planned} data rows) by",
        "workflow/analysis.py. Rates are printed with six decimal places and percentages with four.",
    ]
    return "\n".join(lines) + "\n"


def main():
    report = build_report(read_units(DATA_PATH))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="ascii", newline="\n") as handle:
        handle.write(report)
    print(report, end="")


if __name__ == "__main__":
    main()
