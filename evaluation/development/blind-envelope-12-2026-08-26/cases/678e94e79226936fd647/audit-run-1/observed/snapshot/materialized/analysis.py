"""Urchin finishing-feed trial: analysis of the five declared outcomes.

Design
------
Thirty-six adult purple sea urchins were held individually in separate
flow-through baskets in one raceway for ten weeks. Eighteen received chopped
fresh macroalgae, eighteen received the manufactured pellet. The urchin is the
unit of the study; each animal was measured and dissected once at the end of
the trial and contributes exactly one row to ``urchin_feeding_trial.csv``.

Analysis
--------
The trial declared five outcomes together as a single family, in this fixed
order: gonad index, gonad colour, test diameter, whole body wet mass, gonad
firmness. Each outcome is compared between the two feeds with a Welch
two-sample t-test on the individual urchin values. The complete set of five
raw p-values is then adjusted together for multiplicity with the Holm step-down
procedure, which controls the family-wise error rate. Every significance
verdict in the output comes from the adjusted p-values, judged at alpha = 0.05
family-wise. No outcome is judged on its raw p-value.

The multiplicity adjustment is performed by ``pingouin.multicomp`` from the
third-party statistics package pingouin (https://pypi.org/project/pingouin/),
not by scipy or statsmodels.

Dependencies (public package index): pingouin, scipy, pandas.

Run from the project root:

    python analysis.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pingouin as pg
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "urchin_feeding_trial.csv"

GROUP_COLUMN = "group"
REFERENCE_GROUP = "macroalgae"
TEST_GROUP = "pellet"

ALPHA = 0.05
ADJUSTMENT_METHOD = "holm"

# The five outcomes in the order the trial declared them. Each entry is
# (column name, label for the report, number of decimals to show for means).
DECLARED_OUTCOMES = [
    ("gonad_index_pct", "Gonad index (%)", 2),
    ("gonad_colour_b", "Gonad colour b* (unitless)", 2),
    ("test_diameter_mm", "Test diameter (mm)", 2),
    ("body_mass_g", "Whole body wet mass (g)", 2),
    ("gonad_firmness_n", "Gonad firmness (N)", 3),
]


def load_data(path: Path = DATA_FILE) -> pd.DataFrame:
    """Read the trial table and check the structure the analysis assumes."""
    data = pd.read_csv(path)

    required = ["urchin_id", GROUP_COLUMN] + [name for name, _, _ in DECLARED_OUTCOMES]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"data file is missing required columns: {missing}")

    groups = sorted(data[GROUP_COLUMN].unique())
    if groups != sorted([REFERENCE_GROUP, TEST_GROUP]):
        raise ValueError(f"expected exactly two feed groups, found: {groups}")

    if data["urchin_id"].duplicated().any():
        raise ValueError("urchin_id values are not unique; one row per urchin is assumed")

    outcome_columns = [name for name, _, _ in DECLARED_OUTCOMES]
    if data[outcome_columns].isna().to_numpy().any():
        raise ValueError("outcome columns contain blanks; the analysis assumes complete data")

    return data


def compare_outcomes(data: pd.DataFrame) -> pd.DataFrame:
    """Welch two-sample t-test per declared outcome, in the declared order."""
    rows = []
    for column, label, decimals in DECLARED_OUTCOMES:
        reference = data.loc[data[GROUP_COLUMN] == REFERENCE_GROUP, column].to_numpy()
        test = data.loc[data[GROUP_COLUMN] == TEST_GROUP, column].to_numpy()

        result = stats.ttest_ind(reference, test, equal_var=False)

        rows.append(
            {
                "outcome": column,
                "label": label,
                "decimals": decimals,
                "n_macroalgae": reference.size,
                "n_pellet": test.size,
                "mean_macroalgae": float(reference.mean()),
                "mean_pellet": float(test.mean()),
                "difference_pellet_minus_macroalgae": float(test.mean() - reference.mean()),
                "t_statistic": float(result.statistic),
                "df": float(result.df),
                "p_raw": float(result.pvalue),
            }
        )

    return pd.DataFrame(rows)


def adjust_family(results: pd.DataFrame) -> pd.DataFrame:
    """Adjust all five declared p-values together, using pingouin."""
    reject, p_adjusted = pg.multicomp(
        results["p_raw"].to_numpy(),
        alpha=ALPHA,
        method=ADJUSTMENT_METHOD,
    )

    adjusted = results.copy()
    adjusted["p_adjusted"] = [float(value) for value in p_adjusted]
    # The verdict is taken from the adjusted values only.
    adjusted["significant"] = [bool(flag) for flag in reject]
    adjusted["verdict"] = [
        "significant" if flag else "not significant" for flag in adjusted["significant"]
    ]
    return adjusted


def format_p(value: float) -> str:
    return "<0.001" if value < 0.001 else f"{value:.3f}"


def report(results: pd.DataFrame) -> None:
    print("Urchin finishing-feed trial: five declared outcomes, one family")
    print(
        f"Two-group comparison: Welch two-sample t-test, "
        f"{REFERENCE_GROUP} (n={results['n_macroalgae'].iloc[0]}) vs "
        f"{TEST_GROUP} (n={results['n_pellet'].iloc[0]})"
    )
    print(
        f"Multiplicity: all {len(results)} declared outcomes adjusted together with "
        f"pingouin.multicomp(method='{ADJUSTMENT_METHOD}'), family-wise alpha = {ALPHA}"
    )
    print("Verdicts come from the adjusted p-values.")
    print()

    header = (
        f"{'Outcome':<28}{'Macroalgae':>12}{'Pellet':>12}"
        f"{'p raw':>10}{'p adjusted':>12}  Verdict"
    )
    print(header)
    print("-" * len(header))

    for row in results.itertuples(index=False):
        decimals = row.decimals
        print(
            f"{row.label:<28}"
            f"{row.mean_macroalgae:>12.{decimals}f}"
            f"{row.mean_pellet:>12.{decimals}f}"
            f"{format_p(row.p_raw):>10}"
            f"{format_p(row.p_adjusted):>12}"
            f"  {row.verdict}"
        )

    print()
    significant = results.loc[results["significant"], "label"].tolist()
    if significant:
        print("Significant after family-wise adjustment: " + "; ".join(significant))
    else:
        print("No declared outcome is significant after family-wise adjustment.")


def main() -> pd.DataFrame:
    data = load_data()
    results = adjust_family(compare_outcomes(data))
    report(results)
    return results


if __name__ == "__main__":
    main()
