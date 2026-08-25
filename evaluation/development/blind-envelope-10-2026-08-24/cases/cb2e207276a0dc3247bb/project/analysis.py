"""Nitrogen rate comparison for grain sorghum at physiological maturity.

Compares the n60 (60 kg N/ha) and n120 (120 kg N/ha) groups on the four
outcomes declared in advance by the protocol, in the declared order:

    1. grain_yield_g
    2. panicle_length_cm
    3. stem_brix_pct
    4. plant_height_cm

Each outcome is tested once with an independent two-sample t-test. The four
raw p-values are then passed together, in the declared order, as a single
family in one call to the multiple comparisons adjustment routine of
statsmodels. The correction method is left unspecified so that the routine's
own default adjustment is applied, and every significance verdict is taken
from what that routine returns at a family-wise level of 0.05.
"""

from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = Path(__file__).resolve().parent / "sorghum_nitrogen_plants.csv"

GROUP_COLUMN = "n_rate_group"
GROUP_A = "n60"
GROUP_B = "n120"

# The declared family of outcomes, in the order fixed by the protocol.
DECLARED_OUTCOMES = [
    ("grain_yield_g", "Grain yield (g/plant)"),
    ("panicle_length_cm", "Panicle length (cm)"),
    ("stem_brix_pct", "Stem juice sugar (degrees Brix)"),
    ("plant_height_cm", "Plant height (cm)"),
]

FAMILY_ALPHA = 0.05


def load_data(path):
    """Read the plant-level field sample and check its basic shape."""
    frame = pd.read_csv(path)

    expected_columns = ["plant_id", GROUP_COLUMN] + [name for name, _ in DECLARED_OUTCOMES]
    if list(frame.columns) != expected_columns:
        raise ValueError(f"unexpected columns: {list(frame.columns)}")
    if frame.isna().any().any():
        raise ValueError("data file contains empty cells")
    if frame["plant_id"].duplicated().any():
        raise ValueError("plant_id values are not unique")

    observed_groups = set(frame[GROUP_COLUMN].unique())
    if observed_groups != {GROUP_A, GROUP_B}:
        raise ValueError(f"unexpected group values: {sorted(observed_groups)}")

    return frame


def summarise_group(values):
    """Return n, mean and sample standard deviation for one group."""
    return {
        "n": int(values.count()),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
    }


def main():
    frame = load_data(DATA_FILE)

    group_a = frame[frame[GROUP_COLUMN] == GROUP_A]
    group_b = frame[frame[GROUP_COLUMN] == GROUP_B]

    results = []
    raw_p_values = []

    for column, label in DECLARED_OUTCOMES:
        values_a = group_a[column]
        values_b = group_b[column]

        test = stats.ttest_ind(values_a, values_b)

        summary_a = summarise_group(values_a)
        summary_b = summarise_group(values_b)

        results.append(
            {
                "column": column,
                "label": label,
                "a": summary_a,
                "b": summary_b,
                "difference": summary_b["mean"] - summary_a["mean"],
                "t": float(test.statistic),
                "df": float(test.df),
                "p_raw": float(test.pvalue),
            }
        )
        raw_p_values.append(float(test.pvalue))

    # One call, whole declared family together, method left unspecified.
    reject, p_adjusted, _, _ = multipletests(raw_p_values, alpha=FAMILY_ALPHA)

    for result, adjusted, is_rejected in zip(results, p_adjusted, reject):
        result["p_adjusted"] = float(adjusted)
        result["significant"] = bool(is_rejected)

    print(f"Data file: {DATA_FILE.name}")
    print(f"Plants: {len(frame)}  ({GROUP_A}: {len(group_a)}, {GROUP_B}: {len(group_b)})")
    print(f"Declared family size: {len(results)}   family-wise alpha: {FAMILY_ALPHA}")
    print()

    print("Group summaries (mean +/- SD)")
    print(f"{'Outcome':<34}{GROUP_A:>20}{GROUP_B:>20}")
    for result in results:
        cell_a = f"{result['a']['mean']:.2f} +/- {result['a']['sd']:.2f}"
        cell_b = f"{result['b']['mean']:.2f} +/- {result['b']['sd']:.2f}"
        print(f"{result['label']:<34}{cell_a:>20}{cell_b:>20}")
    print()

    print("Independent two-sample t-tests, declared order")
    header = f"{'Outcome':<34}{'t':>9}{'df':>7}{'p_raw':>12}{'p_adj':>12}{'verdict':>18}"
    print(header)
    for result in results:
        verdict = "significant" if result["significant"] else "not significant"
        print(
            f"{result['label']:<34}"
            f"{result['t']:>9.3f}"
            f"{result['df']:>7.0f}"
            f"{result['p_raw']:>12.6f}"
            f"{result['p_adjusted']:>12.6f}"
            f"{verdict:>18}"
        )
    print()

    print("Mean difference (n120 minus n60)")
    for result in results:
        print(f"  {result['label']:<34}{result['difference']:+.2f}")

    return results


if __name__ == "__main__":
    main()
