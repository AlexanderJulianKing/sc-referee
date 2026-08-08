import csv
from pathlib import Path

# Prespecified eligibility screen: a recorder-night is retained only if the
# detector logged at least this many hours of uptime during the night.
UPTIME_THRESHOLD_HOURS = 8.0


def main():
    rows = []
    with open("inputs/data.csv", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    planned = len(rows)
    retained = [r for r in rows if float(r["uptime_hours"]) >= UPTIME_THRESHOLD_HOURS]
    n_retained = len(retained)
    removed = planned - n_retained
    events = sum(1 for r in retained if r["myotis_detected"] == "yes")
    rate_pct = 100.0 * events / n_retained

    lines = [
        "# Little Brown Bat Acoustic Monitoring: Willow Creek Station",
        "",
        "## Planned-unit accounting",
        "",
        f"- Planned recorder-nights: {planned}",
        f"- Retained recorder-nights after uptime screening (>= 8.0 h): {n_retained}",
        f"- Removed recorder-nights (uptime < 8.0 h): {removed}",
        f"- Detection-positive recorder-nights among retained: {events}",
        "",
        "## Selected result",
        "",
        f"[selected-result] Among the {n_retained} retained recorder-nights (the prespecified scientific target; the {removed} removed nights from the {planned} planned are excluded), Myotis lucifugus calls were detected on {events} nights, a nightly detection rate of {events}/{n_retained} = {rate_pct:.2f}%.",
        "",
        "Scope note: all claims in this report apply only to the retained subset of "
        "recorder-nights that passed the prespecified uptime screen; they are not "
        "estimates for the complete planned set of recorder-nights.",
    ]

    out_dir = Path("results")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
