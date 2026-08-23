"""Alpaca fibre trial: does the trace-mineral supplement give finer fleece?

Reads `alpaca_fibre.csv`, compares mean fibre diameter between the supplemented
and unsupplemented rations with an independent two-sample t-test, and prints the
group means, the test statistic and the p-value.

Every monthly fibre sample in the table is one observation, so all 80 rows enter
the comparison.

Run:  python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alpaca_fibre.csv")
OUTCOME = "fibre_diameter_um"
GROUP = "diet_group"
SUPPLEMENTED = "supplemented"
UNSUPPLEMENTED = "unsupplemented"
ALPHA = 0.05


def load_data(path=DATA_FILE):
    """Load the trial table and check it is complete."""
    df = pd.read_csv(path)

    expected = [
        "alpaca_id",
        "diet_group",
        "sampling_month",
        "fibre_diameter_um",
        "age_years",
        "body_weight_kg",
    ]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError("missing column(s) in %s: %s" % (path, ", ".join(missing)))

    if df[expected].isna().any().any():
        raise ValueError("the table has missing cells; expected a complete table")

    return df


def describe_group(values):
    """Mean, standard deviation and count for one ration group."""
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def compare_groups(df):
    """Independent two-sample t-test on every fibre measurement in the table."""
    supp = df.loc[df[GROUP] == SUPPLEMENTED, OUTCOME]
    unsupp = df.loc[df[GROUP] == UNSUPPLEMENTED, OUTCOME]

    result = stats.ttest_ind(supp, unsupp)

    # Pooled standard deviation and Cohen's d, on the same observations.
    n1, n2 = supp.size, unsupp.size
    pooled_var = (
        (n1 - 1) * supp.var(ddof=1) + (n2 - 1) * unsupp.var(ddof=1)
    ) / (n1 + n2 - 2)
    pooled_sd = float(pooled_var ** 0.5)
    difference = float(supp.mean() - unsupp.mean())

    return {
        "supplemented": describe_group(supp),
        "unsupplemented": describe_group(unsupp),
        "n_total": int(n1 + n2),
        "df": int(n1 + n2 - 2),
        "difference_um": difference,
        "pooled_sd_um": pooled_sd,
        "cohens_d": difference / pooled_sd,
        "t_statistic": float(result.statistic),
        "p_value": float(result.pvalue),
    }


def monthly_means(df):
    """Group means for each sampling month, for the report's supporting table."""
    table = (
        df.groupby(["sampling_month", GROUP])[OUTCOME]
        .mean()
        .unstack(GROUP)
        .round(2)
    )
    return table[[UNSUPPLEMENTED, SUPPLEMENTED]]


def main():
    df = load_data()
    res = compare_groups(df)

    print("Alpaca fibre trial: trace-mineral supplement and mean fibre diameter")
    print("=" * 70)
    print("Rows in the table:            %d" % len(df))
    print("Animals in the table:         %d" % df["alpaca_id"].nunique())
    print("Sampling months:              %s" % ", ".join(sorted(df["sampling_month"].unique())))
    print()

    print("Group summaries (micrometres)")
    print("-" * 70)
    print("%-16s %5s %9s %8s %8s %8s" % ("group", "n", "mean", "sd", "min", "max"))
    for name in (UNSUPPLEMENTED, SUPPLEMENTED):
        g = res[name]
        print(
            "%-16s %5d %9.2f %8.2f %8.2f %8.2f"
            % (name, g["n"], g["mean"], g["sd"], g["min"], g["max"])
        )
    print()

    print("Mean fibre diameter by sampling month (micrometres)")
    print("-" * 70)
    print(monthly_means(df).to_string())
    print()

    print("Independent two-sample t-test (supplemented vs unsupplemented)")
    print("-" * 70)
    print("Observations entering the test: %d" % res["n_total"])
    print("Degrees of freedom:             %d" % res["df"])
    print("Difference in means:            %+.2f um" % res["difference_um"])
    print("Pooled SD:                      %.2f um" % res["pooled_sd_um"])
    print("Cohen's d:                      %+.2f" % res["cohens_d"])
    print("t statistic:                    %.3f" % res["t_statistic"])
    print("p-value:                        %.3e" % res["p_value"])
    print()

    verdict = "significant" if res["p_value"] < ALPHA else "not significant"
    print(
        "At alpha = %.2f the difference is %s: the supplemented group averages "
        "%.2f um %s fibre." % (
            ALPHA,
            verdict,
            abs(res["difference_um"]),
            "finer" if res["difference_um"] < 0 else "coarser",
        )
    )


if __name__ == "__main__":
    main()
