"""Rooftop planter crossover: do perforated shade screens cut daily water use?

Reads the session-level logs in data/input.csv and writes results/report.md.
Each planter module is logged on six days, so the daily rows are repeated
measurements of the same unit; the reported test therefore runs on
module-level contrasts, one analysed row per planter.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import fmean, stdev

from scipy import stats

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

UNIT_COL = "module_id"
STATE_COL = "screen_state"
RESPONSE_COL = "et_mm_day"
SCREENED = "screened"
OPEN_TOP = "open"


def read_sessions(path):
    """Group the raw daily water-use logs by planter module and top treatment."""
    logs = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            logs[(row[UNIT_COL], row[STATE_COL])].append(float(row[RESPONSE_COL]))
    return logs


def collapse_to_modules(logs):
    """Reduce each module's repeated logging days to one analysed row."""
    records = []
    for unit in sorted({unit for unit, _state in logs}):
        screened_days = logs[(unit, SCREENED)]
        open_days = logs[(unit, OPEN_TOP)]
        screened_mean = fmean(screened_days)
        open_mean = fmean(open_days)
        records.append(
            {
                "module": unit,
                "logged_days": len(screened_days) + len(open_days),
                "screened": screened_mean,
                "open": open_mean,
                "contrast": screened_mean - open_mean,
            }
        )
    return records


def format_p(pvalue):
    if pvalue < 0.001:
        return "p < 0.001"
    return "p = {:.3f}".format(pvalue)


def build_report(records, n_sessions):
    screened = [record["screened"] for record in records]
    open_top = [record["open"] for record in records]
    contrasts = [record["contrast"] for record in records]
    n_modules = len(records)
    df = n_modules - 1

    outcome = stats.ttest_rel(screened, open_top)
    tstat = float(outcome.statistic)
    p_text = format_p(float(outcome.pvalue))
    mean_contrast = fmean(contrasts)
    sd_contrast = stdev(contrasts)
    negative = sum(1 for value in contrasts if value < 0.0)
    exception = max(records, key=lambda record: record["contrast"])

    lines = [
        "# Perforated shade screens and daily water use in rooftop planter modules",
        "",
        "## Design",
        "",
        "Fourteen modular rooftop planters (module_id P01-P14) were logged on six",
        "consecutive days in July 2025. Each module spent three of those days under a",
        "perforated shade screen and three days with an open top; the day order was",
        "counterbalanced, so half the array was screened on the even-numbered days and",
        "half on the odd-numbered days. Daily evapotranspiration was metered once per",
        "module-day, giving {} session rows in total.".format(n_sessions),
        "",
        "## Analysis",
        "",
        "The {n} session rows are repeated measurements rather than {n} independent".format(
            n=n_sessions
        ),
        "observations: six of them belong to each planter. Every module's three",
        "screened days and three open days were therefore averaged first, and the",
        "module-level contrast (screened mean minus open mean) was what entered the",
        "test. That leaves exactly one analysed row per planter module, so the units",
        "in the reported comparison are the {} modules, not the {} daily logs.".format(
            n_modules, n_sessions
        ),
        "",
        "The {} module-level pairs were compared with a two-sided paired t-test".format(
            n_modules
        ),
        "(scipy.stats.ttest_rel), which is equivalent to a one-sample t-test on the {}".format(
            n_modules
        ),
        "contrasts.",
        "",
        "## Module-level summary (mm/day)",
        "",
        "| module_id | logged days | screened mean | open mean | contrast |",
        "| --- | --- | --- | --- | --- |",
    ]

    for record in records:
        lines.append(
            "| {module} | {logged_days} | {screened:.3f} | {open:.3f} |"
            " {contrast:+.3f} |".format(**record)
        )

    lines.extend(
        [
            "",
            "## Result",
            "",
            "- Grand mean, screened days: {:.3f} mm/day".format(fmean(screened)),
            "- Grand mean, open days: {:.3f} mm/day".format(fmean(open_top)),
            "- Mean contrast: {:+.3f} mm/day (SD {:.3f}, n = {} modules)".format(
                mean_contrast, sd_contrast, n_modules
            ),
            "- Paired t-test: t({}) = {:.2f}, {}".format(df, tstat, p_text),
            "",
            "[selected-result] Averaging each planter's repeated days into one"
            " analysed row per module (n = {} independent modules from {} session"
            " rows), a two-sided paired t-test shows that screened days use less"
            " water than open days: mean contrast {:+.3f} mm/day (SD {:.3f}),"
            " t({}) = {:.2f}, {}.".format(
                n_modules, n_sessions, mean_contrast, sd_contrast, df, tstat, p_text
            ),
            "",
            "## Notes",
            "",
            "{} of the {} modules had a negative contrast; module {} was the"
            " single".format(negative, n_modules, exception["module"]),
            "exception ({:+.3f} mm/day). The within-module spread across logging"
            " days is".format(exception["contrast"]),
            "not treated as replication, and no claim is made about individual days.",
        ]
    )
    return lines


def main():
    logs = read_sessions(INPUT_PATH)
    n_sessions = sum(len(values) for values in logs.values())
    records = collapse_to_modules(logs)
    lines = build_report(records, n_sessions)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
