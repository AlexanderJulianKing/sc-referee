"""Disposable vs powered air-purifying respirators in a stone-cutting workshop.

Six endpoints are worked through in a fixed order. Each one is given a number, is
tested on its own, and its p-value is stored at that number's slot in the results
array so the summary at the end can be re-walked in the same order.
"""

import numpy as np
import pandas as pd
from scipy import stats

DATA = "data.csv"
GROUP = "respirator"
TYPE_ONE = "disposable"
TYPE_TWO = "powered"

OUTCOME_NAMES = [
    "silica_exposure_mg_m3",
    "fit_factor",
    "fev1_pct_predicted",
    "cough_score",
    "comfort_score",
    "wear_compliance_pct",
]

ALPHA = 0.05

N_OUTCOMES = len(OUTCOME_NAMES)


def main():
    masons = pd.read_csv(DATA)
    print("Masons: %d (%s %d, %s %d)" % (
        len(masons),
        TYPE_ONE, int((masons[GROUP] == TYPE_ONE).sum()),
        TYPE_TWO, int((masons[GROUP] == TYPE_TWO).sum()),
    ))
    print("Endpoints tested: %d, each against alpha = %.2f" % (N_OUTCOMES, ALPHA))
    print()

    p_values = np.full(N_OUTCOMES, np.nan)
    mean_one = np.full(N_OUTCOMES, np.nan)
    mean_two = np.full(N_OUTCOMES, np.nan)

    for i, outcome in enumerate(OUTCOME_NAMES):

        group_one = masons.loc[masons[GROUP] == TYPE_ONE, outcome].to_numpy()
        group_two = masons.loc[masons[GROUP] == TYPE_TWO, outcome].to_numpy()

        test = stats.ttest_ind(group_one, group_two, equal_var=False)

        p_values[i] = float(test.pvalue)
        mean_one[i] = group_one.mean()
        mean_two[i] = group_two.mean()

        verdict = "significant" if p_values[i] < ALPHA else "not significant"
        print(f"[{i + 1}] {outcome}")
        print(f"     {TYPE_ONE} mean = {mean_one[i]:.5g}, {TYPE_TWO} mean = {mean_two[i]:.5g}")
        print(f"     t = {test.statistic:.3f}, p = {p_values[i]:.4f} -> {verdict}")


    print()
    print("Summary")
    header = "%3s  %-24s %12s %12s %9s  %s" % (
        "#", "outcome", TYPE_ONE, TYPE_TWO, "p", "verdict")
    print(header)
    print("-" * len(header))

    for i in range(N_OUTCOMES):
        verdict = "significant" if p_values[i] < ALPHA else "not significant"
        print(f"{i + 1:3d}  {OUTCOME_NAMES[i]:-24s} {mean_one[i]:12.5g} {mean_two[i]:12.5g} {p_values[i]:9.4f}  {verdict}")


if __name__ == "__main__":
    main()
