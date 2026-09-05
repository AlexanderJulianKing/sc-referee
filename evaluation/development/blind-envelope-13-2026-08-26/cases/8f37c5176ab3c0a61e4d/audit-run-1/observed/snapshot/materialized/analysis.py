"""Two-stage screen-and-confirm analysis of the school-based screen time cohort.

Stage one screens all six pre-declared outcomes in the discovery half.
Stage two tests only the outcomes carried forward, in the validation half,
at a significance level adjusted for how many outcomes were carried forward.

The study's conclusions come only from the validation stage. Discovery-half
results are screening output and are never reported as confirmed findings.

Run from the project root:

    python3 analysis.py
"""

import pandas as pd
from scipy import stats

DATA_FILE = "screen_time_cohort.csv"

GROUP_COLUMN = "screen_time_group"
HALF_COLUMN = "analysis_half"

HIGH_GROUP = "high"
LOW_GROUP = "low"

DISCOVERY_HALF = "discovery"
VALIDATION_HALF = "validation"

# The six outcomes in the order they were declared in the analysis plan.
OUTCOMES = [
    ("bmi_z_score", "BMI z-score", "z-score"),
    ("waist_circumference_cm", "Waist circumference", "cm"),
    ("fasting_insulin_miu_l", "Fasting insulin", "mIU/L"),
    ("fasting_triglycerides_mmol_l", "Fasting triglycerides", "mmol/L"),
    ("hdl_cholesterol_mmol_l", "HDL cholesterol", "mmol/L"),
    ("alt_u_l", "Alanine aminotransferase", "U/L"),
]

# Stage one screening threshold, applied to the unadjusted discovery-half
# p-value of each of the six declared outcomes.
SCREENING_ALPHA = 0.10

# Stage two family-wise level, divided by the number of outcomes carried
# forward into the validation stage.
CONFIRMATORY_ALPHA = 0.05

SEPARATOR = "=" * 78


def two_sample_test(half_frame, outcome_column):
    """Welch's two-sample t-test comparing high vs low screen time.

    The same test is used for every outcome in both stages.
    """
    high_values = half_frame.loc[
        half_frame[GROUP_COLUMN] == HIGH_GROUP, outcome_column
    ].astype(float)
    low_values = half_frame.loc[
        half_frame[GROUP_COLUMN] == LOW_GROUP, outcome_column
    ].astype(float)

    result = stats.ttest_ind(high_values, low_values, equal_var=False)

    return {
        "n_high": int(high_values.size),
        "n_low": int(low_values.size),
        "mean_high": float(high_values.mean()),
        "mean_low": float(low_values.mean()),
        "sd_high": float(high_values.std(ddof=1)),
        "sd_low": float(low_values.std(ddof=1)),
        "difference": float(high_values.mean() - low_values.mean()),
        "t_statistic": float(result.statistic),
        "p_value": float(result.pvalue),
    }


def print_result_row(label, unit, result, decision):
    print(
        "  {label:<28} {unit:<8} {mean_high:>8.3f} {mean_low:>8.3f} "
        "{difference:>+9.3f} {t_statistic:>8.3f} {p_value:>9.4f}  {decision}".format(
            label=label,
            unit=unit,
            decision=decision,
            **result
        )
    )


def print_header():
    print(
        "  {:<28} {:<8} {:>8} {:>8} {:>9} {:>8} {:>9}  {}".format(
            "Outcome", "Unit", "High", "Low", "Diff", "t", "p", "Decision"
        )
    )
    print("  " + "-" * 74)


def main():
    cohort = pd.read_csv(DATA_FILE)

    discovery = cohort[cohort[HALF_COLUMN] == DISCOVERY_HALF]
    validation = cohort[cohort[HALF_COLUMN] == VALIDATION_HALF]

    print(SEPARATOR)
    print("SCREEN TIME COHORT: TWO-STAGE SCREEN-AND-CONFIRM ANALYSIS")
    print(SEPARATOR)
    print("Data file:            {}".format(DATA_FILE))
    print("Adolescents:          {}".format(len(cohort)))
    print(
        "Screen time groups:   {} high, {} low".format(
            int((cohort[GROUP_COLUMN] == HIGH_GROUP).sum()),
            int((cohort[GROUP_COLUMN] == LOW_GROUP).sum()),
        )
    )
    print(
        "Analysis halves:      {} discovery, {} validation".format(
            len(discovery), len(validation)
        )
    )
    print("Test used throughout: Welch's two-sample t-test (high minus low)")
    print("Declared outcomes:    {}".format(len(OUTCOMES)))
    print()

    print(SEPARATOR)
    print("STAGE ONE - SCREENING (DISCOVERY HALF ONLY)")
    print(SEPARATOR)
    print(
        "Screening rule: an outcome is carried forward to stage two if its "
        "unadjusted"
    )
    print(
        "                discovery-half p-value is below {:.2f}. All six "
        "declared".format(SCREENING_ALPHA)
    )
    print(
        "                outcomes are screened. Screening results are not "
        "findings."
    )
    print(
        "Discovery half: {} high, {} low".format(
            int((discovery[GROUP_COLUMN] == HIGH_GROUP).sum()),
            int((discovery[GROUP_COLUMN] == LOW_GROUP).sum()),
        )
    )
    print()
    print_header()

    carried_forward = []
    discovery_results = {}

    for column, label, unit in OUTCOMES:
        result = two_sample_test(discovery, column)
        discovery_results[column] = result
        passed = result["p_value"] < SCREENING_ALPHA
        if passed:
            carried_forward.append((column, label, unit))
        print_result_row(
            label, unit, result, "carried forward" if passed else "dropped"
        )

    print()
    print(
        "Outcomes screened: {}. Carried forward: {}.".format(
            len(OUTCOMES), len(carried_forward)
        )
    )
    if carried_forward:
        print(
            "Carried forward:   {}".format(
                ", ".join(column for column, _, _ in carried_forward)
            )
        )
    print()

    print(SEPARATOR)
    print("STAGE TWO - CONFIRMATION (VALIDATION HALF ONLY)")
    print(SEPARATOR)

    n_entering = len(carried_forward)
    print("Outcomes entering stage two: {}".format(n_entering))

    if n_entering == 0:
        print("No outcome passed screening, so no confirmatory test was run.")
        print("The study reports no confirmed difference.")
        return

    adjusted_alpha = CONFIRMATORY_ALPHA / n_entering
    print(
        "Adjusted significance level: {:.2f} / {} = {:.6f} "
        "(Bonferroni over the".format(
            CONFIRMATORY_ALPHA, n_entering, adjusted_alpha
        )
    )
    print(
        "                             {} outcomes carried into this "
        "stage)".format(n_entering)
    )
    print(
        "Validation half: {} high, {} low".format(
            int((validation[GROUP_COLUMN] == HIGH_GROUP).sum()),
            int((validation[GROUP_COLUMN] == LOW_GROUP).sum()),
        )
    )
    print()
    print_header()

    confirmed = []
    for column, label, unit in carried_forward:
        result = two_sample_test(validation, column)
        is_confirmed = result["p_value"] < adjusted_alpha
        if is_confirmed:
            confirmed.append((column, label, unit))
        print_result_row(
            label, unit, result, "CONFIRMED" if is_confirmed else "not confirmed"
        )

    print()
    print(SEPARATOR)
    print("CONCLUSION (VALIDATION HALF ONLY)")
    print(SEPARATOR)
    print(
        "Confirmed at the adjusted level {:.6f}: {} of {} outcomes "
        "tested.".format(adjusted_alpha, len(confirmed), n_entering)
    )
    if confirmed:
        print(
            "Confirmed outcomes: {}".format(
                ", ".join(column for column, _, _ in confirmed)
            )
        )
    else:
        print("Confirmed outcomes: none.")
    print(
        "Discovery-half results above are screening output only and are not "
        "reported"
    )
    print("as confirmed findings.")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
