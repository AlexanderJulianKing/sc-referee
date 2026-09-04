"""Two-stage analysis of serum micronutrient status in coeliac disease versus controls.

Reads the fixed authored file ``data.csv`` and runs the two-stage plan fixed by the
protocol before any measurement was taken:

  Stage 1 (screening) uses the discovery half only.  All six declared outcomes are
  compared between the two disease groups and screened at the conventional 0.05
  screening level.  Outcomes with p < 0.05 are the survivors.

  Stage 2 (validation) uses the validation half only.  The survivors are compared
  again, each judged at a level adjusted for the number of survivors carried
  forward, so the family error in the validation stage is controlled at 0.05.

Every confirmed conclusion comes from stage 2.  A stage 1 result on its own is a
screening result and confirms nothing.

Run with no arguments:  python3 analysis.py
"""

import pandas as pd
from scipy import stats

DATA_FILE = "data.csv"

GROUP_COLUMN = "disease_group"
HALF_COLUMN = "study_half"
CASE_GROUP = "coeliac"
CONTROL_GROUP = "control"

# The six outcomes declared in advance, in the order the analysis plan fixed.
DECLARED_OUTCOMES = [
    "serum_ferritin_ug_l",
    "serum_vitamin_b12_pmol_l",
    "serum_folate_nmol_l",
    "serum_zinc_umol_l",
    "serum_25oh_vitamin_d_nmol_l",
    "serum_magnesium_mmol_l",
]

SCREENING_LEVEL = 0.05
VALIDATION_FAMILY_LEVEL = 0.05


def compare_groups(frame, outcome):
    """Standard two-group comparison of one outcome between the two disease groups."""
    case_values = frame.loc[frame[GROUP_COLUMN] == CASE_GROUP, outcome]
    control_values = frame.loc[frame[GROUP_COLUMN] == CONTROL_GROUP, outcome]
    t_statistic, p_value = stats.ttest_ind(case_values, control_values)
    return {
        "outcome": outcome,
        "n_case": int(case_values.size),
        "n_control": int(control_values.size),
        "mean_case": float(case_values.mean()),
        "sd_case": float(case_values.std(ddof=1)),
        "mean_control": float(control_values.mean()),
        "sd_control": float(control_values.std(ddof=1)),
        "t": float(t_statistic),
        "p": float(p_value),
    }


def format_p(p_value):
    """Readable p-value: plain decimals, scientific notation when very small."""
    return f"{p_value:.6f}" if p_value >= 1e-6 else f"{p_value:.3e}"


def print_result_table(results, level_by_outcome, level_label):
    header = (
        f"{'outcome':<28}{'n coeliac':>10}{'n control':>11}"
        f"{'mean (SD) coeliac':>24}{'mean (SD) control':>24}"
        f"{'p-value':>12}{level_label:>14}{'verdict':>12}"
    )
    print(header)
    print("-" * len(header))
    for result in results:
        level = level_by_outcome[result["outcome"]]
        case_summary = f"{result['mean_case']:.3f} ({result['sd_case']:.3f})"
        control_summary = f"{result['mean_control']:.3f} ({result['sd_control']:.3f})"
        verdict = ("pass at {}".format(level) if result["p"] < level else "not passed at {}".format(level))
        print(
            f"{result['outcome']:<28}{result['n_case']:>10}{result['n_control']:>11}"
            f"{case_summary:>24}{control_summary:>24}"
            f"{format_p(result['p']):>12}{level:>14.6f}{verdict:>12}"
        )


def main():
    data = pd.read_csv(DATA_FILE)

    print("=" * 100)
    print("Serum micronutrient status: coeliac disease on a gluten-free diet versus healthy controls")
    print("=" * 100)
    print(f"Rows read from {DATA_FILE}: {len(data)}")
    print(f"Participants per disease group: {dict(data[GROUP_COLUMN].value_counts().sort_index())}")
    print(f"Participants per study half:    {dict(data[HALF_COLUMN].value_counts().sort_index())}")
    print(
        "Disease group by study half:    "
        f"{dict(data.groupby([HALF_COLUMN, GROUP_COLUMN]).size())}"
    )
    print(f"Declared outcomes, in plan order: {DECLARED_OUTCOMES}")
    print()

    # ------------------------------------------------------------------
    # Stage 1: screening in the discovery half
    # ------------------------------------------------------------------
    discovery = data[data[HALF_COLUMN] == "discovery"]

    print("=" * 100)
    print("STAGE 1  SCREENING  (discovery half only, all six declared outcomes)")
    print("=" * 100)
    print(f"Discovery half size: {len(discovery)} participants")
    print(f"Screening level applied to every outcome: {SCREENING_LEVEL}")
    print()

    stage1_results = [compare_groups(discovery, outcome) for outcome in DECLARED_OUTCOMES]
    stage1_levels = {result["outcome"]: SCREENING_LEVEL for result in stage1_results}
    print_result_table(stage1_results, stage1_levels, "level")
    print()

    survivors = [result["outcome"] for result in stage1_results if result["p"] < SCREENING_LEVEL]
    print(f"Outcomes screened: {len(stage1_results)}")
    print(f"Survivors carried forward to validation ({len(survivors)}): {survivors}")
    print("Stage 1 outcome: a screening result only. Nothing is confirmed by this stage.")
    print()

    # ------------------------------------------------------------------
    # Stage 2: validation in the validation half
    # ------------------------------------------------------------------
    validation = data[data[HALF_COLUMN] == "validation"]

    print("=" * 100)
    print("STAGE 2  VALIDATION  (validation half only, surviving outcomes only)")
    print("=" * 100)
    print(f"Validation half size: {len(validation)} participants")

    if not survivors:
        print("No outcome survived screening. The validation stage has nothing to test.")
        print("Stage 2 outcome: no confirmed difference between the groups.")
        return

    adjusted_level = VALIDATION_FAMILY_LEVEL / len(survivors)
    print(
        f"Survivors carried forward: {len(survivors)}. "
        f"Family error for the validation stage held at {VALIDATION_FAMILY_LEVEL}, so each "
        f"survivor is judged against {VALIDATION_FAMILY_LEVEL} / {len(survivors)} = "
        f"{adjusted_level:.6f}."
    )
    print()

    stage2_results = [compare_groups(validation, outcome) for outcome in survivors]
    stage2_levels = {result["outcome"]: adjusted_level for result in stage2_results}
    print_result_table(stage2_results, stage2_levels, "adj. level")
    print()

    confirmed = [result for result in stage2_results if result["p"] < adjusted_level]
    not_confirmed = [result for result in stage2_results if result["p"] >= adjusted_level]

    print("Stage 2 outcome (the only stage that confirms anything):")
    if confirmed:
        for result in confirmed:
            direction = "lower" if result["mean_case"] < result["mean_control"] else "higher"
            print(
                f"  CONFIRMED  {result['outcome']}: coeliac {direction} than control "
                f"({result['mean_case']:.3f} vs {result['mean_control']:.3f}), "
                f"p = {format_p(result['p'])} < {adjusted_level:.6f}"
            )
    else:
        print("  No survivor met its adjusted level. Nothing is confirmed.")
    for result in not_confirmed:
        print(
            f"  NOT CONFIRMED  {result['outcome']}: p = {format_p(result['p'])} "
            f">= {adjusted_level:.6f}"
        )
    print()
    print("Outcomes that did not survive stage 1 were never tested in the validation half "
          "and are not confirmed.")


if __name__ == "__main__":
    main()
