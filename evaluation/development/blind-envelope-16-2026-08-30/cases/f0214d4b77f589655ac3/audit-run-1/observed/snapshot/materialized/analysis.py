"""Girth pad trial: two-group comparison over the five declared outcomes.

Compares donkeys working in a closed-cell foam girth pad against donkeys working
in a traditional sacking-wrapped girth on each of the five pre-declared outcomes,
using a two-sample t-test per outcome. The family-wise error rate across the five
declared outcomes is controlled with a Sidak per-comparison threshold computed
explicitly below.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "girth_pad_trial.csv"
GROUP_COL = "girth_type"
GROUP_A = "foam_pad"
GROUP_B = "sacking_wrap"

# The five outcomes declared in advance, in the declared order.
OUTCOMES = [
    "lesion_score_pts",
    "hair_loss_cm2",
    "nociceptive_threshold_n",
    "body_condition_pts",
    "rectal_temp_c",
]

# --- Sidak per-comparison threshold, worked out by hand -----------------------
FAMILY_WISE_ALPHA = 0.05
FAMILY_SIZE = 5  # number of declared outcomes in the family
assert FAMILY_SIZE == len(OUTCOMES), "family size must match the declared outcome list"

# Sidak: alpha_pc = 1 - (1 - alpha_fw) ** (1 / m)
SIDAK_THRESHOLD = 1.0 - (1.0 - FAMILY_WISE_ALPHA) ** (1.0 / FAMILY_SIZE)


def main():
    df = pd.read_csv(DATA_FILE)

    group_a = df[df[GROUP_COL] == GROUP_A]
    group_b = df[df[GROUP_COL] == GROUP_B]

    print("Girth pad trial: foam pad vs traditional sacking-wrapped girth")
    print(f"Rows loaded: {len(df)}  ({GROUP_A}: {len(group_a)}, {GROUP_B}: {len(group_b)})")
    print()
    print("Multiplicity control (Sidak, computed by hand):")
    print(f"  family-wise alpha           = {FAMILY_WISE_ALPHA}")
    print(f"  family size (m)             = {FAMILY_SIZE}")
    print(f"  1 - (1 - {FAMILY_WISE_ALPHA}) ** (1 / {FAMILY_SIZE})")
    print(f"  per-comparison threshold    = {SIDAK_THRESHOLD:.6f}")
    print()

    header = (
        f"{'outcome':<26}{'mean_' + GROUP_A:>16}{'mean_' + GROUP_B:>18}"
        f"{'p_value':>14}{'threshold':>12}  verdict"
    )
    print(header)
    print("-" * len(header))

    results = []
    for outcome in OUTCOMES:
        a = group_a[outcome]
        b = group_b[outcome]
        t_stat, p_value = stats.ttest_ind(a, b)

        significant = p_value < SIDAK_THRESHOLD
        verdict = "significant" if significant else "not significant"

        results.append(
            {
                "outcome": outcome,
                "mean_foam_pad": a.mean(),
                "mean_sacking_wrap": b.mean(),
                "t_stat": t_stat,
                "p_value": p_value,
                "threshold": SIDAK_THRESHOLD,
                "verdict": verdict,
            }
        )

        print(
            f"{outcome:<26}{a.mean():>16.4f}{b.mean():>18.4f}"
            f"{p_value:>14.6g}{SIDAK_THRESHOLD:>12.6f}  {verdict}"
        )

    print()
    print("Per-outcome detail:")
    for r in results:
        print(
            f"  {r['outcome']}: mean({GROUP_A}) = {r['mean_foam_pad']:.4f}, "
            f"mean({GROUP_B}) = {r['mean_sacking_wrap']:.4f}, "
            f"t = {r['t_stat']:.4f}, p = {r['p_value']:.6g}, "
            f"Sidak threshold = {SIDAK_THRESHOLD:.6f} -> {r['verdict']}"
        )


if __name__ == "__main__":
    main()
