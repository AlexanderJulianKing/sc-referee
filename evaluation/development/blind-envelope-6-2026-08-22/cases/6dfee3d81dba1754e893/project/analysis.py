"""Six-minute walk distance three months after total knee replacement.

Compares two rehabilitation protocols, standard supervised outpatient
physiotherapy against a home-based programme with weekly telephone coaching.

Design note that drives the whole analysis: every patient performed the
six-minute walk test exactly once, so the data file holds exactly one row per
patient. The patient is both the unit of randomisation and the unit of
measurement, the two protocol groups contain different patients, and therefore
an independent two-sample comparison on the patient rows is the correct test.
The sample size per protocol is the number of patients in that protocol, which
is the same as the number of rows in that protocol.

Run:  python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = "knee_rehab_6mwt.csv"

OUTCOME = "six_min_walk_m"
GROUP = "rehab_protocol"
UNIT = "patient_ref"

PROTOCOL_ORDER = ["standard_outpatient", "home_based_telephone"]
PROTOCOL_LABEL = {
    "standard_outpatient": "Standard supervised outpatient physiotherapy",
    "home_based_telephone": "Home-based programme with weekly telephone coaching",
}


def load_data():
    """Read the single data file that sits next to this script."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
    return pd.read_csv(path)


def check_one_row_per_patient(data):
    """Confirm the design assumption before any test is run.

    The independent two-sample test is only correct if each patient contributes
    exactly one measurement. That is a checkable property of the file, so it is
    checked rather than assumed.
    """
    n_rows = len(data)
    n_patients = data[UNIT].nunique()
    repeated = data[UNIT].value_counts()
    repeated = repeated[repeated > 1]

    print("Design check")
    print("-" * 62)
    print("Rows in file                     : {}".format(n_rows))
    print("Distinct patients (patient_ref)  : {}".format(n_patients))
    print("Patients appearing more than once: {}".format(len(repeated)))

    if n_rows != n_patients:
        raise ValueError(
            "Expected one row per patient, found {} rows for {} patients. "
            "An independent two-sample test on the rows would then treat "
            "repeated measurements as if they were separate patients.".format(
                n_rows, n_patients
            )
        )

    # Each patient must sit in one protocol only, or the groups would not be
    # independent of each other.
    protocols_per_patient = data.groupby(UNIT)[GROUP].nunique()
    crossing = protocols_per_patient[protocols_per_patient > 1]
    print("Patients in both protocols       : {}".format(len(crossing)))
    if len(crossing) > 0:
        raise ValueError(
            "{} patient(s) appear under both protocols, so the two groups are "
            "not independent.".format(len(crossing))
        )

    missing = int(data[OUTCOME].isna().sum())
    print("Missing outcome values           : {}".format(missing))
    if missing > 0:
        raise ValueError("Missing outcome values are not handled by this script.")

    print("One row per patient confirmed.")
    print()
    return n_patients


def describe(data):
    """Summarise every column by protocol, and print the outcome summary."""
    print("Summary by protocol")
    print("-" * 62)

    summary = {}
    for protocol in PROTOCOL_ORDER:
        arm = data.loc[data[GROUP] == protocol]
        outcome = arm[OUTCOME]
        stats_row = {
            "n_patients": len(arm),
            "n_rows": len(arm),
            "mean": outcome.mean(),
            "sd": outcome.std(ddof=1),
            "median": outcome.median(),
            "min": outcome.min(),
            "max": outcome.max(),
            "mean_age": arm["age_years"].mean(),
            "sd_age": arm["age_years"].std(ddof=1),
            "mean_bmi": arm["bmi"].mean(),
            "sd_bmi": arm["bmi"].std(ddof=1),
        }
        summary[protocol] = stats_row

        print(PROTOCOL_LABEL[protocol])
        print("  patients (= rows)   : {}".format(stats_row["n_patients"]))
        print("  six-min walk mean   : {:.1f} m".format(stats_row["mean"]))
        print("  six-min walk SD     : {:.1f} m".format(stats_row["sd"]))
        print("  six-min walk median : {:.1f} m".format(stats_row["median"]))
        print(
            "  six-min walk range  : {:.1f} to {:.1f} m".format(
                stats_row["min"], stats_row["max"]
            )
        )
        print(
            "  age                 : mean {:.1f} y (SD {:.1f})".format(
                stats_row["mean_age"], stats_row["sd_age"]
            )
        )
        print(
            "  BMI                 : mean {:.1f} (SD {:.1f})".format(
                stats_row["mean_bmi"], stats_row["sd_bmi"]
            )
        )
        print()

    return summary


def compare(data, summary):
    """Independent two-sample comparison on the patient rows."""
    standard = data.loc[data[GROUP] == "standard_outpatient", OUTCOME]
    home = data.loc[data[GROUP] == "home_based_telephone", OUTCOME]

    n1, n2 = len(standard), len(home)
    m1, m2 = standard.mean(), home.mean()
    s1, s2 = standard.std(ddof=1), home.std(ddof=1)

    difference = m2 - m1  # home-based minus standard outpatient

    # Welch's two-sample t-test: independent samples, no assumption that the
    # two protocols share the same variance.
    welch = stats.ttest_ind(home, standard, equal_var=False)

    # Welch standard error and degrees of freedom, for the confidence interval.
    se = ((s1 ** 2) / n1 + (s2 ** 2) / n2) ** 0.5
    df = ((s1 ** 2) / n1 + (s2 ** 2) / n2) ** 2 / (
        ((s1 ** 2) / n1) ** 2 / (n1 - 1) + ((s2 ** 2) / n2) ** 2 / (n2 - 1)
    )
    t_crit = stats.t.ppf(0.975, df)
    ci_low = difference - t_crit * se
    ci_high = difference + t_crit * se

    # Student's two-sample t-test, reported alongside as a sensitivity check.
    student = stats.ttest_ind(home, standard, equal_var=True)

    # Mann-Whitney U, a rank-based check that does not assume normality.
    mwu = stats.mannwhitneyu(home, standard, alternative="two-sided")

    # Standardised effect size (Hedges' g, pooled SD with small-sample
    # correction), a unit-free measure of how far apart the two means are.
    pooled_sd = (
        (((n1 - 1) * s1 ** 2) + ((n2 - 1) * s2 ** 2)) / (n1 + n2 - 2)
    ) ** 0.5
    cohens_d = difference / pooled_sd
    correction = 1.0 - (3.0 / (4.0 * (n1 + n2) - 9.0))
    hedges_g = cohens_d * correction

    # Normality of the outcome inside each protocol, for transparency only.
    sw_standard = stats.shapiro(standard)
    sw_home = stats.shapiro(home)
    levene = stats.levene(home, standard, center="median")

    print("Primary comparison: independent two-sample t-test (Welch)")
    print("-" * 62)
    print("Unit of analysis    : the patient (one row per patient)")
    print("n per protocol      : standard {} patients, home-based {} patients".format(n1, n2))
    print("Mean standard       : {:.1f} m (SD {:.1f})".format(m1, s1))
    print("Mean home-based     : {:.1f} m (SD {:.1f})".format(m2, s2))
    print("Difference (home - standard): {:+.1f} m".format(difference))
    print("95% CI for difference      : {:.1f} to {:.1f} m".format(ci_low, ci_high))
    print("Standard error      : {:.2f} m".format(se))
    print("t = {:.3f}, df = {:.2f}, p = {:.4f}".format(welch.statistic, df, welch.pvalue))
    print("Hedges' g           : {:.3f} (Cohen's d {:.3f})".format(hedges_g, cohens_d))
    print()

    print("Supporting checks")
    print("-" * 62)
    print(
        "Student t-test (equal variance): t = {:.3f}, p = {:.4f}".format(
            student.statistic, student.pvalue
        )
    )
    print(
        "Mann-Whitney U (rank based)    : U = {:.1f}, p = {:.4f}".format(
            mwu.statistic, mwu.pvalue
        )
    )
    print(
        "Shapiro-Wilk, standard arm     : W = {:.3f}, p = {:.4f}".format(
            sw_standard.statistic, sw_standard.pvalue
        )
    )
    print(
        "Shapiro-Wilk, home-based arm   : W = {:.3f}, p = {:.4f}".format(
            sw_home.statistic, sw_home.pvalue
        )
    )
    print(
        "Levene equal-variance test     : W = {:.3f}, p = {:.4f}".format(
            levene.statistic, levene.pvalue
        )
    )
    print()

    return {
        "n1": n1,
        "n2": n2,
        "m1": m1,
        "m2": m2,
        "s1": s1,
        "s2": s2,
        "difference": difference,
        "se": se,
        "df": df,
        "t": welch.statistic,
        "p": welch.pvalue,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "hedges_g": hedges_g,
        "cohens_d": cohens_d,
        "student_t": student.statistic,
        "student_p": student.pvalue,
        "mwu_u": mwu.statistic,
        "mwu_p": mwu.pvalue,
        "sw_standard": sw_standard,
        "sw_home": sw_home,
        "levene": levene,
    }


def main():
    data = load_data()

    print("=" * 62)
    print("Six-minute walk distance at three months after knee replacement")
    print("=" * 62)
    print()

    check_one_row_per_patient(data)
    summary = describe(data)
    result = compare(data, summary)

    print("Conclusion line")
    print("-" * 62)
    verdict = "a statistically significant" if result["p"] < 0.05 else "no statistically significant"
    print(
        "At the 5% level there is {} difference between the two protocols "
        "(p = {:.4f}).".format(verdict, result["p"])
    )
    print(
        "Home-based patients walked {:+.1f} m compared with standard outpatient "
        "patients, 95% CI {:.1f} to {:.1f} m.".format(
            result["difference"], result["ci_low"], result["ci_high"]
        )
    )


if __name__ == "__main__":
    main()
