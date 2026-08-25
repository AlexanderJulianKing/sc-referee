"""Greenhouse cucumber grafting trial: analysis of the eight declared outcomes.

Reads the trial record sheet, summarises each declared outcome within each
propagation group, and compares grafted plants with self-rooted plants on every
declared outcome with a two-sample t-test.

The first three declared outcomes are the headline yield outcomes. Their
p-values are multiplied by the number of comparisons run and capped at one
before being judged against the 0.05 threshold. The remaining five declared
outcomes are judged on their raw p-values.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

CSV_PATH = Path(__file__).parent / "cucumber_grafting_trial.csv"
GROUP_COLUMN = "propagation_method"
GRAFTED = "grafted"
SELF_ROOTED = "self_rooted"
ALPHA = 0.05

# The eight declared outcomes, in the order set out in the trial plan.
DECLARED_OUTCOMES = [
    ("marketable_yield_kg", "Marketable fruit yield per plant (kg)"),
    ("marketable_fruit_count", "Marketable fruits per plant (count)"),
    ("mean_fruit_mass_g", "Mean fruit fresh mass (g)"),
    ("stem_diameter_mm", "Stem diameter 20 cm above graft union (mm)"),
    ("leaf_chlorophyll_index", "Leaf chlorophyll index (unitless)"),
    ("root_dry_mass_g", "Root system dry mass (g)"),
    ("soluble_solids_brix", "Fruit soluble solids (degrees Brix)"),
    ("days_to_first_harvest", "Days from planting to first harvest"),
]

# The first three declared outcomes are the headline yield outcomes.
HEADLINE_OUTCOMES = [name for name, _ in DECLARED_OUTCOMES[:3]]


def load_data(path):
    """Read the trial record sheet."""
    frame = pd.read_csv(path)
    return frame


def report_group_sizes(frame):
    """Print the number of plants in each propagation group."""
    print("=" * 72)
    print("GROUP SIZES")
    print("=" * 72)
    counts = frame[GROUP_COLUMN].value_counts()
    for group in (GRAFTED, SELF_ROOTED):
        print(f"  {group:<12} n = {int(counts[group])} plants")
    print(f"  {'total':<12} n = {len(frame)} plants")
    print()


def report_group_summaries(frame):
    """Print the mean and standard deviation of each outcome within each group."""
    print("=" * 72)
    print("PER-GROUP SUMMARY (mean and standard deviation)")
    print("=" * 72)
    header = f"{'outcome':<28}{'group':<13}{'n':>4}{'mean':>12}{'sd':>10}"
    print(header)
    print("-" * 72)
    for column, _label in DECLARED_OUTCOMES:
        for group in (GRAFTED, SELF_ROOTED):
            values = frame.loc[frame[GROUP_COLUMN] == group, column]
            print(
                f"{column:<28}{group:<13}{len(values):>4}"
                f"{values.mean():>12.3f}{values.std(ddof=1):>10.3f}"
            )
        print("-" * 72)
    print()


def run_tests(frame):
    """Run a two-sample t-test for each declared outcome, grafted vs self-rooted."""
    results = []
    for column, label in DECLARED_OUTCOMES:
        grafted_values = frame.loc[frame[GROUP_COLUMN] == GRAFTED, column]
        self_rooted_values = frame.loc[frame[GROUP_COLUMN] == SELF_ROOTED, column]
        statistic, p_value = stats.ttest_ind(grafted_values, self_rooted_values)
        results.append(
            {
                "column": column,
                "label": label,
                "grafted_mean": grafted_values.mean(),
                "self_rooted_mean": self_rooted_values.mean(),
                "t_statistic": statistic,
                "p_raw": p_value,
            }
        )
    return results


def apply_headline_correction(results):
    """Correct the three headline yield p-values.

    Each headline p-value is multiplied by the number of comparisons that were
    run and capped at one. The other five declared outcomes keep their raw
    p-value and are given no corrected value.
    """
    n_comparisons = len(results)
    for result in results:
        if result["column"] in HEADLINE_OUTCOMES:
            result["headline"] = True
            result["p_corrected"] = min(result["p_raw"] * n_comparisons, 1.0)
            result["p_decision"] = result["p_corrected"]
        else:
            result["headline"] = False
            result["p_corrected"] = None
            result["p_decision"] = result["p_raw"]
        result["significant"] = result["p_decision"] < ALPHA
    return results, n_comparisons


def report_tests(results, n_comparisons):
    """Print each outcome's raw p-value, corrected value, and verdict."""
    print("=" * 72)
    print("SIGNIFICANCE TESTS: grafted vs self-rooted")
    print("=" * 72)
    print(f"Two-sample t-test on each of the {n_comparisons} declared outcomes.")
    print(
        f"Headline yield outcomes ({', '.join(HEADLINE_OUTCOMES)}) have their "
        f"p-value multiplied by {n_comparisons} and capped at 1."
    )
    print(f"Threshold for significance: {ALPHA}")
    print()
    header = (
        f"{'#':<3}{'outcome':<28}{'t':>8}{'p_raw':>12}"
        f"{'p_corrected':>14}{'verdict':>18}"
    )
    print(header)
    print("-" * 83)
    for index, result in enumerate(results, start=1):
        corrected = (
            f"{result['p_corrected']:.5f}"
            if result["p_corrected"] is not None
            else "-"
        )
        verdict = "SIGNIFICANT" if result["significant"] else "not significant"
        marker = " (headline)" if result["headline"] else ""
        print(
            f"{index:<3}{result['column']:<28}{result['t_statistic']:>8.3f}"
            f"{result['p_raw']:>12.5f}{corrected:>14}{verdict:>18}{marker}"
        )
    print("-" * 83)
    print()

    print("=" * 72)
    print("OUTCOME-BY-OUTCOME CONCLUSIONS (declared order)")
    print("=" * 72)
    for index, result in enumerate(results, start=1):
        basis = "corrected p" if result["headline"] else "raw p"
        verdict = (
            "grafted plants differ significantly from self-rooted plants"
            if result["significant"]
            else "no significant difference between grafted and self-rooted plants"
        )
        print(f"{index}. {result['label']}")
        print(
            f"   grafted mean = {result['grafted_mean']:.3f}, "
            f"self-rooted mean = {result['self_rooted_mean']:.3f}"
        )
        print(
            f"   raw p = {result['p_raw']:.5f}"
            + (
                f", corrected p = {result['p_corrected']:.5f}"
                if result["p_corrected"] is not None
                else ""
            )
        )
        print(f"   decided on {basis} against {ALPHA}: {verdict}")
        print()


def main():
    frame = load_data(CSV_PATH)
    report_group_sizes(frame)
    report_group_summaries(frame)
    results = run_tests(frame)
    results, n_comparisons = apply_headline_correction(results)
    report_tests(results, n_comparisons)


if __name__ == "__main__":
    main()
