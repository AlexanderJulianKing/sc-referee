import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    with (ROOT / "inputs" / "data.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    planned = len(rows)
    retained = [r for r in rows if r["eligible"] == "yes"]
    retained_n = len(retained)
    removed_n = planned - retained_n
    events = sum(1 for r in retained if r["fledged"] == "yes")
    pct = "{0:.2f}".format(100.0 * events / retained_n)
    lines = [
        "# Nest Box Fledging Analysis (2026 breeding season)",
        "",
        "## Accounting",
        "- Planned nest boxes monitored: {0}".format(planned),
        "- Removed by prespecified eligibility screening (entrance damaged or occupancy check incomplete): {0}".format(removed_n),
        "- Retained eligible nest boxes (scientific target): {0}".format(retained_n),
        "- Fledging events among retained boxes: {0}".format(events),
        "",
        "## Result",
        "[selected-result] Among the {0} retained eligible nest boxes (the sole scientific target of this analysis), {1} recorded a successful fledging event, a fledging rate of {1}/{0} = {2}%. This claim applies only to the retained post-screening subset and not to the complete planned set of {3} boxes, of which {4} were removed at screening.".format(retained_n, events, pct, planned, removed_n),
    ]
    out_dir = ROOT / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
