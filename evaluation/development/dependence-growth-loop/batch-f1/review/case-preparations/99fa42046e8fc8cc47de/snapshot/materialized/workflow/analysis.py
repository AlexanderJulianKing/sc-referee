"""Dissolved zinc attenuation in constructed treatment wetland mesocosms.

Reads data/input.csv, compares outflow zinc between the two substrate builds
and writes results/report.md.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

GROUP_ORDER = ("biochar_amended", "gravel_control")
ALPHA = 0.05


def read_samples(path):
    """Return one tuple per outflow water sample, in file order."""
    samples = []
    with path.open("r", encoding="ascii", newline="") as handle:
        for record in csv.DictReader(handle):
            samples.append(
                (
                    record["mesocosm_id"],
                    record["substrate"],
                    int(record["sampling_week"]),
                    float(record["zinc_mg_per_l"]),
                )
            )
    return samples


def welch_df(var_a, n_a, var_b, n_b):
    """Welch-Satterthwaite degrees of freedom for two independent groups."""
    term_a = var_a / n_a
    term_b = var_b / n_b
    return (term_a + term_b) ** 2 / (
        term_a ** 2 / (n_a - 1) + term_b ** 2 / (n_b - 1)
    )


def format_p(p_value):
    if p_value < 1e-6:
        return "p < 1e-06"
    return "p = {0:.4f}".format(p_value)


def main():
    samples = read_samples(INPUT_PATH)

    weeks = sorted({week for _, _, week, _ in samples})

    mesocosm_order = []
    mesocosm_substrate = {}
    mesocosm_values = {}
    group_values = {name: [] for name in GROUP_ORDER}

    for mesocosm_id, substrate, _week, zinc in samples:
        if mesocosm_id not in mesocosm_values:
            mesocosm_order.append(mesocosm_id)
            mesocosm_substrate[mesocosm_id] = substrate
            mesocosm_values[mesocosm_id] = []
        mesocosm_values[mesocosm_id].append(zinc)
        group_values[substrate].append(zinc)

    values_a = group_values[GROUP_ORDER[0]]
    values_b = group_values[GROUP_ORDER[1]]

    mean_a = statistics.fmean(values_a)
    mean_b = statistics.fmean(values_b)
    sd_a = statistics.stdev(values_a)
    sd_b = statistics.stdev(values_b)
    difference = mean_a - mean_b

    outcome = stats.ttest_ind(values_a, values_b, equal_var=False)
    t_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)
    df = welch_df(sd_a ** 2, len(values_a), sd_b ** 2, len(values_b))
    verdict = "significant" if p_value < ALPHA else "not significant"

    lines = [
        "# Dissolved zinc in constructed wetland mesocosm outflow",
        "",
        "## Data",
        "",
        "Bench-scale constructed treatment wetlands were run for eight weeks and",
        "their outflow was assayed for dissolved zinc on four sampling weeks.",
        "",
        "- Outflow water samples analysed: {0}".format(len(samples)),
        "- Sampling weeks represented: {0}".format(
            ", ".join(str(week) for week in weeks)
        ),
    ]

    for name in GROUP_ORDER:
        lines.append(
            "- Samples with substrate {0}: {1}".format(name, len(group_values[name]))
        )

    lines.extend(
        [
            "",
            "## Mean outflow zinc by mesocosm",
            "",
            "| mesocosm_id | substrate | samples | mean zinc (mg/L) |",
            "| --- | --- | --- | --- |",
        ]
    )

    for mesocosm_id in mesocosm_order:
        readings = mesocosm_values[mesocosm_id]
        lines.append(
            "| {0} | {1} | {2} | {3:.3f} |".format(
                mesocosm_id,
                mesocosm_substrate[mesocosm_id],
                len(readings),
                statistics.fmean(readings),
            )
        )

    lines.extend(
        [
            "",
            "## Substrate group summary",
            "",
            "| substrate | samples | mean (mg/L) | SD (mg/L) |",
            "| --- | --- | --- | --- |",
            "| {0} | {1} | {2:.4f} | {3:.4f} |".format(
                GROUP_ORDER[0], len(values_a), mean_a, sd_a
            ),
            "| {0} | {1} | {2:.4f} | {3:.4f} |".format(
                GROUP_ORDER[1], len(values_b), mean_b, sd_b
            ),
            "",
            "## Analysis",
            "",
            "Welch's two-sample t-test (two-sided, unequal variances) compares the",
            "dissolved zinc concentration of the two substrate builds. Each outflow",
            "water sample in data/input.csv enters the test as one observation.",
            "",
            "- Mean difference ({0} - {1}): {2:.4f} mg/L".format(
                GROUP_ORDER[0], GROUP_ORDER[1], difference
            ),
            "- Welch t = {0:.3f} on df = {1:.2f}".format(t_stat, df),
            "- {0}".format(format_p(p_value)),
            "- Significance threshold: alpha = {0}".format(ALPHA),
            "",
            "## Conclusion",
            "",
            (
                "[selected-result] Welch's two-sample t-test on {0} outflow water "
                "samples: mean dissolved zinc is {1:.4f} mg/L lower under {2} "
                "({3:.4f} mg/L) than under {4} ({5:.4f} mg/L), t = {6:.3f}, "
                "df = {7:.2f}, {8}, {9} at alpha = {10}."
            ).format(
                len(samples),
                abs(difference),
                GROUP_ORDER[0],
                mean_a,
                GROUP_ORDER[1],
                mean_b,
                t_stat,
                df,
                format_p(p_value),
                verdict,
                ALPHA,
            ),
        ]
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
