"""Exoskeleton picking trial: compare the exoskeleton and control groups on the five
declared outcomes.

One row of exo_picking_trial.csv is one order picker, measured once on a standardised
mixed-case picking round. The five outcomes below are the outcomes the protocol declared
in advance, in the declared order.

The protocol fixed the per-outcome significance threshold at 0.01 before any data were
collected. This script uses that fixed threshold as given and does nothing else with it.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "exo_picking_trial.csv"

GROUP_COLUMN = "exo_group"
TREATMENT_GROUP = "exoskeleton"
CONTROL_GROUP = "control"

# Fixed by the protocol in advance. Used here as a plain constant.
ALPHA = 0.01

# The five declared outcomes, in declared order.
OUTCOMES = [
    ("peak_lumbar_compression_n", "Peak lumbar compression (N)"),
    ("borg_exertion_score", "Borg perceived exertion (6-20)"),
    ("round_time_min", "Round completion time (min)"),
    ("picking_errors", "Picking errors (count)"),
    ("shoulder_discomfort_score", "Shoulder discomfort (0-10)"),
]


def load_data(path=DATA_FILE):
    frame = pd.read_csv(path)
    expected = [
        "picker_id",
        GROUP_COLUMN,
        *[column for column, _ in OUTCOMES],
    ]
    missing = [column for column in expected if column not in frame.columns]
    if missing:
        raise ValueError(f"missing expected columns: {missing}")
    groups = set(frame[GROUP_COLUMN].unique())
    if groups != {TREATMENT_GROUP, CONTROL_GROUP}:
        raise ValueError(f"unexpected group values: {sorted(groups)}")
    if frame[expected].isna().any().any():
        raise ValueError("data file contains missing values")
    if frame["picker_id"].duplicated().any():
        raise ValueError("picker_id is not unique")
    return frame


def compare_outcome(frame, column):
    exo = frame.loc[frame[GROUP_COLUMN] == TREATMENT_GROUP, column].astype(float)
    control = frame.loc[frame[GROUP_COLUMN] == CONTROL_GROUP, column].astype(float)
    # Two-group significance test for independent samples (Welch's t-test).
    result = stats.ttest_ind(exo, control, equal_var=False)
    return {
        "outcome": column,
        "n_exo": int(exo.size),
        "n_control": int(control.size),
        "mean_exo": float(exo.mean()),
        "sd_exo": float(exo.std(ddof=1)),
        "mean_control": float(control.mean()),
        "sd_control": float(control.std(ddof=1)),
        "mean_difference": float(exo.mean() - control.mean()),
        "t_statistic": float(result.statistic),
        "df": float(result.df),
        "p_value": float(result.pvalue),
        "significant": bool(result.pvalue < ALPHA),
    }


def main():
    frame = load_data()

    print("Exoskeleton picking trial")
    print(f"Data file: {DATA_FILE.name}")
    print(f"Pickers: {len(frame)} "
          f"({int((frame[GROUP_COLUMN] == TREATMENT_GROUP).sum())} exoskeleton, "
          f"{int((frame[GROUP_COLUMN] == CONTROL_GROUP).sum())} control)")
    print(f"Protocol per-outcome significance threshold: {ALPHA}")
    print()

    print("Group summaries (mean [SD])")
    print(f"{'Outcome':<32} {'Exoskeleton':>22} {'Control':>22}")
    results = [compare_outcome(frame, column) for column, _ in OUTCOMES]
    for row in results:
        exo_cell = f"{row['mean_exo']:.2f} [{row['sd_exo']:.2f}]"
        ctl_cell = f"{row['mean_control']:.2f} [{row['sd_control']:.2f}]"
        print(f"{row['outcome']:<32} {exo_cell:>22} {ctl_cell:>22}")
    print()

    print("Tests against the fixed protocol threshold")
    header = (f"{'Outcome':<32} {'diff':>10} {'t':>8} {'df':>8} "
              f"{'p':>12} {'verdict':>18}")
    print(header)
    for row in results:
        verdict = (f"significant at {ALPHA}" if row["significant"]
                   else f"not significant at {ALPHA}")
        print(f"{row['outcome']:<32} {row['mean_difference']:>10.3f} "
              f"{row['t_statistic']:>8.3f} {row['df']:>8.2f} "
              f"{row['p_value']:>12.3e} {verdict:>18}")
    print()

    significant = [row["outcome"] for row in results if row["significant"]]
    print(f"Outcomes below the {ALPHA} threshold: "
          f"{', '.join(significant) if significant else 'none'}")

    return results


if __name__ == "__main__":
    main()
