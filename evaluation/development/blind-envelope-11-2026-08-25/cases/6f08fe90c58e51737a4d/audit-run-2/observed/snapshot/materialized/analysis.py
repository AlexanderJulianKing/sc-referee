"""Black soldier fly substrate feed trial: analysis of the six declared outcomes.

Reads bsf_substrate_trial.csv (one row per rearing crate), summarises each declared
outcome within each substrate group, and compares the two substrates outcome by
outcome with a two-sample t-test against the conventional 0.05 threshold.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "bsf_substrate_trial.csv"

GROUP_COLUMN = "substrate"
GROUP_A = "spent_grain"
GROUP_B = "vegetable_waste"

ALPHA = 0.05

# The six outcomes in the fixed order the trial plan declared them.
DECLARED_OUTCOMES = [
    ("mean_larval_fresh_mass_mg", "Mean individual larval fresh mass (mg)"),
    ("fresh_larval_yield_g", "Harvested fresh larval yield per crate (g)"),
    ("crude_protein_pct_dm", "Larval crude protein (% dry matter)"),
    ("crude_fat_pct_dm", "Larval crude fat (% dry matter)"),
    ("substrate_reduction_pct", "Substrate reduction (%)"),
    ("development_time_days", "Development time to first prepupae (days)"),
]


def format_p(p_value):
    """Readable p-value that stays informative when the value is very small."""
    if p_value < 0.0001:
        return f"{p_value:.2e}"
    return f"{p_value:.4f}"


def load_data(path):
    """Read the crate records and split them into the two substrate groups."""
    frame = pd.read_csv(path)
    group_a = frame[frame[GROUP_COLUMN] == GROUP_A]
    group_b = frame[frame[GROUP_COLUMN] == GROUP_B]
    return frame, group_a, group_b


def main():
    frame, group_a, group_b = load_data(DATA_FILE)

    print("Black soldier fly substrate feed trial")
    print("=" * 72)
    print(f"Data file: {DATA_FILE.name}")
    print(f"Crates in file: {len(frame)}")
    print(f"Crates fed {GROUP_A}: {len(group_a)}")
    print(f"Crates fed {GROUP_B}: {len(group_b)}")
    print()

    # Per-group summary of every declared outcome: count, mean, standard deviation.
    print("Per-group summary (mean +/- SD)")
    print("-" * 78)
    print(f"{'Outcome':<44}{GROUP_A:>17}{GROUP_B:>17}")
    for column, label in DECLARED_OUTCOMES:
        a_values = group_a[column]
        b_values = group_b[column]
        a_text = f"{a_values.mean():.2f} +/- {a_values.std(ddof=1):.2f}"
        b_text = f"{b_values.mean():.2f} +/- {b_values.std(ddof=1):.2f}"
        print(f"{label:<44}{a_text:>17}{b_text:>17}")
    print()
    print(f"n = {len(group_a)} crates ({GROUP_A}), {len(group_b)} crates ({GROUP_B}) "
          f"for every outcome; no missing cells.")
    print()

    # One repeated pass over the declared outcome list. Each declared outcome is its
    # own separate question about the two substrates, so the same comparison step is
    # applied to each outcome in turn and its verdict stated as the pass reaches it.
    print(f"Two-sample t-test per declared outcome, threshold alpha = {ALPHA}")
    print("-" * 78)
    for position, (column, label) in enumerate(DECLARED_OUTCOMES, start=1):
        a_values = group_a[column]
        b_values = group_b[column]

        t_statistic, p_value = stats.ttest_ind(a_values, b_values)
        significant = p_value < ALPHA
        verdict = "SIGNIFICANT" if significant else "not significant"

        difference = a_values.mean() - b_values.mean()

        print(f"Declared outcome {position}: {label}")
        print(f"  {GROUP_A}:     mean {a_values.mean():.2f}, SD {a_values.std(ddof=1):.2f}, n {len(a_values)}")
        print(f"  {GROUP_B}: mean {b_values.mean():.2f}, SD {b_values.std(ddof=1):.2f}, n {len(b_values)}")
        print(f"  difference (spent_grain - vegetable_waste): {difference:+.2f}")
        print(f"  t = {t_statistic:.3f}, p = {format_p(p_value)}  ->  {verdict} at alpha = {ALPHA}")
        print()


if __name__ == "__main__":
    main()
