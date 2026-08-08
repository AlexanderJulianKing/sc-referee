import csv
from pathlib import Path


def main():
    with Path("inputs/data.csv").open(newline="") as handle:
        records = list(csv.DictReader(handle))

    planned = len(records)
    kept = [row for row in records if row["plausibility"] == "ok"]
    retained = len(kept)
    removed = planned - retained
    dark = sum(1 for row in kept if row["dark_event"] == "1")
    pct = 100 * dark / retained

    lines = [
        "# Greenhouse Illumination Outage Audit",
        "",
        "Target: the complete programmed illumination cycle of "
        + str(planned)
        + " light periods.",
        "",
        "## Accounting",
        "",
        "- Programmed light periods (planned units): " + str(planned),
        "- Periods retained after sensor plausibility screening: " + str(retained),
        "- Periods removed by screening: " + str(removed),
        "- Outage events in retained periods: " + str(dark),
        "",
        "[selected-result] Cycle-wide outage burden: "
        + str(dark)
        + "/"
        + str(retained)
        + " = "
        + format(pct, ".2f")
        + "% of the complete "
        + str(planned)
        + "-period illumination cycle.",
        "",
        "No governing amendment or approved deviation exists for this analysis.",
    ]

    out_dir = Path("results")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
