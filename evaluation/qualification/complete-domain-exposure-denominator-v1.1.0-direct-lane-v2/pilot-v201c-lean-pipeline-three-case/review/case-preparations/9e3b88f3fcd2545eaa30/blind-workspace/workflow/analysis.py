import csv
from decimal import Decimal
from pathlib import Path


def main():
    with Path("inputs/data.csv").open(newline="", encoding="ascii") as f:
        rows = list(csv.DictReader(f))

    planned = len(rows)
    retained_rows = [r for r in rows if r["weather_ok"] == "yes"]
    retained = len(retained_rows)
    removed = planned - retained
    events = sum(1 for r in retained_rows if r["hawkmoth_detected"] == "1")

    rate_pct = (Decimal(events) / Decimal(retained) * Decimal(100)).quantize(Decimal("0.1"))

    lines = [
        "# Hawkmoth Detection in Dry-Weather Light-Trap Nights",
        "",
        "## Accounting",
        f"- Planned trap-nights: {planned}",
        f"- Retained trap-nights after weather screening (dry nights only): {retained}",
        f"- Removed trap-nights (rain recorded): {removed}",
        f"- Hawkmoth detection events among retained trap-nights: {events}",
        "",
        "## Target and result",
        f"The scientific target is defined explicitly and only as the retained post-screening subset of {retained} dry trap-nights; claims here do not extend to the complete planned set of {planned} trap-nights.",
        "",
        f"[selected-result] Among the {retained} retained dry trap-nights, hawkmoths were detected on {events} nights, a detection rate of {events}/{retained} = {rate_pct}%.",
    ]

    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
