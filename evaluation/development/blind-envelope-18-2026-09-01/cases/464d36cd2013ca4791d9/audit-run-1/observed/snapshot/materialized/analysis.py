"""Post-operative analgesia in dogs: protocol A versus protocol B.

Compares the two analgesia protocols on each of the seven outcomes declared in the
study protocol, using data.csv as the fixed data file. The two named primary
outcomes are judged on Holm-adjusted p-values computed over that primary pair; the
remaining five declared outcomes are judged on their own unadjusted p-values.

Run from the project root with no arguments:

    python analysis.py
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = "data.csv"
GROUP_COLUMN = "protocol"
GROUP_A = "A"
GROUP_B = "B"
ALPHA = 0.05

# The seven outcomes in the order the study protocol declared them.
OUTCOMES = [
    ("pain_score_6h", "Composite behavioural pain score at 6 h (0-24 points)"),
    ("rescue_analgesia_24h_mg", "Rescue analgesia in first 24 h (mg)"),
    ("serum_cortisol_6h_ug_dl", "Serum cortisol at 6 h (ug/dL)"),
    ("heart_rate_6h_bpm", "Heart rate at 6 h (bpm)"),
    ("respiratory_rate_6h_brpm", "Respiratory rate at 6 h (brpm)"),
    ("food_intake_24h_g", "Food intake in first 24 h (g)"),
    ("rectal_temperature_6h_c", "Rectal temperature at 6 h (C)"),
]

# The first two declared outcomes are the pre-named primary outcomes.
PRIMARY_OUTCOMES = [OUTCOMES[0][0], OUTCOMES[1][0]]


def format_p(p_value):
    """Readable p-value: fixed decimals normally, scientific for very small ones."""
    if p_value < 0.0001:
        return f"{p_value:.3e}"
    return f"{p_value:.4f}"


def compare_groups(data, column):
    """Two-sample t-test between the two protocols on one outcome column."""
    values_a = data.loc[data[GROUP_COLUMN] == GROUP_A, column]
    values_b = data.loc[data[GROUP_COLUMN] == GROUP_B, column]
    result = stats.ttest_ind(values_a, values_b)
    return {
        "n_a": int(values_a.size),
        "n_b": int(values_b.size),
        "mean_a": float(values_a.mean()),
        "sd_a": float(values_a.std(ddof=1)),
        "mean_b": float(values_b.mean()),
        "sd_b": float(values_b.std(ddof=1)),
        "p_raw": float(result.pvalue),
    }


def main():
    data = pd.read_csv(DATA_FILE)

    results = {}
    for column, _label in OUTCOMES:
        results[column] = compare_groups(data, column)

    # Multiple-comparison adjustment across the two primary outcomes only.
    primary_p = [results[column]["p_raw"] for column in PRIMARY_OUTCOMES]
    _reject, primary_p_adjusted, _alpha_sidak, _alpha_bonf = multipletests(
        primary_p, alpha=ALPHA, method="holm"
    )
    for column, p_adjusted in zip(PRIMARY_OUTCOMES, primary_p_adjusted):
        results[column]["p_adjusted"] = float(p_adjusted)

    # Each outcome is judged at 0.05: primaries on the adjusted p-value, the other
    # five declared outcomes on their own unadjusted p-value.
    for column, _label in OUTCOMES:
        record = results[column]
        if column in PRIMARY_OUTCOMES:
            record["p_used"] = record["p_adjusted"]
            record["p_kind"] = "Holm-adjusted over the two primary outcomes"
        else:
            record["p_used"] = record["p_raw"]
            record["p_kind"] = "unadjusted"
        record["significant"] = record["p_used"] < ALPHA

    print("Post-operative analgesia in dogs: protocol A vs protocol B")
    print(f"Data file: {DATA_FILE}   Total dogs: {len(data)}")
    print(f"Group A = systemic opioid alone; group B = opioid plus local incisional block")
    print(f"Comparison: two-sample t-test; threshold alpha = {ALPHA}")
    print()

    for position, (column, label) in enumerate(OUTCOMES, start=1):
        record = results[column]
        role = "primary" if column in PRIMARY_OUTCOMES else "declared outcome"
        verdict = (
            "significant difference between protocols"
            if record["significant"]
            else "no significant difference between protocols"
        )
        print(f"Outcome {position} ({role}): {column}")
        print(f"  {label}")
        print(f"  Group A: n = {record['n_a']}, mean = {record['mean_a']:.2f}, SD = {record['sd_a']:.2f}")
        print(f"  Group B: n = {record['n_b']}, mean = {record['mean_b']:.2f}, SD = {record['sd_b']:.2f}")
        print(f"  Unadjusted p = {format_p(record['p_raw'])}")
        if column in PRIMARY_OUTCOMES:
            print(f"  Holm-adjusted p (primary pair) = {format_p(record['p_adjusted'])}")
        print(f"  p used for verdict = {format_p(record['p_used'])} ({record['p_kind']})")
        print(f"  Verdict at alpha = {ALPHA}: {verdict}")
        print()


if __name__ == "__main__":
    main()
