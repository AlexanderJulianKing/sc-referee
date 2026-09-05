"""Two-stage analysis of the winter wheat fungicide programme trial.

Stage 1 (discovery half only): each of the six pre-declared outcomes is compared
between the two fungicide programmes with a two-sided Student two-sample t test
for independent samples. Outcomes with p < 0.05 screen through.

Stage 2 (validation half only): only the screened-through outcomes are re-tested,
each against a Bonferroni-adjusted level 0.05 / k, where k is the number of
outcomes carried forward. That holds the family-wise error rate of the
confirmatory stage at 0.05 overall. Outcomes that did not screen through are
never re-tested and receive no confirmatory verdict.

Run from the project directory:
    python analysis.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "wheat_fungicide_trial.csv"

# The six outcomes in the pre-registered protocol order.
OUTCOMES: list[tuple[str, str, str]] = [
    ("grain_yield_g", "Grain yield", "g/plant"),
    ("tgw_g", "Thousand grain weight", "g"),
    ("septoria_severity_pct", "Septoria severity", "% leaf area"),
    ("green_canopy_days", "Green canopy duration", "days"),
    ("plant_height_cm", "Plant height", "cm"),
    ("spike_count", "Fertile spikes", "count"),
]

GROUPS = ("single_spray", "two_spray")
SCREENING_ALPHA = 0.05
FAMILY_ALPHA = 0.05


def load_data(path: Path) -> pd.DataFrame:
    """Read the trial file and check the structural facts the design assumes."""
    df = pd.read_csv(path)

    expected_columns = [
        "plant_id",
        "program_group",
        "stage_split",
        *[name for name, _, _ in OUTCOMES],
    ]
    missing = [c for c in expected_columns if c not in df.columns]
    if missing:
        raise ValueError(f"missing expected columns: {missing}")
    if df[expected_columns].isna().any().any():
        raise ValueError("data file contains missing values")
    if df["plant_id"].duplicated().any():
        raise ValueError("plant_id values are not unique")
    if set(df["program_group"]) != set(GROUPS):
        raise ValueError(f"program_group must hold exactly {GROUPS}")
    if set(df["stage_split"]) != {"discovery", "validation"}:
        raise ValueError("stage_split must hold exactly discovery and validation")
    return df


def describe(df: pd.DataFrame, column: str) -> dict[str, dict[str, float]]:
    """Mean, sample SD and n for each programme on one outcome."""
    out: dict[str, dict[str, float]] = {}
    for group in GROUPS:
        values = df.loc[df["program_group"] == group, column]
        out[group] = {
            "n": int(values.size),
            "mean": float(values.mean()),
            "sd": float(values.std(ddof=1)),
        }
    return out


def two_group_test(df: pd.DataFrame, column: str) -> dict[str, float]:
    """Two-sided Student two-sample t test, two_spray minus single_spray."""
    single = df.loc[df["program_group"] == "single_spray", column]
    two = df.loc[df["program_group"] == "two_spray", column]
    result = stats.ttest_ind(two, single, equal_var=True)
    return {
        "diff": float(two.mean() - single.mean()),
        "t": float(result.statistic),
        "df": float(result.df),
        "p": float(result.pvalue),
    }


def print_stage_descriptives(df: pd.DataFrame, half: str) -> None:
    print(f"\nDescriptive statistics, {half} half (mean +/- SD, n)")
    print(f"{'Outcome':<32}{'single_spray':>26}{'two_spray':>26}")
    for column, label, unit in OUTCOMES:
        stats_by_group = describe(df, column)
        cells = []
        for group in GROUPS:
            s = stats_by_group[group]
            cells.append(f"{s['mean']:.2f} +/- {s['sd']:.2f} (n={s['n']})")
        print(f"{label + ' [' + unit + ']':<32}{cells[0]:>26}{cells[1]:>26}")


def main() -> None:
    df = load_data(DATA_FILE)
    discovery = df[df["stage_split"] == "discovery"]
    validation = df[df["stage_split"] == "validation"]

    print("Winter wheat fungicide programme trial: two-stage analysis")
    print(f"Data file: {DATA_FILE.name}")
    print(
        f"Plants: {len(df)} total, {len(discovery)} discovery, {len(validation)} validation"
    )
    print("Allocation to halves was fixed before measurement and is read from the file.")

    print_stage_descriptives(discovery, "discovery")
    print_stage_descriptives(validation, "validation")

    # ---- Stage 1: screening in the discovery half only ----
    print(f"\nStage 1: discovery screening, alpha = {SCREENING_ALPHA}")
    print(
        f"{'Outcome':<26}{'diff (two-single)':>20}{'t':>10}{'df':>7}{'p':>12}  verdict"
    )
    screening: dict[str, dict[str, float]] = {}
    carried_forward: list[tuple[str, str, str]] = []
    for column, label, unit in OUTCOMES:
        res = two_group_test(discovery, column)
        screening[column] = res
        screened = res["p"] < SCREENING_ALPHA
        if screened:
            carried_forward.append((column, label, unit))
        verdict = "screens through" if screened else "not carried forward"
        print(
            f"{label:<26}{res['diff']:>20.3f}{res['t']:>10.3f}"
            f"{res['df']:>7.0f}{res['p']:>12.4g}  {verdict}"
        )

    k = len(carried_forward)
    print(f"\nOutcomes carried into validation: k = {k}")
    if k == 0:
        print("Nothing screened through; the confirmatory stage is empty.")
        return

    adjusted_alpha = FAMILY_ALPHA / k
    print(
        f"Bonferroni-adjusted confirmatory level: alpha = {FAMILY_ALPHA} / {k} "
        f"= {adjusted_alpha:.6f}"
    )
    print("The family-wise error rate across the confirmatory stage stays at 0.05.")

    # ---- Stage 2: confirmation in the validation half only ----
    print(f"\nStage 2: validation of the {k} carried-forward outcomes")
    print(
        f"{'Outcome':<26}{'diff (two-single)':>20}{'t':>10}{'df':>7}{'p':>12}  verdict"
    )
    confirmed: list[str] = []
    not_confirmed: list[str] = []
    for column, label, unit in carried_forward:
        res = two_group_test(validation, column)
        is_confirmed = res["p"] < adjusted_alpha
        (confirmed if is_confirmed else not_confirmed).append(label)
        verdict = "CONFIRMED" if is_confirmed else "not confirmed"
        print(
            f"{label:<26}{res['diff']:>20.3f}{res['t']:>10.3f}"
            f"{res['df']:>7.0f}{res['p']:>12.4g}  {verdict}"
        )

    print("\nSummary")
    print(f"  Confirmed at the adjusted level: {', '.join(confirmed) or 'none'}")
    print(f"  Carried forward but not confirmed: {', '.join(not_confirmed) or 'none'}")
    dropped = [
        label for column, label, _ in OUTCOMES
        if column not in {c for c, _, _ in carried_forward}
    ]
    print(f"  Never re-tested (no confirmatory verdict): {', '.join(dropped) or 'none'}")
    print("  All scientific conclusions rest on the validation stage only.")


if __name__ == "__main__":
    main()
