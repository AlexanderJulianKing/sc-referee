"""Compare oxidation peak current between two screen-printed graphene inks."""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")


def read_scans(path):
    """Return one tuple per recorded amperometric scan."""
    scans = []
    with path.open("r", encoding="ascii", newline="") as handle:
        for row in csv.DictReader(handle):
            scans.append(
                (
                    row["ink_formulation"],
                    row["electrode_id"],
                    float(row["peak_current_ua"]),
                )
            )
    return scans


def currents_by_ink(scans):
    grouped = {}
    for ink, _strip, current in scans:
        grouped.setdefault(ink, []).append(current)
    return grouped


def strips_by_ink(scans):
    grouped = {}
    for ink, strip, _current in scans:
        grouped.setdefault(ink, set()).add(strip)
    return grouped


def welch_dof(sample_a, sample_b):
    """Welch-Satterthwaite degrees of freedom for two samples."""
    term_a = statistics.variance(sample_a) / len(sample_a)
    term_b = statistics.variance(sample_b) / len(sample_b)
    numerator = (term_a + term_b) ** 2
    denominator = (
        term_a ** 2 / (len(sample_a) - 1) + term_b ** 2 / (len(sample_b) - 1)
    )
    return numerator / denominator


def compose_report(scans):
    currents = currents_by_ink(scans)
    strips = strips_by_ink(scans)
    inks = sorted(currents)
    reference, candidate = inks[0], inks[1]

    outcome = stats.ttest_ind(
        currents[candidate], currents[reference], equal_var=False
    )
    t_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)
    dof = welch_dof(currents[candidate], currents[reference])

    mean_reference = statistics.fmean(currents[reference])
    mean_candidate = statistics.fmean(currents[candidate])
    gap = mean_candidate - mean_reference

    if p_value < 1e-06:
        p_text = "p < 1e-06"
    else:
        p_text = "p = {0:.6f}".format(p_value)

    lines = [
        "# Peak Current Response of Screen-Printed Graphene Electrodes",
        "",
        "## Design",
        "",
        "Amperometric scans were collected from screen-printed graphene strips coated",
        "with one of two carbon ink formulations, GX7 and GX9. Each strip was mounted",
        "in the flow cell once and scanned four times in immediate succession against a",
        "fixed ferrocyanide standard; the oxidation peak current of each scan was",
        "recorded in microamperes (uA).",
        "",
        "| Formulation | Scans | Strips | Mean peak current (uA) | SD (uA) |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for ink in inks:
        lines.append(
            "| {0} | {1} | {2} | {3:.2f} | {4:.2f} |".format(
                ink,
                len(currents[ink]),
                len(strips[ink]),
                statistics.fmean(currents[ink]),
                statistics.stdev(currents[ink]),
            )
        )

    lines.extend(
        [
            "",
            "## Analysis",
            "",
            "Each recorded scan was entered as one observation and the two formulations",
            "were compared on peak current with a two-sided Welch two-sample t-test",
            "(unequal variances).",
            "",
            "## Result",
            "",
            "Mean peak current was {0:.2f} uA higher under {1} than under {2}".format(
                gap, candidate, reference
            ),
            "(t = {0:.2f}, df = {1:.1f}, {2}).".format(t_stat, dof, p_text),
            "",
            (
                "[selected-result] Welch two-sample t-test on scan-level peak "
                "current: {0} ({1:.2f} uA) exceeds {2} ({3:.2f} uA) by {4:.2f} uA, "
                "t = {5:.2f}, df = {6:.1f}, {7}."
            ).format(
                candidate,
                mean_candidate,
                reference,
                mean_reference,
                gap,
                t_stat,
                dof,
                p_text,
            ),
        ]
    )

    return "\n".join(lines) + "\n"


def main():
    scans = read_scans(INPUT_PATH)
    report = compose_report(scans)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
