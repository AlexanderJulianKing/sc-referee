"""Farm pond smooth newt survey: body mass in buffered versus unfenced ponds.

Reads `newt_body_mass.csv` and compares adult male smooth newt body mass
between ponds ringed by a fenced grass buffer strip and ponds where livestock
can reach the water's edge.

Every weighed newt in the table is one observation in the comparison, so the
two groups enter an independent two-sample t-test with 40 and 35 observations,
75 in total.

Run:  python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "newt_body_mass.csv")

GROUP_COL = "buffer_strip"
OUTCOME_COL = "body_mass_g"
BUFFERED = "buffered"
UNFENCED = "unfenced"


def load_data(path=DATA_PATH):
    """Load the survey table, one row per weighed newt."""
    data = pd.read_csv(path)
    expected = ["pond_code", "buffer_strip", "newt_number", "body_mass_g"]
    missing = [name for name in expected if name not in data.columns]
    if missing:
        raise ValueError("missing expected column(s): %s" % ", ".join(missing))
    return data


def describe_group(values):
    """Mean, standard deviation and count for one group of body masses."""
    return {
        "n": int(values.size),
        "mean_g": float(values.mean()),
        "sd_g": float(values.std(ddof=1)),
        "min_g": float(values.min()),
        "max_g": float(values.max()),
    }


def compare_groups(data):
    """Independent two-sample t-test on body mass, one observation per row."""
    buffered = data.loc[data[GROUP_COL] == BUFFERED, OUTCOME_COL]
    unfenced = data.loc[data[GROUP_COL] == UNFENCED, OUTCOME_COL]

    result = stats.ttest_ind(buffered, unfenced)

    n_buffered = buffered.size
    n_unfenced = unfenced.size
    df = n_buffered + n_unfenced - 2

    pooled_var = (
        (n_buffered - 1) * buffered.var(ddof=1)
        + (n_unfenced - 1) * unfenced.var(ddof=1)
    ) / df
    pooled_sd = pooled_var ** 0.5
    se_diff = pooled_sd * ((1.0 / n_buffered + 1.0 / n_unfenced) ** 0.5)

    difference = float(buffered.mean() - unfenced.mean())
    t_crit = stats.t.ppf(0.975, df)
    ci_low = difference - t_crit * se_diff
    ci_high = difference + t_crit * se_diff

    return {
        "buffered": describe_group(buffered),
        "unfenced": describe_group(unfenced),
        "n_total": int(n_buffered + n_unfenced),
        "difference_g": difference,
        "se_difference_g": float(se_diff),
        "ci_low_g": float(ci_low),
        "ci_high_g": float(ci_high),
        "t_statistic": float(result.statistic),
        "df": int(df),
        "p_value": float(result.pvalue),
        "cohens_d": difference / float(pooled_sd),
    }


def report(summary):
    """Print the comparison to standard output."""
    buffered = summary["buffered"]
    unfenced = summary["unfenced"]

    print("Smooth newt body mass by pond margin condition")
    print("=" * 46)
    print(
        "buffered : n = %d, mean = %.3f g, SD = %.3f g, range %.2f-%.2f g"
        % (
            buffered["n"],
            buffered["mean_g"],
            buffered["sd_g"],
            buffered["min_g"],
            buffered["max_g"],
        )
    )
    print(
        "unfenced : n = %d, mean = %.3f g, SD = %.3f g, range %.2f-%.2f g"
        % (
            unfenced["n"],
            unfenced["mean_g"],
            unfenced["sd_g"],
            unfenced["min_g"],
            unfenced["max_g"],
        )
    )
    print("")
    print("Total observations entering the test: %d" % summary["n_total"])
    print(
        "Difference (buffered - unfenced): %.3f g (95%% CI %.3f to %.3f g)"
        % (summary["difference_g"], summary["ci_low_g"], summary["ci_high_g"])
    )
    print(
        "Independent two-sample t-test: t(%d) = %.3f, p = %.5f"
        % (summary["df"], summary["t_statistic"], summary["p_value"])
    )
    print("Cohen's d = %.3f" % summary["cohens_d"])


def main():
    data = load_data()
    print("Loaded %d weighed newts from %d ponds." % (len(data), data["pond_code"].nunique()))
    print("")
    summary = compare_groups(data)
    report(summary)
    return summary


if __name__ == "__main__":
    main()
