"""Warm-up protocol comparison in senior club handball players.

Reads handball_warmup.csv and compares the two warm-up groups (usual vs
neuromuscular) on the five pre-declared performance outcomes.

Inference follows the study protocol: the five declared outcomes form one
outcome family, so the complete set of five raw p-values is adjusted together
with the Holm-Bonferroni step-down procedure, which controls the family-wise
error rate across the whole family. Every inferential verdict is taken from the
adjusted p-values only.

A separate sensitivity re-run for the sprint outcome, with the single
implausible timing-gate value excluded, is reported after the family analysis.
It is not part of the declared family, is not adjusted, and yields no
inferential verdict.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

CSV_PATH = Path(__file__).resolve().parent / "handball_warmup.csv"

GROUP_COL = "warm_up"
REFERENCE_GROUP = "usual"
TEST_GROUP = "neuromuscular"

# The pre-declared outcome family, in the declared order.
DECLARED_FAMILY = [
    ("cmj_height_cm", "Countermovement jump height (cm)", "higher is better"),
    ("sprint_20m_s", "20 m sprint time (s)", "lower is better"),
    ("throw_velocity_kmh", "Throwing velocity (km/h)", "higher is better"),
    ("agility_time_s", "Agility test time (s)", "lower is better"),
    ("knee_flexor_torque_nm", "Peak knee flexor torque (N*m)", "higher is better"),
]

ALPHA = 0.05

# Sensitivity check: the one recorded sprint time that is physiologically
# implausible for a senior player and consistent with a late timing gate.
IMPLAUSIBLE_SPRINT_MIN_S = 5.0


def holm_bonferroni(pvalues):
    """Holm-Bonferroni step-down adjusted p-values.

    Controls the family-wise error rate over the complete set of p-values
    passed in. Returns adjusted p-values in the same order as the input.
    """
    n = len(pvalues)
    order = sorted(range(n), key=lambda i: pvalues[i])
    adjusted = [0.0] * n
    running_max = 0.0
    for rank, idx in enumerate(order):
        value = (n - rank) * pvalues[idx]
        running_max = max(running_max, value)
        adjusted[idx] = min(1.0, running_max)
    return adjusted


def compare_groups(frame, column):
    """Welch two-sample t-test for one outcome between the two warm-up groups."""
    reference = frame.loc[frame[GROUP_COL] == REFERENCE_GROUP, column].dropna()
    test = frame.loc[frame[GROUP_COL] == TEST_GROUP, column].dropna()
    result = stats.ttest_ind(test, reference, equal_var=False)
    return {
        "n_usual": int(reference.size),
        "n_neuromuscular": int(test.size),
        "mean_usual": float(reference.mean()),
        "mean_neuromuscular": float(test.mean()),
        "difference": float(test.mean() - reference.mean()),
        "t_statistic": float(result.statistic),
        "p_raw": float(result.pvalue),
    }


def main():
    data = pd.read_csv(CSV_PATH)

    print("=" * 78)
    print("Warm-up protocol comparison: usual vs neuromuscular")
    print("=" * 78)
    print(f"Data file: {CSV_PATH.name}")
    print(f"Players: {len(data)}")
    for name, count in data[GROUP_COL].value_counts().sort_index().items():
        print(f"  {name}: {count}")
    print()

    # ---------------------------------------------------------------
    # Declared family analysis (the only source of inferential verdicts)
    # ---------------------------------------------------------------
    rows = []
    for column, label, direction in DECLARED_FAMILY:
        summary = compare_groups(data, column)
        summary["column"] = column
        summary["label"] = label
        summary["direction"] = direction
        rows.append(summary)

    raw_pvalues = [row["p_raw"] for row in rows]
    assert len(raw_pvalues) == len(DECLARED_FAMILY), "family must be complete"
    adjusted_pvalues = holm_bonferroni(raw_pvalues)
    for row, p_adj in zip(rows, adjusted_pvalues):
        row["p_adjusted"] = p_adj
        row["verdict"] = (
            "difference supported" if p_adj < ALPHA else "no supported difference"
        )

    print("DECLARED FAMILY OF FIVE OUTCOMES")
    print(
        f"All {len(rows)} raw p-values were adjusted together with the "
        "Holm-Bonferroni step-down"
    )
    print(
        f"procedure (family-wise error rate controlled at alpha = {ALPHA:.2f}). "
        "Verdicts come"
    )
    print("from the adjusted p-values only.")
    print()

    header = (
        f"{'Outcome':<34}{'usual':>9}{'neuro':>9}{'diff':>9}"
        f"{'p raw':>9}{'p adj':>9}  Verdict"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['label']:<34}"
            f"{row['mean_usual']:>9.2f}"
            f"{row['mean_neuromuscular']:>9.2f}"
            f"{row['difference']:>9.2f}"
            f"{row['p_raw']:>9.4f}"
            f"{row['p_adjusted']:>9.4f}"
            f"  {row['verdict']}"
        )
    print()
    print("diff = neuromuscular mean minus usual mean.")
    print("Group sizes per outcome:")
    for row in rows:
        print(
            f"  {row['label']:<34} usual n={row['n_usual']}, "
            f"neuromuscular n={row['n_neuromuscular']}"
        )
    print()

    # ---------------------------------------------------------------
    # Sensitivity check, outside the declared family
    # ---------------------------------------------------------------
    sprint_column = "sprint_20m_s"
    suspect = data.loc[data[sprint_column] >= IMPLAUSIBLE_SPRINT_MIN_S]

    print("-" * 78)
    print("SENSITIVITY CHECK ON ONE OUTCOME (NOT PART OF THE DECLARED FAMILY)")
    print("-" * 78)
    print(
        "Re-run of the 20 m sprint comparison with the single implausible "
        "timing-gate"
    )
    print(
        "value excluded. This is a robustness check only. It is not adjusted, "
        "it does"
    )
    print("not enter the family, and it produces no inferential verdict.")
    print()

    for _, record in suspect.iterrows():
        print(
            f"Excluded record: {record['player_id']} "
            f"({record[GROUP_COL]}), {sprint_column} = "
            f"{record[sprint_column]:.2f} s"
        )
    print(f"Records excluded: {len(suspect)}")
    print()

    sprint_family = next(r for r in rows if r["column"] == sprint_column)
    filtered = data.loc[data[sprint_column] < IMPLAUSIBLE_SPRINT_MIN_S]
    sprint_sensitivity = compare_groups(filtered, sprint_column)

    print(
        f"{'':<26}{'usual':>9}{'neuro':>9}{'diff':>9}{'p raw':>9}"
        f"{'n usual':>10}{'n neuro':>10}"
    )
    print(
        f"{'Family analysis (all data)':<26}"
        f"{sprint_family['mean_usual']:>9.2f}"
        f"{sprint_family['mean_neuromuscular']:>9.2f}"
        f"{sprint_family['difference']:>9.2f}"
        f"{sprint_family['p_raw']:>9.4f}"
        f"{sprint_family['n_usual']:>10d}"
        f"{sprint_family['n_neuromuscular']:>10d}"
    )
    print(
        f"{'Sensitivity (value out)':<26}"
        f"{sprint_sensitivity['mean_usual']:>9.2f}"
        f"{sprint_sensitivity['mean_neuromuscular']:>9.2f}"
        f"{sprint_sensitivity['difference']:>9.2f}"
        f"{sprint_sensitivity['p_raw']:>9.4f}"
        f"{sprint_sensitivity['n_usual']:>10d}"
        f"{sprint_sensitivity['n_neuromuscular']:>10d}"
    )
    print()
    print(
        "The sprint conclusion reported by the study remains the one from the "
        "adjusted"
    )
    print(
        f"family analysis: p adjusted = {sprint_family['p_adjusted']:.4f}, "
        f"{sprint_family['verdict']}."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()
