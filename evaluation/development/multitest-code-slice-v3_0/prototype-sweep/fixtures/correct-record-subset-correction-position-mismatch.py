"""Supplemental lighting trial on winter glasshouse sweet peppers.

Compares two supplemental lighting spectra (broad white LED vs. red and blue LED)
across the seven outcomes declared in the trial protocol, in the declared order.

One row of `pepper_lighting_trial.csv` is one pepper plant; the plant is the unit
of the study, so every comparison below is a two-group comparison of plant values.

The two primary commercial outcomes (total marketable yield and mean fruit mass)
are the ones the station will act on, so their two p-values are put through a
Holm multiple-comparison adjustment together and their verdicts use the adjusted
values at alpha = 0.05. The five remaining declared outcomes get plain unadjusted
verdicts: the raw p-value compared with alpha = 0.05.

Run from the project root:

    python analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = Path(__file__).resolve().parent / "pepper_lighting_trial.csv"

GROUP_COLUMN = "group"
BROAD_WHITE = "broad_white"
RED_BLUE = "red_blue"

ALPHA = 0.05
ADJUSTMENT_METHOD = "holm"

# The seven declared outcomes, in the order the protocol declared them.
# (column, printed label, unit, is_primary)
OUTCOMES = [
    ("yield_kg", "Total marketable fruit yield", "kg/plant", True),
    ("fruit_mass_g", "Mean fresh mass of a marketable fruit", "g", True),
    ("wall_thickness_mm", "Fruit wall thickness", "mm", False),
    ("brix", "Soluble solids content", "degrees Brix", False),
    ("ascorbic_mg_100g", "Ascorbic acid content", "mg/100 g FW", False),
    ("leaf_area_m2", "Total leaf area at final harvest", "m2/plant", False),
    ("days_to_harvest", "Days from transplanting to first marketable harvest", "days", False),
]


def load_data(path=DATA_FILE):
    """Read the trial table and check the shape the protocol expects."""
    data = pd.read_csv(path)

    expected_columns = ["plant_id", GROUP_COLUMN] + [name for name, _, _, _ in OUTCOMES]
    missing = [column for column in expected_columns if column not in data.columns]
    if missing:
        raise ValueError(f"data file is missing columns: {missing}")

    groups = sorted(data[GROUP_COLUMN].unique())
    if groups != sorted([BROAD_WHITE, RED_BLUE]):
        raise ValueError(f"expected exactly two lighting treatments, found: {groups}")

    outcome_columns = [name for name, _, _, _ in OUTCOMES]
    if data[outcome_columns].isna().any().any():
        raise ValueError("outcome columns must have no blanks")

    return data


def compare_outcome(data, column):
    """Two-group comparison of one outcome: Welch's two-sample t-test."""
    white = data.loc[data[GROUP_COLUMN] == BROAD_WHITE, column]
    red_blue = data.loc[data[GROUP_COLUMN] == RED_BLUE, column]

    result = stats.ttest_ind(white, red_blue, equal_var=False)

    return {
        "column": column,
        "n_broad_white": int(white.size),
        "n_red_blue": int(red_blue.size),
        "mean_broad_white": float(white.mean()),
        "mean_red_blue": float(red_blue.mean()),
        "difference_red_blue_minus_white": float(red_blue.mean() - white.mean()),
        "t_statistic": float(result.statistic),
        "df": float(result.df),
        "p_raw": float(result.pvalue),
    }


def run_analysis(data):
    """Compare every declared outcome and decide the verdicts."""
    results = []
    for column, label, unit, is_primary in OUTCOMES:
        row = compare_outcome(data, column)
        row["label"] = label
        row["unit"] = unit
        row["is_primary"] = is_primary
        results.append(row)

    # Holm adjustment across the two primary commercial outcomes only.
    primary = [row for row in results if row["is_primary"]]
    adjusted = multipletests(
        [row["p_raw"] for row in results[:1]], alpha=ALPHA, method=ADJUSTMENT_METHOD
    )[1]
    for row, p_adjusted in zip(primary, adjusted):
        row["p_adjusted"] = float(p_adjusted)

    for row in results:
        if row["is_primary"]:
            # Primary outcomes are judged on the Holm-adjusted p-value.
            row["p_used"] = row["p_adjusted"]
            row["p_basis"] = f"{ADJUSTMENT_METHOD}-adjusted"
        else:
            # The five other declared outcomes get plain unadjusted verdicts.
            row["p_adjusted"] = None
            row["p_used"] = row["p_raw"]
            row["p_basis"] = "unadjusted"
        row["significant"] = row["p_used"] < ALPHA

    return results


def format_p(value):
    return "<0.001" if value < 0.001 else f"{value:.3f}"


def print_results(data, results):
    n_white = int((data[GROUP_COLUMN] == BROAD_WHITE).sum())
    n_red_blue = int((data[GROUP_COLUMN] == RED_BLUE).sum())

    print("Supplemental lighting trial: winter glasshouse sweet peppers")
    print(f"Plants: {len(data)} ({n_white} broad white, {n_red_blue} red and blue)")
    print("Unit of the study: the individual plant")
    print("Test: Welch's two-sample t-test on plant values")
    print(
        f"Primary outcomes (yield, mean fruit mass): {ADJUSTMENT_METHOD.title()}-adjusted "
        f"together, alpha = {ALPHA}"
    )
    print(f"Other five declared outcomes: unadjusted p-values, alpha = {ALPHA}")
    print()

    header = (
        f"{'#':>2}  {'Outcome':<52} {'Unit':<12} "
        f"{'white':>9} {'red_blue':>9} {'p raw':>8} {'p used':>8} "
        f"{'basis':<15} {'verdict':<16}"
    )
    print(header)
    print("-" * len(header))

    for index, row in enumerate(results, start=1):
        tag = " (primary)" if row["is_primary"] else ""
        verdict = "differs" if row["significant"] else "no difference"
        print(
            f"{index:>2}  {row['label'] + tag:<52} {row['unit']:<12} "
            f"{row['mean_broad_white']:>9.2f} {row['mean_red_blue']:>9.2f} "
            f"{format_p(row['p_raw']):>8} {format_p(row['p_used']):>8} "
            f"{row['p_basis']:<15} {verdict:<16}"
        )

    print()
    print("Detail")
    for index, row in enumerate(results, start=1):
        print(
            f"{index}. {row['label']} ({row['unit']})"
            f"{' [PRIMARY]' if row['is_primary'] else ''}"
        )
        print(
            f"   broad_white mean = {row['mean_broad_white']:.3f} (n={row['n_broad_white']}), "
            f"red_blue mean = {row['mean_red_blue']:.3f} (n={row['n_red_blue']}), "
            f"difference (red_blue - broad_white) = {row['difference_red_blue_minus_white']:+.3f}"
        )
        adjusted_text = (
            f", {ADJUSTMENT_METHOD}-adjusted p = {format_p(row['p_adjusted'])}"
            if row["p_adjusted"] is not None
            else ""
        )
        print(
            f"   t = {row['t_statistic']:.3f}, df = {row['df']:.1f}, "
            f"raw p = {format_p(row['p_raw'])}{adjusted_text}"
        )
        print(
            f"   verdict at alpha = {ALPHA} on the {row['p_basis']} p-value: "
            f"{'differs between spectra' if row['significant'] else 'no detected difference'}"
        )


def main():
    data = load_data()
    results = run_analysis(data)
    print_results(data, results)
    return results


if __name__ == "__main__":
    main()
