"""Hoverflies on arable field margins: flowering mix versus grass-only mix.

Reads the fixed survey file data.csv, summarises the two sown-mix groups on each of
the five outcomes declared in the survey protocol, and compares the groups on each
declared outcome with one two-sample test per outcome.

The five outcomes form a single declared family, so the family-wise error rate is
controlled with a Sidak per-comparison level computed below from the family-wise
rate and the number of declared outcomes. Every verdict in this script is taken
against that computed per-comparison level.

This script only reads data.csv. It never generates, simulates, or writes it.
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.csv")

GROUP_COLUMN = "sown_mix"
GROUP_LABELS = ("flower_mix", "grass_only")

# The outcome family declared in the survey protocol, in the declared order.
# The length of this list is the family size used for the multiplicity correction.
DECLARED_OUTCOMES = [
    ("hoverfly_individuals", "Hoverfly individuals on a 50 m walk", "individuals"),
    ("hoverfly_species_richness", "Hoverfly species richness", "species"),
    ("flowering_plant_cover_pct", "Flowering plant cover", "%"),
    ("aphid_colonies_with_hoverfly_larvae",
     "Aphid colonies with hoverfly larvae", "per 20 plants"),
    ("seed_set_seeds_per_head", "Sentinel plant seed set", "seeds per head"),
]

# Family-wise error rate declared for the whole outcome family.
FAMILY_WISE_ALPHA = 0.05

# Pre-specified test for every outcome in the family: Welch's two-sample t test
# (two sided, unequal variances not assumed equal). The same test is applied to
# all five outcomes; no test is chosen after looking at the data.


def sidak_per_comparison_alpha(family_wise_alpha, family_size):
    """Sidak per-comparison level: 1 minus the family-size root of (1 - alpha_fw).

    With alpha_fw = 0.05 and family size m this is 1 - 0.95 ** (1 / m), the level
    at which m independent comparisons each held to it give a family-wise error
    rate of alpha_fw.
    """
    return 1.0 - (1.0 - family_wise_alpha) ** (1.0 / family_size)


def format_p(p_value):
    """Format a p-value, switching to scientific notation for very small values."""
    if p_value < 1e-4:
        return "{:.2e}".format(p_value)
    return "{:.5f}".format(p_value)


def main():
    data = pd.read_csv(DATA_FILE)

    group_a, group_b = GROUP_LABELS
    rows_a = data[data[GROUP_COLUMN] == group_a]
    rows_b = data[data[GROUP_COLUMN] == group_b]

    # Family size comes from the declared outcome list, not from a typed-in number.
    family_size = len(DECLARED_OUTCOMES)
    alpha_pc = sidak_per_comparison_alpha(FAMILY_WISE_ALPHA, family_size)

    print("Hoverflies on arable field margins: flowering mix vs grass-only mix")
    print("=" * 72)
    print("Rows in data.csv (one row per margin strip): {}".format(len(data)))
    print("Group sizes:")
    print("  {}: n = {}".format(group_a, len(rows_a)))
    print("  {}: n = {}".format(group_b, len(rows_b)))
    print()

    print("Multiplicity control")
    print("-" * 72)
    print("Declared outcome family, in declared order:")
    for position, (column, label, unit) in enumerate(DECLARED_OUTCOMES, start=1):
        print("  {}. {} ({}, unit: {})".format(position, label, column, unit))
    print("Family size m (number of declared outcomes) = {}".format(family_size))
    print("Family-wise error rate alpha_fw = {:.2f}".format(FAMILY_WISE_ALPHA))
    print("Sidak per-comparison level = 1 - (1 - {:.2f}) ** (1 / {}) "
          "= 1 - {:.4f} ** (1 / {})".format(
              FAMILY_WISE_ALPHA, family_size, 1.0 - FAMILY_WISE_ALPHA, family_size))
    print("Sidak per-comparison level alpha_pc = {:.6f}".format(alpha_pc))
    print("Every outcome below is judged against alpha_pc, not against {:.2f}."
          .format(FAMILY_WISE_ALPHA))
    print()

    print("Per-outcome summaries and tests")
    print("-" * 72)
    print("Test used for every outcome: Welch's two-sample t test, two sided.")
    print()

    results = []
    for position, (column, label, unit) in enumerate(DECLARED_OUTCOMES, start=1):
        values_a = rows_a[column].astype(float)
        values_b = rows_b[column].astype(float)

        mean_a, sd_a = values_a.mean(), values_a.std(ddof=1)
        mean_b, sd_b = values_b.mean(), values_b.std(ddof=1)
        difference = mean_a - mean_b

        t_statistic, p_value = stats.ttest_ind(values_a, values_b, equal_var=False)
        significant = p_value < alpha_pc
        verdict = ("significant at the Sidak level" if significant
                   else "not significant at the Sidak level")

        results.append({
            "position": position,
            "column": column,
            "label": label,
            "unit": unit,
            "n_a": len(values_a),
            "n_b": len(values_b),
            "mean_a": mean_a,
            "sd_a": sd_a,
            "mean_b": mean_b,
            "sd_b": sd_b,
            "difference": difference,
            "t": float(t_statistic),
            "p": float(p_value),
            "significant": significant,
        })

        print("Outcome {} of {}: {} [{}]".format(position, family_size, label, column))
        print("  {} (n = {}): mean = {:.2f} {}, SD = {:.2f}".format(
            group_a, len(values_a), mean_a, unit, sd_a))
        print("  {} (n = {}): mean = {:.2f} {}, SD = {:.2f}".format(
            group_b, len(values_b), mean_b, unit, sd_b))
        print("  Difference ({} - {}) = {:+.2f} {}".format(
            group_a, group_b, difference, unit))
        print("  Welch t = {:.3f}, p = {}".format(t_statistic, format_p(p_value)))
        print("  p {} alpha_pc = {:.6f}  ->  {}".format(
            "<" if significant else ">=", alpha_pc, verdict))
        print()

    print("Summary of verdicts (all against alpha_pc = {:.6f})".format(alpha_pc))
    print("-" * 72)
    for result in results:
        print("  {}. {:<38} p = {:<10} {}".format(
            result["position"],
            result["column"],
            format_p(result["p"]),
            "significant" if result["significant"] else "not significant"))

    significant_columns = [r["column"] for r in results if r["significant"]]
    print()
    print("{} of {} declared outcomes separate the two mixes at the Sidak level."
          .format(len(significant_columns), family_size))
    if significant_columns:
        print("Separated: {}".format(", ".join(significant_columns)))


if __name__ == "__main__":
    main()
