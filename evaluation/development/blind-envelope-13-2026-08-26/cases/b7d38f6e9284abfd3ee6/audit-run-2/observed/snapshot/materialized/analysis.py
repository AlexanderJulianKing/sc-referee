"""Compare two trail-running midsole types on the five pre-declared outcomes.

Reads trail_midsole_biomechanics.csv from the project root, runs the same
two-sample test on each of the five declared outcomes, then passes the five raw
p-values to the multiple-comparison routine as one family so that the
family-wise error rate is controlled across all five outcomes together.

Every significance verdict below comes from the adjusted p-values, at the
conventional 0.05 threshold. No verdict is taken from a raw p-value.
"""

from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

CSV_NAME = "trail_midsole_biomechanics.csv"
GROUP_COLUMN = "midsole_group"
GROUP_A = "cushioned"
GROUP_B = "standard"
ALPHA = 0.05

# The pre-declared outcome family, in the order given in the study protocol.
OUTCOMES = [
    ("ground_contact_time_ms", "mean ground contact time (ms)"),
    ("vertical_oscillation_cm", "mean vertical oscillation (cm)"),
    ("cadence_steps_per_min", "mean cadence (steps/min)"),
    ("rpe_borg_6_20", "rating of perceived exertion (Borg 6-20)"),
    ("finish_time_s", "5 km finish time (s)"),
]


def main():
    csv_path = Path(__file__).resolve().parent / CSV_NAME
    data = pd.read_csv(csv_path)

    group_a = data[data[GROUP_COLUMN] == GROUP_A]
    group_b = data[data[GROUP_COLUMN] == GROUP_B]

    print(f"Data file: {CSV_NAME}")
    print(f"Rows (runners): {len(data)}")
    print(f"Group sizes: {GROUP_A} n={len(group_a)}, {GROUP_B} n={len(group_b)}")
    print(f"Declared outcome family: {len(OUTCOMES)} outcomes, tested together")
    print()

    raw_p_values = []
    rows = []

    # Step 1: the same two-sample test for every outcome, collecting raw p-values.
    for column, label in OUTCOMES:
        values_a = group_a[column]
        values_b = group_b[column]
        result = stats.ttest_ind(values_a, values_b)

        raw_p_values.append(result.pvalue)
        rows.append(
            {
                "column": column,
                "label": label,
                "n_a": len(values_a),
                "n_b": len(values_b),
                "mean_a": values_a.mean(),
                "mean_b": values_b.mean(),
                "statistic": result.statistic,
                "raw_p": result.pvalue,
            }
        )

        print(f"Outcome: {column} ({label})")
        print(f"  {GROUP_A}: n = {len(values_a)}, mean = {values_a.mean():.3f}")
        print(f"  {GROUP_B}: n = {len(values_b)}, mean = {values_b.mean():.3f}")
        print(f"  two-sample t statistic = {result.statistic:.4f}")
        print(f"  raw p-value = {result.pvalue:.6f}")
        print()

    # Step 2: one call, the whole family of five raw p-values at once, with no
    # method argument, so the routine's own default adjustment is applied.
    reject, adjusted_p_values, _, _ = multipletests(raw_p_values)

    print("Family-wise adjustment across all five declared outcomes together,")
    print("using the multiple-comparison routine's default behaviour")
    print(f"(statsmodels.stats.multitest.multipletests called with the family of "
          f"{len(raw_p_values)} raw p-values and no method argument).")
    print(f"Verdicts use the adjusted p-values at alpha = {ALPHA}.")
    print()

    header = (
        f"{'outcome':<26}{'mean_' + GROUP_A:>16}{'mean_' + GROUP_B:>16}"
        f"{'t':>10}{'raw_p':>12}{'adj_p':>12}  verdict"
    )
    print(header)
    print("-" * len(header))

    for row, adjusted_p, is_rejected in zip(rows, adjusted_p_values, reject):
        verdict = "significant" if is_rejected else "not significant"
        print(
            f"{row['column']:<26}{row['mean_a']:>16.3f}{row['mean_b']:>16.3f}"
            f"{row['statistic']:>10.4f}{row['raw_p']:>12.6f}{adjusted_p:>12.6f}"
            f"  {verdict}"
        )

    print()
    significant = [
        row["column"]
        for row, is_rejected in zip(rows, reject)
        if is_rejected
    ]
    if significant:
        print("Outcomes significant after family-wise adjustment: "
              + ", ".join(significant))
    else:
        print("No outcome is significant after family-wise adjustment.")


if __name__ == "__main__":
    main()
