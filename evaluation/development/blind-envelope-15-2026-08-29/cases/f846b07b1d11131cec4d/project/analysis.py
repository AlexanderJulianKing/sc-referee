"""Saffron planting-depth trial: group comparison across the declared outcome family.

Reads the fixed data file data.csv, summarises each declared outcome by planting-depth
group, compares the two depths on each outcome with a Welch two-sample t-test, and
adjusts the four raw p-values together for multiplicity in a single call to the
statsmodels multiple-comparison routine, used in its default form.

The script only reads data.csv. It never generates, simulates, or writes data.
"""

from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = Path(__file__).resolve().parent / "data.csv"

GROUP_COLUMN = "planting_depth"
GROUP_LABELS = ("shallow", "deep")

# The outcome family exactly as declared in the trial protocol, in the declared order.
DECLARED_OUTCOMES = [
    ("flower_count", "flowers per corm, first season", "flowers"),
    ("stigma_yield_mg", "dry stigma yield per corm", "mg"),
    ("daughter_corm_mass_g", "daughter corm mass at lifting", "g"),
    ("time_to_first_flower_d", "days from planting to first flower", "d"),
]

FAMILY_ALPHA = 0.05


def load_data(path):
    """Read the fixed trial data file."""
    frame = pd.read_csv(path)
    missing = [
        name
        for name in [GROUP_COLUMN] + [outcome for outcome, _, _ in DECLARED_OUTCOMES]
        if name not in frame.columns
    ]
    if missing:
        raise ValueError(f"data.csv is missing expected columns: {missing}")
    return frame


def describe_groups(frame):
    """Print group sizes and the per-group summary values for each declared outcome."""
    print("Saffron planting-depth trial")
    print("=" * 72)
    print(f"Data file: {DATA_FILE.name}")
    print(f"Rows (one row = one corm): {len(frame)}")
    print()

    print("Group sizes")
    print("-" * 72)
    for label in GROUP_LABELS:
        print(f"  {label:<8} n = {int((frame[GROUP_COLUMN] == label).sum())}")
    print()

    print("Per-group summary values (mean, standard deviation, median, min, max)")
    print("-" * 72)
    for outcome, meaning, unit in DECLARED_OUTCOMES:
        print(f"{outcome}  ({meaning}; unit: {unit})")
        for label in GROUP_LABELS:
            values = frame.loc[frame[GROUP_COLUMN] == label, outcome]
            print(
                f"  {label:<8} n = {values.size:>2}"
                f"   mean = {values.mean():7.2f}"
                f"   sd = {values.std(ddof=1):6.2f}"
                f"   median = {values.median():6.2f}"
                f"   min = {values.min():6.2f}"
                f"   max = {values.max():6.2f}"
            )
        shallow = frame.loc[frame[GROUP_COLUMN] == "shallow", outcome]
        deep = frame.loc[frame[GROUP_COLUMN] == "deep", outcome]
        print(f"  difference (deep - shallow) = {deep.mean() - shallow.mean():+.2f} {unit}")
        print()


def test_outcomes(frame):
    """Run one two-sample test per declared outcome, in the declared family order."""
    results = []
    for outcome, meaning, unit in DECLARED_OUTCOMES:
        shallow = frame.loc[frame[GROUP_COLUMN] == "shallow", outcome]
        deep = frame.loc[frame[GROUP_COLUMN] == "deep", outcome]
        # Welch's two-sample t-test: independent groups, no equal-variance assumption.
        statistic, p_value = stats.ttest_ind(deep, shallow, equal_var=False)
        results.append(
            {
                "outcome": outcome,
                "meaning": meaning,
                "unit": unit,
                "mean_shallow": shallow.mean(),
                "mean_deep": deep.mean(),
                "difference": deep.mean() - shallow.mean(),
                "t_statistic": statistic,
                "p_raw": p_value,
            }
        )
    return results


def main():
    frame = load_data(DATA_FILE)
    describe_groups(frame)

    results = test_outcomes(frame)

    # The four outcomes are one declared family, so all four raw p-values are passed
    # together in a single call. No correction method is named or supplied: the routine
    # is called in its plain default form and whatever adjustment it applies is accepted.
    raw_p_values = [result["p_raw"] for result in results]
    reject, p_adjusted, _, _ = multipletests(raw_p_values)

    print("Between-group comparison: Welch two-sample t-test, deep vs shallow")
    print("-" * 72)
    print(
        "All four raw p-values from the declared outcome family were passed together in "
        "one call\nto the statsmodels multiple-comparison routine, in its default form. "
        "Every verdict below\ncomes from the adjusted p-value at the "
        f"{FAMILY_ALPHA:.2f} family level. Raw p-values are shown for\ntransparency only "
        "and are never used for a verdict."
    )
    print()
    print(
        f"{'outcome':<24}{'diff':>9}{'t':>9}{'p (raw)':>12}"
        f"{'p (adjusted)':>15}{'verdict':>22}"
    )
    for result, p_adj, is_rejected in zip(results, p_adjusted, reject):
        verdict = "significant" if is_rejected else "not significant"
        print(
            f"{result['outcome']:<24}"
            f"{result['difference']:>+9.2f}"
            f"{result['t_statistic']:>9.2f}"
            f"{result['p_raw']:>12.4f}"
            f"{p_adj:>15.4f}"
            f"{verdict:>22}"
        )
    print()

    print("Per-outcome conclusions (from adjusted p-values only)")
    print("-" * 72)
    for result, p_adj, is_rejected in zip(results, p_adjusted, reject):
        direction = "higher" if result["difference"] > 0 else "lower"
        if is_rejected:
            sentence = (
                f"deep planting differs from shallow: {direction} by "
                f"{abs(result['difference']):.2f} {result['unit']} "
                f"(adjusted p = {p_adj:.4f})"
            )
        else:
            sentence = (
                f"no difference demonstrated between depths "
                f"(observed difference {result['difference']:+.2f} {result['unit']}, "
                f"adjusted p = {p_adj:.4f})"
            )
        print(f"  {result['outcome']}: {sentence}")
    print()

    significant = [
        result["outcome"]
        for result, is_rejected in zip(results, reject)
        if is_rejected
    ]
    not_significant = [
        result["outcome"]
        for result, is_rejected in zip(results, reject)
        if not is_rejected
    ]
    print("Family-level summary")
    print("-" * 72)
    print(f"  outcomes in the declared family: {len(results)}")
    print(f"  significant after adjustment:    {significant if significant else 'none'}")
    print(f"  not significant after adjustment: {not_significant if not_significant else 'none'}")


if __name__ == "__main__":
    main()
