import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

DATA = Path("inputs/data.csv")
OUT = Path("results/report.md")


def main():
    with DATA.open(newline="") as f:
        rows = list(csv.DictReader(f))
    planned = len(rows)
    retained = [
        r for r in rows
        if r["equipment_fault"] == "no"
        and Decimal(r["min_temp_c"]) >= Decimal("10.0")
    ]
    n = len(retained)
    removed = planned - n
    events = sum(1 for r in retained if r["hawkmoth_captured"] == "yes")
    rate = (Decimal(events) / Decimal(n)).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP)
    lines = [
        "# Hawkmoth Capture Rate in a Light-Trap Survey",
        "",
        "## Study accounting",
        "",
        f"- Planned observation units (trap-nights): {planned}",
        f"- Retained after eligibility screening (no equipment fault and minimum temperature >= 10.0 C): {n}",
        f"- Removed by screening: {removed}",
        f"- Hawkmoth capture events among retained trap-nights: {events}",
        "",
        "## Scientific target",
        "",
        "The scientific target of this analysis is defined explicitly and only as the",
        f"retained post-screening subset of {n} eligible trap-nights. All claims below",
        f"apply to that retained subset, not to the complete planned set of {planned}",
        "trap-nights.",
        "",
        f"[selected-result] Among the {n} retained eligible trap-nights, {events} recorded at least one hawkmoth (Sphingidae) capture, a capture rate of {events}/{n} = {rate}.",
        "",
        f"This capture rate uses the retained post-screening subset (n = {n}) as its",
        f"denominator and makes no claim about the {removed} screened-out trap-nights or about",
        f"the complete planned set of {planned} trap-nights.",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="ascii")


main()
