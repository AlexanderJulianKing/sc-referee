"""Analysis of the twelve-week diet comparison in adult African grey parrots.

Two maintenance diets, a complete extruded pelleted diet and a continued seed-based
diet with fresh produce, are compared on the four outcomes declared in the study
protocol. Each outcome is its own clinical question and is reported on its own.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "parrot_diet_data.csv"

GROUP_COLUMN = "diet"
GROUP_A = "pellet"
GROUP_B = "seed"

# The declared outcome family, in the fixed order given by the study protocol.
DECLARED_OUTCOMES = [
    "plasma_retinol_ug_dl",
    "body_mass_g",
    "plasma_calcium_mmol_l",
    "feather_condition_score",
]

ALPHA = 0.05


def compare_outcomes(data, outcomes):
    """Run a two-sample t-test on each declared outcome and collect the results.

    Takes the data frame and the ordered list of declared outcomes. For each
    outcome in that order it compares the two diet groups with the standard
    two-group test for continuous data (independent-samples t-test) and records
    the group means, the t statistic and the p-value. Returns the collected
    per-outcome results in the declared order.
    """
    results = []
    for outcome in outcomes:
        values_a = data.loc[data[GROUP_COLUMN] == GROUP_A, outcome]
        values_b = data.loc[data[GROUP_COLUMN] == GROUP_B, outcome]
        t_statistic, p_value = stats.ttest_ind(values_a, values_b)
        results.append(
            {
                "outcome": outcome,
                "n_a": int(values_a.size),
                "n_b": int(values_b.size),
                "mean_a": float(values_a.mean()),
                "mean_b": float(values_b.mean()),
                "t_statistic": float(t_statistic),
                "p_value": float(p_value),
            }
        )
    return results


def main():
    data = pd.read_csv(DATA_FILE)

    results = compare_outcomes(data, DECLARED_OUTCOMES)

    print("African grey parrot diet study: week-twelve outcomes")
    print("Groups: {} (n={}) vs {} (n={})".format(
        GROUP_A, results[0]["n_a"], GROUP_B, results[0]["n_b"]))
    print("Significance threshold: {}".format(ALPHA))
    print()

    for result in results:
        verdict = "significant" if result["p_value"] < ALPHA else "not significant"
        print(result["outcome"])
        print("  mean ({}) = {:.3f}".format(GROUP_A, result["mean_a"]))
        print("  mean ({})   = {:.3f}".format(GROUP_B, result["mean_b"]))
        print("  t = {:.3f}".format(result["t_statistic"]))
        print("  p = {:.4f}".format(result["p_value"]))
        print("  verdict: {}".format(verdict))
        print()


if __name__ == "__main__":
    main()
