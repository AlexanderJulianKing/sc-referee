"""Mini-silo fermentation trial: inoculated versus untreated grass silage.

Reads mini_silo_fermentation.csv, summarises the five declared outcomes within
each treatment group, and tests each outcome for a difference between the two
groups with Welch's two-sample t-test.

The protocol written before packing fixed the per-outcome significance
threshold for this experiment at 0.01. That value is a protocol constant. This
script carries it as given and compares each p-value against it.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

# Significance threshold fixed by the study protocol before the mini-silos were
# packed. Carried here as a given constant; the reasoning behind the value is
# recorded in the report, not computed here.
PROTOCOL_SIGNIFICANCE_THRESHOLD = 0.01

DATA_FILE = Path(__file__).resolve().parent / "mini_silo_fermentation.csv"

GROUP_COLUMN = "treatment"
INOCULATED = "inoculated"
UNTREATED = "untreated"

# The five outcomes declared in the protocol, in the declared order.
DECLARED_OUTCOMES = [
    ("dry_matter_loss_percent", "Dry matter loss (% of DM packed)"),
    ("silage_ph", "Silage pH at opening"),
    ("lactic_acid_g_per_kg_dm", "Lactic acid (g/kg DM)"),
    ("ammonia_n_percent_of_total_n", "Ammonia N (% of total N)"),
    ("aerobic_stability_hours", "Aerobic stability (hours)"),
]


def load_data(path):
    """Read the study data and check the shape we expect."""
    frame = pd.read_csv(path)
    missing = frame.isna().sum().sum()
    if missing:
        raise ValueError(f"expected no missing cells, found {missing}")
    groups = sorted(frame[GROUP_COLUMN].unique())
    if groups != sorted([INOCULATED, UNTREATED]):
        raise ValueError(f"unexpected treatment values: {groups}")
    return frame


def report_group_sizes(frame):
    print("Mini-silos per treatment group")
    print("-" * 62)
    counts = frame[GROUP_COLUMN].value_counts()
    for group in (INOCULATED, UNTREATED):
        print(f"  {group:<12s} n = {int(counts[group])}")
    print(f"  {'total':<12s} n = {len(frame)}")
    print()


def report_group_summaries(frame):
    """Mean and standard deviation of every outcome within each group."""
    print("Per-group summary of each declared outcome (mean +/- SD)")
    print("-" * 62)
    header = f"{'Outcome':<34s}{'group':<13s}{'n':>4s}{'mean':>9s}{'SD':>9s}"
    print(header)
    for column, label in DECLARED_OUTCOMES:
        for group in (INOCULATED, UNTREATED):
            values = frame.loc[frame[GROUP_COLUMN] == group, column]
            print(
                f"{label:<34s}{group:<13s}{len(values):>4d}"
                f"{values.mean():>9.2f}{values.std(ddof=1):>9.2f}"
            )
    print()


def test_outcomes(frame):
    """Welch's two-sample t-test for each declared outcome, in order."""
    print("Two-group tests of the five declared outcomes")
    print(
        "Test: Welch's two-sample t-test (two-sided), "
        "inoculated versus untreated"
    )
    print(
        "Protocol significance threshold for each outcome: "
        f"{PROTOCOL_SIGNIFICANCE_THRESHOLD}"
    )
    print("-" * 62)

    results = []
    for position, (column, label) in enumerate(DECLARED_OUTCOMES, start=1):
        inoculated = frame.loc[frame[GROUP_COLUMN] == INOCULATED, column]
        untreated = frame.loc[frame[GROUP_COLUMN] == UNTREATED, column]
        test = stats.ttest_ind(inoculated, untreated, equal_var=False)
        difference = inoculated.mean() - untreated.mean()
        significant = test.pvalue < PROTOCOL_SIGNIFICANCE_THRESHOLD
        verdict = (
            "significant at the protocol threshold"
            if significant
            else "not significant at the protocol threshold"
        )

        print(f"Outcome {position}: {label}")
        print(
            f"  inoculated mean = {inoculated.mean():.3f}   "
            f"untreated mean = {untreated.mean():.3f}   "
            f"difference = {difference:+.3f}"
        )
        print(f"  t = {test.statistic:.3f}   df = {test.df:.1f}")
        print(
            f"  p = {test.pvalue:.6f}   "
            f"vs protocol threshold {PROTOCOL_SIGNIFICANCE_THRESHOLD}   "
            f"-> {verdict}"
        )
        print()

        results.append((position, label, test.pvalue, significant))

    return results


def report_verdicts(results):
    print("Verdicts in declared outcome order")
    print("-" * 62)
    for position, label, pvalue, significant in results:
        mark = "SIGNIFICANT" if significant else "not significant"
        print(f"  {position}. {label:<34s} p = {pvalue:.6f}   {mark}")
    print()
    print(
        "Each verdict is a comparison of that outcome's p-value against the "
        f"protocol threshold of {PROTOCOL_SIGNIFICANCE_THRESHOLD}."
    )


def main():
    frame = load_data(DATA_FILE)
    print("Mini-silo fermentation trial: inoculated versus untreated silage")
    print("=" * 62)
    print()
    report_group_sizes(frame)
    report_group_summaries(frame)
    results = test_outcomes(frame)
    report_verdicts(results)


if __name__ == "__main__":
    main()
