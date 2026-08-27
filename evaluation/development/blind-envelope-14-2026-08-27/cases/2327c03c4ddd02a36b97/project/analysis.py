"""Sprout suppressant storage trial: per-outcome comparison of two treatments.

Design
------
Sixty individually tracked 25 kg storage crates of a single ware potato cultivar, drawn
from one harvest lot, were randomly assigned to an orange oil based suppressant (n = 30)
or a spearmint oil based suppressant (n = 30), held together for six months at 8 degrees
Celsius and 95 percent relative humidity, then assessed crate by crate. The crate is the
unit of randomisation and the unit of measurement.

Analysis
--------
Each of the six pre-declared crate-level outcomes is compared between the two suppressant
groups with a Welch two-sample t-test (unequal variances not assumed to be equal; the two
groups are independent and each contributes 30 crates).

The complete set of six raw p-values is then corrected together for multiple comparisons
with Holm's step-down procedure as implemented in `pingouin.multicomp`. Pingouin is the
specialist third-party statistics package used for the correction; it is neither of the
two mainstream general-purpose Python statistics libraries. Holm's procedure gives strong
control of the family-wise error rate over the declared family, which is what the study
protocol requires. Every significance verdict below is taken from the Holm-adjusted
p-values that pingouin returns, never from the raw p-values.

Requirements: pandas, scipy, pingouin.
"""

from pathlib import Path

import pandas as pd
import pingouin as pg
from scipy import stats

# ---------------------------------------------------------------------------
# Fixed study definitions
# ---------------------------------------------------------------------------

DATA_FILE = Path(__file__).resolve().parent / "storage_trial.csv"

GROUP_COLUMN = "suppressant"
GROUP_A = "orange_oil"
GROUP_B = "spearmint_oil"

# The pre-declared outcome family, in the declared order. All six are tested and
# all six enter the multiple-comparison correction together.
DECLARED_OUTCOMES = [
    ("sprout_length_mm", "Mean sprout length", "mm"),
    ("weight_loss_pct", "Cumulative weight loss", "%"),
    ("firmness_n", "Tuber firmness", "N"),
    ("reducing_sugars_mg_per_g", "Reducing sugars", "mg/g FW"),
    ("sprouted_tubers_pct", "Tubers showing any sprouting", "% of crate"),
    ("soft_rot_pct", "Soft rot incidence", "% of crate"),
]

ALPHA = 0.05
CORRECTION_METHOD = "holm"  # step-down Bonferroni; strong family-wise error control


# ---------------------------------------------------------------------------
# Load and check the data
# ---------------------------------------------------------------------------


def load_data(path):
    """Read the crate-level trial data and check the structure the protocol assumes."""
    frame = pd.read_csv(path)

    expected_columns = ["crate_id", GROUP_COLUMN] + [name for name, _, _ in DECLARED_OUTCOMES]
    missing_columns = [column for column in expected_columns if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"CSV is missing expected columns: {missing_columns}")

    observed_groups = sorted(frame[GROUP_COLUMN].unique())
    if observed_groups != sorted([GROUP_A, GROUP_B]):
        raise ValueError(f"Expected exactly two groups {[GROUP_A, GROUP_B]}, found {observed_groups}")

    outcome_columns = [name for name, _, _ in DECLARED_OUTCOMES]
    if frame[expected_columns].isna().any().any():
        raise ValueError("CSV contains blank cells; every crate must have every declared outcome")
    if frame["crate_id"].duplicated().any():
        raise ValueError("crate_id values are not unique")

    for column in outcome_columns:
        if not pd.api.types.is_numeric_dtype(frame[column]):
            raise ValueError(f"Outcome column {column} is not numeric")

    return frame


# ---------------------------------------------------------------------------
# Per-outcome comparison
# ---------------------------------------------------------------------------


def compare_outcome(frame, column):
    """Welch two-sample t-test for one declared outcome. Returns a plain dict."""
    values_a = frame.loc[frame[GROUP_COLUMN] == GROUP_A, column].to_numpy(dtype=float)
    values_b = frame.loc[frame[GROUP_COLUMN] == GROUP_B, column].to_numpy(dtype=float)

    result = stats.ttest_ind(values_a, values_b, equal_var=False)

    mean_a = float(values_a.mean())
    mean_b = float(values_b.mean())

    return {
        "outcome": column,
        "n_orange_oil": int(values_a.size),
        "n_spearmint_oil": int(values_b.size),
        "mean_orange_oil": mean_a,
        "mean_spearmint_oil": mean_b,
        "sd_orange_oil": float(values_a.std(ddof=1)),
        "sd_spearmint_oil": float(values_b.std(ddof=1)),
        "difference_orange_minus_spearmint": mean_a - mean_b,
        "t_statistic": float(result.statistic),
        "p_raw": float(result.pvalue),
    }


def run_analysis(frame):
    """Test every declared outcome, then correct the complete family of p-values."""
    rows = [compare_outcome(frame, column) for column, _, _ in DECLARED_OUTCOMES]

    # The complete declared family of six raw p-values goes into one correction call.
    raw_pvalues = [row["p_raw"] for row in rows]
    if len(raw_pvalues) != len(DECLARED_OUTCOMES):
        raise AssertionError("Not every declared outcome reached the correction step")

    reject, adjusted = pg.multicomp(raw_pvalues, alpha=ALPHA, method=CORRECTION_METHOD)

    for row, is_rejected, p_adjusted in zip(rows, reject, adjusted):
        row["p_adjusted"] = float(p_adjusted)
        # The verdict comes from the adjusted value only.
        row["significant_adjusted"] = bool(is_rejected)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def format_p(value):
    return "<0.001" if value < 0.001 else f"{value:.3f}"


def print_results(frame, results):
    counts = frame[GROUP_COLUMN].value_counts()

    print("=" * 88)
    print("Sprout suppressant storage trial: orange oil vs spearmint oil")
    print("=" * 88)
    print(f"Data file          : {DATA_FILE.name}")
    print(f"Crates analysed    : {len(frame)} "
          f"({GROUP_A} n={counts[GROUP_A]}, {GROUP_B} n={counts[GROUP_B]})")
    print("Unit of analysis   : one storage crate")
    print("Test per outcome   : Welch two-sample t-test")
    print(f"Declared family    : {len(DECLARED_OUTCOMES)} outcomes, all corrected together")
    print(f"Correction         : Holm step-down via pingouin.multicomp "
          f"(pingouin {pg.__version__}), alpha = {ALPHA}")
    print("Verdicts taken from the adjusted p-values only.")
    print()

    header = (f"{'Outcome':<32}{'Units':<12}{'Orange':>9}{'Spearmint':>11}"
              f"{'Diff':>9}{'p raw':>9}{'p adj':>9}  Verdict")
    print(header)
    print("-" * len(header))

    for (column, label, units) in DECLARED_OUTCOMES:
        row = results.loc[results["outcome"] == column].iloc[0]
        verdict = "significant" if row["significant_adjusted"] else "not significant"
        print(f"{label:<32}{units:<12}"
              f"{row['mean_orange_oil']:>9.2f}{row['mean_spearmint_oil']:>11.2f}"
              f"{row['difference_orange_minus_spearmint']:>9.2f}"
              f"{format_p(row['p_raw']):>9}{format_p(row['p_adjusted']):>9}  {verdict}")

    print("-" * len(header))
    print("Diff = orange_oil mean minus spearmint_oil mean.")
    print()

    print("Per-outcome detail (group means with standard deviations):")
    for (column, label, units) in DECLARED_OUTCOMES:
        row = results.loc[results["outcome"] == column].iloc[0]
        print(f"  {label} ({units}): "
              f"{GROUP_A} {row['mean_orange_oil']:.2f} (SD {row['sd_orange_oil']:.2f}), "
              f"{GROUP_B} {row['mean_spearmint_oil']:.2f} (SD {row['sd_spearmint_oil']:.2f}); "
              f"t = {row['t_statistic']:.2f}, raw p = {row['p_raw']:.4f}, "
              f"Holm-adjusted p = {row['p_adjusted']:.4f}")

    n_significant = int(results["significant_adjusted"].sum())
    print()
    print(f"Outcomes significant after Holm correction across the declared family of "
          f"{len(DECLARED_OUTCOMES)}: {n_significant}")


def main():
    frame = load_data(DATA_FILE)
    results = run_analysis(frame)
    print_results(frame, results)


if __name__ == "__main__":
    main()
