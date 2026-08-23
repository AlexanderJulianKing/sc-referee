"""Two-drench comparison of post-treatment faecal egg counts in yearling dairy goats.

Reads faecal_egg_counts.csv, compares post_treatment_epg between the benzimidazole
and macrocyclic lactone arms with an independent two-sample test of the difference
in means, and prints the results.

Every counting slide in the table is passed into the comparison as a separate
observation, so the sample size reported is the number of counts analysed.
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = "faecal_egg_counts.csv"
GROUP_COL = "drench_group"
OUTCOME_COL = "post_treatment_epg"
GROUP_A = "benzimidazole"
GROUP_B = "macrocyclic_lactone"
ALPHA = 0.05


def load_data():
    here = os.path.dirname(os.path.abspath(__file__))
    return pd.read_csv(os.path.join(here, DATA_FILE))


def describe(values):
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "sem": float(values.std(ddof=1) / (values.size ** 0.5)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def main():
    data = load_data()

    a = data.loc[data[GROUP_COL] == GROUP_A, OUTCOME_COL]
    b = data.loc[data[GROUP_COL] == GROUP_B, OUTCOME_COL]

    stats_a = describe(a)
    stats_b = describe(b)

    # Independent two-sample test of the difference in means (Welch), with each
    # counting slide entered as its own observation.
    t_stat, p_value = stats.ttest_ind(a, b, equal_var=False)

    difference = stats_a["mean"] - stats_b["mean"]
    se_diff = (stats_a["sem"] ** 2 + stats_b["sem"] ** 2) ** 0.5
    df = se_diff ** 4 / (
        stats_a["sem"] ** 4 / (stats_a["n"] - 1)
        + stats_b["sem"] ** 4 / (stats_b["n"] - 1)
    )
    t_crit = stats.t.ppf(1 - ALPHA / 2, df)
    ci_low = difference - t_crit * se_diff
    ci_high = difference + t_crit * se_diff

    pre_a = data.loc[data[GROUP_COL] == GROUP_A, "pre_treatment_epg"]
    pre_b = data.loc[data[GROUP_COL] == GROUP_B, "pre_treatment_epg"]

    reduction_a = 100.0 * (1.0 - stats_a["mean"] / float(pre_a.mean()))
    reduction_b = 100.0 * (1.0 - stats_b["mean"] / float(pre_b.mean()))

    print("Post-treatment faecal egg count: benzimidazole vs macrocyclic lactone")
    print("=" * 70)
    print("Counts analysed (total): %d" % len(data))
    print()

    header = "%-22s %6s %10s %10s %10s %8s %8s" % (
        "Group", "n", "Mean", "SD", "SEM", "Min", "Max",
    )
    print(header)
    print("-" * len(header))
    for label, s in ((GROUP_A, stats_a), (GROUP_B, stats_b)):
        print(
            "%-22s %6d %10.1f %10.1f %10.1f %8.0f %8.0f"
            % (label, s["n"], s["mean"], s["sd"], s["sem"], s["min"], s["max"])
        )
    print()

    print("Mean pre-treatment epg, %s: %.1f" % (GROUP_A, pre_a.mean()))
    print("Mean pre-treatment epg, %s: %.1f" % (GROUP_B, pre_b.mean()))
    print(
        "Faecal egg count reduction, %s: %.1f%%" % (GROUP_A, reduction_a)
    )
    print(
        "Faecal egg count reduction, %s: %.1f%%" % (GROUP_B, reduction_b)
    )
    print()

    print("Independent two-sample test of the difference in means (Welch)")
    print("Sample size analysed: n = %d counts (%d vs %d)"
          % (stats_a["n"] + stats_b["n"], stats_a["n"], stats_b["n"]))
    print("Difference in means (%s - %s): %.1f epg" % (GROUP_A, GROUP_B, difference))
    print("95%% CI for the difference: %.1f to %.1f epg" % (ci_low, ci_high))
    print("t = %.3f, df = %.1f" % (t_stat, df))
    print("p = %.3e" % p_value)
    print()

    if p_value < ALPHA:
        better = GROUP_B if stats_b["mean"] < stats_a["mean"] else GROUP_A
        print(
            "Conclusion: the two drenches differ at alpha = %.2f. The %s drench left "
            "the lower post-treatment egg count and is the more efficacious of the two."
            % (ALPHA, better)
        )
    else:
        print(
            "Conclusion: no difference between the two drenches at alpha = %.2f."
            % ALPHA
        )


if __name__ == "__main__":
    main()
