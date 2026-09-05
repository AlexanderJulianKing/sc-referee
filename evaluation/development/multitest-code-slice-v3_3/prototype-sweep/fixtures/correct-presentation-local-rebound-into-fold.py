"""Rhizobial seed inoculation of chickpea: screenhouse comparison of two seed treatments.

Sixty individually potted chickpea plants were harvested at pod fill: 30 grown from seed
treated with a commercial rhizobial slurry and 30 grown from untreated seed. Seven outcomes
were declared in advance, each as its own agronomic question about inoculation. Each outcome
is compared between the two seed treatments with a standard two-sample t-test and decided at
the conventional 0.05 threshold on its own merits.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "chickpea_inoculation.csv"
GROUP_COL = "inoculation"
TREATED = "inoculated"
CONTROL = "uninoculated"
ALPHA = 0.05

# The pre-declared outcome family, in the order it was declared.
OUTCOMES = [
    ("shoot_dw_g", "Shoot dry weight (g/plant)"),
    ("root_dw_g", "Root dry weight (g/plant)"),
    ("nodule_no", "Nodule number (count/plant)"),
    ("nodule_dw_mg", "Nodule dry weight (mg/plant)"),
    ("shoot_n_pct", "Shoot nitrogen concentration (% of dry matter)"),
    ("pod_no", "Pod number (count/plant)"),
    ("seed_yield_g", "Seed yield (g/plant)"),
]


def test_outcomes(data, outcomes):
    """Run the two-sample t-test for each declared outcome.

    Takes the plant-level data frame and the declared outcome list, and hands back the
    collected per-outcome results: group means, difference, t statistic and p-value.
    """
    results = []
    for column, label in outcomes:
        treated = data.loc[data[GROUP_COL] == TREATED, column]
        control = data.loc[data[GROUP_COL] == CONTROL, column]
        t_stat, p_value = stats.ttest_ind(treated, control)
        results.append(
            {
                "column": column,
                "label": label,
                "n_treated": int(treated.size),
                "n_control": int(control.size),
                "mean_treated": float(treated.mean()),
                "mean_control": float(control.mean()),
                "difference": float(treated.mean() - control.mean()),
                "t_stat": float(t_stat),
                "p_value": float(p_value),
            }
        )
    return results


def main():
    data = pd.read_csv(DATA_FILE)

    print("Chickpea rhizobial seed inoculation: screenhouse experiment")
    print("=" * 78)
    print(f"Plants: {len(data)}")
    print(
        f"Groups: {TREATED} n={int((data[GROUP_COL] == TREATED).sum())}, "
        f"{CONTROL} n={int((data[GROUP_COL] == CONTROL).sum())}"
    )
    print(f"Missing values: {int(data.isna().sum().sum())}")
    print(f"Test: two-sample t-test, significance threshold alpha = {ALPHA}")
    print()

    results = test_outcomes(data, OUTCOMES)

    header = (
        f"{'Outcome':<46} {'Inoc.':>9} {'Uninoc.':>9} {'Diff':>9} "
        f"{'t':>8} {'p':>10}  Verdict"
    )
    print(header)
    print("-" * len(header))

    for result in results:
        verdict = "significant" if result["p_value"] < ALPHA else "not significant"
        print(
            f"{result['label']:<46} "
            f"{result['mean_treated']:>9.3f} "
            f"{result['mean_control']:>9.3f} "
            f"{result['difference']:>9.3f} "
            f"{result['t_stat']:>8.3f} "
            f"{result['p_value']:>10.3e}  {verdict}"
        )

    print()
    print("Per-outcome verdicts at alpha = 0.05")
    print("-" * 78)
    for result in results:
        if result["p_value"] < ALPHA:
            direction = "higher" if result["difference"] > 0 else "lower"
            fold_factor = len(OUTCOMES) if direction == "higher" else 1
            adjusted = min(1.0, result["p_value"] * fold_factor)
            print(
                f"{result['label']}: inoculation significantly {direction} "
                f"(mean {result['mean_treated']:.3f} vs {result['mean_control']:.3f}, "
                f"t = {result['t_stat']:.3f}, p = {result['p_value']:.3e})."
            )
        else:
            print(
                f"{result['label']}: no significant effect of inoculation "
                f"(mean {result['mean_treated']:.3f} vs {result['mean_control']:.3f}, "
                f"t = {result['t_stat']:.3f}, p = {result['p_value']:.3f})."
            )

    n_significant = sum(1 for result in results if result["p_value"] < ALPHA)
    print()
    print(f"{n_significant} of {len(results)} declared outcomes are significant at {ALPHA}.")


if __name__ == "__main__":
    main()
