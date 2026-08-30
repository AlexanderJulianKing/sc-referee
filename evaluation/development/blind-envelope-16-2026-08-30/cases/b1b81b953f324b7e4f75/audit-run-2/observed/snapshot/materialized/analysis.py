"""Week-eight comparison of two emollient regimens in childhood atopic dermatitis.

The protocol declares five outcomes as a single family. Each outcome is compared
between the two regimens with a two-sample t-test; the complete set of five raw
p-values is then adjusted together with the Holm step-down correction, which
controls the family-wise error rate at 0.05. Every inferential verdict is taken
from the adjusted values.

A separate, clearly labelled sensitivity re-run repeats the transepidermal water
loss comparison with the single implausibly high probe reading excluded. That
re-run is a robustness check on one questionable measurement, not an inferential
result, and it changes no verdict.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = "eczema_trial.csv"
GROUP_COL = "emollient"
GROUP_A = "ointment"
GROUP_B = "lotion"
ALPHA = 0.05

# Declared outcome family, in the protocol's fixed order.
OUTCOMES = [
    ("severity_pts", "Eczema severity index (points, 0-72)"),
    ("itch_pts", "Worst itch in past 24 h (points, 0-10)"),
    ("tewl_gm2h", "Transepidermal water loss (g/m^2/h)"),
    ("sleep_nights", "Nights with disturbed sleep (0-7)"),
    ("steroid_g", "Topical corticosteroid used (g)"),
]

SENSITIVITY_OUTCOME = "tewl_gm2h"


def two_sample_test(frame, column):
    """Two-sample t-test between the two emollient groups on one outcome."""
    a = frame.loc[frame[GROUP_COL] == GROUP_A, column]
    b = frame.loc[frame[GROUP_COL] == GROUP_B, column]
    result = stats.ttest_ind(a, b)
    return a.mean(), b.mean(), len(a), len(b), float(result.pvalue)


def main():
    data = pd.read_csv(DATA_FILE)

    print("=" * 78)
    print("EMOLLIENT TRIAL: WEEK-EIGHT COMPARISON OF TWO REGIMENS")
    print("=" * 78)
    print(f"Rows (children): {len(data)}")
    print(f"Group sizes: {GROUP_A} = {int((data[GROUP_COL] == GROUP_A).sum())}, "
          f"{GROUP_B} = {int((data[GROUP_COL] == GROUP_B).sum())}")
    print(f"Missing values in file: {int(data.isna().sum().sum())}")
    print()

    # ---- Primary inference over the declared family of five outcomes ----
    rows = []
    for column, label in OUTCOMES:
        mean_a, mean_b, n_a, n_b, p_raw = two_sample_test(data, column)
        rows.append({
            "column": column,
            "label": label,
            "mean_ointment": mean_a,
            "mean_lotion": mean_b,
            "n_ointment": n_a,
            "n_lotion": n_b,
            "p_raw": p_raw,
        })

    raw_p = [row["p_raw"] for row in rows]
    reject, p_adj, _, _ = multipletests(raw_p, alpha=ALPHA, method="holm")
    for row, adjusted, significant in zip(rows, p_adj, reject):
        row["p_adj"] = float(adjusted)
        row["significant"] = bool(significant)

    print("-" * 78)
    print("DECLARED OUTCOME FAMILY (5 outcomes, Holm-adjusted, family-wise alpha = 0.05)")
    print("-" * 78)
    header = (f"{'Outcome':<38}{'Ointment':>10}{'Lotion':>10}"
              f"{'raw p':>11}{'adj p':>11}  Verdict")
    print(header)
    for row in rows:
        verdict = "significant" if row["significant"] else "not significant"
        print(f"{row['label']:<38}"
              f"{row['mean_ointment']:>10.2f}"
              f"{row['mean_lotion']:>10.2f}"
              f"{row['p_raw']:>11.4f}"
              f"{row['p_adj']:>11.4f}"
              f"  {verdict}")
    print()
    print("All verdicts above are taken from the Holm-adjusted values, not the raw ones.")
    print()

    # ---- Sensitivity check (NOT an inferential result) ----
    main_row = next(row for row in rows if row["column"] == SENSITIVITY_OUTCOME)
    dropped_index = data[SENSITIVITY_OUTCOME].idxmax()
    dropped = data.loc[dropped_index]
    trimmed = data.drop(index=dropped_index)
    s_mean_a, s_mean_b, s_n_a, s_n_b, s_p_raw = two_sample_test(trimmed, SENSITIVITY_OUTCOME)

    print("-" * 78)
    print("SENSITIVITY CHECK (NOT AN INFERENTIAL RESULT, CHANGES NO VERDICT)")
    print("-" * 78)
    print(f"Outcome re-run: {SENSITIVITY_OUTCOME}")
    print(f"Excluded reading: {dropped['child_id']} ({dropped[GROUP_COL]}), "
          f"{SENSITIVITY_OUTCOME} = {dropped[SENSITIVITY_OUTCOME]} "
          f"(single implausibly high probe reading)")
    print(f"Group sizes after exclusion: {GROUP_A} = {s_n_a}, {GROUP_B} = {s_n_b}")
    print()
    print(f"{'Version':<28}{'Ointment':>10}{'Lotion':>10}{'raw p':>11}{'adj p':>11}")
    print(f"{'Main (all 66 children)':<28}"
          f"{main_row['mean_ointment']:>10.2f}"
          f"{main_row['mean_lotion']:>10.2f}"
          f"{main_row['p_raw']:>11.4f}"
          f"{main_row['p_adj']:>11.4f}")
    print(f"{'Re-run (reading excluded)':<28}"
          f"{s_mean_a:>10.2f}"
          f"{s_mean_b:>10.2f}"
          f"{s_p_raw:>11.4f}"
          f"{'n/a':>11}")
    print()
    print("The re-run is a robustness check on one questionable measurement. It is not")
    print("part of the declared family, is not adjusted, and the water loss verdict")
    print(f"remains the Holm-adjusted main result "
          f"({'significant' if main_row['significant'] else 'not significant'}).")
    print("=" * 78)


if __name__ == "__main__":
    main()
