"""Eel catchment survey: two-stage discovery / validation analysis.

Reads eel_catchment_survey.csv and runs the two pre-specified analysis stages
in the declared order:

  1. Discovery stage  -- eels with stage == "discovery" only. All six declared
     outcomes are compared between catchments and screened at a liberal
     screening level of 0.05. This stage is screening only; it makes no claim.

  2. Validation stage -- eels with stage == "validation" only. Only the
     outcomes that survived the discovery screen are re-tested, each judged
     against 0.05 divided by the number of outcomes carried into validation.

Every conclusion rests on the validation stage.

Two-sample comparisons use Welch's two-sample t-test (unequal-variance
t-test), a standard significance test for continuous measurements.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "eel_catchment_survey.csv"

GROUP_COL = "catchment"
STAGE_COL = "stage"
GROUP_A = "impacted"
GROUP_B = "reference"

SCREENING_ALPHA = 0.05
VALIDATION_FAMILY_ALPHA = 0.05

# The six declared outcomes, in the pre-declared order, with display labels.
OUTCOMES = [
    ("hg_mg_kg", "Muscle total mercury (mg/kg ww)"),
    ("pcb6_ug_kg", "Sum of 6 indicator PCBs (ug/kg ww)"),
    ("erod_pmol_min_mg", "Liver EROD activity (pmol/min/mg protein)"),
    ("fulton_k", "Fulton condition factor (dimensionless)"),
    ("hsi_pct", "Hepatosomatic index (% body mass)"),
    ("lipid_pct", "Muscle lipid content (% wet mass)"),
]


def compare(frame, outcome):
    """Welch two-sample t-test of `outcome` between the two catchments."""
    a = frame.loc[frame[GROUP_COL] == GROUP_A, outcome]
    b = frame.loc[frame[GROUP_COL] == GROUP_B, outcome]
    t_stat, p_value = stats.ttest_ind(a, b, equal_var=False)
    return {
        "n_a": len(a),
        "n_b": len(b),
        "mean_a": a.mean(),
        "mean_b": b.mean(),
        "sd_a": a.std(ddof=1),
        "sd_b": b.std(ddof=1),
        "t": t_stat,
        "p": p_value,
    }


def main():
    data = pd.read_csv(DATA_FILE)

    print("=" * 78)
    print("EEL CATCHMENT SURVEY -- TWO-STAGE ANALYSIS")
    print("=" * 78)
    print(f"Rows loaded: {len(data)}")
    print(f"Catchment counts: {data[GROUP_COL].value_counts().to_dict()}")
    print(f"Stage counts:     {data[STAGE_COL].value_counts().to_dict()}")
    print("Test: Welch's two-sample t-test (impacted vs reference)")
    print()

    discovery = data[data[STAGE_COL] == "discovery"]
    validation = data[data[STAGE_COL] == "validation"]

    # ---------------------------------------------------------------- stage 1
    print("-" * 78)
    print("STAGE 1: DISCOVERY SCREEN")
    print(f"Eels used: {len(discovery)} "
          f"({(discovery[GROUP_COL] == GROUP_A).sum()} impacted, "
          f"{(discovery[GROUP_COL] == GROUP_B).sum()} reference)")
    print(f"Screening level: p < {SCREENING_ALPHA}")
    print("Screening only -- this stage makes no claim of its own.")
    print("-" * 78)
    print(f"{'outcome':<20}{'impacted':>12}{'reference':>12}"
          f"{'t':>10}{'p':>12}  screen")
    print()

    survivors = []
    discovery_results = {}
    for outcome, _label in OUTCOMES:
        res = compare(discovery, outcome)
        discovery_results[outcome] = res
        passed = res["p"] < SCREENING_ALPHA
        if passed:
            survivors.append(outcome)
        print(f"{outcome:<20}{res['mean_a']:>12.4f}{res['mean_b']:>12.4f}"
              f"{res['t']:>10.3f}{res['p']:>12.4g}  "
              f"{'SURVIVES' if passed else 'screened out'}")

    print()
    print(f"Outcomes surviving the discovery screen ({len(survivors)} of "
          f"{len(OUTCOMES)}): {', '.join(survivors) if survivors else 'none'}")
    print()

    # ---------------------------------------------------------------- stage 2
    print("-" * 78)
    print("STAGE 2: VALIDATION")
    print(f"Eels used: {len(validation)} "
          f"({(validation[GROUP_COL] == GROUP_A).sum()} impacted, "
          f"{(validation[GROUP_COL] == GROUP_B).sum()} reference)")
    print("-" * 78)

    if not survivors:
        print("No outcome survived the discovery screen. "
              "Nothing is carried into validation and no claim is made.")
        return

    adjusted_alpha = VALIDATION_FAMILY_ALPHA / len(survivors)
    print(f"Outcomes carried into validation: {len(survivors)}")
    print(f"Adjusted validation level: {VALIDATION_FAMILY_ALPHA} / "
          f"{len(survivors)} = {adjusted_alpha:.6f}")
    print()
    print(f"{'outcome':<20}{'impacted':>12}{'reference':>12}"
          f"{'t':>10}{'p':>12}  verdict")
    print()

    confirmed = []
    for outcome, _label in OUTCOMES:
        if outcome not in survivors:
            continue
        res = compare(validation, outcome)
        passed = res["p"] < adjusted_alpha
        if passed:
            confirmed.append(outcome)
        print(f"{outcome:<20}{res['mean_a']:>12.4f}{res['mean_b']:>12.4f}"
              f"{res['t']:>10.3f}{res['p']:>12.4g}  "
              f"{'CONFIRMED' if passed else 'not confirmed'}")
        print(f"{'':<20}SD {res['sd_a']:.4f} / {res['sd_b']:.4f}"
              f"   n {res['n_a']} / {res['n_b']}")

    print()
    print(f"Confirmed in validation ({len(confirmed)} of {len(survivors)} "
          f"carried forward): "
          f"{', '.join(confirmed) if confirmed else 'none'}")
    print()
    print("All conclusions of this project rest on the validation stage above.")
    print("=" * 78)


if __name__ == "__main__":
    main()
