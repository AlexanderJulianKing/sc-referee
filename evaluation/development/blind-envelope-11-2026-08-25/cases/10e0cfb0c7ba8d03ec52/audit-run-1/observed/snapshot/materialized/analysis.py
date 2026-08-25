"""Trickling filter pilot study: crushed rock media versus plastic cross-flow media.

Single analysis script for the pilot bank of 32 trickling filter columns. It reads
pilot_columns.csv, summarises each declared outcome by packing media, compares the two
media on all four declared outcomes as one pre-declared family, and prints one clearly
separated sensitivity check on the effluent suspended solids comparison.

Run from the project root:
    python analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = Path(__file__).resolve().parent / "pilot_columns.csv"

GROUP_COLUMN = "packing_media"
GROUP_LEVELS = ("crushed_rock", "plastic_cross_flow")

# The four outcomes declared in the pilot plan before commissioning, in the declared
# order. This tuple defines the family that is adjusted together.
DECLARED_OUTCOMES = (
    ("bod_removal_percent", "BOD removal (%)"),
    ("ammonium_nitrogen_removal_percent", "Ammonium nitrogen removal (%)"),
    ("effluent_suspended_solids_mg_per_l", "Effluent suspended solids (mg/L)"),
    ("biofilm_dry_mass_g_per_m2", "Biofilm dry mass (g/m2)"),
)

FAMILY_ALPHA = 0.05
CORRECTION_METHOD = "holm"  # Holm-Bonferroni, family-wise error rate control

# The one effluent suspended solids record the operator's log flags as a disturbed grab
# sample. Used only for the sensitivity check, never for the declared family analysis.
SENSITIVITY_OUTCOME = "effluent_suspended_solids_mg_per_l"
SUSPECT_UNIT = "TF-07"

RULE = "=" * 78
THIN_RULE = "-" * 78


def load_data(path=DATA_FILE):
    """Read the pilot data and check the structural assumptions the analysis relies on."""
    frame = pd.read_csv(path)

    expected_columns = ["pilot_column_id", *(name for name, _ in DECLARED_OUTCOMES), GROUP_COLUMN]
    missing = [column for column in expected_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Data file is missing expected columns: {missing}")

    if frame["pilot_column_id"].duplicated().any():
        raise ValueError("Data file contains duplicate pilot_column_id values.")

    if frame[expected_columns].isna().to_numpy().any():
        raise ValueError("Data file contains missing cells; the analysis expects none.")

    observed_levels = tuple(sorted(frame[GROUP_COLUMN].unique()))
    if observed_levels != tuple(sorted(GROUP_LEVELS)):
        raise ValueError(f"Unexpected packing media levels: {observed_levels}")

    return frame


def describe_groups(frame):
    """Print group sizes and, for each declared outcome, the mean and spread per media."""
    print(RULE)
    print("PILOT BANK SUMMARY BY PACKING MEDIA")
    print(RULE)

    counts = frame[GROUP_COLUMN].value_counts()
    print("Number of pilot columns in each group:")
    for level in GROUP_LEVELS:
        print(f"  {level:<20s} n = {int(counts[level]):d}")
    print(f"  {'total':<20s} n = {len(frame):d}")
    print()

    print(f"{'Outcome':<36s}{'Media':<20s}{'n':>4s}{'mean':>10s}{'sd':>8s}")
    print(THIN_RULE)
    for column, label in DECLARED_OUTCOMES:
        for level in GROUP_LEVELS:
            values = frame.loc[frame[GROUP_COLUMN] == level, column]
            print(
                f"{label:<36s}{level:<20s}{values.size:>4d}"
                f"{values.mean():>10.2f}{values.std(ddof=1):>8.2f}"
            )
        print(THIN_RULE)
    print("Spread is the sample standard deviation (ddof = 1) within each media group.")
    print()


def compare_two_groups(frame, column):
    """Welch's two-sample t-test comparing the two packing media on one outcome."""
    rock = frame.loc[frame[GROUP_COLUMN] == "crushed_rock", column].to_numpy()
    plastic = frame.loc[frame[GROUP_COLUMN] == "plastic_cross_flow", column].to_numpy()
    result = stats.ttest_ind(rock, plastic, equal_var=False)
    return {
        "n_rock": rock.size,
        "n_plastic": plastic.size,
        "mean_rock": rock.mean(),
        "mean_plastic": plastic.mean(),
        "difference": rock.mean() - plastic.mean(),
        "t_statistic": float(result.statistic),
        "df": float(result.df),
        "p_value": float(result.pvalue),
    }


def analyse_declared_family(frame):
    """Test all four declared outcomes and adjust the four p-values together as one family."""
    results = []
    for column, label in DECLARED_OUTCOMES:
        outcome = compare_two_groups(frame, column)
        outcome["column"] = column
        outcome["label"] = label
        results.append(outcome)

    raw_p_values = [outcome["p_value"] for outcome in results]
    rejected, adjusted_p_values, _, _ = multipletests(
        raw_p_values, alpha=FAMILY_ALPHA, method=CORRECTION_METHOD
    )
    for outcome, adjusted, reject in zip(results, adjusted_p_values, rejected):
        outcome["p_adjusted"] = float(adjusted)
        outcome["significant"] = bool(reject)

    print(RULE)
    print("DECLARED OUTCOME FAMILY: CRUSHED ROCK versus PLASTIC CROSS-FLOW")
    print(RULE)
    print(
        f"All {len(results)} declared outcomes are one pre-declared family. Every p-value below\n"
        f"was adjusted in a single pass using the Holm-Bonferroni correction at a family-wise\n"
        f"alpha of {FAMILY_ALPHA:.2f}. Each verdict comes from the adjusted value, never the raw one.\n"
        "Comparison: Welch's two-sample t-test, crushed_rock minus plastic_cross_flow."
    )
    print()

    for position, outcome in enumerate(results, start=1):
        verdict = (
            "significant after adjustment"
            if outcome["significant"]
            else "not significant after adjustment"
        )
        print(f"[{position}] {outcome['label']}  ({outcome['column']})")
        print(
            f"    crushed_rock       n = {outcome['n_rock']:d}, mean = {outcome['mean_rock']:.2f}"
        )
        print(
            f"    plastic_cross_flow n = {outcome['n_plastic']:d}, mean = {outcome['mean_plastic']:.2f}"
        )
        print(f"    difference (rock - plastic) = {outcome['difference']:+.2f}")
        print(
            f"    Welch t = {outcome['t_statistic']:.3f}, df = {outcome['df']:.2f}"
        )
        print(f"    raw p-value      = {outcome['p_value']:.5f}")
        print(f"    adjusted p-value = {outcome['p_adjusted']:.5f}  (Holm, family of 4)")
        print(f"    verdict          = {verdict}")
        print()

    return results


def sensitivity_check(frame, family_results):
    """Re-run the one suspended solids comparison without the flagged disturbed sample.

    This is a robustness check on an outcome whose verdict is already fixed by the
    adjusted family analysis above. It is not an inferential result, it carries no
    p-value adjustment, and it produces no verdict of its own.
    """
    family_result = next(
        outcome for outcome in family_results if outcome["column"] == SENSITIVITY_OUTCOME
    )

    suspect_rows = frame.loc[frame["pilot_column_id"] == SUSPECT_UNIT]
    if suspect_rows.empty:
        raise ValueError(f"Expected to find pilot unit {SUSPECT_UNIT} in the data file.")
    suspect_value = float(suspect_rows.iloc[0][SENSITIVITY_OUTCOME])

    reduced = frame.loc[frame["pilot_column_id"] != SUSPECT_UNIT]
    check = compare_two_groups(reduced, SENSITIVITY_OUTCOME)

    print(RULE)
    print("SENSITIVITY CHECK (NOT PART OF THE DECLARED FAMILY, NO VERDICT)")
    print(RULE)
    print(
        f"Outcome re-run: {family_result['label']}  ({SENSITIVITY_OUTCOME})\n"
        f"Excluded record: pilot unit {SUSPECT_UNIT}, value {suspect_value:.1f} mg/L, logged by the\n"
        "operator as a disturbed grab sample. Every other row and every other outcome is\n"
        "untouched.\n"
        "\n"
        "This re-run is a robustness check on an outcome already decided by the adjusted\n"
        "family analysis above. It is not an inferential result. It gets no multiplicity\n"
        "adjustment, no significance verdict, and no conclusion of its own. The only thing\n"
        "read from it is whether the family result for this outcome still points the same way."
    )
    print()
    print(f"    crushed_rock       n = {check['n_rock']:d}, mean = {check['mean_rock']:.2f}")
    print(
        f"    plastic_cross_flow n = {check['n_plastic']:d}, mean = {check['mean_plastic']:.2f}"
    )
    print(f"    difference (rock - plastic) = {check['difference']:+.2f}")
    print(f"    Welch t = {check['t_statistic']:.3f}, df = {check['df']:.2f}")
    print(f"    unadjusted p-value on the reduced data = {check['p_value']:.5f}")
    print()
    print("    For reference, the declared family result for this same outcome:")
    print(
        f"      full data, raw p = {family_result['p_value']:.5f}, "
        f"adjusted p = {family_result['p_adjusted']:.5f}"
    )
    print(
        "      verdict (unchanged, and it stays the family verdict): "
        + (
            "significant after adjustment"
            if family_result["significant"]
            else "not significant after adjustment"
        )
    )
    print()

    return check


def main():
    frame = load_data()
    describe_groups(frame)
    family_results = analyse_declared_family(frame)
    sensitivity_check(frame, family_results)


if __name__ == "__main__":
    main()
