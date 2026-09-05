"""Week-12 outcomes of the resistance training trial in adults aged 65-80.

Five outcomes are tested as one family. The family-wide error rate is fixed at 5%
before any test is run, and the per-outcome threshold is the Sidak value written out
by hand below so that a reader can check the arithmetic.
"""

import pandas as pd
from scipy import stats

FAMILY_ALPHA = 0.05

OUTCOMES = [
    ("leg_press_1rm_kg", "Leg press 1RM (kg)"),
    ("gait_speed_m_s", "4 m gait speed (m/s)"),
    ("sts_time_s", "5x sit-to-stand (s)"),
    ("lean_mass_kg", "Appendicular lean mass (kg)"),
    ("sf36_physical", "SF-36 physical function"),
]


def main():
    data = pd.read_csv("data.csv")
    stretch = data[data["arm"] == "stretch"]
    resistance = data[data["arm"] == "resistance"]

    # Sidak threshold for a family of k outcomes at a family-wide rate of alpha:
    #     alpha_per_outcome = 1 - (1 - alpha) ** (1 / k)
    # With k = 5 and alpha = 0.05 that is one minus the fifth root of 0.95.
    k = len(OUTCOMES)
    one_minus_alpha = 1 - FAMILY_ALPHA          # 0.95
    fifth_root = one_minus_alpha ** (1 / k)     # 0.95 ** 0.2
    per_outcome_alpha = 1 - fifth_root

    print(f"Family: {k} outcomes, family-wide alpha = {FAMILY_ALPHA}")
    print(f"Sidak: 1 - (1 - {FAMILY_ALPHA}) ** (1/{k}) = 1 - {one_minus_alpha}"
          f" ** {1 / k} = 1 - {fifth_root:.6f}")
    print(f"Per-outcome threshold = {per_outcome_alpha:.6f}")
    print(f"n = {len(stretch)} stretch, {len(resistance)} resistance")
    print()
    print(f"{'outcome':<28}{'stretch':>10}{'resistance':>12}{'p':>12}  verdict")

    for column, label in OUTCOMES:
        a = stretch[column]
        b = resistance[column]
        result = stats.ttest_ind(a, b, equal_var=False)
        verdict = ("clears threshold" if result.pvalue < per_outcome_alpha
                   else "does not clear threshold")
        print(f"{label:<28}{a.mean():>10.2f}{b.mean():>12.2f}"
              f"{result.pvalue:>12.5f}  {verdict}")


if __name__ == "__main__":
    main()
