"""Comparison of two coagulants for firm tofu across the declared outcome family.

Reads the fixed data file ``data.csv`` (one row per tofu block), reports the group
sizes and per-group summary values, and compares the two coagulant groups on each
declared outcome with a two-sample Welch t-test.

The script only reads ``data.csv``; it never generates, simulates, or overwrites it.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "data.csv"

GROUP_COLUMN = "coagulant"
GROUP_A = "caso4"
GROUP_B = "gdl"
GROUP_LABELS = {GROUP_A: "calcium sulfate", GROUP_B: "glucono-delta-lactone"}

ALPHA = 0.05

# The pre-declared outcome family, in the fixed order it was declared in the study
# plan: (column name, readable name, unit, decimals used for reporting).
DECLARED_OUTCOMES = [
    ("yield_g_per_100g", "Tofu yield", "g per 100 g dry soybeans", 1),
    ("hardness_n", "Hardness at 30% compression", "N", 2),
    ("syneresis_pct", "Syneresis after 24 h", "% of block weight", 2),
    ("whiteness_index", "Whiteness index", "0-100 index", 1),
    ("protein_g_per_100g", "Protein content", "g per 100 g fresh tofu", 2),
    ("ph", "pH of the pressed block", "pH units", 2),
]


def load_data(path):
    """Read the fixed block-level data file."""
    frame = pd.read_csv(path)
    missing = [name for name, *_ in DECLARED_OUTCOMES if name not in frame.columns]
    if missing:
        raise ValueError("data.csv is missing declared outcome columns: %s" % missing)
    return frame


def describe_groups(frame):
    """Print the number of blocks in each coagulant group."""
    counts = frame[GROUP_COLUMN].value_counts()
    print("Design")
    print("-" * 72)
    print("One row is one tofu block. Total blocks: %d" % len(frame))
    for group in (GROUP_A, GROUP_B):
        print("  %-6s (%-21s) n = %d" % (group, GROUP_LABELS[group], counts.get(group, 0)))
    print()


def compare_outcome(frame, column, name, unit, decimals):
    """Run the same sequence of steps for one declared outcome.

    Summarises both groups, runs a two-sample Welch t-test (independent blocks,
    groups not assumed to share a variance), and returns the collected numbers.
    """
    values_a = frame.loc[frame[GROUP_COLUMN] == GROUP_A, column].astype(float)
    values_b = frame.loc[frame[GROUP_COLUMN] == GROUP_B, column].astype(float)

    result = stats.ttest_ind(values_a, values_b, equal_var=False)

    return {
        "column": column,
        "name": name,
        "unit": unit,
        "decimals": decimals,
        "n_a": int(values_a.size),
        "n_b": int(values_b.size),
        "mean_a": float(values_a.mean()),
        "mean_b": float(values_b.mean()),
        "sd_a": float(values_a.std(ddof=1)),
        "sd_b": float(values_b.std(ddof=1)),
        "difference": float(values_a.mean() - values_b.mean()),
        "t_statistic": float(result.statistic),
        "p_value": float(result.pvalue),
    }


def report_outcome(summary):
    """Print one outcome's summary values, test statistic, p-value, and verdict."""
    places = summary["decimals"]
    fmt = "%%.%df" % places

    # Each declared outcome is its own quality question, so the verdict for this
    # outcome is read straight from this outcome's own p-value at the 0.05 level.
    significant = summary["p_value"] < ALPHA
    verdict = "SIGNIFICANT" if significant else "not significant"

    print("%s (%s)  [%s]" % (summary["name"], summary["unit"], summary["column"]))
    print("-" * 72)
    print(
        "  %-21s n = %2d   mean = %s   sd = %s"
        % (
            GROUP_LABELS[GROUP_A],
            summary["n_a"],
            fmt % summary["mean_a"],
            fmt % summary["sd_a"],
        )
    )
    print(
        "  %-21s n = %2d   mean = %s   sd = %s"
        % (
            GROUP_LABELS[GROUP_B],
            summary["n_b"],
            fmt % summary["mean_b"],
            fmt % summary["sd_b"],
        )
    )
    print("  difference (calcium sulfate - lactone) = %s" % (fmt % summary["difference"]))
    print(
        "  Welch two-sample t-test: t = %.3f, p = %.6f"
        % (summary["t_statistic"], summary["p_value"])
    )
    print("  verdict at alpha = %.2f: %s" % (ALPHA, verdict))
    print()


def print_overview(summaries):
    """Print a compact table of every declared outcome in declared order."""
    print("Overview, declared outcome family in declared order")
    print("-" * 72)
    print(
        "%-22s %12s %12s %12s %s"
        % ("outcome", "caso4 mean", "gdl mean", "p-value", "verdict")
    )
    for summary in summaries:
        fmt = "%%.%df" % summary["decimals"]
        verdict = "significant" if summary["p_value"] < ALPHA else "not significant"
        print(
            "%-22s %12s %12s %12.6f %s"
            % (
                summary["column"],
                fmt % summary["mean_a"],
                fmt % summary["mean_b"],
                summary["p_value"],
                verdict,
            )
        )
    print()


def main():
    frame = load_data(DATA_FILE)

    print("Firm tofu: calcium sulfate versus glucono-delta-lactone")
    print("=" * 72)
    print()

    describe_groups(frame)

    print("Per-outcome comparisons")
    print("=" * 72)
    print()

    # One repeated pass over the declared outcome family: the same sequence of
    # steps is applied to each outcome in turn, in the declared order.
    summaries = []
    for column, name, unit, decimals in DECLARED_OUTCOMES:
        summary = compare_outcome(frame, column, name, unit, decimals)
        report_outcome(summary)
        summaries.append(summary)

    print_overview(summaries)


if __name__ == "__main__":
    main()
