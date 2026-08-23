"""Sedation protocol and oxygenation in mechanically ventilated ICU adults.

Single-centre comparison of a light sedation protocol against a deep sedation
protocol. The outcome is the ratio of arterial oxygen tension to inspired oxygen
fraction (PaO2/FiO2, mmHg), measured on arterial blood gas.

Every arterial blood gas result in `sedation_abg.csv` is an observation for the
analysis, so the sample size is the total number of blood gas measurements
available. The two arms are compared with an independent two-sample t-test on
Student's assumption of equal variances, run over every row in the table as
supplied.

Run:  python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = "sedation_abg.csv"
ARM_LIGHT = "light"
ARM_DEEP = "deep"
ALPHA = 0.05


def load_measurements(path):
    """Read the arterial blood gas table and check it is the expected shape."""
    frame = pd.read_csv(path)
    expected_columns = [
        "PatientID",
        "SedationArm",
        "HoursFromEnrolment",
        "PFRatio",
    ]
    if list(frame.columns) != expected_columns:
        raise ValueError(
            "unexpected columns in %s: %s" % (path, list(frame.columns))
        )
    if frame["PFRatio"].isna().any():
        raise ValueError("PFRatio contains missing values")
    arms = set(frame["SedationArm"].unique())
    if arms != {ARM_LIGHT, ARM_DEEP}:
        raise ValueError("unexpected SedationArm values: %s" % sorted(arms))
    return frame


def describe_arm(frame, arm):
    """Return count, mean and standard deviation of PFRatio for one arm."""
    values = frame.loc[frame["SedationArm"] == arm, "PFRatio"]
    return {
        "arm": arm,
        "n": int(values.shape[0]),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
    }


def compare_arms(frame):
    """Independent two-sample t-test of PFRatio, light arm against deep arm.

    Each row of the table is one arterial blood gas measurement and enters the
    test as one observation, so the sample size of the test is the total number
    of blood gas measurements available for analysis.
    """
    light_values = frame.loc[frame["SedationArm"] == ARM_LIGHT, "PFRatio"]
    deep_values = frame.loc[frame["SedationArm"] == ARM_DEEP, "PFRatio"]
    result = stats.ttest_ind(light_values, deep_values, equal_var=True)
    n_light = int(light_values.shape[0])
    n_deep = int(deep_values.shape[0])
    return {
        "n_total": n_light + n_deep,
        "n_light": n_light,
        "n_deep": n_deep,
        "mean_light": float(light_values.mean()),
        "mean_deep": float(deep_values.mean()),
        "difference": float(light_values.mean() - deep_values.mean()),
        "t_statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "df": n_light + n_deep - 2,
    }


def means_by_timepoint(frame):
    """Mean PFRatio at each scheduled time point, for the report's description."""
    table = (
        frame.groupby(["HoursFromEnrolment", "SedationArm"])["PFRatio"]
        .mean()
        .unstack("SedationArm")
    )
    return table[[ARM_LIGHT, ARM_DEEP]]


def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
    frame = load_measurements(path)

    print("Sedation protocol and oxygenation (PaO2/FiO2, mmHg)")
    print("=" * 55)
    print()
    print("Blood gas measurements read: %d" % frame.shape[0])
    print("Patients represented:        %d" % frame["PatientID"].nunique())
    print("Scheduled time points:       %s"
          % sorted(frame["HoursFromEnrolment"].unique()))
    print()

    print("PFRatio by sedation arm")
    print("-" * 55)
    print("%-8s %6s %10s %10s" % ("arm", "n", "mean", "sd"))
    for arm in (ARM_LIGHT, ARM_DEEP):
        summary = describe_arm(frame, arm)
        print("%-8s %6d %10.1f %10.1f"
              % (summary["arm"], summary["n"], summary["mean"], summary["sd"]))
    print()

    print("Mean PFRatio by time point")
    print("-" * 55)
    print("%-8s %10s %10s" % ("hours", ARM_LIGHT, ARM_DEEP))
    for hours, row in means_by_timepoint(frame).iterrows():
        print("%-8d %10.1f %10.1f" % (hours, row[ARM_LIGHT], row[ARM_DEEP]))
    print()

    test = compare_arms(frame)
    print("Independent two-sample t-test (equal variances)")
    print("-" * 55)
    print("N (blood gas measurements): %d" % test["n_total"])
    print("  light arm:                %d" % test["n_light"])
    print("  deep arm:                 %d" % test["n_deep"])
    print("Mean, light arm:            %.1f mmHg" % test["mean_light"])
    print("Mean, deep arm:             %.1f mmHg" % test["mean_deep"])
    print("Difference (light - deep):  %.1f mmHg" % test["difference"])
    print("t(%d) = %.3f" % (test["df"], test["t_statistic"]))
    print("p = %.6g" % test["p_value"])
    print()

    if test["p_value"] < ALPHA and test["difference"] > 0:
        print("Conclusion: light sedation is associated with better oxygenation "
              "(p < %.2f)." % ALPHA)
    elif test["p_value"] < ALPHA:
        print("Conclusion: deep sedation is associated with better oxygenation "
              "(p < %.2f)." % ALPHA)
    else:
        print("Conclusion: no significant difference in oxygenation between the "
              "two sedation arms at alpha = %.2f." % ALPHA)


if __name__ == "__main__":
    main()
