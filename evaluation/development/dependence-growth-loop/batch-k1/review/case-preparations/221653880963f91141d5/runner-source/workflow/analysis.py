"""Entrance-reducer design and honey bee overwintering survival.

One research apiary, one row per colony: every colony carries a single spring
survival call, so the design-by-outcome table counts independent colonies and
is analysed with Fisher's exact test.
"""

from __future__ import annotations

import csv
from pathlib import Path

from scipy.stats import fisher_exact

DESIGNS = ("notched", "open")
LIVE = "survived"
DEAD = "died"


def locate_base() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in (Path.cwd(), here.parent, here):
        if (candidate / "data" / "input.csv").is_file():
            return candidate
    raise SystemExit("could not locate data/input.csv")


def load_colonies(path: Path):
    with path.open(newline="", encoding="ascii") as handle:
        colonies = list(csv.DictReader(handle))
    if not colonies:
        raise SystemExit("data/input.csv holds no colonies")
    tags = [row["colony_id"] for row in colonies]
    if len(set(tags)) != len(tags):
        raise SystemExit("every colony_id must appear on exactly one row")
    for row in colonies:
        if row["entrance_design"] not in DESIGNS:
            raise SystemExit("unexpected entrance_design: " + row["entrance_design"])
        if row["overwinter_outcome"] not in (LIVE, DEAD):
            raise SystemExit("unexpected overwinter_outcome: " + row["overwinter_outcome"])
    return colonies


class Arm:
    """One entrance-reducer design, summarised over its own colonies."""

    def __init__(self, design, rows):
        self.design = design
        self.size = len(rows)
        self.lived = sum(1 for row in rows if row["overwinter_outcome"] == LIVE)
        self.lost = self.size - self.lived
        self.frames = sum(float(row["autumn_bee_frames"]) for row in rows) / self.size
        self.mites = sum(float(row["varroa_per_100_bees"]) for row in rows) / self.size

    @property
    def survival(self):
        return self.lived / self.size


def build_report(notched, plain, table, p_value):
    total = notched.size + plain.size
    diff = notched.survival - plain.survival
    odds = (notched.lived * plain.lost) / (notched.lost * plain.lived)
    lines = [
        "# Entrance-reducer design and honey bee overwintering survival",
        "",
        "## Design",
        "",
        f"{total} queenright colonies in one research apiary were assigned by",
        "coin toss to one of two winter entrance-reducer designs. Each colony was",
        "opened once, at the spring inspection, and scored survived or died. A colony",
        "contributes exactly one row, so the survival calls are one per independent",
        "unit and the design-by-outcome table below counts colonies, not visits.",
        "",
        "## Colony counts",
        "",
        "| Entrance design | Survived | Died | Colonies | Survival |",
        "| --- | --- | --- | --- | --- |",
        f"| {notched.design} | {notched.lived} | {notched.lost} | {notched.size} | {notched.survival:.3f} |",
        f"| {plain.design} | {plain.lived} | {plain.lost} | {plain.size} | {plain.survival:.3f} |",
        "",
        f"Autumn strength was balanced at assignment: {notched.frames:.2f} bee-covered",
        f"frames on average for {notched.design} colonies against {plain.frames:.2f} for",
        f"{plain.design} colonies, with mean autumn mite loads of {notched.mites:.2f} and",
        f"{plain.mites:.2f} mites per 100 bees.",
        "",
        "## Test",
        "",
        "Fisher's exact test, two-sided, on the 2 x 2 table of entrance design by",
        f"overwinter outcome: {table}.",
        "",
        f"- Survival difference ({notched.design} minus {plain.design}): {diff:.3f}",
        f"- Sample odds ratio: {odds:.3f}",
        f"- Two-sided p-value: {p_value:.4f}",
        "",
        (
            f"[selected-result] Fisher's exact test on {total} independent colonies "
            f"(one row per colony) returns a two-sided p-value of {p_value:.4f}: "
            f"{notched.lived}/{notched.size} ({notched.survival:.3f}) of {notched.design} "
            f"colonies overwintered against {plain.lived}/{plain.size} "
            f"({plain.survival:.3f}) of {plain.design} colonies."
        ),
        "",
        "## Reading",
        "",
        "Because each colony is observed once, there is no within-colony replication",
        "to absorb and the row count equals the number of independent units. The",
        "exact conditional test is used in preference to a chi-square approximation",
        "at these cell counts, and no odds-ratio interval is quoted because the",
        "conditional estimate is poorly determined with single-digit cells.",
        "",
    ]
    return "\n".join(lines)


def main():
    base = locate_base()
    colonies = load_colonies(base / "data" / "input.csv")
    notched = Arm("notched", [r for r in colonies if r["entrance_design"] == "notched"])
    plain = Arm("open", [r for r in colonies if r["entrance_design"] == "open"])
    table = [[notched.lived, notched.lost], [plain.lived, plain.lost]]
    p_value = fisher_exact(table)[1]
    report = build_report(notched, plain, table, p_value)
    target = base / "results" / "report.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
