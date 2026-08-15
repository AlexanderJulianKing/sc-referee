#!/usr/bin/env python3
"""Colony-level analysis of the alpine warming-chamber foraging assay.

data/input.csv stores one row per 30-minute foraging trial. The trials belonging
to a colony are repeated measurements of that same colony, so they are averaged
into a single value per colony per chamber setting before anything is tested.
The paired comparison therefore runs over colonies, one analyzed pair each, and
the summary is written to results/report.md.
"""

import csv
from collections import OrderedDict
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

CONDITIONS = ("ambient", "warmed")
MEASURE_COLUMN = "sorties_per_hour"
ALPHA = 0.05


def read_trials(path):
    """Return colony metadata in file order, trial values per cell, and the row count."""
    colonies = OrderedDict()
    cells = {}
    n_rows = 0
    with path.open("r", encoding="ascii", newline="") as handle:
        for row in csv.DictReader(handle):
            n_rows += 1
            colony = row["colony_id"]
            if colony not in colonies:
                colonies[colony] = (row["site"], row["block_order"])
            condition = row["condition"]
            if condition not in CONDITIONS:
                raise ValueError("unexpected condition label: " + condition)
            cells.setdefault((colony, condition), []).append(
                float(row[MEASURE_COLUMN])
            )
    if not colonies:
        raise ValueError("no trial rows found in " + str(path))
    return colonies, cells, n_rows


def collapse_to_colony_means(colonies, cells):
    """Average the repeated trials into one value per colony per condition."""
    per_condition = dict((condition, []) for condition in CONDITIONS)
    trial_counts = set()
    for colony in colonies:
        for condition in CONDITIONS:
            values = cells.get((colony, condition), [])
            if not values:
                raise ValueError(
                    "colony %s has no %s trials" % (colony, condition)
                )
            trial_counts.add(len(values))
            per_condition[condition].append(sum(values) / len(values))
    if len(trial_counts) != 1:
        raise ValueError("colonies differ in the number of trials per condition")
    ambient = np.asarray(per_condition["ambient"], dtype=float)
    warmed = np.asarray(per_condition["warmed"], dtype=float)
    return ambient, warmed, trial_counts.pop()


def table_rows(colonies, ambient, warmed):
    rows = [
        "| colony | site | block order | ambient | warmed | warmed - ambient |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for index, colony in enumerate(colonies):
        site, block_order = colonies[colony]
        cool = float(ambient[index])
        hot = float(warmed[index])
        rows.append(
            "| %s | %s | %s | %.2f | %.2f | %.2f |"
            % (colony, site, block_order, cool, hot, hot - cool)
        )
    return rows


def build_report(colonies, ambient, warmed, n_rows, trials_per_cell):
    n_colonies = int(ambient.size)
    differences = warmed - ambient
    mean_diff = float(differences.mean())
    sd_diff = float(differences.std(ddof=1))
    se_diff = sd_diff / float(np.sqrt(n_colonies))
    df = n_colonies - 1
    outcome = stats.ttest_rel(warmed, ambient)
    t_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)
    half_width = float(stats.t.ppf(1.0 - ALPHA / 2.0, df)) * se_diff
    ci_low = mean_diff - half_width
    ci_high = mean_diff + half_width
    dz = mean_diff / sd_diff
    n_sites = len(set(site for site, _ in colonies.values()))
    n_lower = int((differences < 0.0).sum())
    smallest_drop = -float(differences.max())
    largest_drop = -float(differences.min())

    lines = []
    lines.append("# Warming and colony foraging output in *Bombus sylvicola*")
    lines.append("")
    lines.append("## Study")
    lines.append("")
    lines.append(
        "Ten queenright *Bombus sylvicola* colonies from three alpine sites were run "
        "through a paired warming assay. Each colony foraged under an ambient chamber "
        "setting (about 19 C) and under a warmed setting (about 26 C). Each setting was "
        "split across two sessions of two 30-minute trials, and block order was "
        "counterbalanced (AW = ambient block first, WA = warmed block first). The outcome "
        "is the rate of returning foragers at the nest entrance, in sorties per hour."
    )
    lines.append("")
    lines.append(
        "The input table `data/input.csv` holds %d trial rows: %d colonies x %d "
        "conditions x %d trials per condition."
        % (n_rows, n_colonies, len(CONDITIONS), trials_per_cell)
    )
    lines.append("")
    lines.append("## Unit of analysis")
    lines.append("")
    lines.append(
        "The %d trials a colony contributes within a condition are repeated measurements "
        "of the same colony; they replicate the measurement, not the warming manipulation. "
        "Every colony is therefore collapsed to one ambient mean and one warmed mean before "
        "any test is run, and the inferential comparison uses the %d colony-level "
        "differences - one analyzed observation per independent unit."
        % (trials_per_cell, n_colonies)
    )
    lines.append("")
    lines.append("## Colony-level means (sorties per hour)")
    lines.append("")
    lines.extend(table_rows(colonies, ambient, warmed))
    lines.append("")
    lines.append(
        "- ambient colony means: %.2f +/- %.2f SD (n = %d colonies)"
        % (ambient.mean(), ambient.std(ddof=1), n_colonies)
    )
    lines.append(
        "- warmed colony means: %.2f +/- %.2f SD (n = %d colonies)"
        % (warmed.mean(), warmed.std(ddof=1), n_colonies)
    )
    lines.append("")
    lines.append("## Test")
    lines.append("")
    lines.append(
        "Two-sided paired t-test (scipy.stats.ttest_rel) on the %d colony-level "
        "differences (warmed minus ambient)." % n_colonies
    )
    lines.append("")
    lines.append(
        "- mean difference: %.3f sorties/hour (SD %.3f, SE %.3f)"
        % (mean_diff, sd_diff, se_diff)
    )
    lines.append(
        "- 95%% confidence interval: %.3f to %.3f sorties/hour" % (ci_low, ci_high)
    )
    lines.append("- t(%d) = %.3f, p = %.1e" % (df, t_stat, p_value))
    lines.append("- standardized paired effect size dz = %.2f" % dz)
    lines.append("")
    lines.append(
        "[selected-result] Paired t-test on colony-level mean foraging rates "
        "(n = %d colonies): warming lowered foraging by %.3f sorties/hour "
        "(95%% CI %.3f to %.3f), t(%d) = %.3f, p = %.1e."
        % (n_colonies, abs(mean_diff), ci_low, ci_high, df, t_stat, p_value)
    )
    lines.append("")
    lines.append("## Reading of the result")
    lines.append("")
    lines.append(
        "Every colony (%d of %d) foraged less under the warmed setting; the smallest "
        "colony-level drop was %.2f and the largest %.2f sorties per hour. The confidence "
        "interval excludes zero, so these colonies foraged less under the warmer chamber "
        "setting. The trial-to-trial and session-to-session spread inside a colony feeds "
        "into the colony means but is not counted as replication of the manipulation; with "
        "%d colonies from %d collection sites, site effects are not separable from colony "
        "identity in this design."
        % (n_lower, n_colonies, smallest_drop, largest_drop, n_colonies, n_sites)
    )
    return "\n".join(lines) + "\n"


def main():
    colonies, cells, n_rows = read_trials(INPUT_PATH)
    ambient, warmed, trials_per_cell = collapse_to_colony_means(colonies, cells)
    report = build_report(colonies, ambient, warmed, n_rows, trials_per_cell)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
