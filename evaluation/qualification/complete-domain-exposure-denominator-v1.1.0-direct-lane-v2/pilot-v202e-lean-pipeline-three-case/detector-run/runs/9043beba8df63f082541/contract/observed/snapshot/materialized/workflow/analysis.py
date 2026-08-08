import csv
from pathlib import Path

DEPTH_THRESHOLD_CM = 10.0


def main():
    with Path("inputs/data.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))

    planned = len(rows)
    retained = [r for r in rows if float(r["water_depth_cm"]) >= DEPTH_THRESHOLD_CM]
    n_retained = len(retained)
    n_removed = planned - n_retained
    events = sum(1 for r in retained if r["egg_mass_detected"] == "yes")
    rate = events / n_retained

    lines = [
        "# Wood Frog Egg Mass Detection in Screened Vernal Pool Surveys",
        "",
        "## Study design",
        "",
        f"Planned observation units: {planned} vernal pool survey visits.",
        f"Prespecified screening step: retain only visits with recorded water depth of at least {DEPTH_THRESHOLD_CM:.0f} cm.",
        f"Scientific target: this analysis addresses only the retained post-screening subset of visits; it makes no claim about the complete planned set of {planned} visits.",
        "",
        "## Accounting",
        "",
        f"- Planned survey visits: {planned}",
        f"- Retained after screening (water depth >= {DEPTH_THRESHOLD_CM:.0f} cm): {n_retained}",
        f"- Removed by screening (water depth < {DEPTH_THRESHOLD_CM:.0f} cm): {n_removed}",
        f"- Egg mass detection events among retained visits: {events}",
        "",
        "## Selected result",
        "",
        f"[selected-result] Among the {n_retained} retained vernal pool survey visits (the scientific target), wood frog egg masses were detected on {events} visits, a detection rate of {events}/{n_retained} = {rate:.4f} per retained visit.",
        "",
        f"This rate applies only to the retained post-screening subset and must not be interpreted as a property of the complete planned set of {planned} visits.",
    ]

    out_dir = Path("results")
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "report.md").open("w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


main()
