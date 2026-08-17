"""Nitrate removal in bench-scale denitrifying bioreactors: methanol vs glycerol.

Reads data/input.csv and writes results/report.md.
"""

from __future__ import annotations

import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

SOURCE_ORDER = ("methanol", "glycerol")
VALUE_FIELD = "nitrate_removal_mg_n_per_l_per_h"
ALPHA = 0.05


def read_table(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def welch_df(sample_a, sample_b):
    term_a = statistics.variance(sample_a) / len(sample_a)
    term_b = statistics.variance(sample_b) / len(sample_b)
    numerator = (term_a + term_b) ** 2
    denominator = term_a ** 2 / (len(sample_a) - 1) + term_b ** 2 / (len(sample_b) - 1)
    return numerator / denominator


def main():
    rows = read_table(INPUT_PATH)

    values = defaultdict(list)
    reactors = defaultdict(set)
    per_reactor = Counter()
    for row in rows:
        source = row["carbon_source"]
        values[source].append(float(row[VALUE_FIELD]))
        reactors[source].add(row["reactor_id"])
        per_reactor[row["reactor_id"]] += 1

    methanol = values["methanol"]
    glycerol = values["glycerol"]

    outcome = stats.ttest_ind(glycerol, methanol, equal_var=False)
    t_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)
    dof = welch_df(glycerol, methanol)

    mean_methanol = statistics.fmean(methanol)
    mean_glycerol = statistics.fmean(glycerol)
    difference = mean_glycerol - mean_methanol

    days = sorted({int(row["run_day"]) for row in rows})
    occasion_counts = sorted(set(per_reactor.values()))
    occasions = (
        str(occasion_counts[0])
        if len(occasion_counts) == 1
        else "{}-{}".format(occasion_counts[0], occasion_counts[-1])
    )

    p_text = "p < 1e-12" if p_value < 1e-12 else "p = {:.6f}".format(p_value)
    verdict = (
        "the difference is significant at alpha = {:.2f}".format(ALPHA)
        if p_value < ALPHA
        else "the difference is not significant at alpha = {:.2f}".format(ALPHA)
    )

    lines = [
        "# Nitrate removal under two external carbon sources",
        "",
        "## Data",
        "",
        "- Source file: `data/input.csv`",
        "- Measurement rows analysed: {}".format(len(rows)),
        "- Bioreactors: {} ({} on methanol, {} on glycerol)".format(
            len(per_reactor), len(reactors["methanol"]), len(reactors["glycerol"])
        ),
        "- Sampling occasions per bioreactor: {} (run days {})".format(
            occasions, ", ".join(str(day) for day in days)
        ),
        "",
        "| carbon source | rows | mean removal (mg N/L/h) | sd |",
        "| --- | --- | --- | --- |",
    ]
    for source in SOURCE_ORDER:
        sample = values[source]
        lines.append(
            "| {} | {} | {:.3f} | {:.3f} |".format(
                source,
                len(sample),
                statistics.fmean(sample),
                statistics.stdev(sample),
            )
        )
    lines.extend(
        [
            "",
            "## Analysis",
            "",
            "Each sampling-day measurement in the file was entered as one observation,",
            "and the two carbon-source groups were compared with Welch's two-sample",
            "t test (`scipy.stats.ttest_ind`, `equal_var=False`), two-sided.",
            "",
            "## Result",
            "",
            "- Mean difference (glycerol minus methanol): {:.3f} mg N/L/h".format(difference),
            "- Welch t = {:.2f} on {:.1f} degrees of freedom".format(t_stat, dof),
            "- {}".format(p_text),
            "",
            (
                "[selected-result] Welch two-sample t test on the {} measurement rows: "
                "mean nitrate removal is {:.3f} mg N/L/h with glycerol versus {:.3f} mg N/L/h "
                "with methanol, a difference of {:.3f} mg N/L/h (t = {:.2f}, df = {:.1f}, {}); {}."
            ).format(
                len(rows),
                mean_glycerol,
                mean_methanol,
                difference,
                t_stat,
                dof,
                p_text,
                verdict,
            ),
            "",
        ]
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
