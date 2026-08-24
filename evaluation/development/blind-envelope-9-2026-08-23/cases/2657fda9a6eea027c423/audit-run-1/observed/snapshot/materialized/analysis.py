"""Analysis for the rowing training-block study.

Compares mean 500 m ergometer power output between the two six-week training
blocks (interval versus endurance) using an independent two-sample t-test.

Every recorded trial in erg_trials.csv enters the comparison as its own
observation, so the comparison is made over all 72 measured rows.

Run:
    python3 analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_CSV = Path(__file__).resolve().parent / "erg_trials.csv"

OUTCOME = "mean_power_w"
GROUP_COLUMN = "training_block"
GROUP_A = "interval"
GROUP_B = "endurance"


def load_trials(path=DATA_CSV):
    """Read the trial table and check it is complete."""
    trials = pd.read_csv(path)

    expected_columns = ["rower_id", "training_block", "trial_number", "mean_power_w"]
    missing = [c for c in expected_columns if c not in trials.columns]
    if missing:
        raise ValueError("missing expected column(s): %s" % ", ".join(missing))
    if trials[OUTCOME].isna().any():
        raise ValueError("outcome column contains missing values")

    return trials


def describe_group(values):
    """Summary statistics for one group of observations."""
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def compare_blocks(trials):
    """Independent two-sample t-test over every row of the table."""
    a = trials.loc[trials[GROUP_COLUMN] == GROUP_A, OUTCOME]
    b = trials.loc[trials[GROUP_COLUMN] == GROUP_B, OUTCOME]

    summary_a = describe_group(a)
    summary_b = describe_group(b)

    t_stat, p_value = stats.ttest_ind(a, b, equal_var=True)

    n_a, n_b = summary_a["n"], summary_b["n"]
    df = n_a + n_b - 2
    pooled_sd = (
        ((n_a - 1) * summary_a["sd"] ** 2 + (n_b - 1) * summary_b["sd"] ** 2) / df
    ) ** 0.5

    difference = summary_a["mean"] - summary_b["mean"]
    se_difference = pooled_sd * (1.0 / n_a + 1.0 / n_b) ** 0.5
    t_crit = stats.t.ppf(0.975, df)
    ci_low = difference - t_crit * se_difference
    ci_high = difference + t_crit * se_difference
    cohens_d = difference / pooled_sd

    return {
        "summary_a": summary_a,
        "summary_b": summary_b,
        "n_total": n_a + n_b,
        "difference": difference,
        "se_difference": se_difference,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "t_stat": float(t_stat),
        "df": df,
        "p_value": float(p_value),
        "pooled_sd": pooled_sd,
        "cohens_d": cohens_d,
    }


def main():
    trials = load_trials()

    print("Rowing training-block study: 500 m ergometer mean power")
    print("=" * 60)
    print("rows read:            %d" % len(trials))
    print("rower codes present:  %d" % trials["rower_id"].nunique())
    print("trials per rower:     %s"
          % sorted(trials.groupby("rower_id").size().unique().tolist()))
    print()

    result = compare_blocks(trials)

    print("Group summaries (watts)")
    print("-" * 60)
    header = "%-12s %5s %9s %8s %8s %8s" % ("block", "n", "mean", "sd", "min", "max")
    print(header)
    for name, summary in ((GROUP_A, result["summary_a"]), (GROUP_B, result["summary_b"])):
        print("%-12s %5d %9.2f %8.2f %8.1f %8.1f"
              % (name, summary["n"], summary["mean"], summary["sd"],
                 summary["min"], summary["max"]))
    print()

    print("Independent two-sample t-test (%s vs %s), all rows" % (GROUP_A, GROUP_B))
    print("-" * 60)
    print("observations:         %d" % result["n_total"])
    print("mean difference:      %.2f W" % result["difference"])
    print("standard error:       %.2f W" % result["se_difference"])
    print("95%% CI:               [%.2f, %.2f] W" % (result["ci_low"], result["ci_high"]))
    print("pooled SD:            %.2f W" % result["pooled_sd"])
    print("t(%d):                 %.3f" % (result["df"], result["t_stat"]))
    print("p-value:              %.6f" % result["p_value"])
    print("Cohen's d:            %.3f" % result["cohens_d"])


if __name__ == "__main__":
    main()
