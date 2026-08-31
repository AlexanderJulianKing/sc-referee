"""Analysis for the twelve-month juvenile pearl mussel rearing substrate trial.

Compares sand-reared and gravel-reared juveniles on the five pre-declared
outcomes. The five outcomes form one declared family, and the family-wise error
rate is controlled with a Sidak correction computed by hand in this script.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "mussel_rearing_data.csv"

GROUP_COLUMN = "substrate"
GROUP_A = "sand"
GROUP_B = "gravel"

# The declared outcome family, in the order fixed in the rearing protocol.
DECLARED_OUTCOMES = [
    "shell_length_increment_mm",
    "wet_mass_gain_g",
    "condition_index_pct",
    "foot_glycogen_mg_per_g",
    "clearance_rate_l_per_h",
]

FAMILY_WISE_ALPHA = 0.05


def sidak_threshold(family_wise_alpha, family_size):
    """Sidak per-comparison threshold: 1 - (1 - alpha) ** (1 / family_size)."""
    return 1.0 - (1.0 - family_wise_alpha) ** (1.0 / family_size)


def main():
    data = pd.read_csv(DATA_FILE)

    # Family size is taken from the declared outcome list, not typed in as a
    # bare constant.
    family_size = len(DECLARED_OUTCOMES)
    threshold = sidak_threshold(FAMILY_WISE_ALPHA, family_size)

    sand = data[data[GROUP_COLUMN] == GROUP_A]
    gravel = data[data[GROUP_COLUMN] == GROUP_B]

    print("Juvenile pearl mussel rearing substrate trial")
    print("Data file: {}".format(DATA_FILE))
    print("Mussels: {} total, {} {}, {} {}".format(
        len(data), len(sand), GROUP_A, len(gravel), GROUP_B))
    print()
    print("Declared outcome family (in order): {}".format(
        ", ".join(DECLARED_OUTCOMES)))
    print("Family-wise level: {:.2f}".format(FAMILY_WISE_ALPHA))
    print("Family size: {}".format(family_size))
    print("Sidak per-comparison threshold = 1 - (1 - {:.2f}) ** (1 / {}) "
          "= {:.6f}".format(FAMILY_WISE_ALPHA, family_size, threshold))
    print()

    for outcome in DECLARED_OUTCOMES:
        sand_values = sand[outcome]
        gravel_values = gravel[outcome]

        result = stats.ttest_ind(sand_values, gravel_values)
        p_value = float(result.pvalue)
        verdict = "significant" if p_value < threshold else "not significant"

        print(outcome)
        print("  mean {}   = {:.4f}".format(GROUP_A, sand_values.mean()))
        print("  mean {} = {:.4f}".format(GROUP_B, gravel_values.mean()))
        print("  two-sample t-test p-value = {:.6f}".format(p_value))
        print("  Sidak threshold = {:.6f}".format(threshold))
        print("  verdict: {}".format(verdict))
        print()


if __name__ == "__main__":
    main()
