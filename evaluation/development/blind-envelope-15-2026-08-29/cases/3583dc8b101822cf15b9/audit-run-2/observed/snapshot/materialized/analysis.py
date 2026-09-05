"""Two-stage analysis of the informal e-waste recycling survey.

Reads the fixed survey data file ``data.csv`` and runs the two-stage
discovery/validation procedure that the survey protocol fixed in advance:

  Stage 1 (discovery half only)
      Each of the six pre-declared outcomes is compared between the two
      trades with one Welch two-sample t-test.  Outcomes reaching the
      screening level of 0.05 are carried forward as survivors.  The
      discovery half yields no conclusion of its own.

  Stage 2 (validation half only)
      Only the survivors are tested, again with a Welch two-sample
      t-test, and each is judged at a Bonferroni level adjusted for the
      number of outcomes actually carried into validation, so that the
      family-wise error rate across the confirmed findings stays at 0.05.

The script only reads ``data.csv``; it never generates, simulates or
overwrites it.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "data.csv"

GROUP_COLUMN = "trade"
EXPOSED_GROUP = "recycling"
CONTROL_GROUP = "textile"

STAGE_COLUMN = "analysis_stage"
DISCOVERY_STAGE = "discovery"
VALIDATION_STAGE = "validation"

# The outcome family exactly as the survey protocol declared it, in order.
DECLARED_OUTCOMES = [
    ("blood_lead_ug_dl", "Blood lead", "ug/dL", 2),
    ("urinary_cadmium_ug_g_cr", "Urinary cadmium", "ug/g creatinine", 3),
    ("urinary_nickel_ug_l", "Urinary nickel", "ug/L", 2),
    ("haemoglobin_g_dl", "Haemoglobin", "g/dL", 2),
    ("serum_alt_u_l", "Serum ALT", "U/L", 2),
    ("urinary_8ohdg_ng_mg_cr", "Urinary 8-OHdG", "ng/mg creatinine", 2),
]

SCREENING_LEVEL = 0.05
FAMILY_ERROR_RATE = 0.05


def load_data():
    """Read the fixed survey data file."""
    return pd.read_csv(DATA_FILE)


def format_p(p):
    """Render a p-value without collapsing very small values to zero."""
    if p < 0.00001:
        return f"{p:.2e}"
    return f"{p:.5f}"


def report_group_sizes(data):
    """Print the number of workers of each trade in each half of the survey."""
    print("GROUP SIZES BY ANALYSIS STAGE")
    print("-" * 72)
    counts = pd.crosstab(data[GROUP_COLUMN], data[STAGE_COLUMN])
    counts = counts.reindex(
        index=[EXPOSED_GROUP, CONTROL_GROUP],
        columns=[DISCOVERY_STAGE, VALIDATION_STAGE],
    )
    header = f"{'trade':<12}" + "".join(
        f"{stage:>14}" for stage in [DISCOVERY_STAGE, VALIDATION_STAGE]
    )
    print(header + f"{'total':>14}")
    for group in [EXPOSED_GROUP, CONTROL_GROUP]:
        row = counts.loc[group]
        print(
            f"{group:<12}"
            + "".join(f"{int(row[stage]):>14}" for stage in [DISCOVERY_STAGE, VALIDATION_STAGE])
            + f"{int(row.sum()):>14}"
        )
    print(f"{'total':<12}" + "".join(
        f"{int(counts[stage].sum()):>14}" for stage in [DISCOVERY_STAGE, VALIDATION_STAGE]
    ) + f"{int(counts.values.sum()):>14}")
    print()


def report_summaries(data):
    """Print per-group mean and standard deviation for every declared outcome."""
    print("PER-GROUP SUMMARY VALUES FOR EACH DECLARED OUTCOME (mean +/- SD)")
    print("-" * 72)
    for stage in [DISCOVERY_STAGE, VALIDATION_STAGE]:
        half = data[data[STAGE_COLUMN] == stage]
        n_exposed = int((half[GROUP_COLUMN] == EXPOSED_GROUP).sum())
        n_control = int((half[GROUP_COLUMN] == CONTROL_GROUP).sum())
        print(f"{stage} half")
        print(
            f"  {'outcome':<26}{'unit':<20}"
            f"{f'{EXPOSED_GROUP} (n={n_exposed})':>20}"
            f"{f'{CONTROL_GROUP} (n={n_control})':>20}"
        )
        for column, label, unit, places in DECLARED_OUTCOMES:
            exposed = half.loc[half[GROUP_COLUMN] == EXPOSED_GROUP, column]
            control = half.loc[half[GROUP_COLUMN] == CONTROL_GROUP, column]
            exposed_text = f"{exposed.mean():.{places}f} +/- {exposed.std(ddof=1):.{places}f}"
            control_text = f"{control.mean():.{places}f} +/- {control.std(ddof=1):.{places}f}"
            print(f"  {label:<26}{unit:<20}{exposed_text:>20}{control_text:>20}")
        print()


def welch_test(half, column):
    """Welch two-sample t-test comparing the two trades on one outcome."""
    exposed = half.loc[half[GROUP_COLUMN] == EXPOSED_GROUP, column]
    control = half.loc[half[GROUP_COLUMN] == CONTROL_GROUP, column]
    result = stats.ttest_ind(exposed, control, equal_var=False)
    return {
        "exposed_n": int(exposed.size),
        "control_n": int(control.size),
        "exposed_mean": float(exposed.mean()),
        "control_mean": float(control.mean()),
        "difference": float(exposed.mean() - control.mean()),
        "t": float(result.statistic),
        "p": float(result.pvalue),
    }


def run_discovery(data):
    """Stage 1: screen all six declared outcomes in the discovery half only."""
    print("STAGE 1: DISCOVERY HALF SCREENING")
    print("-" * 72)
    print(f"Screening level: {SCREENING_LEVEL:.2f} (unadjusted; screening yields no conclusions)")
    print(
        f"  {'outcome':<26}{'diff':>10}{'t':>10}{'p':>12}   outcome of screening"
    )

    half = data[data[STAGE_COLUMN] == DISCOVERY_STAGE]
    results = {}
    survivors = []
    for column, label, _unit, places in DECLARED_OUTCOMES:
        result = welch_test(half, column)
        results[column] = result
        carried = result["p"] < SCREENING_LEVEL
        if carried:
            survivors.append(column)
        verdict = "carried forward" if carried else "not carried forward"
        print(
            f"  {label:<26}{result['difference']:>10.{places}f}"
            f"{result['t']:>10.3f}{format_p(result['p']):>12}   {verdict}"
        )
    print()

    survivor_labels = [
        label for column, label, _u, _p in DECLARED_OUTCOMES if column in survivors
    ]
    if survivor_labels:
        print("Survivors of screening: " + ", ".join(survivor_labels))
    else:
        print("Survivors of screening: none")
    print(f"Number carried forward into validation: {len(survivors)}")
    print()
    return results, survivors


def run_validation(data, survivors):
    """Stage 2: test only the survivors in the validation half only."""
    print("STAGE 2: VALIDATION HALF CONFIRMATION")
    print("-" * 72)

    carried = len(survivors)
    if carried == 0:
        print("No outcome was carried forward, so no validation test was run.")
        print("The survey confirms no finding.")
        print()
        return {}, None, []

    adjusted_level = FAMILY_ERROR_RATE / carried
    print(
        f"Family-wise error rate to hold across confirmed findings: {FAMILY_ERROR_RATE:.2f}"
    )
    print(
        f"Adjusted validation level: {FAMILY_ERROR_RATE:.2f} / {carried} "
        f"= {adjusted_level:.6f} (Bonferroni over the {carried} outcomes carried forward)"
    )
    print(
        f"  {'outcome':<26}{'diff':>10}{'t':>10}{'p':>12}   validation result"
    )

    half = data[data[STAGE_COLUMN] == VALIDATION_STAGE]
    results = {}
    confirmed = []
    for column, label, _unit, places in DECLARED_OUTCOMES:
        if column not in survivors:
            continue
        result = welch_test(half, column)
        results[column] = result
        is_confirmed = result["p"] < adjusted_level
        if is_confirmed:
            confirmed.append(column)
        verdict = "confirmed" if is_confirmed else "not confirmed"
        print(
            f"  {label:<26}{result['difference']:>10.{places}f}"
            f"{result['t']:>10.3f}{format_p(result['p']):>12}   {verdict}"
        )
    print()
    return results, adjusted_level, confirmed


def report_conclusions(survivors, confirmed):
    """Print the confirmed findings, which rest on the validation stage only."""
    print("CONFIRMED FINDINGS (validation stage only)")
    print("-" * 72)
    labels = {column: label for column, label, _u, _p in DECLARED_OUTCOMES}
    if confirmed:
        for column, label, _unit, _places in DECLARED_OUTCOMES:
            if column in confirmed:
                print(f"  {label}: confirmed at the adjusted validation level")
    else:
        print("  none")

    not_confirmed = [c for c in survivors if c not in confirmed]
    if not_confirmed:
        print("Carried forward but not confirmed in validation: "
              + ", ".join(labels[c] for c in not_confirmed))

    not_carried = [
        label
        for column, label, _u, _p in DECLARED_OUTCOMES
        if column not in survivors
    ]
    if not_carried:
        print("Not carried forward out of screening (no finding claimed): "
              + ", ".join(not_carried))
    print()


def main():
    data = load_data()

    print("=" * 72)
    print("INFORMAL E-WASTE RECYCLING SURVEY: TWO-STAGE ANALYSIS")
    print("=" * 72)
    print(f"Workers in file: {len(data)}")
    print()

    report_group_sizes(data)
    report_summaries(data)

    _discovery_results, survivors = run_discovery(data)
    _validation_results, _adjusted_level, confirmed = run_validation(data, survivors)
    report_conclusions(survivors, confirmed)


if __name__ == "__main__":
    main()
