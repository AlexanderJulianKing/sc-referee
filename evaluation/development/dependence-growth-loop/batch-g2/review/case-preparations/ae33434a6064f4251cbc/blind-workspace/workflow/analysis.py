"""Critical thermal maximum of shore limpets in two tidal zones.

Reads data/input.csv, compares the CTmax column between the low-shore and
high-shore groups with a two-sample t-test, and writes results/report.md.
"""

import csv
import math
import os
from collections import OrderedDict

from scipy import stats

INPUT_PATH = os.path.join("data", "input.csv")
OUTPUT_PATH = os.path.join("results", "report.md")

ZONES = ("low", "high")
ZONE_TITLE = {"low": "Low shore", "high": "High shore"}


def read_table(path):
    with open(path, newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def split_by_zone(rows):
    ctmax = OrderedDict((zone, []) for zone in ZONES)
    animals = OrderedDict((zone, []) for zone in ZONES)
    for row in rows:
        zone = row["shore_zone"].strip()
        ctmax[zone].append(float(row["ctmax_c"]))
        tag = row["limpet_id"].strip()
        if tag not in animals[zone]:
            animals[zone].append(tag)
    return ctmax, animals


def mean_sd(values):
    n = len(values)
    mean = math.fsum(values) / n
    ss = math.fsum((value - mean) ** 2 for value in values)
    return mean, math.sqrt(ss / (n - 1))


def build_report(ctmax, animals):
    summary = OrderedDict()
    for zone in ZONES:
        values = ctmax[zone]
        mean, sd = mean_sd(values)
        summary[zone] = {
            "animals": len(animals[zone]),
            "n": len(values),
            "reps": len(values) // len(animals[zone]),
            "mean": mean,
            "sd": sd,
        }

    outcome = stats.ttest_ind(ctmax["low"], ctmax["high"], equal_var=True)
    t_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)
    total = summary["low"]["n"] + summary["high"]["n"]
    df = total - 2
    gap = summary["high"]["mean"] - summary["low"]["mean"]
    p_text = "p < 0.0001" if p_value < 1e-4 else "p = {0:.4f}".format(p_value)

    lines = [
        "# Critical thermal maximum of shore limpets in two tidal zones",
        "",
        "## Data",
        "",
        "Column `ctmax_c` of `data/input.csv` records the critical thermal maximum, in",
        "degrees Celsius, reached by intertidal limpets during a heated-seawater ramp.",
        "Animals were collected from one granite shore platform in two tidal zones and",
        "each animal was ramped on several consecutive days.",
        "",
        "| Shore zone | Animals | Measurements | Ramps per animal | Mean CTmax (C) | SD (C) |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for zone in ZONES:
        item = summary[zone]
        lines.append(
            "| {0} | {1} | {2} | {3} | {4:.3f} | {5:.3f} |".format(
                ZONE_TITLE[zone],
                item["animals"],
                item["n"],
                item["reps"],
                item["mean"],
                item["sd"],
            )
        )

    lines.extend(
        [
            "",
            "## Analysis",
            "",
            "Two-sided two-sample Student t-test (pooled variance) comparing `ctmax_c`",
            "between the low-shore and high-shore groups. Every measurement in the file",
            "was entered into the test as one observation of its group.",
            "",
            "## Result",
            "",
            "High-shore limpets reached a mean CTmax {0:.3f} C above low-shore limpets.".format(
                gap
            ),
            "",
            (
                "[selected-result] Two-sample t-test of ctmax_c by shore zone: "
                "t({0}) = {1:.3f}, {2} (low shore {3:.3f} C, n = {4}; "
                "high shore {5:.3f} C, n = {6}; difference {7:.3f} C)."
            ).format(
                df,
                t_stat,
                p_text,
                summary["low"]["mean"],
                summary["low"]["n"],
                summary["high"]["mean"],
                summary["high"]["n"],
                gap,
            ),
            "",
            "All {0} measurements were treated as independent observations, giving {1}".format(
                total, df
            ),
            "degrees of freedom.",
        ]
    )
    return "\n".join(lines) + "\n"


def main():
    rows = read_table(INPUT_PATH)
    ctmax, animals = split_by_zone(rows)
    report = build_report(ctmax, animals)
    directory = os.path.dirname(OUTPUT_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
