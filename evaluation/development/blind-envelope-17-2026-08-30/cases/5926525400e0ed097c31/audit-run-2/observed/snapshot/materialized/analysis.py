"""Analysis for the sugarcane chemical ripener trial.

Two-stage plan fixed before harvest:

  Stage 1 (screening): in the discovery half only, compare the two ripener
  conditions on all six declared outcomes with a two-sample t-test and screen
  at 0.05. This stage is screening only and never a conclusion.

  Stage 2 (confirmatory): in the validation half only, test only the outcomes
  that survived the screen, and judge each against 0.05 divided by the number
  of outcomes carried forward from the screen.

Reads cane_ripener_trial.csv from the current directory.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "cane_ripener_trial.csv"

GROUP_COL = "treatment"
HALF_COL = "study_half"
GROUP_A = "ripened"
GROUP_B = "untreated"

# Declared outcome family, in the pre-fixed order.
OUTCOMES = [
    "stalk_height_cm",
    "stalk_fresh_mass_kg",
    "soluble_solids_brix",
    "juice_purity_pct",
    "fibre_pct",
    "recoverable_sugar_kg_per_t",
]

SCREEN_ALPHA = 0.05
CONFIRM_ALPHA = 0.05


def compare(frame, outcome):
    """Two-sample t-test between the two ripener conditions on one outcome."""
    ripened = frame.loc[frame[GROUP_COL] == GROUP_A, outcome]
    untreated = frame.loc[frame[GROUP_COL] == GROUP_B, outcome]
    t_stat, p_value = stats.ttest_ind(ripened, untreated)
    return {
        "mean_ripened": ripened.mean(),
        "mean_untreated": untreated.mean(),
        "n_ripened": len(ripened),
        "n_untreated": len(untreated),
        "t": t_stat,
        "p": p_value,
    }


def main():
    data = pd.read_csv(DATA_FILE)

    discovery = data[data[HALF_COL] == "discovery"]
    validation = data[data[HALF_COL] == "validation"]

    print("Sugarcane chemical ripener trial: two-stage analysis")
    print("=" * 60)
    print(f"Rows read: {len(data)}")
    print(f"Discovery half: {len(discovery)} stools "
          f"({(discovery[GROUP_COL] == GROUP_A).sum()} {GROUP_A}, "
          f"{(discovery[GROUP_COL] == GROUP_B).sum()} {GROUP_B})")
    print(f"Validation half: {len(validation)} stools "
          f"({(validation[GROUP_COL] == GROUP_A).sum()} {GROUP_A}, "
          f"{(validation[GROUP_COL] == GROUP_B).sum()} {GROUP_B})")
    print()

    # ------------------------------------------------------------------
    # Stage 1: screening in the discovery half only.
    # ------------------------------------------------------------------
    print("STAGE 1 - SCREENING (discovery half only, alpha = 0.05)")
    print("Screening only. No outcome is declared on discovery-half evidence.")
    print("-" * 60)

    survivors = []
    for outcome in OUTCOMES:
        res = compare(discovery, outcome)
        passed = res["p"] < SCREEN_ALPHA
        if passed:
            survivors.append(outcome)
        print(f"{outcome}:")
        print(f"  mean {GROUP_A} = {res['mean_ripened']:.3f} "
              f"(n = {res['n_ripened']}), "
              f"mean {GROUP_B} = {res['mean_untreated']:.3f} "
              f"(n = {res['n_untreated']})")
        print(f"  t = {res['t']:.3f}, p = {res['p']:.6g} -> "
              f"{'survives screen' if passed else 'does not survive screen'}")
    print()

    print(f"Outcomes surviving the screen ({len(survivors)} of {len(OUTCOMES)}): "
          f"{', '.join(survivors) if survivors else 'none'}")
    not_carried = [o for o in OUTCOMES if o not in survivors]
    print(f"Not carried forward ({len(not_carried)}): "
          f"{', '.join(not_carried) if not_carried else 'none'}")
    print()

    # ------------------------------------------------------------------
    # Stage 2: confirmation in the validation half only.
    # ------------------------------------------------------------------
    if not survivors:
        print("STAGE 2 - CONFIRMATORY: no outcome survived the screen, "
              "so nothing is carried forward and no outcome is confirmed.")
        return

    threshold = CONFIRM_ALPHA / len(survivors)

    print("STAGE 2 - CONFIRMATORY (validation half only)")
    print(f"Threshold: 0.05 / {len(survivors)} carried forward = "
          f"{threshold:.6f}")
    print("-" * 60)

    for outcome in survivors:
        res = compare(validation, outcome)
        confirmed = res["p"] < threshold
        print(f"{outcome}:")
        print(f"  validation mean {GROUP_A} = {res['mean_ripened']:.3f} "
              f"(n = {res['n_ripened']})")
        print(f"  validation mean {GROUP_B} = {res['mean_untreated']:.3f} "
              f"(n = {res['n_untreated']})")
        print(f"  difference ({GROUP_A} - {GROUP_B}) = "
              f"{res['mean_ripened'] - res['mean_untreated']:.3f}")
        print(f"  validation p = {res['p']:.6g}")
        print(f"  compared against threshold = {threshold:.6g}")
        print(f"  verdict: {'CONFIRMED' if confirmed else 'NOT CONFIRMED'}")

    print()
    print("Outcomes that did not survive the screen receive no confirmatory "
          "verdict.")
    print("All conclusions rest on the validation half.")


if __name__ == "__main__":
    main()
