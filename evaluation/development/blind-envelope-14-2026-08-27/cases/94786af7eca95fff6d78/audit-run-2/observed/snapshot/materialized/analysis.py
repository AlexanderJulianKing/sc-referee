"""Room attendant workload study: solo vs paired work-organisation schemes.

Reads room_attendant_workload.csv and compares the two work schemes on each of
the eight pre-declared outcomes with a two-sample Welch t-test, reporting the
group means, the solo-minus-paired difference, and the p-value.

Outcomes 1, 2, 3 and 5 in the declared order are the team's headline symptom and
effort measures. Their p-values are corrected by hand: each is multiplied by the
number of comparisons and capped at 1.0, then judged against 0.05. The remaining
declared outcomes are judged on their raw p-values against 0.05.
"""

import pandas as pd
from scipy import stats

CSV_PATH = "room_attendant_workload.csv"
ALPHA = 0.05

# The eight pre-declared outcomes, in the declared order.
OUTCOMES = [
    ("borg_exertion", "Perceived exertion (Borg 6-20)"),
    ("neck_shoulder_vas_mm", "Neck/shoulder pain (VAS mm)"),
    ("wrist_hand_vas_mm", "Wrist/hand pain (VAS mm)"),
    ("rooms_per_shift", "Rooms cleaned per shift"),
    ("mean_heart_rate_bpm", "Mean heart rate (bpm)"),
    ("trunk_flexion_over60_pct", "Trunk flexion >60 deg (% of shift)"),
    ("step_count", "Step count"),
    ("recovery_need_score", "Need for recovery (0-100)"),
]

# Headline symptom and effort measures: declared outcomes 1, 2, 3 and 5.
CORRECTED_OUTCOMES = [
    "borg_exertion",
    "neck_shoulder_vas_mm",
    "wrist_hand_vas_mm",
    "mean_heart_rate_bpm",
]


def load_data(path=CSV_PATH):
    """Load the attendant table and check it is complete and correctly sized."""
    df = pd.read_csv(path)

    missing = [c for c, _ in OUTCOMES if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing declared outcome columns: {missing}")
    if df[[c for c, _ in OUTCOMES]].isna().any().any():
        raise ValueError("CSV contains blank outcome cells")
    if df["worker_id"].duplicated().any():
        raise ValueError("CSV contains duplicate worker_id values")

    schemes = sorted(df["work_scheme"].unique())
    if schemes != ["paired", "solo"]:
        raise ValueError(f"Expected exactly the schemes solo and paired, found {schemes}")

    return df


def compare(df, column):
    """Welch two-sample t-test of solo against paired for one outcome column."""
    solo = df.loc[df["work_scheme"] == "solo", column].astype(float)
    paired = df.loc[df["work_scheme"] == "paired", column].astype(float)
    t_stat, p_value = stats.ttest_ind(solo, paired, equal_var=False)
    return {
        "mean_solo": solo.mean(),
        "mean_paired": paired.mean(),
        "difference": solo.mean() - paired.mean(),
        "t_stat": t_stat,
        "p_raw": p_value,
    }


def main():
    df = load_data()

    n_solo = int((df["work_scheme"] == "solo").sum())
    n_paired = int((df["work_scheme"] == "paired").sum())

    print("Room attendant workload study: solo vs paired work schemes")
    print(f"Attendants: {len(df)} total, {n_solo} solo, {n_paired} paired")
    print("Test: two-sample Welch t-test (solo minus paired), alpha = 0.05")
    print()

    n_comparisons = len(CORRECTED_OUTCOMES)
    print(
        f"Hand correction applied to the headline outcomes "
        f"({', '.join(CORRECTED_OUTCOMES)}): "
        f"p x {n_comparisons}, capped at 1.0."
    )
    print("Remaining declared outcomes are judged on their raw p-values.")
    print()

    results = []
    for column, label in OUTCOMES:
        res = compare(df, column)
        res["column"] = column
        res["label"] = label

        if column in CORRECTED_OUTCOMES:
            res["p_used"] = min(res["p_raw"] * n_comparisons, 1.0)
            res["p_kind"] = "corrected"
        else:
            res["p_used"] = res["p_raw"]
            res["p_kind"] = "raw"

        res["significant"] = res["p_used"] < ALPHA
        results.append(res)

    header = (
        f"{'#':>2}  {'Outcome':<36} {'Mean solo':>10} {'Mean paired':>12} "
        f"{'Diff':>9} {'p (raw)':>10} {'p (used)':>10} {'Kind':>10} {'Verdict':>16}"
    )
    print(header)
    print("-" * len(header))
    for i, res in enumerate(results, start=1):
        verdict = "significant" if res["significant"] else "not significant"
        print(
            f"{i:>2}  {res['label']:<36} {res['mean_solo']:>10.2f} "
            f"{res['mean_paired']:>12.2f} {res['difference']:>9.2f} "
            f"{res['p_raw']:>10.4f} {res['p_used']:>10.4f} "
            f"{res['p_kind']:>10} {verdict:>16}"
        )
    print()

    print("Per-outcome conclusions:")
    for i, res in enumerate(results, start=1):
        direction = "higher" if res["difference"] > 0 else "lower"
        if res["significant"]:
            sentence = (
                f"solo attendants are {direction} than paired attendants "
                f"({res['p_kind']} p = {res['p_used']:.4f} < {ALPHA})"
            )
        else:
            sentence = (
                f"no difference detected between the schemes "
                f"({res['p_kind']} p = {res['p_used']:.4f} >= {ALPHA})"
            )
        print(f"  {i}. {res['label']}: {sentence}")


if __name__ == "__main__":
    main()
