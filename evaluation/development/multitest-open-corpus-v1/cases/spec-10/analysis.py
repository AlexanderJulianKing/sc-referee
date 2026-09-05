"""Bumblebee colonies beside treated and untreated oilseed rape.

Primary analysis: Welch two-sample t-tests on the five colony outcomes, with the
whole family of five p-values corrected together by Holm's step-down procedure
(statsmodels), family-wide error rate 5%.

Sensitivity analysis: the same five comparisons with the Mann-Whitney U test,
corrected the same way over the same family of five.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

ALPHA = 0.05

OUTCOMES = [
    "colony_mass_g",
    "new_queens",
    "worker_count",
    "foraging_trips_per_h",
    "pollen_load_mg",
]


def run_family(untreated, treated, test):
    """Test every outcome with `test`, then correct the five p-values as one family."""
    raw = [test(untreated[o], treated[o]).pvalue for o in OUTCOMES]
    reject, adjusted, _, _ = multipletests(raw, alpha=ALPHA, method="holm")
    return raw, adjusted, reject


def show(title, untreated, treated, raw, adjusted, reject):
    print(title)
    print(f"{'outcome':<24}{'untreated':>11}{'treated':>10}{'raw p':>10}"
          f"{'Holm p':>10}  decision")
    for outcome, p, p_adj, rejected in zip(OUTCOMES, raw, adjusted, reject):
        decision = "significant" if rejected else "not significant"
        print(f"{outcome:<24}{untreated[outcome].mean():>11.2f}{treated[outcome].mean():>10.2f}"
              f"{p:>10.4f}{p_adj:>10.4f}  {decision}")
    print()


def main():
    data = pd.read_csv("data.csv")
    untreated = data[data["seed_treatment"] == "untreated"]
    treated = data[data["seed_treatment"] == "treated"]
    print(f"{len(untreated)} untreated colonies, {len(treated)} treated colonies")
    print(f"Family = the {len(OUTCOMES)} colony outcomes, Holm correction at "
          f"alpha = {ALPHA}\n")

    raw, adjusted, reject = run_family(
        untreated, treated, lambda a, b: stats.ttest_ind(a, b, equal_var=False))
    show("PRIMARY: Welch t-tests, Holm-corrected across the five outcomes",
         untreated, treated, raw, adjusted, reject)

    raw_s, adjusted_s, reject_s = run_family(
        untreated, treated, lambda a, b: stats.mannwhitneyu(a, b, alternative="two-sided"))
    show("SENSITIVITY ANALYSIS of the primary result: Mann-Whitney U on the same "
         "five outcomes,\nHolm-corrected across the same family of five",
         untreated, treated, raw_s, adjusted_s, reject_s)

    agree = all(a == b for a, b in zip(reject, reject_s))
    print("Sensitivity re-run agrees with the primary decisions."
          if agree else
          "Sensitivity re-run differs from the primary decisions on at least one outcome.")
    print("Conclusions are taken from the corrected primary (t-test) results.")


if __name__ == "__main__":
    main()
