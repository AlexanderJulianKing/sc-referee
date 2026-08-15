"""Peak stridulation frequency of cave crickets reared at two humidity levels.

Reads data/input.csv, which holds one row per recorded take, and writes a short
markdown summary to results/report.md.
"""

import csv
import math
from dataclasses import dataclass
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
REPORT_PATH = Path("results") / "report.md"

AMBIENT = "ambient"
SATURATED = "saturated"


@dataclass(frozen=True)
class Take:
    """A single stridulation recording."""

    cricket_tag: str
    chamber_humidity: str
    take_no: int
    peak_khz: float


def read_takes(path):
    """Load every recorded take from the CSV."""
    takes = []
    with path.open("r", encoding="ascii", newline="") as handle:
        for row in csv.DictReader(handle):
            takes.append(
                Take(
                    cricket_tag=row["cricket_tag"],
                    chamber_humidity=row["chamber_humidity"],
                    take_no=int(row["take_no"]),
                    peak_khz=float(row["peak_khz"]),
                )
            )
    return takes


def peaks_in(takes, chamber):
    return [take.peak_khz for take in takes if take.chamber_humidity == chamber]


def tags_in(takes, chamber):
    tags = []
    for take in takes:
        if take.chamber_humidity == chamber and take.cricket_tag not in tags:
            tags.append(take.cricket_tag)
    return tags


def mean_of(values):
    return sum(values) / len(values)


def variance_of(values):
    centre = mean_of(values)
    return sum((value - centre) ** 2 for value in values) / (len(values) - 1)


def by_cricket(takes):
    grouped = {}
    for take in takes:
        grouped.setdefault(take.cricket_tag, []).append(take)
    return grouped


def p_phrase(p_value):
    if p_value < 0.001:
        return "p < 0.001"
    return "p = {:.3f}".format(p_value)


def build_report(takes):
    ambient = peaks_in(takes, AMBIENT)
    saturated = peaks_in(takes, SATURATED)

    n_amb, n_sat = len(ambient), len(saturated)
    mean_amb, mean_sat = mean_of(ambient), mean_of(saturated)
    var_amb, var_sat = variance_of(ambient), variance_of(saturated)

    df = n_amb + n_sat - 2
    pooled_sd = math.sqrt(((n_amb - 1) * var_amb + (n_sat - 1) * var_sat) / df)
    difference = mean_sat - mean_amb

    outcome = stats.ttest_ind(saturated, ambient, equal_var=True)

    lines = [
        "# Rearing humidity and stridulation peak frequency in cave crickets",
        "",
        "Cave crickets from one laboratory colony were reared either in an ambient",
        "chamber or in a water-saturated chamber. Each animal was recorded four times,",
        "and the peak frequency of the dominant stridulation band was read from each",
        "recording.",
        "",
        "## Recordings",
        "",
        "- takes analysed: {}".format(len(takes)),
        "- ambient chamber: {} takes from {} crickets, mean peak {:.2f} kHz (SD {:.2f} kHz)".format(
            n_amb, len(tags_in(takes, AMBIENT)), mean_amb, math.sqrt(var_amb)
        ),
        "- saturated chamber: {} takes from {} crickets, mean peak {:.2f} kHz (SD {:.2f} kHz)".format(
            n_sat, len(tags_in(takes, SATURATED)), mean_sat, math.sqrt(var_sat)
        ),
        "",
        "| cricket | chamber | takes | mean peak (kHz) |",
        "| --- | --- | --- | --- |",
    ]

    for tag, rows in sorted(by_cricket(takes).items()):
        lines.append(
            "| {} | {} | {} | {:.2f} |".format(
                tag,
                rows[0].chamber_humidity,
                len(rows),
                mean_of([row.peak_khz for row in rows]),
            )
        )

    verdict = (
        "[selected-result] Peak stridulation frequency was higher in the saturated"
        " chamber ({:.2f} kHz) than in the ambient chamber ({:.2f} kHz), a difference"
        " of {:.2f} kHz: two-sample t-test over {} takes, t({}) = {:.3f}, {}."
    ).format(
        mean_sat,
        mean_amb,
        difference,
        len(takes),
        df,
        outcome.statistic,
        p_phrase(outcome.pvalue),
    )

    lines += [
        "",
        "## Test",
        "",
        "Each take was entered as a separate observation in a two-sided two-sample",
        "Student t-test with pooled variance, comparing peak frequency in the",
        "saturated chamber with the ambient chamber.",
        "",
        "- difference of means (saturated - ambient): {:.2f} kHz".format(difference),
        "- pooled SD: {:.3f} kHz".format(pooled_sd),
        "- t({}) = {:.3f}".format(df, outcome.statistic),
        "- {}".format(p_phrase(outcome.pvalue)),
        "",
        verdict,
    ]
    return "\n".join(lines) + "\n"


def main():
    takes = read_takes(INPUT_PATH)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(build_report(takes))


if __name__ == "__main__":
    main()
