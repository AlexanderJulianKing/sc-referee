"""Homing accuracy of tagged mason bee females at a rotated nest block."""

from __future__ import annotations

import csv
from pathlib import Path

from scipy.stats import binomtest

TABLE = Path("data/input.csv")
REPORT = Path("results/report.md")
CHANCE = 0.5
ALPHA = 0.05


def read_trips(path):
    with path.open(newline="", encoding="ascii") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def tally_by_female(trips):
    counts = {}
    for trip in trips:
        tag = trip["bee_tag"]
        hits, total = counts.get(tag, (0, 0))
        counts[tag] = (hits + int(trip["natal_tube_return"]), total + 1)
    return counts


def build_report(trips):
    hits = sum(int(trip["natal_tube_return"]) for trip in trips)
    n_trips = len(trips)
    accuracy = hits / n_trips
    per_female = tally_by_female(trips)
    outcome = binomtest(hits, n_trips, CHANCE, alternative="two-sided")
    verdict = "significant" if outcome.pvalue < ALPHA else "not significant"
    trip_counts = [total for _, total in per_female.values()]

    lines = [
        "# Natal-tube homing accuracy in tagged Osmia females",
        "",
        "## Data",
        "",
        f"- Source table: `{TABLE.as_posix()}`",
        f"- Provisioning trips scored: {n_trips}",
        f"- Tagged females contributing trips: {len(per_female)}",
        f"- Trips ending in the natal tube: {hits}",
        f"- Pooled accuracy: {accuracy:.3f}",
        "",
        "## Procedure",
        "",
        "Every provisioning trip in the table was treated as one Bernoulli trial, scored",
        "1 when the female re-entered her own tube and 0 when she entered a different",
        f"tube. The {n_trips} trips were pooled into a single count and compared with the chance",
        f"expectation of {CHANCE:.3f} using an exact two-sided binomial test",
        '(`scipy.stats.binomtest`, alternative "two-sided").',
        "",
        "## Result",
        "",
        (
            f"[selected-result] Exact two-sided binomial test of {hits} natal-tube returns "
            f"in {n_trips} pooled trips against p0 = {CHANCE:.3f}: accuracy = {accuracy:.3f}, "
            f"p = {outcome.pvalue:.6f}, {verdict} at alpha = {ALPHA:.2f}."
        ),
        "",
        "## Per-female tallies",
        "",
        "| bee_tag | trips | natal returns | accuracy |",
        "| --- | --- | --- | --- |",
    ]
    for tag, (tag_hits, tag_total) in per_female.items():
        lines.append(f"| {tag} | {tag_total} | {tag_hits} | {tag_hits / tag_total:.3f} |")
    lines.append("")
    lines.append(f"Trip counts per female range from {min(trip_counts)} to {max(trip_counts)}.")
    return "\n".join(lines) + "\n"


def main():
    trips = read_trips(TABLE)
    text = build_report(trips)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
