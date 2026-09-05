"""Compare Adelie penguin chick condition between the near and far sub-colonies.

Reads penguin_chick_condition.csv from the project root and compares the two
sub-colonies on each of the four pre-declared condition outcomes, using the same
two-sample significance test (Welch's two-sample t-test) for every outcome.

Each outcome answers its own biological question, so each comparison is written
out as its own visible step, in the declared order, and each one is judged at the
conventional 0.05 threshold.
"""

import pandas as pd
from scipy import stats

ALPHA = 0.05
CSV_PATH = "penguin_chick_condition.csv"


def report_outcome(number, column, label, unit, near_values, far_values):
    """Run and print one two-sample comparison for a single outcome."""
    n_near = len(near_values)
    n_far = len(far_values)
    mean_near = near_values.mean()
    mean_far = far_values.mean()

    t_statistic, p_value = stats.ttest_ind(near_values, far_values, equal_var=False)

    verdict = "SIGNIFICANT" if p_value < ALPHA else "NOT SIGNIFICANT"

    print(f"Outcome {number}: {label} ({column}, {unit})")
    print(f"  n: near = {n_near}, far = {n_far}")
    print(f"  mean near = {mean_near:.3f} {unit}")
    print(f"  mean far  = {mean_far:.3f} {unit}")
    print(f"  difference (near - far) = {mean_near - mean_far:.3f} {unit}")
    print(f"  Welch t = {t_statistic:.4f}")
    print(f"  p-value = {p_value:.4f}")
    print(f"  verdict at alpha = {ALPHA}: {verdict}")
    print()


def main():
    data = pd.read_csv(CSV_PATH)

    near = data[data["sub_colony"] == "near"]
    far = data[data["sub_colony"] == "far"]

    print("Adelie penguin chick condition: near vs far sub-colony")
    print(f"Chicks read from {CSV_PATH}: {len(data)}")
    print("Test used for every outcome: Welch's two-sample t-test (two-sided)")
    print(f"Significance threshold for every outcome: alpha = {ALPHA}")
    print()

    # Outcome 1 of the declared family: body mass.
    report_outcome(
        1,
        "body_mass_g",
        "Body mass",
        "g",
        near["body_mass_g"],
        far["body_mass_g"],
    )

    # Outcome 2 of the declared family: flipper length.
    report_outcome(
        2,
        "flipper_length_mm",
        "Flipper length",
        "mm",
        near["flipper_length_mm"],
        far["flipper_length_mm"],
    )

    # Outcome 3 of the declared family: haemoglobin.
    report_outcome(
        3,
        "haemoglobin_g_dl",
        "Blood haemoglobin",
        "g/dL",
        near["haemoglobin_g_dl"],
        far["haemoglobin_g_dl"],
    )

    # Outcome 4 of the declared family: corticosterone.
    report_outcome(
        4,
        "corticosterone_ng_ml",
        "Plasma corticosterone",
        "ng/mL",
        near["corticosterone_ng_ml"],
        far["corticosterone_ng_ml"],
    )


if __name__ == "__main__":
    main()
