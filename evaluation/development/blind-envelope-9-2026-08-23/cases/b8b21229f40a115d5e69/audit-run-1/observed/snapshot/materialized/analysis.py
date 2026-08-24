"""Hepatic lead in grey squirrels: inner-city park versus rural woodland.

Reads squirrel_liver_lead.csv and compares lead_mg_per_kg_dw between the two
levels of collection_setting with an independent two-sample t-test.

Every measured row in the table enters the comparison as one observation.

Run:
    python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = "squirrel_liver_lead.csv"
OUTCOME = "lead_mg_per_kg_dw"
GROUP_COLUMN = "collection_setting"
URBAN = "urban_park"
RURAL = "rural_woodland"


def load_data():
    """Read the study table."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
    return pd.read_csv(path)


def describe_group(values):
    """Summary statistics for one group of measurements."""
    return {
        "n": int(values.shape[0]),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def main():
    data = load_data()

    urban = data.loc[data[GROUP_COLUMN] == URBAN, OUTCOME]
    rural = data.loc[data[GROUP_COLUMN] == RURAL, OUTCOME]

    urban_stats = describe_group(urban)
    rural_stats = describe_group(rural)

    total_n = int(data.shape[0])

    # Independent two-sample t-test on every row of the table.
    t_stat, p_value = stats.ttest_ind(urban, rural, equal_var=True)

    difference = urban_stats["mean"] - rural_stats["mean"]
    df = urban_stats["n"] + rural_stats["n"] - 2

    # Pooled standard deviation, for the confidence interval and effect size.
    pooled_var = (
        (urban_stats["n"] - 1) * urban_stats["sd"] ** 2
        + (rural_stats["n"] - 1) * rural_stats["sd"] ** 2
    ) / df
    pooled_sd = pooled_var ** 0.5
    se_difference = pooled_sd * (1.0 / urban_stats["n"] + 1.0 / rural_stats["n"]) ** 0.5
    t_crit = stats.t.ppf(0.975, df)
    ci_low = difference - t_crit * se_difference
    ci_high = difference + t_crit * se_difference
    cohens_d = difference / pooled_sd

    print("Hepatic lead in grey squirrels")
    print("==============================")
    print("Total observations analysed: %d" % total_n)
    print("")
    print("Group summaries (%s, mg/kg dry weight)" % OUTCOME)
    print("  %-15s n=%2d  mean=%.4f  sd=%.4f  min=%.4f  max=%.4f"
          % (URBAN, urban_stats["n"], urban_stats["mean"], urban_stats["sd"],
             urban_stats["min"], urban_stats["max"]))
    print("  %-15s n=%2d  mean=%.4f  sd=%.4f  min=%.4f  max=%.4f"
          % (RURAL, rural_stats["n"], rural_stats["mean"], rural_stats["sd"],
             rural_stats["min"], rural_stats["max"]))
    print("")
    print("Independent two-sample t-test (urban_park - rural_woodland)")
    print("  mean difference : %.4f mg/kg dry weight" % difference)
    print("  95%% CI          : %.4f to %.4f" % (ci_low, ci_high))
    print("  t(%d)           : %.4f" % (df, t_stat))
    print("  p-value         : %.6g" % p_value)
    print("  Cohen's d       : %.4f" % cohens_d)


if __name__ == "__main__":
    main()
