"""Week-12 glove-protocol comparison for the apprentice hairdresser hand-skin study.

Reads hand_skin_study.csv from the project root, compares the two glove protocols on
each of the seven declared outcomes with a two-sample t-test, and prints group sizes,
group means, the test statistic and the p-value for every outcome.

The two primary barrier-function outcomes (transepidermal water loss and stratum
corneum hydration) carry the protocol's main claim, so their two p-values are adjusted
together with statsmodels' Holm multiple-comparison routine and their verdicts are based
on the adjusted values. The five secondary outcomes are reported with plain unadjusted
p-values and judged at the conventional 0.05 threshold.

Run from the project root:  python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = "hand_skin_study.csv"
GROUP_COLUMN = "glove_protocol"
GROUP_A = "liner_under_nitrile"
GROUP_B = "nitrile_only"
ALPHA = 0.05
ADJUST_METHOD = "holm"

# Declared outcome order from the study protocol. The first two are the primary
# barrier-function outcomes; the remaining five are secondary.
PRIMARY_OUTCOMES = [
    ("transepidermal_water_loss_g_m2_h", "Transepidermal water loss (g/m2/h)"),
    ("stratum_corneum_hydration_au", "Stratum corneum hydration (a.u.)"),
]
SECONDARY_OUTCOMES = [
    ("hand_eczema_severity_score_points", "Hand eczema severity score (0-30 points)"),
    ("self_reported_itch_score_points", "Self-reported itch score (0-10 points)"),
    ("skin_surface_ph", "Skin surface pH"),
    ("erythema_index_au", "Erythema index (a.u.)"),
    ("hand_symptom_days_last_4_weeks_days", "Hand symptom days, last 4 weeks (days)"),
]


def load_data():
    """Load the week-12 measurements from the project root."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
    frame = pd.read_csv(path)
    groups = sorted(frame[GROUP_COLUMN].unique())
    if groups != sorted([GROUP_A, GROUP_B]):
        raise ValueError("unexpected values in %s: %s" % (GROUP_COLUMN, groups))
    return frame


def compare_outcome(frame, column):
    """Two-sample t-test of one outcome between the two glove protocols."""
    values_a = frame.loc[frame[GROUP_COLUMN] == GROUP_A, column].astype(float)
    values_b = frame.loc[frame[GROUP_COLUMN] == GROUP_B, column].astype(float)
    statistic, p_value = stats.ttest_ind(values_a, values_b)
    return {
        "column": column,
        "n_a": int(values_a.size),
        "n_b": int(values_b.size),
        "mean_a": float(values_a.mean()),
        "mean_b": float(values_b.mean()),
        "difference": float(values_a.mean() - values_b.mean()),
        "statistic": float(statistic),
        "p_value": float(p_value),
    }


def verdict(p_value):
    return "SIGNIFICANT" if p_value < ALPHA else "not significant"


def print_result(label, result, adjusted_p=None):
    print(label)
    print("  column                : %s" % result["column"])
    print("  group sizes           : %s n=%d, %s n=%d"
          % (GROUP_A, result["n_a"], GROUP_B, result["n_b"]))
    print("  group means           : %s %.3f, %s %.3f (difference %+.3f)"
          % (GROUP_A, result["mean_a"], GROUP_B, result["mean_b"], result["difference"]))
    print("  t statistic           : %+.3f" % result["statistic"])
    print("  p-value (unadjusted)  : %.4f" % result["p_value"])
    if adjusted_p is None:
        print("  verdict at alpha=%.2f  : %s (unadjusted p)" % (ALPHA, verdict(result["p_value"])))
    else:
        print("  p-value (%s-adjusted, primary pair): %.4f" % (ADJUST_METHOD, adjusted_p))
        print("  verdict at alpha=%.2f  : %s (adjusted p)" % (ALPHA, verdict(adjusted_p)))
    print()


def main():
    frame = load_data()

    print("=" * 78)
    print("Twelve-week hand-skin study in apprentice hairdressers")
    print("Week-12 comparison of %s vs %s" % (GROUP_A, GROUP_B))
    print("Rows read: %d apprentices, one measurement occasion each" % len(frame))
    print("Test: two-sample Student t-test (scipy.stats.ttest_ind) for every outcome")
    print("=" * 78)
    print()

    primary_results = [compare_outcome(frame, column) for column, _ in PRIMARY_OUTCOMES]
    primary_p = [result["p_value"] for result in primary_results]
    _, primary_p_adjusted, _, _ = multipletests(primary_p, alpha=ALPHA, method=ADJUST_METHOD)

    print("PRIMARY BARRIER-FUNCTION OUTCOMES")
    print("p-values adjusted across these two outcomes only, method: %s" % ADJUST_METHOD)
    print("-" * 78)
    for index, (_, label) in enumerate(PRIMARY_OUTCOMES):
        print_result("Primary %d. %s" % (index + 1, label),
                     primary_results[index],
                     adjusted_p=float(primary_p_adjusted[index]))

    print("SECONDARY OUTCOMES")
    print("unadjusted p-values, judged at alpha=%.2f" % ALPHA)
    print("-" * 78)
    secondary_results = []
    for index, (column, label) in enumerate(SECONDARY_OUTCOMES):
        result = compare_outcome(frame, column)
        secondary_results.append(result)
        print_result("Secondary %d. %s" % (index + 1, label), result)

    print("SUMMARY TABLE")
    print("-" * 78)
    header = "%-38s %9s %9s %9s %s" % ("outcome", "t", "p", "p_used", "verdict")
    print(header)
    for index, (_, label) in enumerate(PRIMARY_OUTCOMES):
        result = primary_results[index]
        used = float(primary_p_adjusted[index])
        print("%-38s %9.3f %9.4f %9.4f %s"
              % (label[:38], result["statistic"], result["p_value"], used, verdict(used)))
    for index, (_, label) in enumerate(SECONDARY_OUTCOMES):
        result = secondary_results[index]
        used = result["p_value"]
        print("%-38s %9.3f %9.4f %9.4f %s"
              % (label[:38], result["statistic"], result["p_value"], used, verdict(used)))
    print("-" * 78)


if __name__ == "__main__":
    main()
