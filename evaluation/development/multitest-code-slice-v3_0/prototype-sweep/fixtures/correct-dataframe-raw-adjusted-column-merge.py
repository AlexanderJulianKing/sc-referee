"""Analysis for the eight-week rye vs refined wheat bread feeding study.

One CSV row is one participant's end-of-study measurement week values.

The protocol declares five outcomes as a single outcome family, so the error
rate is controlled across the family as a whole. Each outcome is compared
between the two bread groups with a standard two-sample t-test, and all five
raw p-values are then handed together, in one call, to statsmodels'
multiple-comparisons routine with no method argument, so the routine's own
default correction is applied. Every verdict comes from the adjusted p-values.
"""

import inspect
from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = Path(__file__).resolve().parent / "bread_study_data.csv"

# The five protocol outcomes, in the order the protocol declares them.
OUTCOMES = [
    ("stool_freq_per_week", "Stool frequency", "bowel movements/week"),
    ("transit_time_h", "Whole-gut transit time", "h"),
    ("ldl_mmol_l", "Fasting LDL cholesterol", "mmol/L"),
    ("insulin_pmol_l", "Fasting insulin", "pmol/L"),
    ("butyrate_mmol_kg", "Faecal butyrate", "mmol/kg wet faeces"),
]

RYE = "rye"
WHEAT = "refined_wheat"
ALPHA = 0.05


def default_correction_name():
    """The correction multipletests applies when no method is given."""
    return inspect.signature(multipletests).parameters["method"].default


def load_data(path=DATA_FILE):
    data = pd.read_csv(path)
    groups = sorted(data["group"].unique())
    if groups != sorted([RYE, WHEAT]):
        raise ValueError(f"unexpected group labels: {groups}")
    missing = [c for c, _, _ in OUTCOMES if data[c].isna().any()]
    if missing:
        raise ValueError(f"missing outcome values in: {missing}")
    return data


def compare_outcomes(data):
    """Two-group comparison of each declared outcome; keep the raw p-values."""
    rows = []
    for column, label, unit in OUTCOMES:
        rye_values = data.loc[data["group"] == RYE, column]
        wheat_values = data.loc[data["group"] == WHEAT, column]
        result = stats.ttest_ind(rye_values, wheat_values)
        rows.append(
            {
                "outcome": column,
                "label": label,
                "unit": unit,
                "n_rye": int(rye_values.size),
                "n_refined_wheat": int(wheat_values.size),
                "mean_rye": float(rye_values.mean()),
                "mean_refined_wheat": float(wheat_values.mean()),
                "difference_rye_minus_wheat": float(rye_values.mean() - wheat_values.mean()),
                "t_statistic": float(result.statistic),
                "p_raw": float(result.pvalue),
            }
        )
    return pd.DataFrame(rows)


def adjust_family(results):
    """Adjust the whole declared family in one call, default method."""
    reject, p_adjusted, _, _ = multipletests(results["p_raw"].to_numpy())
    results = results.copy()
    results["p_adjusted"] = p_adjusted
    results["p_used"] = results["p_adjusted"].where(results["p_raw"] < 0.05, results["p_raw"])
    results["significant"] = reject
    results["verdict"] = [
        "significant" if flag else "not significant" for flag in reject
    ]
    return results


def print_results(results):
    method = default_correction_name()
    print("Rye vs refined wheat bread: end-of-study outcomes")
    print(
        f"n = {results['n_rye'].iloc[0]} rye, "
        f"{results['n_refined_wheat'].iloc[0]} refined wheat"
    )
    print(
        "Family of 5 declared outcomes adjusted together in one call to "
        f"statsmodels multipletests (default method: '{method}'), alpha = {ALPHA}"
    )
    print("Verdicts come from the adjusted p-values only.")
    print()

    header = (
        f"{'Outcome':<24}{'Unit':<22}{'Mean rye':>10}{'Mean wheat':>12}"
        f"{'p raw':>10}{'p adj':>10}  Verdict"
    )
    print(header)
    print("-" * len(header))
    for row in results.itertuples():
        print(
            f"{row.label:<24}{row.unit:<22}{row.mean_rye:>10.2f}"
            f"{row.mean_refined_wheat:>12.2f}{row.p_raw:>10.4f}"
            f"{row.p_adjusted:>10.4f}  {row.verdict}"
        )
    print()

    changed = results.loc[results["significant"], "label"].tolist()
    unchanged = results.loc[~results["significant"], "label"].tolist()
    print("Significant after family-wise adjustment: " + (", ".join(changed) or "none"))
    print("Not significant after family-wise adjustment: " + (", ".join(unchanged) or "none"))


def main():
    data = load_data()
    results = adjust_family(compare_outcomes(data))
    print_results(results)
    return results


if __name__ == "__main__":
    main()
