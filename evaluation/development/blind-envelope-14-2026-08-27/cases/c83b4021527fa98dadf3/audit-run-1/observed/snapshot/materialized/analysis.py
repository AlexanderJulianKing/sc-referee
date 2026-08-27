"""Eight-week parallel-group walnut vs. cracker feeding study: lipid panel analysis.

Reads lipid_panel.csv, compares the walnut and cracker snack groups on each of the five
pre-declared lipid outcomes with Welch's two-sample t-test, and judges every outcome
against a single Sidak per-comparison threshold computed from the declared family size.

Run:  python3 analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "lipid_panel.csv"

GROUP_COLUMN = "snack"
TREATMENT_GROUP = "walnut"
CONTROL_GROUP = "cracker"

# The outcome family declared before recruitment, in the declared order.
# Every one of these outcomes is tested, and every one of them is counted in the
# family size that sets the multiplicity threshold below.
DECLARED_OUTCOMES = [
    ("ldl_c_mmol_per_l", "LDL cholesterol", "mmol/L"),
    ("hdl_c_mmol_per_l", "HDL cholesterol", "mmol/L"),
    ("triglycerides_mmol_per_l", "Fasting triglycerides", "mmol/L"),
    ("total_c_mmol_per_l", "Total cholesterol", "mmol/L"),
    ("apo_b_g_per_l", "Apolipoprotein B", "g/L"),
]

# ---------------------------------------------------------------------------
# Multiplicity control: Sidak per-comparison threshold, worked out here by hand.
#
#   FAMILY_SIZE          = number of declared outcomes tested  = 5
#   FAMILY_WISE_ALPHA    = conventional family-wise error rate = 0.05
#
# Under the Sidak correction the probability of no false positive anywhere in the
# family is (1 - alpha_pc) ** FAMILY_SIZE, and we require that to equal
# 1 - FAMILY_WISE_ALPHA.  Solving for the per-comparison threshold gives
#
#   alpha_pc = 1 - (1 - FAMILY_WISE_ALPHA) ** (1 / FAMILY_SIZE)
# ---------------------------------------------------------------------------
FAMILY_SIZE = len(DECLARED_OUTCOMES)
FAMILY_WISE_ALPHA = 0.05
SIDAK_PER_COMPARISON_ALPHA = 1.0 - (1.0 - FAMILY_WISE_ALPHA) ** (1.0 / FAMILY_SIZE)


def load_data(path):
    """Load the lipid panel and check the structure the analysis assumes."""
    data = pd.read_csv(path)

    required = ["participant_id", GROUP_COLUMN] + [name for name, _, _ in DECLARED_OUTCOMES]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError("CSV is missing required columns: " + ", ".join(missing))

    if data[required].isna().any().any():
        raise ValueError("CSV contains blank cells in the analysed columns.")

    groups = sorted(data[GROUP_COLUMN].unique())
    if groups != sorted([CONTROL_GROUP, TREATMENT_GROUP]):
        raise ValueError("Unexpected values in the '%s' column: %s" % (GROUP_COLUMN, groups))

    return data


def compare_groups(data, outcome):
    """Welch's two-sample t-test for one outcome: means, difference, p-value."""
    treatment_values = data.loc[data[GROUP_COLUMN] == TREATMENT_GROUP, outcome]
    control_values = data.loc[data[GROUP_COLUMN] == CONTROL_GROUP, outcome]

    result = stats.ttest_ind(treatment_values, control_values, equal_var=False)

    return {
        "outcome": outcome,
        "n_treatment": int(treatment_values.size),
        "n_control": int(control_values.size),
        "mean_treatment": float(treatment_values.mean()),
        "mean_control": float(control_values.mean()),
        "difference": float(treatment_values.mean() - control_values.mean()),
        "p_value": float(result.pvalue),
    }


def main():
    data = load_data(DATA_FILE)

    n_treatment = int((data[GROUP_COLUMN] == TREATMENT_GROUP).sum())
    n_control = int((data[GROUP_COLUMN] == CONTROL_GROUP).sum())

    print("Walnut vs. cracker snack: eight-week parallel-group feeding study")
    print("=" * 78)
    print("Data file: %s" % DATA_FILE.name)
    print("Participants: %d total (%s n=%d, %s n=%d)"
          % (len(data), TREATMENT_GROUP, n_treatment, CONTROL_GROUP, n_control))
    print("Test: Welch's two-sample t-test, two-sided, %s minus %s"
          % (TREATMENT_GROUP, CONTROL_GROUP))
    print()
    print("Multiplicity control (Sidak)")
    print("-" * 78)
    print("  declared family size          : %d" % FAMILY_SIZE)
    print("  family-wise alpha             : %.4f" % FAMILY_WISE_ALPHA)
    print("  alpha_pc = 1 - (1 - %.2f) ** (1 / %d)" % (FAMILY_WISE_ALPHA, FAMILY_SIZE))
    print("  Sidak per-comparison threshold: %.6f" % SIDAK_PER_COMPARISON_ALPHA)
    print("  Every one of the %d declared outcomes is judged against this one threshold."
          % FAMILY_SIZE)
    print()

    results = [compare_groups(data, name) for name, _, _ in DECLARED_OUTCOMES]

    header = "%-32s %8s %8s %8s %10s  %s" % (
        "Outcome (units)", "Walnut", "Cracker", "Diff", "p-value", "Verdict")
    print("Results, in the declared order")
    print("-" * 78)
    print(header)
    print("-" * 78)

    for (name, label, units), result in zip(DECLARED_OUTCOMES, results):
        significant = result["p_value"] < SIDAK_PER_COMPARISON_ALPHA
        verdict = "significant" if significant else "not significant"
        print("%-32s %8.3f %8.3f %8.3f %10.5f  %s" % (
            "%s (%s)" % (label, units),
            result["mean_treatment"],
            result["mean_control"],
            result["difference"],
            result["p_value"],
            verdict,
        ))

    print("-" * 78)
    n_significant = sum(1 for r in results if r["p_value"] < SIDAK_PER_COMPARISON_ALPHA)
    print("Outcomes below the Sidak threshold of %.6f: %d of %d."
          % (SIDAK_PER_COMPARISON_ALPHA, n_significant, FAMILY_SIZE))
    print("'significant' means p < %.6f; 'not significant' means p >= %.6f."
          % (SIDAK_PER_COMPARISON_ALPHA, SIDAK_PER_COMPARISON_ALPHA))


if __name__ == "__main__":
    main()
