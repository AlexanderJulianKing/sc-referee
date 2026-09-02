"""Seven-day duckweed growth assay: reference medium vs 10% effluent medium.

Reads the fixed authored data file data.csv and compares the two media on each
of the five outcomes declared in the assay plan, using an independent
two-sample t-test for each outcome.

The family-wise error rate over the five declared outcomes is held at 0.05 by
comparing every p-value against a Sidak per-comparison threshold that is
computed here by hand from the family size.

Run from the project root with no arguments:  python3 analysis.py
"""

import pandas as pd
from scipy import stats

DATA_FILE = "data.csv"
GROUP_COLUMN = "medium"
REFERENCE_GROUP = "reference_medium"
EFFLUENT_GROUP = "effluent_10pct"

# The five outcomes declared in the assay plan, in the declared order.
DECLARED_OUTCOMES = [
    "frond_number_increase",
    "total_frond_area_mm2",
    "chlorophyll_a_ug_per_g",
    "mean_root_length_mm",
    "dry_biomass_mg",
]

# Family-wise error rate held at 0.05 across the whole declared family.
FAMILY_WISE_ALPHA = 0.05

# Family size: the number of declared outcomes, used directly in the Sidak
# arithmetic below.
FAMILY_SIZE = len(DECLARED_OUTCOMES)

# Sidak per-comparison threshold, computed by hand from the family size:
#   alpha_pc = 1 - (1 - alpha_fw) ** (1 / m)
PER_COMPARISON_ALPHA = 1.0 - (1.0 - FAMILY_WISE_ALPHA) ** (1.0 / FAMILY_SIZE)


def main():
    data = pd.read_csv(DATA_FILE)

    reference = data[data[GROUP_COLUMN] == REFERENCE_GROUP]
    effluent = data[data[GROUP_COLUMN] == EFFLUENT_GROUP]

    print("Seven-day duckweed growth assay")
    print("Reference medium vs medium with 10% treated municipal effluent")
    print("Rows read from {}: {}".format(DATA_FILE, len(data)))
    print("")
    print("Multiplicity control (Sidak, computed here):")
    print("  family-wise level (alpha_fw)      = {:.4f}".format(FAMILY_WISE_ALPHA))
    print("  family size (m, declared outcomes) = {}".format(FAMILY_SIZE))
    print(
        "  alpha_pc = 1 - (1 - {:.2f}) ** (1 / {}) = {:.6f}".format(
            FAMILY_WISE_ALPHA, FAMILY_SIZE, PER_COMPARISON_ALPHA
        )
    )
    print("  per-comparison significance threshold = {:.6f}".format(PER_COMPARISON_ALPHA))
    print("")

    for position, outcome in enumerate(DECLARED_OUTCOMES, start=1):
        reference_values = reference[outcome]
        effluent_values = effluent[outcome]

        t_statistic, p_value = stats.ttest_ind(reference_values, effluent_values)

        significant = p_value < PER_COMPARISON_ALPHA
        verdict = (
            "SIGNIFICANT at the Sidak per-comparison threshold"
            if significant
            else "not significant at the Sidak per-comparison threshold"
        )

        print("Outcome {} of {}: {}".format(position, FAMILY_SIZE, outcome))
        print(
            "  {:<16} n = {:2d}   mean = {:9.3f}   sd = {:8.3f}".format(
                REFERENCE_GROUP + ":",
                len(reference_values),
                reference_values.mean(),
                reference_values.std(ddof=1),
            )
        )
        print(
            "  {:<16} n = {:2d}   mean = {:9.3f}   sd = {:8.3f}".format(
                EFFLUENT_GROUP + ":",
                len(effluent_values),
                effluent_values.mean(),
                effluent_values.std(ddof=1),
            )
        )
        print("  two-sample t-test: t = {:.4f}".format(t_statistic))
        print("  p-value                              = {:.6g}".format(p_value))
        print("  compared against threshold           = {:.6f}".format(PER_COMPARISON_ALPHA))
        print("  verdict: {}".format(verdict))
        print("")


if __name__ == "__main__":
    main()
