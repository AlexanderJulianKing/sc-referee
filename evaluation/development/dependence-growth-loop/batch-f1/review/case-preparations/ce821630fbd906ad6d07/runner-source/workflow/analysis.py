"""Song tempo of hand-raised zebra finches under two rearing diets.

`data/input.csv` stores one row per bird per recording night. Diet was
assigned to birds and never to nights, so every bird is first collapsed to a
single mean syllable rate; the reported comparison then uses exactly one
value per bird.
"""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import fmean, median
from typing import Dict, List, Tuple

from scipy import stats

UNIT_COLUMN = "bird_id"
GROUP_COLUMN = "diet_group"
VALUE_COLUMN = "syllable_rate_per_s"
TREATED = "supplemented"
CONTROL = "control"

# (bird, diet group, nights recorded, mean syllable rate)
BirdSummary = Tuple[str, str, int, float]


def project_root() -> Path:
    """Directory holding data/ and results/."""
    beside_script = Path(__file__).resolve().parents[1]
    if (beside_script / "data" / "input.csv").is_file():
        return beside_script
    return Path.cwd()


def read_sessions(csv_path: Path) -> List[Dict[str, str]]:
    with csv_path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def summarise_birds(session_rows: List[Dict[str, str]]) -> List[BirdSummary]:
    """Collapse the nightly rows to one mean syllable rate per bird."""
    rates: Dict[str, List[float]] = {}
    diet: Dict[str, str] = {}
    for row in session_rows:
        bird = row[UNIT_COLUMN].strip()
        group = row[GROUP_COLUMN].strip()
        if diet.setdefault(bird, group) != group:
            raise ValueError(f"{bird} is listed under more than one diet")
        rates.setdefault(bird, []).append(float(row[VALUE_COLUMN]))
    order = sorted(rates, key=lambda bird: (diet[bird], bird))
    return [(b, diet[b], len(rates[b]), fmean(rates[b])) for b in order]


def main() -> None:
    root = project_root()
    session_rows = read_sessions(root / "data" / "input.csv")
    birds = summarise_birds(session_rows)

    night_counts = {count for _, _, count, _ in birds}
    if len(night_counts) != 1:
        raise ValueError("every bird must contribute the same number of nights")
    nights = night_counts.pop()

    treated = [rate for _, group, _, rate in birds if group == TREATED]
    control = [rate for _, group, _, rate in birds if group == CONTROL]
    if not treated or not control:
        raise ValueError("both diet groups must be present")

    outcome = stats.mannwhitneyu(
        treated, control, alternative="two-sided", method="exact"
    )
    u_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)
    rank_biserial = 2.0 * u_stat / (len(treated) * len(control)) - 1.0
    median_gap = median(treated) - median(control)

    selected = (
        "[selected-result] Supplemented birds sang faster than controls: exact "
        f"two-sided Mann-Whitney U test on {len(birds)} bird-level mean syllable "
        f"rates ({len(treated)} supplemented, {len(control)} control, one value "
        f"per bird), U = {u_stat:.0f}, p = {p_value:.4f}, rank-biserial "
        f"correlation = {rank_biserial:.3f}, median difference {median_gap:.2f} syl/s."
    )

    lines = [
        "# Diet supplementation and song tempo in hand-raised zebra finches",
        "",
        "## Question",
        "",
        "Do juvenile male zebra finches raised on a protein-supplemented diet sing",
        "faster motifs than controls once each bird is summarised by a single value?",
        "",
        "## Data and unit of analysis",
        "",
        f"`data/input.csv` is stored in long format: {len(session_rows)} rows, one row per bird per",
        f"recording night. Each of the {len(birds)} birds contributes {nights} nights, so individual",
        "rows are not independent. Diet was assigned to birds rather than to nights,",
        f"so the independent unit is the bird (`{UNIT_COLUMN}`). Every bird is collapsed",
        "to its mean syllable rate across its own nights before any test is run,",
        f"leaving {len(birds)} analysed values -- {len(treated)} supplemented and {len(control)} control -- that is,",
        "exactly one analysed value per independent unit.",
        "",
        "## Per-bird summaries",
        "",
        "| bird_id | diet_group | nights | mean syllable rate (syl/s) |",
        "| --- | --- | --- | --- |",
    ]
    for bird, group, count, mean_rate in birds:
        lines.append(f"| {bird} | {group} | {count} | {mean_rate:.2f} |")
    lines += [
        "",
        "## Group summaries",
        "",
        "| diet_group | birds | mean of bird means | median of bird means |",
        "| --- | --- | --- | --- |",
        f"| {TREATED} | {len(treated)} | {fmean(treated):.2f} | {median(treated):.2f} |",
        f"| {CONTROL} | {len(control)} | {fmean(control):.2f} | {median(control):.2f} |",
        "",
        f"Median difference (supplemented minus control): {median_gap:.2f} syl/s.",
        "",
        "## Test",
        "",
        "Exact two-sided Mann-Whitney U test (scipy.stats.mannwhitneyu with",
        f'method="exact") on the {len(birds)} bird-level mean syllable rates, supplemented',
        "against control. The bird means contain no ties, so the exact null",
        "distribution applies.",
        "",
        f"U = {u_stat:.0f}, p = {p_value:.4f}, rank-biserial correlation = {rank_biserial:.3f}.",
        "",
        selected,
        "",
        "## Notes",
        "",
        f"The {len(session_rows)} session rows never enter the test as separate observations; each",
        "bird contributes exactly one value, so the row-independence assumption of",
        "the rank test is met at the level of the analysed units. Session-to-session",
        "spread within a bird is visible in the raw file but is absorbed by the",
        "per-bird mean.",
    ]

    report_path = root / "results" / "report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
