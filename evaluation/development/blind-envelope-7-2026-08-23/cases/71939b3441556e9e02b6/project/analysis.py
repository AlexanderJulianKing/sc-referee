"""Grove irrigation trial: oil content under full-season vs deficit irrigation.

Reads the committed data table `olive_oil_content.csv` and compares oil content
(percentage of fruit fresh weight) between the two irrigation regimes with an
independent two-sample t-test. Every canopy-position sample in the table is one
observation in that test.

Run:  python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "olive_oil_content.csv")

OUTCOME = "oil_content_pct"
GROUP = "irrigation_regime"
REGIMES = ["full", "deficit"]


def load_data(path):
    """Load the committed CSV and check it against the recorded design."""
    data = pd.read_csv(path)

    expected_columns = ["tree_id", GROUP, "canopy_position", OUTCOME]
    missing = [name for name in expected_columns if name not in data.columns]
    if missing:
        raise ValueError("data table is missing columns: {}".format(missing))

    if data[OUTCOME].isna().any():
        raise ValueError("data table has missing oil content values")

    found = sorted(data[GROUP].unique())
    if found != sorted(REGIMES):
        raise ValueError("unexpected irrigation regimes: {}".format(found))

    return data


def describe_groups(data):
    """Group means, standard deviations and sample sizes, one row per regime."""
    summary = (
        data.groupby(GROUP)[OUTCOME]
        .agg(n_samples="count", mean="mean", sd="std", minimum="min", maximum="max")
        .reindex(REGIMES)
    )
    return summary


def compare_regimes(data):
    """Independent two-sample t-test on every canopy-position sample."""
    full = data.loc[data[GROUP] == "full", OUTCOME]
    deficit = data.loc[data[GROUP] == "deficit", OUTCOME]

    result = stats.ttest_ind(deficit, full)
    df = len(deficit) + len(full) - 2

    return {
        "n_full": len(full),
        "n_deficit": len(deficit),
        "mean_full": full.mean(),
        "mean_deficit": deficit.mean(),
        "sd_full": full.std(ddof=1),
        "sd_deficit": deficit.std(ddof=1),
        "difference": deficit.mean() - full.mean(),
        "t_statistic": result.statistic,
        "p_value": result.pvalue,
        "df": df,
    }


def main():
    data = load_data(DATA_PATH)

    print("Grove irrigation trial: oil content by irrigation regime")
    print("=" * 62)
    print("rows in table: {}".format(len(data)))
    print("trees in table: {}".format(data["tree_id"].nunique()))
    print("canopy positions per tree: {}".format(
        int(data.groupby("tree_id")["canopy_position"].count().unique()[0])
    ))
    print()

    summary = describe_groups(data)
    print("Group summary (oil content, % of fruit fresh weight)")
    print(summary.round(3).to_string())
    print()

    test = compare_regimes(data)
    print("Independent two-sample t-test (deficit vs full)")
    print("-" * 62)
    print("n (full irrigation samples):     {}".format(test["n_full"]))
    print("n (deficit irrigation samples):  {}".format(test["n_deficit"]))
    print("mean full:      {:.3f} %  (sd {:.3f})".format(test["mean_full"], test["sd_full"]))
    print("mean deficit:   {:.3f} %  (sd {:.3f})".format(test["mean_deficit"], test["sd_deficit"]))
    print("difference (deficit - full): {:+.3f} percentage points".format(test["difference"]))
    print("t = {:.4f}  df = {}  p = {:.6g}".format(
        test["t_statistic"], test["df"], test["p_value"]
    ))


if __name__ == "__main__":
    main()
