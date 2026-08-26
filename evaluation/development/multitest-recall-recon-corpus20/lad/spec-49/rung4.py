"""Atlantic salmon smolts on a standard marine-oil diet or a diet with half the
fish oil replaced by algal oil.

108 fish sampled at the end of sixteen weeks, 54 per diet. Six outcomes were
recorded. Each outcome goes through the same comparison step below, which does
its own test and reaches its own verdict, and the six are reported in the order
they were declared.
"""

from collections import namedtuple

import pandas as pd
from scipy import stats

Comparison = namedtuple(
    "Comparison", "outcome mean_fish_oil mean_algal_oil difference p_value verdict"
)

OUTCOMES = [
    ("final_weight_g", "final weight (g)", 0),
    ("specific_growth_rate", "specific growth rate (%/day)", 3),
    ("fillet_epa_dha_mg_g", "fillet EPA+DHA (mg/g)", 2),
    ("liver_lipid_pct", "liver lipid (%)", 2),
    ("condition_factor", "condition factor", 3),
    ("fillet_colour_score", "SalmoFan colour score", 1),
]


def compare_diets(table, outcome):
    """Compare the two diets on one outcome and decide on it.

    Splits the fish by diet, runs a two-sample Welch t-test on the difference in
    means, and returns the two means, their difference, the p-value, and a
    verdict. The cutoff lives here, in the step that does the test.
    """
    fish_oil = table.loc[table["diet"] == "fish_oil", outcome]
    algal_oil = table.loc[table["diet"] == "algal_oil", outcome]
    result = stats.ttest_ind(fish_oil, algal_oil, equal_var=False)
    return {
        "outcome": outcome,
        "mean_fish_oil": fish_oil.mean(),
        "mean_algal_oil": algal_oil.mean(),
        "difference": fish_oil.mean() - algal_oil.mean(),
        "p_value": result.pvalue,
    }


def fmt_p(p):
    return f"{p:.2e}" if p < 1e-4 else f"{p:.5f}"


def main():
    data = pd.read_csv("data.csv")
    print(f"Fish: fish_oil n={(data['diet'] == 'fish_oil').sum()}, "
          f"algal_oil n={(data['diet'] == 'algal_oil').sum()}")
    print("Test: two-sample Welch t-test on the difference in means, two sided.\n")

    header = (f"{'outcome':<30}{'fish_oil':>11}{'algal_oil':>11}{'diff':>10}"
              f"{'p':>12}  verdict")
    print(header)
    print("-" * len(header))
    for column, label, dp in OUTCOMES:
        result = compare_diets(data, column)
        verdict = "significant" if result['p_value'] < 0.05 else "not significant"
        print(f"{label:<30}{result['mean_fish_oil']:>11.{dp}f}"
              f"{result['mean_algal_oil']:>11.{dp}f}{result['difference']:>10.{dp}f}"
              f"{result['p_value']:>12.5f}  {verdict}")


if __name__ == "__main__":
    main()
