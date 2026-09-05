"""Post-training comparison of two eight-week hangboard programmes in sport climbers.

Reads the fixed data file ``data.csv`` (one row per climber, 34 climbers) and compares
the two training groups, ``max_hangs`` and ``repeaters``, on each of the seven outcomes
declared in the study protocol.

The two primary endpoints (peak force and critical force) are tested together and their
two p-values are adjusted with the Holm step-down procedure; the verdicts for those two
outcomes use the adjusted values. The five secondary outcomes are reported with their
plain unadjusted p-values, each judged on its own.

This script only reads ``data.csv``. It never generates, simulates, or overwrites it.
"""

from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_PATH = Path(__file__).resolve().parent / "data.csv"

GROUP_COLUMN = "hangboard_protocol"
GROUP_A = "max_hangs"
GROUP_B = "repeaters"
ALPHA = 0.05

# The declared outcome family, in the fixed order given by the study protocol.
# Each entry is (column, printed label, unit, test).
#   "welch"    - Welch's two-sample t test, for the measured continuous outcomes
#                and the move count, which is high enough to treat as continuous.
#   "mannwhitney" - Mann-Whitney U test, for the self-reported ordinal rating.
OUTCOMES = [
    ("peak_force_n", "Peak finger flexor force", "N", "welch"),
    ("critical_force_pct", "Critical force", "% of peak", "welch"),
    ("time_to_failure_s", "Time to failure at 60% of peak", "s", "welch"),
    ("rate_of_force_development_n_per_s", "Rate of force development (0-200 ms)", "N/s", "welch"),
    ("resaturation_half_time_s", "Oxygen resaturation half time", "s", "welch"),
    ("moves_to_failure", "Moves to failure on the circuit", "moves", "welch"),
    ("finger_soreness_0_10", "Finger soreness, final training week", "0-10", "mannwhitney"),
]

# Outcomes 1 and 2 in the declared order are the protocol's primary endpoints.
PRIMARY_OUTCOMES = ["peak_force_n", "critical_force_pct"]

TEST_NAMES = {
    "welch": "Welch's two-sample t test",
    "mannwhitney": "Mann-Whitney U test",
}


def load_data(path=DATA_PATH):
    """Read the fixed data file and check the two expected groups are present."""
    frame = pd.read_csv(path)
    present = sorted(frame[GROUP_COLUMN].unique())
    if present != sorted([GROUP_A, GROUP_B]):
        raise ValueError(f"expected groups {[GROUP_A, GROUP_B]}, found {present}")
    if frame.isna().any().any():
        raise ValueError("data.csv contains missing values")
    return frame


def group_summary(frame, column):
    """Return n, mean and standard deviation of one outcome in each group."""
    summary = {}
    for group in (GROUP_A, GROUP_B):
        values = frame.loc[frame[GROUP_COLUMN] == group, column]
        summary[group] = {
            "n": int(values.size),
            "mean": float(values.mean()),
            "sd": float(values.std(ddof=1)),
            "median": float(values.median()),
        }
    return summary


def compare_groups(frame, column, test):
    """Run the one appropriate two-sample test for this outcome."""
    a = frame.loc[frame[GROUP_COLUMN] == GROUP_A, column]
    b = frame.loc[frame[GROUP_COLUMN] == GROUP_B, column]
    if test == "welch":
        statistic, p_value = stats.ttest_ind(a, b, equal_var=False)
    elif test == "mannwhitney":
        statistic, p_value = stats.mannwhitneyu(a, b, alternative="two-sided")
    else:
        raise ValueError(f"unknown test: {test}")
    return float(statistic), float(p_value)


def verdict(p_value, alpha=ALPHA):
    return "significant" if p_value < alpha else "not significant"


def main():
    frame = load_data()

    n_a = int((frame[GROUP_COLUMN] == GROUP_A).sum())
    n_b = int((frame[GROUP_COLUMN] == GROUP_B).sum())

    print("Hangboard training study: post-training comparison of two programmes")
    print("=" * 78)
    print(f"Data file: {DATA_PATH.name}")
    print(f"Climbers (one row each): {len(frame)}")
    print(f"  {GROUP_A}: n = {n_a}")
    print(f"  {GROUP_B}: n = {n_b}")
    print()

    # ---------------------------------------------------------------- summaries
    print("Per-group summary of each declared outcome (mean, SD, median)")
    print("-" * 78)
    header = f"{'Outcome':<44}{'Group':<12}{'n':>4}{'mean':>10}{'SD':>9}{'median':>9}"
    print(header)
    summaries = {}
    for column, label, unit, _test in OUTCOMES:
        summaries[column] = group_summary(frame, column)
        for group in (GROUP_A, GROUP_B):
            s = summaries[column][group]
            name = f"{label} ({unit})" if group == GROUP_A else ""
            print(
                f"{name:<44}{group:<12}{s['n']:>4}"
                f"{s['mean']:>10.2f}{s['sd']:>9.2f}{s['median']:>9.2f}"
            )
        print()

    # ------------------------------------------------------------------- tests
    results = []
    for column, label, unit, test in OUTCOMES:
        statistic, p_value = compare_groups(frame, column, test)
        results.append(
            {
                "column": column,
                "label": label,
                "unit": unit,
                "test": test,
                "statistic": statistic,
                "p_raw": p_value,
                "is_primary": column in PRIMARY_OUTCOMES,
            }
        )

    # Adjust the two primary endpoints together, with a standard routine.
    primary = [r for r in results if r["is_primary"]]
    primary_p = [r["p_raw"] for r in primary]
    _reject, p_adjusted, _sidak, _bonf = multipletests(primary_p, alpha=ALPHA, method="holm")
    for result, p_adj in zip(primary, p_adjusted):
        result["p_adjusted"] = float(p_adj)

    print("=" * 78)
    print("Primary endpoints (outcomes 1 and 2 of the declared family)")
    print(f"Holm adjustment applied across these {len(primary)} p-values; alpha = {ALPHA}")
    print("-" * 78)
    for result in primary:
        s_a = summaries[result["column"]][GROUP_A]
        s_b = summaries[result["column"]][GROUP_B]
        difference = s_a["mean"] - s_b["mean"]
        print(f"{result['label']} ({result['unit']})")
        print(f"  test              : {TEST_NAMES[result['test']]}")
        print(
            f"  {GROUP_A} mean (SD)  : {s_a['mean']:.2f} ({s_a['sd']:.2f})   "
            f"{GROUP_B} mean (SD): {s_b['mean']:.2f} ({s_b['sd']:.2f})"
        )
        print(f"  difference        : {difference:+.2f} ({GROUP_A} minus {GROUP_B})")
        print(f"  statistic         : {result['statistic']:.3f}")
        print(f"  unadjusted p      : {result['p_raw']:.4f}")
        print(f"  Holm-adjusted p   : {result['p_adjusted']:.4f}")
        print(f"  verdict           : {verdict(result['p_adjusted'])} at alpha = {ALPHA}")
        print()

    secondary = [r for r in results if not r["is_primary"]]
    print("=" * 78)
    print("Secondary outcomes (outcomes 3 to 7 of the declared family)")
    print(f"Unadjusted p-values, each judged on its own; alpha = {ALPHA}")
    print("-" * 78)
    for result in secondary:
        s_a = summaries[result["column"]][GROUP_A]
        s_b = summaries[result["column"]][GROUP_B]
        difference = s_a["mean"] - s_b["mean"]
        print(f"{result['label']} ({result['unit']})")
        print(f"  test              : {TEST_NAMES[result['test']]}")
        print(
            f"  {GROUP_A} mean (SD)  : {s_a['mean']:.2f} ({s_a['sd']:.2f})   "
            f"{GROUP_B} mean (SD): {s_b['mean']:.2f} ({s_b['sd']:.2f})"
        )
        print(f"  difference        : {difference:+.2f} ({GROUP_A} minus {GROUP_B})")
        print(f"  statistic         : {result['statistic']:.3f}")
        print(f"  unadjusted p      : {result['p_raw']:.4f}")
        print(f"  verdict           : {verdict(result['p_raw'])} at alpha = {ALPHA}")
        print()

    # ------------------------------------------------------------------ recap
    print("=" * 78)
    print("Verdict table, declared outcome family in protocol order")
    print("-" * 78)
    print(f"{'#':>2} {'Outcome':<38}{'role':<11}{'p used':>9}  verdict")
    for index, result in enumerate(results, start=1):
        role = "primary" if result["is_primary"] else "secondary"
        p_used = result["p_adjusted"] if result["is_primary"] else result["p_raw"]
        print(
            f"{index:>2} {result['label']:<38}{role:<11}{p_used:>9.4f}  "
            f"{verdict(p_used)}"
        )
    print()
    print(
        "p used = Holm-adjusted p for the two primary endpoints, "
        "unadjusted p for the five secondary outcomes."
    )


if __name__ == "__main__":
    main()
