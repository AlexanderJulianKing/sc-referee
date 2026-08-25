"""Two-stage biomarker comparison in a blood donor cohort.

Stage one screens the five protocol-declared outcomes in the discovery half at
the conventional 0.05 level. Stage two re-tests only the outcomes carried
forward, in the validation half, at a Bonferroni-adjusted level derived from the
number of outcomes carried forward. Every conclusion rests on stage two.

The discovery/validation split is fixed in the data file; this script never
reassigns it.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "donor_biomarkers.csv"

GROUP_COL = "smoking_status"
STAGE_COL = "study_stage"
SMOKER = "smoker"
NEVER_SMOKER = "never_smoker"
DISCOVERY = "discovery"
VALIDATION = "validation"

# The five protocol-declared outcomes, in the declared order.
OUTCOMES = [
    ("crp_mg_l", "Plasma C-reactive protein (mg/L)"),
    ("wbc_count_10e9_per_l", "White blood cell count (10^9/L)"),
    ("fibrinogen_g_l", "Plasma fibrinogen (g/L)"),
    ("hdl_cholesterol_mmol_l", "HDL cholesterol (mmol/L)"),
    ("vitamin_c_umol_l", "Serum vitamin C (umol/L)"),
]

SCREENING_ALPHA = 0.05
FAMILYWISE_ALPHA = 0.05


def rule(char="-", width=78):
    print(char * width)


def two_group_test(frame, outcome):
    """Welch two-sample t-test, smokers versus never-smokers, on one outcome."""
    smokers = frame.loc[frame[GROUP_COL] == SMOKER, outcome]
    never = frame.loc[frame[GROUP_COL] == NEVER_SMOKER, outcome]
    result = stats.ttest_ind(smokers, never, equal_var=False)
    return {
        "n_smoker": int(smokers.size),
        "n_never": int(never.size),
        "mean_smoker": float(smokers.mean()),
        "mean_never": float(never.mean()),
        "mean_difference": float(smokers.mean() - never.mean()),
        "t_statistic": float(result.statistic),
        "p_value": float(result.pvalue),
    }


def main():
    data = pd.read_csv(DATA_FILE)

    print("Two-stage biomarker comparison in a blood donor cohort")
    rule("=")
    print(f"Data file: {DATA_FILE.name}")
    print(f"Donors read: {len(data)}")
    print(f"Missing cells: {int(data.isna().sum().sum())}")
    print()

    # ------------------------------------------------------------------
    # Cohort composition
    # ------------------------------------------------------------------
    print("Cohort composition")
    rule()
    print("Donors in each smoking group:")
    for group in (SMOKER, NEVER_SMOKER):
        print(f"  {group:<14} {int((data[GROUP_COL] == group).sum()):>3}")
    print("Donors in each half:")
    for stage in (DISCOVERY, VALIDATION):
        print(f"  {stage:<14} {int((data[STAGE_COL] == stage).sum()):>3}")
    print("Smoking group by half:")
    crosstab = pd.crosstab(data[GROUP_COL], data[STAGE_COL])
    for group in (SMOKER, NEVER_SMOKER):
        counts = "  ".join(
            f"{stage}={int(crosstab.loc[group, stage]):>3}"
            for stage in (DISCOVERY, VALIDATION)
        )
        print(f"  {group:<14} {counts}")
    print()

    # ------------------------------------------------------------------
    # Per-group summary of every declared outcome (whole cohort)
    # ------------------------------------------------------------------
    print("Per-group summary of each declared outcome (all 120 donors)")
    rule()
    header = f"{'outcome':<34} {'group':<14} {'n':>4} {'mean':>9} {'sd':>8}"
    print(header)
    for outcome, label in OUTCOMES:
        for group in (SMOKER, NEVER_SMOKER):
            values = data.loc[data[GROUP_COL] == group, outcome]
            print(
                f"{outcome:<34} {group:<14} {values.size:>4} "
                f"{values.mean():>9.3f} {values.std(ddof=1):>8.3f}"
            )
    print()
    print("Spread is the sample standard deviation (ddof=1).")
    print()

    # ------------------------------------------------------------------
    # Stage one: screening in the discovery half
    # ------------------------------------------------------------------
    discovery = data[data[STAGE_COL] == DISCOVERY]
    validation = data[data[STAGE_COL] == VALIDATION]

    print("Stage one: screening (discovery half only)")
    rule()
    print(f"Discovery donors: {len(discovery)}")
    print("Test: Welch two-sample t-test, smokers vs never-smokers.")
    print(f"Screening level: {SCREENING_ALPHA:.2f} (unadjusted).")
    print("This stage produces candidates, not conclusions.")
    print()
    print(
        f"{'outcome':<34} {'diff':>9} {'t':>8} {'p':>10}  screening outcome"
    )

    screening = {}
    carried_forward = []
    for outcome, label in OUTCOMES:
        res = two_group_test(discovery, outcome)
        screening[outcome] = res
        passed = res["p_value"] < SCREENING_ALPHA
        if passed:
            carried_forward.append(outcome)
        verdict = "carried forward" if passed else "screened out"
        print(
            f"{outcome:<34} {res['mean_difference']:>9.3f} "
            f"{res['t_statistic']:>8.3f} {res['p_value']:>10.4g}  {verdict}"
        )
    print()
    print(f"Outcomes carried forward: {len(carried_forward)} of {len(OUTCOMES)}")
    for outcome in carried_forward:
        print(f"  {outcome}")
    print()

    # ------------------------------------------------------------------
    # Stage two: confirmation in the validation half
    # ------------------------------------------------------------------
    print("Stage two: confirmation (validation half only)")
    rule()
    print(f"Validation donors: {len(validation)}")

    n_carried = len(carried_forward)
    if n_carried == 0:
        print("No outcome was carried forward, so no confirmation test was run.")
        confirmation = {}
        adjusted_alpha = None
    else:
        adjusted_alpha = FAMILYWISE_ALPHA / n_carried
        print("Test: Welch two-sample t-test, smokers vs never-smokers.")
        print(
            f"Bonferroni adjustment: family-wise level {FAMILYWISE_ALPHA:.2f} "
            f"divided by {n_carried} outcomes carried forward."
        )
        print(f"Adjusted confirmation level: {adjusted_alpha:.6f}")
        print()
        print(
            f"{'outcome':<34} {'diff':>9} {'t':>8} {'p':>10}  confirmation outcome"
        )
        confirmation = {}
        for outcome in carried_forward:
            res = two_group_test(validation, outcome)
            confirmation[outcome] = res
            verdict = (
                "CONFIRMED" if res["p_value"] < adjusted_alpha else "not confirmed"
            )
            print(
                f"{outcome:<34} {res['mean_difference']:>9.3f} "
                f"{res['t_statistic']:>8.3f} {res['p_value']:>10.4g}  {verdict}"
            )
    print()

    # ------------------------------------------------------------------
    # Conclusions: validation stage only
    # ------------------------------------------------------------------
    print("Conclusions by declared outcome (validation stage only)")
    rule()
    for outcome, label in OUTCOMES:
        if outcome in confirmation:
            res = confirmation[outcome]
            if res["p_value"] < adjusted_alpha:
                direction = "higher" if res["mean_difference"] > 0 else "lower"
                print(
                    f"{label}: confirmed. In the validation half the smoker mean "
                    f"is {direction} than the never-smoker mean "
                    f"(difference {res['mean_difference']:.3f}, "
                    f"p = {res['p_value']:.4g} < {adjusted_alpha:.6f})."
                )
            else:
                print(
                    f"{label}: not confirmed. Carried into the validation half, "
                    f"it did not meet the adjusted level "
                    f"(p = {res['p_value']:.4g}, adjusted level "
                    f"{adjusted_alpha:.6f})."
                )
        else:
            print(
                f"{label}: not confirmed. It did not pass discovery screening, "
                f"so it was never tested in the validation half and no "
                f"significance claim is made for it."
            )
    print()
    print(
        "Discovery-half p-values are screening figures only. No conclusion in "
        "this analysis rests on them."
    )


if __name__ == "__main__":
    main()
