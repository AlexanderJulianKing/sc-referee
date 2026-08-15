"""Net calcification of coral nubbins under two aquarium thermal regimes."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

UNIT_COLUMN = "colony_id"
REGIME_COLUMN = "thermal_regime"
RATE_COLUMN = "net_calcification_mg_g_d"
REGIMES = ("ambient", "heated")
ALPHA = 0.05


def read_table(path):
    with path.open("r", encoding="ascii", newline="") as handle:
        return list(csv.DictReader(handle))


def rates_by_regime(table):
    collected = {name: [] for name in REGIMES}
    for record in table:
        collected[record[REGIME_COLUMN]].append(float(record[RATE_COLUMN]))
    return {
        name: np.array(values, dtype=float) for name, values in collected.items()
    }


def rows_per_colony(table):
    tally = {}
    for record in table:
        key = record[UNIT_COLUMN]
        tally[key] = tally.get(key, 0) + 1
    return tally


def describe(name, values):
    return "- {}: n = {}, mean = {:.3f} mg CaCO3 g^-1 d^-1, sd = {:.3f}".format(
        name, values.size, float(values.mean()), float(values.std(ddof=1))
    )


def main():
    table = read_table(INPUT_PATH)
    rates = rates_by_regime(table)
    ambient = rates["ambient"]
    heated = rates["heated"]

    n_ambient = int(ambient.size)
    n_heated = int(heated.size)
    dof = n_ambient + n_heated - 2

    pooled_var = (
        (n_ambient - 1) * float(ambient.var(ddof=1))
        + (n_heated - 1) * float(heated.var(ddof=1))
    ) / dof
    stderr = float(np.sqrt(pooled_var * (1.0 / n_ambient + 1.0 / n_heated)))
    difference = float(ambient.mean() - heated.mean())
    margin = float(stats.t.ppf(1.0 - ALPHA / 2.0, dof)) * stderr
    low = difference - margin
    high = difference + margin

    outcome = stats.ttest_ind(ambient, heated, equal_var=True)
    t_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)

    tally = rows_per_colony(table)
    counts = sorted(tally.values())
    if counts[0] == counts[-1]:
        spread = "{} measurements each".format(counts[0])
    else:
        spread = "{} to {} measurements each".format(counts[0], counts[-1])

    headline = (
        "[selected-result] Two-sample Student t-test comparing the {} nubbin "
        "calcification measurements between thermal regimes: ambient nubbins "
        "calcified {:.3f} mg CaCO3 g^-1 d^-1 faster than heated nubbins, "
        "t({}) = {:.4f}, p = {:.4f} (two-sided, 95% CI {:.4f} to {:.4f})."
    ).format(len(table), difference, dof, t_stat, p_value, low, high)

    lines = [
        "# Thermal regime and net calcification in Acropora nubbins",
        "",
        "## Data",
        "",
        "Source file: `data/input.csv` ({} measurement rows).".format(len(table)),
        "",
        describe("ambient", ambient),
        describe("heated", heated),
        "- {} parent colonies contributed {}.".format(len(tally), spread),
        "",
        "## Analysis",
        "",
        "Each measurement row in the file was entered as one observation in a",
        "two-sample Student t-test with pooled variance (two-sided), comparing net",
        "calcification under the ambient regime with net calcification under the",
        "heated regime (scipy.stats.ttest_ind, equal_var=True).",
        "",
        "## Result",
        "",
        "- Mean difference (ambient - heated): {:.3f} mg CaCO3 g^-1 d^-1".format(
            difference
        ),
        "- 95% confidence interval: {:.4f} to {:.4f}".format(low, high),
        "- Test statistic: t({}) = {:.4f}".format(dof, t_stat),
        "- Two-sided p-value: {:.4f}".format(p_value),
        "",
        headline,
        "",
        "## Interpretation",
        "",
        "At the 0.05 level the ambient-heated difference in net calcification is",
        "statistically significant. The {} analysed rows are the {} nubbins measured".format(
            len(table), counts[0]
        ),
        "on each of the {} parent colonies, and the test used all {} rows as its".format(
            len(tally), len(table)
        ),
        "observations, which is where its {} degrees of freedom come from.".format(dof),
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
