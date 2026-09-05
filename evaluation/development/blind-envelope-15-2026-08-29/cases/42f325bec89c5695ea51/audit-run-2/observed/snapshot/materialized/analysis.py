"""Week-twelve comparison of a preservative-free and a preserved glaucoma eye drop.

Reads the fixed data file `data.csv`, summarises the five pre-declared outcomes by
formulation group, compares the two groups on each outcome with one two-sample test,
and controls the family-wise error rate across the complete five-outcome family in a
single multiplicity adjustment. Every significance verdict is taken from the adjusted
p-values only.

`data.csv` is input only. This script never writes, generates, simulates or overwrites it.
"""

from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = Path(__file__).resolve().parent / "data.csv"

ID_COL = "patient_id"
GROUP_COL = "formulation"
GROUP_A = "preservative_free"
GROUP_B = "preserved"

# Family-level significance threshold and the family-wise error rate adjustment.
ALPHA = 0.05
ADJUST_METHOD = "holm"  # Holm-Bonferroni step-down, controls FWER over the whole family.

# Patient whose week-twelve intraocular pressure was flagged by the site as a
# suspected tonometer calibration problem. Kept in the data file as recorded; used
# only to define the separate robustness check below.
FLAGGED_PATIENT = "oht_32"

# The pre-declared outcome family, in the fixed protocol order.
# test: "welch"  -> Welch two-sample t-test (unequal variances) for the measured,
#                   approximately continuous outcomes.
#       "mannwhitney" -> Mann-Whitney U test for the two ordinal graded outcomes,
#                   which are recorded on coarse ordered scales.
OUTCOMES = [
    {
        "column": "intraocular_pressure_mmhg",
        "label": "1. Intraocular pressure (mmHg)",
        "test": "welch",
    },
    {
        "column": "osdi_score_0_100",
        "label": "2. OSDI symptom score (0-100 points)",
        "test": "welch",
    },
    {
        "column": "tear_film_breakup_time_s",
        "label": "3. Tear film break-up time (s)",
        "test": "welch",
    },
    {
        "column": "conjunctival_hyperaemia_grade_0_3",
        "label": "4. Conjunctival hyperaemia grade (0-3)",
        "test": "mannwhitney",
    },
    {
        "column": "corneal_staining_score_0_15",
        "label": "5. Corneal staining score (0-15 points)",
        "test": "mannwhitney",
    },
]

TEST_NAMES = {
    "welch": "Welch two-sample t-test",
    "mannwhitney": "Mann-Whitney U test",
}

RULE = "=" * 84
THIN_RULE = "-" * 84


def format_p(value):
    """Render a p-value at a readable precision without collapsing small ones to zero."""
    if value < 0.0001:
        return "%.2e" % value
    return "%.4f" % value


def load_data(path):
    """Read the fixed data file and check the structural assumptions it documents."""
    frame = pd.read_csv(path)

    expected = [ID_COL, GROUP_COL] + [item["column"] for item in OUTCOMES]
    missing = [name for name in expected if name not in frame.columns]
    if missing:
        raise ValueError("data.csv is missing expected columns: %s" % ", ".join(missing))

    if frame[ID_COL].duplicated().any():
        raise ValueError("data.csv contains duplicate patient identifiers")

    labels = sorted(frame[GROUP_COL].unique())
    if labels != sorted([GROUP_A, GROUP_B]):
        raise ValueError("unexpected formulation labels in data.csv: %s" % labels)

    if frame[expected].isna().any().any():
        raise ValueError("data.csv contains missing values")

    return frame


def split_groups(frame, column):
    """Return the outcome values for each formulation group."""
    a = frame.loc[frame[GROUP_COL] == GROUP_A, column]
    b = frame.loc[frame[GROUP_COL] == GROUP_B, column]
    return a, b


def compare(frame, column, test):
    """Run one two-sample test for one outcome and return its statistic and p-value."""
    a, b = split_groups(frame, column)
    if test == "welch":
        statistic, p_value = stats.ttest_ind(a, b, equal_var=False)
    elif test == "mannwhitney":
        statistic, p_value = stats.mannwhitneyu(a, b, alternative="two-sided")
    else:
        raise ValueError("unknown test: %s" % test)
    return float(statistic), float(p_value)


def print_group_sizes(frame):
    print(RULE)
    print("GROUP SIZES")
    print(RULE)
    counts = frame[GROUP_COL].value_counts()
    print("Patients in data.csv (one row = one patient, one study eye): %d" % len(frame))
    for label in (GROUP_A, GROUP_B):
        print("  %-20s n = %d" % (label, int(counts[label])))
    print()


def print_summaries(frame):
    print(RULE)
    print("PER-GROUP SUMMARY VALUES BY DECLARED OUTCOME")
    print(RULE)
    for item in OUTCOMES:
        print(item["label"])
        print("  " + "%-18s %8s %8s %8s %8s" % ("Group", "n", "mean", "SD", "median"))
        a, b = split_groups(frame, item["column"])
        for label, values in ((GROUP_A, a), (GROUP_B, b)):
            print(
                "  %-18s %8d %8.2f %8.2f %8.2f"
                % (label, len(values), values.mean(), values.std(ddof=1), values.median())
            )
        print(
            "  difference (%s minus %s): %+.2f"
            % (GROUP_A, GROUP_B, a.mean() - b.mean())
        )
        print()


def print_family_results(frame):
    """Test every declared outcome, then adjust the complete family in one call."""
    raw_p_values = []
    statistics = []
    for item in OUTCOMES:
        statistic, p_value = compare(frame, item["column"], item["test"])
        statistics.append(statistic)
        raw_p_values.append(p_value)

    # One adjustment call over the complete declared family of five p-values.
    rejected, adjusted_p_values, _, _ = multipletests(
        raw_p_values, alpha=ALPHA, method=ADJUST_METHOD
    )

    print(RULE)
    print("PRIMARY COMPARISONS: COMPLETE DECLARED FAMILY OF FIVE OUTCOMES")
    print(RULE)
    print(
        "Multiplicity adjustment: %s over all %d declared outcomes in one call, "
        "family-wise alpha = %.2f." % (ADJUST_METHOD, len(OUTCOMES), ALPHA)
    )
    print(
        "Raw p-values are shown for transparency only. Every verdict below is taken "
        "from the adjusted p-value."
    )
    print(THIN_RULE)
    print(
        "%-40s %-24s %10s %10s  %s"
        % ("Outcome", "Test", "raw p", "adj p", "Verdict (adjusted)")
    )
    print(THIN_RULE)
    for item, raw_p, adj_p, reject in zip(
        OUTCOMES, raw_p_values, adjusted_p_values, rejected
    ):
        verdict = (
            "significant at family alpha %.2f" % ALPHA
            if reject
            else "not significant at family alpha %.2f" % ALPHA
        )
        print(
            "%-40s %-24s %10s %10s  %s"
            % (
                item["label"],
                TEST_NAMES[item["test"]],
                format_p(raw_p),
                format_p(adj_p),
                verdict,
            )
        )
    print(THIN_RULE)
    print()

    print("Test statistics:")
    for item, statistic in zip(OUTCOMES, statistics):
        print("  %-40s %-24s %10.4f" % (item["label"], TEST_NAMES[item["test"]], statistic))
    print()


def print_sensitivity_check(frame):
    """Robustness check on intraocular pressure only. Not part of the inferential family."""
    column = "intraocular_pressure_mmhg"
    reduced = frame.loc[frame[ID_COL] != FLAGGED_PATIENT]
    statistic, p_value = compare(reduced, column, "welch")
    a, b = split_groups(reduced, column)

    print(RULE)
    print("ROBUSTNESS CHECK (NOT PART OF THE ADJUSTED FAMILY, NO VERDICT DRAWN)")
    print(RULE)
    print(
        "Intraocular pressure comparison repeated once with patient %s excluded "
        "(week-twelve reading of %d mmHg at a visit the site flagged as a suspected "
        "tonometer calibration problem)."
        % (
            FLAGGED_PATIENT,
            int(frame.loc[frame[ID_COL] == FLAGGED_PATIENT, column].iloc[0]),
        )
    )
    print("Patients retained: %d" % len(reduced))
    print("  %-18s n = %2d  mean = %6.2f  SD = %5.2f" % (GROUP_A, len(a), a.mean(), a.std(ddof=1)))
    print("  %-18s n = %2d  mean = %6.2f  SD = %5.2f" % (GROUP_B, len(b), b.mean(), b.std(ddof=1)))
    print(
        "  %s: t = %.4f, unadjusted p = %s"
        % (TEST_NAMES["welch"], statistic, format_p(p_value))
    )
    print(
        "This value is unadjusted, is not entered into the family adjustment, and "
        "supports no significance verdict of its own. It is reported only to show "
        "whether the intraocular pressure result depends on the flagged reading."
    )
    print()


def main():
    frame = load_data(DATA_FILE)
    print("Week-twelve comparison of two glaucoma eye-drop formulations")
    print("Data file: %s" % DATA_FILE.name)
    print()
    print_group_sizes(frame)
    print_summaries(frame)
    print_family_results(frame)
    print_sensitivity_check(frame)


if __name__ == "__main__":
    main()
