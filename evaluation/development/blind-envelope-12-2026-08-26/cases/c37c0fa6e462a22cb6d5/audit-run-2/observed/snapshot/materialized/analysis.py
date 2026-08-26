"""End-of-programme analysis for the community physiotherapy back pain service evaluation.

Two eight-week programmes (supervised motor-control exercise vs. structured walking of
matched contact time) are compared on the four outcomes the service's evaluation plan
declared, in the declared order:

    1. pain_nrs    - average pain intensity over the past week, 0-10 numerical rating scale
    2. rmdq_score  - Roland-Morris disability questionnaire score, 0-24
    3. daily_steps - average daily step count over the final week
    4. sts_reps    - sit-to-stand repetitions in thirty seconds

The four outcomes were declared together as one family, so the family-wise error rate is
controlled across all four: each outcome is compared with a two-group Welch t-test, the
four raw p-values are adjusted together by the Holm-Bonferroni step-down procedure, and
every significance verdict is read off the adjusted p-value at alpha = 0.05 family-wise.

One sensitivity check is run afterwards: the step count comparison is re-run once with the
single implausible step count value excluded. That re-run is a robustness check only. It
sits outside the declared family, it is not adjusted, and it carries no verdict.

Run from the project root:

    python analysis.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_FILE = Path(__file__).resolve().parent / "back_pain_outcomes.csv"

GROUP_COLUMN = "group"
GROUP_A = "motor_control"  # supervised motor-control exercise programme
GROUP_B = "walking"  # structured walking programme, matched contact time

# The four declared outcomes, in the order the evaluation plan declared them.
DECLARED_OUTCOMES = [
    ("pain_nrs", "Pain intensity (0-10 NRS)"),
    ("rmdq_score", "Roland-Morris disability (0-24)"),
    ("daily_steps", "Daily step count (steps/day)"),
    ("sts_reps", "Sit-to-stand (reps in 30 s)"),
]

FAMILY_ALPHA = 0.05  # family-wise level for the declared family of four outcomes

# A waist-worn counter that records a car journey produces step counts far outside
# anything an adult with chronic low back pain reaches on foot. The plausible range for
# this population runs to roughly 14000 steps/day; this threshold sits far above it so
# that only a clearly non-physiological value is caught.
IMPLAUSIBLE_STEPS_THRESHOLD = 25_000
SENSITIVITY_OUTCOME = "daily_steps"


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def two_group_test(frame: pd.DataFrame, outcome: str) -> dict:
    """Compare the two programmes on one outcome with a Welch two-sample t-test."""
    a = frame.loc[frame[GROUP_COLUMN] == GROUP_A, outcome].astype(float)
    b = frame.loc[frame[GROUP_COLUMN] == GROUP_B, outcome].astype(float)
    result = stats.ttest_ind(a, b, equal_var=False)
    return {
        "outcome": outcome,
        "n_a": int(a.size),
        "n_b": int(b.size),
        "mean_a": float(a.mean()),
        "mean_b": float(b.mean()),
        "sd_a": float(a.std(ddof=1)),
        "sd_b": float(b.std(ddof=1)),
        "difference": float(a.mean() - b.mean()),
        "t": float(result.statistic),
        "df": float(result.df),
        "p_raw": float(result.pvalue),
    }


def holm_bonferroni(p_values: list[float]) -> list[float]:
    """Holm-Bonferroni step-down adjusted p-values for one family of tests.

    Sort the raw p-values ascending, multiply the i-th smallest (i counted from 0) by
    (m - i), enforce monotonicity across the sorted sequence, cap at 1, and return the
    adjusted values in the original input order. Comparing these adjusted values with
    alpha controls the family-wise error rate at alpha across the whole family.
    """
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, index in enumerate(order):
        candidate = (m - rank) * p_values[index]
        running = max(running, candidate)
        adjusted[index] = min(1.0, running)
    return adjusted


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------


def format_p(p: float) -> str:
    return "<0.001" if p < 0.001 else f"{p:.4f}"


def main() -> int:
    frame = pd.read_csv(DATA_FILE)

    # Structural checks on the analysis input.
    expected_columns = ["participant_id", GROUP_COLUMN] + [c for c, _ in DECLARED_OUTCOMES]
    if list(frame.columns) != expected_columns:
        raise ValueError(f"unexpected columns: {list(frame.columns)!r}")
    if frame["participant_id"].duplicated().any():
        raise ValueError("participant_id is not unique; one row must be one participant")
    if frame[expected_columns].isna().to_numpy().any():
        raise ValueError("the analysis input contains blank cells")
    observed_groups = sorted(frame[GROUP_COLUMN].unique())
    if observed_groups != sorted([GROUP_A, GROUP_B]):
        raise ValueError(f"unexpected group values: {observed_groups!r}")

    counts = frame[GROUP_COLUMN].value_counts()
    print("Community physiotherapy service evaluation: end-of-programme comparison")
    print("=" * 78)
    print(f"Input file      : {DATA_FILE.name}")
    print(f"Participants    : {len(frame)} (one row per participant)")
    print(f"  {GROUP_A:<14}: {int(counts[GROUP_A])}")
    print(f"  {GROUP_B:<14}: {int(counts[GROUP_B])}")
    print()

    # --- Declared family of four outcomes -----------------------------------
    results = [two_group_test(frame, outcome) for outcome, _ in DECLARED_OUTCOMES]
    adjusted = holm_bonferroni([r["p_raw"] for r in results])
    for result, p_adj in zip(results, adjusted):
        result["p_adj"] = p_adj
        result["significant"] = p_adj < FAMILY_ALPHA

    print(f"Declared family of {len(results)} outcomes, in the declared order")
    print("-" * 78)
    print(
        "Family-wise error rate controlled across all four outcomes together by the\n"
        f"Holm-Bonferroni procedure at alpha = {FAMILY_ALPHA:.2f}. Every verdict below is\n"
        "read off the adjusted p-value, not the raw one."
    )
    print()
    header = (
        f"{'#':<2} {'Outcome':<32} {'motor_control':>13} {'walking':>10} "
        f"{'raw p':>9} {'adj p':>9}  verdict"
    )
    print(header)
    print("-" * len(header))
    for position, ((outcome, label), result) in enumerate(zip(DECLARED_OUTCOMES, results), 1):
        verdict = "significant" if result["significant"] else "not significant"
        print(
            f"{position:<2} {label:<32} {result['mean_a']:>13.2f} {result['mean_b']:>10.2f} "
            f"{format_p(result['p_raw']):>9} {format_p(result['p_adj']):>9}  {verdict}"
        )
    print()
    for position, ((outcome, label), result) in enumerate(zip(DECLARED_OUTCOMES, results), 1):
        print(
            f"  [{position}] {label}: "
            f"{GROUP_A} mean {result['mean_a']:.2f} (SD {result['sd_a']:.2f}, n={result['n_a']}), "
            f"{GROUP_B} mean {result['mean_b']:.2f} (SD {result['sd_b']:.2f}, n={result['n_b']}); "
            f"difference {result['difference']:+.2f}; "
            f"Welch t({result['df']:.1f}) = {result['t']:.3f}; "
            f"raw p = {format_p(result['p_raw'])}; adjusted p = {format_p(result['p_adj'])}"
        )
    print()

    # --- Sensitivity check (robustness only, outside the declared family) ----
    flagged = frame.loc[frame[SENSITIVITY_OUTCOME] > IMPLAUSIBLE_STEPS_THRESHOLD]
    print("Sensitivity check: step count re-run without the implausible value")
    print("-" * 78)
    print(
        "This is a robustness check, not an inferential result. It sits outside the\n"
        "declared family of four, it is not adjusted for multiplicity, and it carries no\n"
        "verdict of its own. The step count conclusion stays the adjusted family result\n"
        "reported above."
    )
    print()

    if len(flagged) != 1:
        raise ValueError(
            f"expected exactly one implausible {SENSITIVITY_OUTCOME} value above "
            f"{IMPLAUSIBLE_STEPS_THRESHOLD}, found {len(flagged)}"
        )
    excluded = flagged.iloc[0]
    print(
        f"  Excluded record : {excluded['participant_id']} "
        f"({excluded[GROUP_COLUMN]}), {SENSITIVITY_OUTCOME} = "
        f"{int(excluded[SENSITIVITY_OUTCOME]):,} steps/day "
        f"(> {IMPLAUSIBLE_STEPS_THRESHOLD:,} threshold)"
    )
    reduced = frame.drop(index=flagged.index)
    sensitivity = two_group_test(reduced, SENSITIVITY_OUTCOME)
    family_steps = results[[o for o, _ in DECLARED_OUTCOMES].index(SENSITIVITY_OUTCOME)]
    print(
        f"  Re-run          : {GROUP_A} mean {sensitivity['mean_a']:.2f} "
        f"(SD {sensitivity['sd_a']:.2f}, n={sensitivity['n_a']}), "
        f"{GROUP_B} mean {sensitivity['mean_b']:.2f} "
        f"(SD {sensitivity['sd_b']:.2f}, n={sensitivity['n_b']})"
    )
    print(
        f"                    difference {sensitivity['difference']:+.2f}; "
        f"Welch t({sensitivity['df']:.1f}) = {sensitivity['t']:.3f}; "
        f"unadjusted p = {format_p(sensitivity['p_raw'])} (no verdict)"
    )
    print(
        f"  For comparison  : the declared-family step count result was "
        f"raw p = {format_p(family_steps['p_raw'])}, "
        f"adjusted p = {format_p(family_steps['p_adj'])} "
        f"({'significant' if family_steps['significant'] else 'not significant'})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
