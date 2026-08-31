"""Starter culture comparison for the set-yoghurt cup trial.

Reads yoghurt_cups.csv (60 cups, 30 per starter culture) and compares the two
starter cultures on the eight declared outcomes, in the declared order.

The two primary product-quality outcomes (syneresis_pct, gel_firmness_n) have
their p-values passed through the multiple-comparison adjustment routine in
statsmodels and are judged on the adjusted values. The six secondary outcomes
are judged on their own plain p-values.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

CSV_FILE = "yoghurt_cups.csv"
GROUP_COLUMN = "starter_culture"
GROUP_A = "conventional"
GROUP_B = "eps"
ALPHA = 0.05

# The declared outcome family, in the order fixed in the trial plan.
OUTCOMES = [
    "ph_24h",
    "titratable_acidity_pct",
    "syneresis_pct",
    "gel_firmness_n",
    "apparent_viscosity_pa_s",
    "water_holding_capacity_pct",
    "lab_count_log10_cfu_g",
    "sensory_smoothness_score",
]

# The two primary product-quality outcomes named in the trial plan.
PRIMARY_OUTCOMES = ["syneresis_pct", "gel_firmness_n"]


def main():
    data = pd.read_csv(CSV_FILE)

    conventional = data[data[GROUP_COLUMN] == GROUP_A]
    eps = data[data[GROUP_COLUMN] == GROUP_B]

    # Two-group comparison test for continuous data, outcome by outcome.
    results = {}
    for outcome in OUTCOMES:
        a = conventional[outcome]
        b = eps[outcome]
        t_stat, p_value = stats.ttest_ind(a, b)
        results[outcome] = {
            "mean_conventional": a.mean(),
            "mean_eps": b.mean(),
            "t": t_stat,
            "p_raw": p_value,
        }

    # Primary outcomes: adjust the two p-values together, judge on the adjusted values.
    primary_p = [results[outcome]["p_raw"] for outcome in PRIMARY_OUTCOMES]
    _, primary_p_adjusted, _, _ = multipletests(primary_p, alpha=ALPHA, method="holm")
    for outcome, p_adj in zip(PRIMARY_OUTCOMES, primary_p_adjusted):
        results[outcome]["p_used"] = p_adj
        results[outcome]["p_kind"] = "adjusted"

    # Secondary outcomes: judge each on its own plain p-value.
    for outcome in OUTCOMES:
        if outcome not in PRIMARY_OUTCOMES:
            results[outcome]["p_used"] = results[outcome]["p_raw"]
            results[outcome]["p_kind"] = "plain"

    for outcome in OUTCOMES:
        results[outcome]["significant"] = results[outcome]["p_used"] < ALPHA

    print("Yoghurt starter culture comparison")
    print(f"Cups read from {CSV_FILE}: {len(data)} "
          f"({len(conventional)} {GROUP_A}, {len(eps)} {GROUP_B})")
    print(f"Test: two-sample t-test. Threshold: {ALPHA}")
    print(f"Primary outcomes (adjusted, Holm): {', '.join(PRIMARY_OUTCOMES)}")
    print(f"Secondary outcomes: judged on plain p-values")
    print()

    header = (f"{'outcome':<28}{'role':<11}{'mean_' + GROUP_A:<19}"
              f"{'mean_' + GROUP_B:<11}{'p_used':<12}{'p_kind':<10}verdict")
    print(header)
    print("-" * len(header))

    for outcome in OUTCOMES:
        r = results[outcome]
        role = "primary" if outcome in PRIMARY_OUTCOMES else "secondary"
        verdict = "significant" if r["significant"] else "not significant"
        print(f"{outcome:<28}{role:<11}{r['mean_conventional']:<19.3f}"
              f"{r['mean_eps']:<11.3f}{r['p_used']:<12.4g}{r['p_kind']:<10}{verdict}")

    print()
    print("Plain p-values for the two primary outcomes, before adjustment:")
    for outcome in PRIMARY_OUTCOMES:
        print(f"  {outcome:<28}{results[outcome]['p_raw']:.4g}")


if __name__ == "__main__":
    main()
