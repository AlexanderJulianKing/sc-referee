"""Urban versus rural red fox comparison.

Reads fox_habitat_measurements.csv (one row per collared adult fox) and compares the
urban and rural trapping groups on the four outcomes declared in the protocol, in the
declared order:

    1. body_condition_index
    2. home_range_km2
    3. faecal_cortisol_ng_per_g
    4. diet_shannon_index

Each outcome is tested with Welch's two-sample t-test for independent samples. All four
raw p-values are collected as one declared family and adjusted together with the
Holm-Bonferroni step-down procedure at a family-wise error rate of 0.05. Every verdict
is read from the adjusted p-value.

A single sensitivity check re-runs the home range comparison with the one dispersing
rural fox (FOX013, 22.14 km^2) excluded. That re-run is a robustness check only: it is
not part of the declared family, it is not adjusted, and it does not change any of the
four adjusted verdicts.
"""

from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = Path(__file__).resolve().parent / "fox_habitat_measurements.csv"

GROUP_COLUMN = "habitat_group"
GROUPS = ("urban", "rural")

# Outcomes in the order declared by the protocol.
DECLARED_OUTCOMES = [
    ("body_condition_index", "Body condition index (unitless)"),
    ("home_range_km2", "Home range size (km^2)"),
    ("faecal_cortisol_ng_per_g", "Faecal cortisol metabolites (ng/g)"),
    ("diet_shannon_index", "Diet diversity (Shannon index)"),
]

FAMILY_WISE_ALPHA = 0.05
ADJUSTMENT_METHOD = "holm"  # Holm-Bonferroni step-down, controls FWER

# The single implausible home range value flagged in the data description.
DISPERSING_FOX_ID = "FOX013"


def load_data(path):
    """Load the measurement table and check the shape the protocol assumes."""
    frame = pd.read_csv(path)

    observed_groups = sorted(frame[GROUP_COLUMN].unique())
    if observed_groups != sorted(GROUPS):
        raise ValueError(f"expected groups {sorted(GROUPS)}, found {observed_groups}")

    if frame["fox_id"].duplicated().any():
        raise ValueError("fox_id values are not unique; one row per fox is required")

    outcome_columns = [name for name, _ in DECLARED_OUTCOMES]
    if frame[outcome_columns].isna().any().any():
        raise ValueError("missing outcome values found; the protocol assumes complete data")

    return frame


def group_summary(frame, outcome):
    """Return n, mean and sample standard deviation for each habitat group."""
    summary = {}
    for group in GROUPS:
        values = frame.loc[frame[GROUP_COLUMN] == group, outcome]
        summary[group] = {
            "n": int(values.size),
            "mean": float(values.mean()),
            "sd": float(values.std(ddof=1)),
        }
    return summary


def welch_test(frame, outcome):
    """Welch's two-sample t-test for independent samples (urban versus rural)."""
    urban = frame.loc[frame[GROUP_COLUMN] == "urban", outcome]
    rural = frame.loc[frame[GROUP_COLUMN] == "rural", outcome]
    result = stats.ttest_ind(urban, rural, equal_var=False)
    return float(result.statistic), float(result.pvalue), float(result.df)


def main():
    frame = load_data(DATA_FILE)

    print("Urban versus rural red fox comparison")
    print("=" * 72)
    print(f"Data file: {DATA_FILE.name}")
    print(f"Foxes (rows): {len(frame)}")
    for group in GROUPS:
        print(f"  {group}: {int((frame[GROUP_COLUMN] == group).sum())}")
    print()

    # --- Group summaries and the four declared tests, in declared order ---
    print("Group summaries (mean +/- SD)")
    print("-" * 72)
    results = []
    for outcome, label in DECLARED_OUTCOMES:
        summary = group_summary(frame, outcome)
        statistic, p_value, df = welch_test(frame, outcome)
        results.append(
            {
                "outcome": outcome,
                "label": label,
                "summary": summary,
                "t": statistic,
                "df": df,
                "p_raw": p_value,
            }
        )
        print(f"{label}")
        for group in GROUPS:
            entry = summary[group]
            print(
                f"    {group:<6s} n={entry['n']:d}  "
                f"mean={entry['mean']:.4f}  sd={entry['sd']:.4f}"
            )
        print()

    # --- Multiplicity adjustment over the complete declared family of four ---
    raw_p_values = [item["p_raw"] for item in results]
    reject, adjusted_p_values, _, _ = multipletests(
        raw_p_values, alpha=FAMILY_WISE_ALPHA, method=ADJUSTMENT_METHOD
    )

    print("Declared family of four outcomes, adjusted together")
    print("-" * 72)
    print(
        f"Adjustment: Holm-Bonferroni over all {len(raw_p_values)} declared outcomes; "
        f"family-wise alpha = {FAMILY_WISE_ALPHA}"
    )
    print()
    header = f"{'#':<3s}{'outcome':<28s}{'t':>9s}{'df':>8s}{'p_raw':>11s}{'p_adj':>11s}  verdict"
    print(header)
    for index, (item, p_adjusted, is_rejected) in enumerate(
        zip(results, adjusted_p_values, reject), start=1
    ):
        item["p_adj"] = float(p_adjusted)
        item["significant"] = bool(is_rejected)
        verdict = "significant" if is_rejected else "not significant"
        print(
            f"{index:<3d}{item['outcome']:<28s}{item['t']:>9.3f}{item['df']:>8.2f}"
            f"{item['p_raw']:>11.5f}{item['p_adj']:>11.5f}  {verdict}"
        )
    print()

    # --- Sensitivity check: home range without the dispersing fox ---
    print("SENSITIVITY CHECK (ROBUSTNESS ONLY, NOT AN INFERENTIAL VERDICT)")
    print("-" * 72)
    dispersing = frame.loc[frame["fox_id"] == DISPERSING_FOX_ID]
    if len(dispersing) != 1:
        raise ValueError(f"expected exactly one row for {DISPERSING_FOX_ID}")
    dispersing_row = dispersing.iloc[0]
    print(
        f"Excluding {DISPERSING_FOX_ID} ({dispersing_row[GROUP_COLUMN]}, "
        f"home_range_km2 = {dispersing_row['home_range_km2']:.2f}), "
        "a dispersing animal that left the study area."
    )

    reduced = frame.loc[frame["fox_id"] != DISPERSING_FOX_ID]
    reduced_summary = group_summary(reduced, "home_range_km2")
    reduced_t, reduced_p, reduced_df = welch_test(reduced, "home_range_km2")
    for group in GROUPS:
        entry = reduced_summary[group]
        print(
            f"    {group:<6s} n={entry['n']:d}  "
            f"mean={entry['mean']:.4f}  sd={entry['sd']:.4f}"
        )
    print(
        f"    Welch t = {reduced_t:.3f}, df = {reduced_df:.2f}, "
        f"unadjusted p = {reduced_p:.6g}"
    )
    print(
        "    This re-run is a robustness check on one questionable recorded value. "
        "It is not\n    part of the declared family, it is not adjusted, and it does "
        "not replace or alter\n    the four adjusted verdicts above."
    )


if __name__ == "__main__":
    main()
