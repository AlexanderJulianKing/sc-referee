"""Levothyroxine formulation trial: week-twelve analysis.

Compares the standard tablet against the oral liquid formulation on the four
pre-declared outcomes. The four outcomes are one declared family: all four
p-values are adjusted together, as one complete family, with the Holm-Bonferroni
step-down procedure, and every verdict is read from the adjusted p-value at the
conventional 0.05 threshold.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = "levothyroxine_formulation_trial.csv"

GROUP_COLUMN = "group"
TABLET = "tablet"
LIQUID = "liquid"

ALPHA = 0.05
ADJUSTMENT_METHOD = "holm"

# The outcome family declared in the trial protocol before randomisation,
# in its fixed order.
DECLARED_OUTCOMES = [
    ("tsh_miu_l", "Serum TSH (mIU/L)"),
    ("free_t4_pmol_l", "Serum free T4 (pmol/L)"),
    ("total_cholesterol_mmol_l", "Total cholesterol (mmol/L)"),
    ("symptom_score_0_40", "Hypothyroid symptom score (0-40)"),
]

# The single implausibly high week-twelve TSH value, read by the clinic as
# likely missed doses before the visit. It stays in the main analysis.
SENSITIVITY_EXCLUDED_PATIENT = "pt_60"


def compare_groups(frame, outcome):
    """Two-sample t-test for one outcome, tablet versus liquid."""
    tablet_values = frame.loc[frame[GROUP_COLUMN] == TABLET, outcome]
    liquid_values = frame.loc[frame[GROUP_COLUMN] == LIQUID, outcome]
    t_statistic, p_value = stats.ttest_ind(tablet_values, liquid_values)
    return {
        "n_tablet": int(tablet_values.size),
        "n_liquid": int(liquid_values.size),
        "mean_tablet": float(tablet_values.mean()),
        "mean_liquid": float(liquid_values.mean()),
        "t": float(t_statistic),
        "p": float(p_value),
    }


def main():
    data = pd.read_csv(DATA_FILE)

    print("=" * 72)
    print("PRIMARY ANALYSIS: declared outcome family (4 outcomes)")
    print("=" * 72)
    print(f"Patients read from {DATA_FILE}: {len(data)}")
    print(
        f"Group sizes: {TABLET} = {int((data[GROUP_COLUMN] == TABLET).sum())}, "
        f"{LIQUID} = {int((data[GROUP_COLUMN] == LIQUID).sum())}"
    )
    print("Test per outcome: two-sample t-test (tablet vs liquid)")
    print(
        "Multiplicity: all 4 p-values adjusted together as one complete family "
        f"({ADJUSTMENT_METHOD}), verdicts read from adjusted p at alpha = {ALPHA}"
    )
    print()

    # One comparison per declared outcome; p-values kept together, in order.
    results = [compare_groups(data, outcome) for outcome, _ in DECLARED_OUTCOMES]
    raw_p_values = [result["p"] for result in results]

    # Adjust the complete family of four p-values in one call.
    rejected, adjusted_p_values, _, _ = multipletests(
        raw_p_values, alpha=ALPHA, method=ADJUSTMENT_METHOD
    )

    for index, (outcome, label) in enumerate(DECLARED_OUTCOMES):
        result = results[index]
        verdict = (
            "significant (adjusted p < 0.05)"
            if rejected[index]
            else "not significant (adjusted p >= 0.05)"
        )
        print(f"Outcome {index + 1}: {label}  [{outcome}]")
        print(
            f"  mean {TABLET} (n={result['n_tablet']}) = {result['mean_tablet']:.3f}"
            f"   mean {LIQUID} (n={result['n_liquid']}) = {result['mean_liquid']:.3f}"
            f"   difference (liquid - tablet) = "
            f"{result['mean_liquid'] - result['mean_tablet']:+.3f}"
        )
        print(f"  unadjusted p (for reference only) = {result['p']:.4f}")
        print(f"  adjusted p ({ADJUSTMENT_METHOD}, family of 4) = "
              f"{adjusted_p_values[index]:.4f}")
        print(f"  verdict = {verdict}")
        print()

    # ------------------------------------------------------------------
    # SENSITIVITY / ROBUSTNESS CHECK (NOT an inferential result)
    # ------------------------------------------------------------------
    print("=" * 72)
    print("ROBUSTNESS CHECK (NOT PART OF THE FAMILY, NOT AN INFERENTIAL RESULT)")
    print("=" * 72)
    print(
        f"Repeat of the TSH comparison only, with patient "
        f"{SENSITIVITY_EXCLUDED_PATIENT} excluded (implausibly high week-twelve "
        "TSH, read as likely missed doses before the visit)."
    )
    print(
        "Nothing below is adjusted, re-adjusted or re-verdicted; the trial's "
        "verdicts stand as printed in the primary analysis above."
    )
    print()

    reduced = data.loc[data["patient_id"] != SENSITIVITY_EXCLUDED_PATIENT]
    check = compare_groups(reduced, "tsh_miu_l")
    print("Robustness check: Serum TSH (mIU/L)  [tsh_miu_l]")
    print(f"  patients used = {len(reduced)}")
    print(
        f"  mean {TABLET} (n={check['n_tablet']}) = {check['mean_tablet']:.3f}"
        f"   mean {LIQUID} (n={check['n_liquid']}) = {check['mean_liquid']:.3f}"
        f"   difference (liquid - tablet) = "
        f"{check['mean_liquid'] - check['mean_tablet']:+.3f}"
    )
    print(f"  p-value of this check (unadjusted, no verdict attached) = "
          f"{check['p']:.4f}")
    print()
    print(
        "This is a robustness check on the TSH result only. It is not an "
        "inferential result of its own."
    )


if __name__ == "__main__":
    main()
