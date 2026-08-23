"""Breakfast type and mid-morning glucose peak: analysis script.

Reads the person-morning data file, compares peak glucose between the
refined-cereal and high-protein breakfast arms with an independent
two-sample test of the difference in means, and prints the results.
"""

import math

import pandas as pd
from scipy import stats

DATA_FILE = "breakfast_glucose_mornings.csv"
OUTCOME = "peak_glucose_mmol_l"
ARM = "breakfast_arm"
COMPARISON_ARM = "refined_cereal"
INTERVENTION_ARM = "high_protein"


def load_data(path=DATA_FILE):
    """Read the person-morning table."""
    data = pd.read_csv(path)
    expected = [
        "volunteer_code",
        "breakfast_arm",
        "study_day",
        "fasting_glucose_mmol_l",
        "peak_glucose_mmol_l",
    ]
    if list(data.columns) != expected:
        raise ValueError(f"unexpected columns: {list(data.columns)}")
    if data.isna().any().any():
        raise ValueError("data file contains missing cells")
    return data


def describe_arm(values):
    """Mean, standard deviation, standard error and range for one arm."""
    n = int(values.size)
    return {
        "n": n,
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "se": float(values.std(ddof=1) / math.sqrt(n)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def main():
    data = load_data()

    # Every morning in the table enters the comparison as a separate
    # observation, so the analysed sample size is the number of mornings.
    cereal = data.loc[data[ARM] == COMPARISON_ARM, OUTCOME]
    protein = data.loc[data[ARM] == INTERVENTION_ARM, OUTCOME]

    total_mornings = int(data.shape[0])
    cereal_stats = describe_arm(cereal)
    protein_stats = describe_arm(protein)

    # Independent two-sample t-test on the difference in means (Welch,
    # which does not assume the two arms share a variance).
    result = stats.ttest_ind(cereal, protein, equal_var=False)
    t_stat = float(result.statistic)
    p_value = float(result.pvalue)

    difference = cereal_stats["mean"] - protein_stats["mean"]
    se_difference = math.sqrt(cereal_stats["se"] ** 2 + protein_stats["se"] ** 2)

    # Welch-Satterthwaite degrees of freedom, for the confidence interval.
    v_cereal = cereal_stats["sd"] ** 2 / cereal_stats["n"]
    v_protein = protein_stats["sd"] ** 2 / protein_stats["n"]
    df = (v_cereal + v_protein) ** 2 / (
        v_cereal**2 / (cereal_stats["n"] - 1)
        + v_protein**2 / (protein_stats["n"] - 1)
    )
    t_crit = float(stats.t.ppf(0.975, df))
    ci_low = difference - t_crit * se_difference
    ci_high = difference + t_crit * se_difference

    print("Breakfast type and mid-morning peak glucose")
    print("=" * 52)
    print(f"Data file: {DATA_FILE}")
    print(f"Mornings analysed (sample size, n): {total_mornings}")
    print()

    print("Peak glucose by breakfast arm (mmol/L)")
    print("-" * 52)
    header = f"{'arm':<16}{'n':>6}{'mean':>9}{'SD':>8}{'SE':>8}{'range':>13}"
    print(header)
    for label, s in (
        ("refined_cereal", cereal_stats),
        ("high_protein", protein_stats),
    ):
        span = f"{s['min']:.1f}-{s['max']:.1f}"
        print(
            f"{label:<16}{s['n']:>6}{s['mean']:>9.2f}"
            f"{s['sd']:>8.2f}{s['se']:>8.3f}{span:>13}"
        )
    print()

    print("Independent two-sample test of the difference in means")
    print("-" * 52)
    print("Test: Welch's independent two-sample t-test")
    print(f"Difference (refined_cereal - high_protein): {difference:.2f} mmol/L")
    print(f"Standard error of the difference:          {se_difference:.3f} mmol/L")
    print(f"95% confidence interval:                   {ci_low:.2f} to {ci_high:.2f} mmol/L")
    print(f"t = {t_stat:.2f}, df = {df:.1f}")
    if p_value < 1e-4:
        print(f"p = {p_value:.3e}")
    else:
        print(f"p = {p_value:.4f}")
    print()

    print("Conclusion")
    print("-" * 52)
    if p_value < 0.05:
        direction = "lower" if difference > 0 else "higher"
        print(
            f"The high-protein breakfast gives a {direction} mid-morning peak "
            f"glucose than the\nrefined-cereal breakfast, by {abs(difference):.2f} mmol/L "
            f"(p = {p_value:.3e}). The breakfast effect\nis statistically significant "
            "at the 5 percent level."
        )
    else:
        print(
            "The two breakfasts do not differ significantly in mid-morning peak "
            f"glucose\n(p = {p_value:.4f})."
        )

    # Fasting glucose, reported as a background description of the sample.
    print()
    print("Fasting glucose, for background (mmol/L)")
    print("-" * 52)
    for label in (COMPARISON_ARM, INTERVENTION_ARM):
        f = data.loc[data[ARM] == label, "fasting_glucose_mmol_l"]
        print(f"{label:<16} mean {f.mean():.2f}   SD {f.std(ddof=1):.2f}")


if __name__ == "__main__":
    main()
