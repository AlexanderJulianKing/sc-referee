"""Compare two disinfectant application methods on the five declared outcomes.

Reads data.csv, runs one two-group comparison per declared outcome, then controls the
family error across the whole declared family of five outcomes in a single step by passing
all five raw p-values through statsmodels' multiple-comparisons adjustment routine with no
method argument, accepting whatever adjustment that routine applies by default.

Every verdict below is read off the adjusted value at the conventional 0.05 threshold.
Raw p-values are printed for reference only and are never used to judge an outcome.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = "data.csv"
GROUP_COLUMN = "application_method"
GROUP_A = "trigger_spray"
GROUP_B = "pre_soaked_wipes"
ALPHA = 0.05

# The five outcomes, in the order they were declared in the monitoring plan.
DECLARED_OUTCOMES = [
    ("fev1_l", "Forced expiratory volume in 1 s (L)"),
    ("feno_ppb", "Fractional exhaled nitric oxide (ppb)"),
    ("airway_symptom_score", "Airway symptom score (0-20)"),
    ("peak_tvoc_mg_m3", "Peak airborne TVOC (mg/m3)"),
    ("eye_skin_irritation_score", "Eye and skin irritation score (0-10)"),
]


def main():
    data = pd.read_csv(DATA_FILE)

    group_a = data[data[GROUP_COLUMN] == GROUP_A]
    group_b = data[data[GROUP_COLUMN] == GROUP_B]

    # Pass 1: one two-group comparison per declared outcome, collecting descriptive
    # statistics and the raw p-values. No verdict is reached in this pass.
    results = []
    raw_p_values = []
    for column, label in DECLARED_OUTCOMES:
        values_a = group_a[column]
        values_b = group_b[column]
        test = stats.ttest_ind(values_a, values_b, equal_var=False)
        results.append(
            {
                "column": column,
                "label": label,
                "n_a": len(values_a),
                "n_b": len(values_b),
                "mean_a": values_a.mean(),
                "sd_a": values_a.std(ddof=1),
                "mean_b": values_b.mean(),
                "sd_b": values_b.std(ddof=1),
                "raw_p": test.pvalue,
            }
        )
        raw_p_values.append(test.pvalue)

    # Pass 2: control the family error across the whole declared family in one step.
    # No method is named, so the routine's own default adjustment is used.
    reject, adjusted_p_values, _, _ = multipletests(raw_p_values)

    print("Two disinfectant application methods compared on five declared outcomes")
    print("Group A: %s" % GROUP_A)
    print("Group B: %s" % GROUP_B)
    print(
        "All %d declared outcomes adjusted together as one family; "
        "verdicts use the adjusted value at alpha = %.2f."
        % (len(DECLARED_OUTCOMES), ALPHA)
    )
    print()

    for result, adjusted_p, rejected in zip(results, adjusted_p_values, reject):
        verdict = "DIFFERENT" if adjusted_p < ALPHA else "NO DIFFERENCE"
        print("%s [%s]" % (result["label"], result["column"]))
        print(
            "  %-17s n = %2d   mean = %8.3f   sd = %7.3f"
            % (GROUP_A, result["n_a"], result["mean_a"], result["sd_a"])
        )
        print(
            "  %-17s n = %2d   mean = %8.3f   sd = %7.3f"
            % (GROUP_B, result["n_b"], result["mean_b"], result["sd_b"])
        )
        print("  raw p-value      = %.6g" % result["raw_p"])
        print("  adjusted value   = %.6g" % adjusted_p)
        print("  verdict          = %s (adjusted value vs %.2f)" % (verdict, ALPHA))
        print()


if __name__ == "__main__":
    main()
