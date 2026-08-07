import csv
from pathlib import Path

MIN_HYDROPERIOD_DAYS = 60


def main():
    with Path("inputs/data.csv").open(newline="", encoding="ascii") as fh:
        rows = list(csv.DictReader(fh))
    planned = len(rows)
    retained = [
        r for r in rows if int(r["hydroperiod_days"]) >= MIN_HYDROPERIOD_DAYS
    ]
    retained_n = len(retained)
    removed_n = planned - retained_n
    events = sum(1 for r in retained if r["egg_mass_detected"] == "yes")
    rate = f"{100.0 * events / retained_n:.2f}"

    lines = [
        "# Wood Frog Egg Mass Survey: Vernal Pool Hydroperiod Screening",
        "",
        "## Accounting",
        "",
        f"- Planned survey pools: {planned}",
        f"- Retained after hydroperiod screening (>= {MIN_HYDROPERIOD_DAYS} days): {retained_n}",
        f"- Removed by screening (< {MIN_HYDROPERIOD_DAYS} days): {removed_n}",
        f"- Retained pools with wood frog egg masses detected: {events}",
        "",
        "## Scientific target",
        "",
        f"The scientific target is defined explicitly and only as the {retained_n}",
        "retained pools that met the prespecified hydroperiod eligibility",
        f"criterion (>= {MIN_HYDROPERIOD_DAYS} days of standing water). Every claim below is",
        "confined to that retained subset and is distinct from the complete",
        f"planned set of {planned} pools; the {removed_n} screened-out pools are excluded",
        "from the denominator by design.",
        "",
        f"[selected-result] Among the {retained_n} retained vernal pools, wood frog egg masses were detected in {events} pools, a detection rate of {rate}% ({events}/{retained_n}) of the retained subset.",
    ]
    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
