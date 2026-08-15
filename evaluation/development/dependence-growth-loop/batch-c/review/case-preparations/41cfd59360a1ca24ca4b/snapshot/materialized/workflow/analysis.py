"""Clearance-rate analysis for the Anodonta anatina warming trial.

The raw table is stored one record per clearance run, so every mussel appears
six times.  Runs are averaged within animal and phase before anything is
tested, which leaves one analysed row per animal.
"""

import csv
import math
from pathlib import Path

import numpy as np
from scipy import stats

INPUT = Path("data/input.csv")
REPORT = Path("results/report.md")
PHASES = ("pre", "post")
ALPHA = 0.05


def read_runs(path):
    """Collect rates as {mussel_id: {phase: [rates]}}, keeping first-seen order."""
    order = []
    runs = {}
    with path.open(newline="", encoding="ascii") as handle:
        for record in csv.DictReader(handle):
            animal = record["mussel_id"].strip()
            phase = record["phase"].strip().lower()
            if phase not in PHASES:
                raise ValueError("unknown phase label: " + repr(phase))
            if animal not in runs:
                runs[animal] = {"pre": [], "post": []}
                order.append(animal)
            runs[animal][phase].append(float(record["clearance_rate_l_h"]))
    if not order:
        raise ValueError("no clearance runs found in " + str(path))
    return order, runs


def per_animal_table(order, runs):
    """Collapse repeated runs to one pre mean and one post mean per animal."""
    table = []
    for animal in order:
        pre_runs = runs[animal]["pre"]
        post_runs = runs[animal]["post"]
        if not pre_runs or not post_runs:
            raise ValueError("mussel " + animal + " does not have both phases")
        pre = float(np.mean(pre_runs))
        post = float(np.mean(post_runs))
        table.append(
            {
                "animal": animal,
                "n_runs": len(pre_runs) + len(post_runs),
                "pre": pre,
                "post": post,
                "change": post - pre,
            }
        )
    return table


def format_p(pvalue):
    if pvalue < 0.0001:
        return "p < 0.0001"
    return "p = {0:.4f}".format(pvalue)


def main():
    order, runs = read_runs(INPUT)
    table = per_animal_table(order, runs)

    n_runs = sum(row["n_runs"] for row in table)
    pre = np.array([row["pre"] for row in table], dtype=float)
    post = np.array([row["post"] for row in table], dtype=float)
    change = post - pre
    n = int(change.size)
    df = n - 1

    mean_change = float(np.mean(change))
    sd_change = float(np.std(change, ddof=1))
    stderr = sd_change / math.sqrt(n)
    tcrit = float(stats.t.ppf(1.0 - ALPHA / 2.0, df))
    ci_low = mean_change - tcrit * stderr
    ci_high = mean_change + tcrit * stderr

    tstat, pvalue = stats.ttest_rel(post, pre)
    tstat = float(tstat)
    ptext = format_p(float(pvalue))

    lines = [
        "# Thermal stress and particle clearance in the duck mussel Anodonta anatina",
        "",
        "## Design and data",
        "",
        "`data/input.csv` stores one row per clearance run: {0} runs recorded from {1} individually".format(n_runs, n),
        "tagged mussels, each held in its own flow-through chamber. Every animal contributed three",
        "runs during the pre-exposure baseline (days 0-4) and three more after a 10-day warming",
        "exposure (days 16-20). Runs from the same animal are repeated measurements of one",
        "individual, so the {0} rows are not {0} independent observations.".format(n_runs),
        "",
        "## Analysis",
        "",
        "Clearance rates were averaged within animal and phase, which leaves one pre-exposure mean",
        "and one post-exposure mean per mussel and therefore exactly one analysed row per",
        "independent unit (`mussel_id`). The {0} within-animal changes (post minus pre) were tested".format(n),
        "against zero with a two-sided paired t-test (`scipy.stats.ttest_rel`); the 95% interval",
        "uses the Student t quantile on {0} degrees of freedom.".format(df),
        "",
        "## Per-animal clearance means (L/h)",
        "",
        "| mussel_id | runs | pre-exposure | post-exposure | change |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for row in table:
        lines.append(
            "| {0} | {1} | {2:.3f} | {3:.3f} | {4:.3f} |".format(
                row["animal"], row["n_runs"], row["pre"], row["post"], row["change"]
            )
        )

    lines.extend(
        [
            "",
            "## Result",
            "",
            "- Independent units analysed: {0} mussels ({1} clearance runs collapsed to {0} paired rows)".format(n, n_runs),
            "- Mean pre-exposure clearance: {0:.3f} L/h".format(float(np.mean(pre))),
            "- Mean post-exposure clearance: {0:.3f} L/h".format(float(np.mean(post))),
            "- Mean within-animal change: {0:.3f} L/h (SD {1:.3f}, 95% CI {2:.3f} to {3:.3f})".format(mean_change, sd_change, ci_low, ci_high),
            "- Paired t-test: t({0}) = {1:.3f}, {2}".format(df, tstat, ptext),
            "",
            "[selected-result] Particle clearance fell after the 10-day warming exposure: mean within-animal change {0:.3f} L/h (95% CI {1:.3f} to {2:.3f}), two-sided paired t({3}) = {4:.3f}, {5}, n = {6} mussels.".format(mean_change, ci_low, ci_high, df, tstat, ptext, n),
            "",
            "## Note on the unit of analysis",
            "",
            "The test statistic rests on {0} numbers, one per mussel. Individual clearance runs enter".format(n),
            "only through those per-animal means, so no animal contributes more than one row to the",
            "comparison.",
        ]
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
