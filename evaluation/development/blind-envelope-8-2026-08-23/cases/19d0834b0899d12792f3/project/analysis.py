"""Week-eight plaque induration thickness: active topical formulation vs vehicle cream.

Reads `plaque_thickness.csv`, compares `thickness_mm` between the two levels of
`treatment_arm` with an independent two-sample t-test, and prints the arm summaries,
the test statistic and the p-value.

Every measured plaque is one observation in the comparison.
"""

import os

import pandas as pd
from scipy import stats

ALPHA = 0.05
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "plaque_thickness.csv")

EXPECTED_COLUMNS = [
    "patient_id",
    "treatment_arm",
    "plaque_site",
    "thickness_mm",
    "age_years",
    "sex",
]


def load_data(path=DATA_PATH):
    """Read the plaque table and check the columns and completeness."""
    frame = pd.read_csv(path)

    missing = [name for name in EXPECTED_COLUMNS if name not in frame.columns]
    if missing:
        raise ValueError("missing expected columns: %s" % ", ".join(missing))

    if frame[EXPECTED_COLUMNS].isna().any().any():
        raise ValueError("the table contains missing values")

    arms = sorted(frame["treatment_arm"].unique())
    if arms != ["active", "vehicle"]:
        raise ValueError("expected exactly the arms 'active' and 'vehicle', found: %s" % arms)

    return frame


def describe_arm(values):
    """Mean, SD, min, max and count for one arm's thickness measurements."""
    return {
        "n": int(values.size),
        "mean_mm": float(values.mean()),
        "sd_mm": float(values.std(ddof=1)),
        "min_mm": float(values.min()),
        "max_mm": float(values.max()),
    }


def compare_arms(frame):
    """Independent two-sample t-test on thickness_mm across every row of the table."""
    active = frame.loc[frame["treatment_arm"] == "active", "thickness_mm"]
    vehicle = frame.loc[frame["treatment_arm"] == "vehicle", "thickness_mm"]

    # Welch's t-test: the two arms are not assumed to share a variance.
    t_statistic, p_value = stats.ttest_ind(active, vehicle, equal_var=False)

    active_summary = describe_arm(active)
    vehicle_summary = describe_arm(vehicle)

    difference_mm = active_summary["mean_mm"] - vehicle_summary["mean_mm"]

    # Welch degrees of freedom and the 95% confidence interval for the difference.
    var_a = active.var(ddof=1)
    var_v = vehicle.var(ddof=1)
    n_a = active.size
    n_v = vehicle.size
    standard_error = ((var_a / n_a) + (var_v / n_v)) ** 0.5
    degrees_of_freedom = ((var_a / n_a + var_v / n_v) ** 2) / (
        (var_a / n_a) ** 2 / (n_a - 1) + (var_v / n_v) ** 2 / (n_v - 1)
    )
    critical = stats.t.ppf(1 - ALPHA / 2, degrees_of_freedom)

    # Pooled SD for a standardised effect size.
    pooled_sd = (((n_a - 1) * var_a + (n_v - 1) * var_v) / (n_a + n_v - 2)) ** 0.5

    return {
        "n_total": int(n_a + n_v),
        "active": active_summary,
        "vehicle": vehicle_summary,
        "difference_mm": float(difference_mm),
        "standard_error_mm": float(standard_error),
        "ci_low_mm": float(difference_mm - critical * standard_error),
        "ci_high_mm": float(difference_mm + critical * standard_error),
        "t_statistic": float(t_statistic),
        "degrees_of_freedom": float(degrees_of_freedom),
        "p_value": float(p_value),
        "cohens_d": float(difference_mm / pooled_sd),
        "relative_reduction_pct": float(
            -100.0 * difference_mm / vehicle_summary["mean_mm"]
        ),
    }


def site_breakdown(frame):
    """Mean thickness by body site within each arm, for description only."""
    return (
        frame.pivot_table(
            index="plaque_site",
            columns="treatment_arm",
            values="thickness_mm",
            aggfunc="mean",
        )
        .round(2)
        .sort_index()
    )


def report(frame, result):
    lines = []
    lines.append("Week-eight plaque induration thickness: active vs vehicle")
    lines.append("=" * 58)
    lines.append("")
    lines.append("Table: %d rows, %d columns" % (frame.shape[0], frame.shape[1]))
    lines.append("Patients: %d" % frame["patient_id"].nunique())
    lines.append(
        "Age (years): %d to %d, mean %.1f"
        % (
            frame["age_years"].min(),
            frame["age_years"].max(),
            frame["age_years"].mean(),
        )
    )
    sex_counts = frame.drop_duplicates("patient_id")["sex"].value_counts()
    lines.append(
        "Sex (patients): %s"
        % ", ".join("%s %d" % (key, value) for key, value in sex_counts.sort_index().items())
    )
    lines.append("")

    lines.append("Arm summaries (thickness_mm)")
    lines.append("-" * 58)
    header = "%-9s %5s %8s %8s %8s %8s" % ("arm", "n", "mean", "sd", "min", "max")
    lines.append(header)
    for arm in ("active", "vehicle"):
        summary = result[arm]
        lines.append(
            "%-9s %5d %8.3f %8.3f %8.2f %8.2f"
            % (
                arm,
                summary["n"],
                summary["mean_mm"],
                summary["sd_mm"],
                summary["min_mm"],
                summary["max_mm"],
            )
        )
    lines.append("")

    lines.append("Independent two-sample t-test (Welch)")
    lines.append("-" * 58)
    lines.append("Observations entering the comparison: %d" % result["n_total"])
    lines.append(
        "Mean difference (active - vehicle): %+.3f mm" % result["difference_mm"]
    )
    lines.append(
        "95%% CI for the difference: %.3f to %.3f mm"
        % (result["ci_low_mm"], result["ci_high_mm"])
    )
    lines.append(
        "t = %.3f, df = %.2f, p = %.3g"
        % (result["t_statistic"], result["degrees_of_freedom"], result["p_value"])
    )
    lines.append("Cohen's d = %.3f" % result["cohens_d"])
    lines.append(
        "Relative reduction vs vehicle: %.1f%%" % result["relative_reduction_pct"]
    )
    lines.append("")

    lines.append("Mean thickness_mm by body site")
    lines.append("-" * 58)
    lines.append(site_breakdown(frame).to_string())
    lines.append("")

    verdict = "significant" if result["p_value"] < ALPHA else "not significant"
    lines.append(
        "At alpha = %.2f the difference between arms is %s." % (ALPHA, verdict)
    )
    return "\n".join(lines)


def main():
    frame = load_data()
    result = compare_arms(frame)
    print(report(frame, result))


if __name__ == "__main__":
    main()
