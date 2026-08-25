"""Cold plasma treatment duration for raw almond kernels: two-group comparison.

Compares thirty lots treated for two minutes against thirty lots treated for five
minutes on the five outcomes declared in advance by the protocol, in the declared
order. Family-wise error across the declared family is controlled by hand with a
Sidak per-comparison threshold computed inside this script from the family size.

Run from the project root:

    python analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "almond_plasma_lots.csv"

GROUP_COLUMN = "plasma_group"
GROUP_A = "plasma_2min"
GROUP_B = "plasma_5min"

FAMILY_LEVEL = 0.05

# The five outcomes declared in advance by the protocol, in the declared order.
# The family size used by the Sidak correction below is the length of this list,
# so the correction always matches the family actually declared and tested.
DECLARED_OUTCOMES = [
    ("surrogate_log_reduction", "Surrogate log reduction (log CFU/g)"),
    ("peroxide_value_meq_kg", "Peroxide value (meq O2/kg oil)"),
    ("colour_l_star", "Kernel surface lightness (CIE L*)"),
    ("moisture_pct", "Moisture content (%)"),
    ("rancid_odour_score", "Rancid odour score (0-6)"),
]


def sidak_per_comparison_alpha(family_level, family_size):
    """Per-comparison level giving an overall family level of `family_level`.

    One minus the family-level complement raised to the power of one over the
    number of declared outcomes.
    """
    return 1.0 - (1.0 - family_level) ** (1.0 / family_size)


def main():
    data = pd.read_csv(DATA_FILE)

    group_a = data[data[GROUP_COLUMN] == GROUP_A]
    group_b = data[data[GROUP_COLUMN] == GROUP_B]

    family_size = len(DECLARED_OUTCOMES)
    alpha_pc = sidak_per_comparison_alpha(FAMILY_LEVEL, family_size)

    print("Cold plasma treatment duration on raw almond kernels")
    print("=" * 72)
    print(f"Data file: {DATA_FILE.name}")
    print(f"Lots loaded: {len(data)}")
    print(f"  {GROUP_A}: n = {len(group_a)}")
    print(f"  {GROUP_B}: n = {len(group_b)}")
    print(f"Missing cells in the analysed columns: "
          f"{int(data[[c for c, _ in DECLARED_OUTCOMES]].isna().sum().sum())}")
    print()

    print("Multiplicity control (Sidak, computed from the declared family)")
    print("-" * 72)
    print(f"Declared outcomes in the family (family size): {family_size}")
    print(f"Overall family level: {FAMILY_LEVEL:.2f}")
    print(f"Sidak per-comparison threshold "
          f"= 1 - (1 - {FAMILY_LEVEL:.2f})^(1/{family_size}) = {alpha_pc:.6f}")
    print()

    print("Group summaries and tests (Welch two-sample t-test, two-sided)")
    print("-" * 72)
    header = (f"{'Outcome':<34}{GROUP_A + ' mean (SD)':>22}"
              f"{GROUP_B + ' mean (SD)':>22}{'p-value':>12}  Verdict")
    print(header)

    results = []
    for column, label in DECLARED_OUTCOMES:
        values_a = group_a[column]
        values_b = group_b[column]

        mean_a, sd_a = values_a.mean(), values_a.std(ddof=1)
        mean_b, sd_b = values_b.mean(), values_b.std(ddof=1)

        t_stat, p_value = stats.ttest_ind(values_a, values_b, equal_var=False)

        significant = p_value < alpha_pc
        verdict = ("significant at the Sidak threshold" if significant
                   else "not significant at the Sidak threshold")

        results.append({
            "column": column,
            "label": label,
            "mean_a": mean_a,
            "sd_a": sd_a,
            "mean_b": mean_b,
            "sd_b": sd_b,
            "t_stat": t_stat,
            "p_value": p_value,
            "verdict": verdict,
        })

        print(f"{column:<34}{mean_a:>13.3f} ({sd_a:.3f}){mean_b:>13.3f} "
              f"({sd_b:.3f}){p_value:>12.3e}  "
              f"{'YES' if significant else 'no'}")

    print()
    print("Per-outcome detail, in declared order")
    print("-" * 72)
    for index, res in enumerate(results, start=1):
        print(f"{index}. {res['label']}")
        print(f"   {GROUP_A}: mean = {res['mean_a']:.3f}, SD = {res['sd_a']:.3f}, "
              f"n = {len(group_a)}")
        print(f"   {GROUP_B}: mean = {res['mean_b']:.3f}, SD = {res['sd_b']:.3f}, "
              f"n = {len(group_b)}")
        print(f"   difference (5 min minus 2 min) = "
              f"{res['mean_b'] - res['mean_a']:+.3f}")
        print(f"   Welch t = {res['t_stat']:.3f}, p = {res['p_value']:.6g}")
        print(f"   verdict vs {alpha_pc:.6f}: {res['verdict']}")
        print()

    n_significant = sum(1 for r in results if r["p_value"] < alpha_pc)
    print(f"Outcomes passing the Sidak per-comparison threshold: "
          f"{n_significant} of {family_size}")


if __name__ == "__main__":
    main()
