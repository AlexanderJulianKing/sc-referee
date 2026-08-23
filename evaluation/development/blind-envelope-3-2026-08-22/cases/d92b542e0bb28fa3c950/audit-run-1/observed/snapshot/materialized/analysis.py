"""Weaning trial: effect of a fibre supplement on gut microbial diversity.

Reads the weekly faecal sampling table and compares Shannon diversity between the
control starter ration and the fibre-supplemented ration. Every faecal sample
collected during the five study weeks enters the comparison as one observation.
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "piglet_shannon.csv")


def load_samples(path=DATA_FILE):
    """Return the faecal sampling table, one row per collected sample."""
    df = pd.read_csv(path)
    expected = [
        "piglet_id",
        "ration",
        "week",
        "shannon_diversity",
        "body_weight_kg",
        "read_depth",
    ]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError("data file is missing columns: %s" % ", ".join(missing))
    return df


def describe_samples(df):
    """Print the size and shape of the collected sample set."""
    n_samples = len(df)
    print("=" * 62)
    print("FAECAL SAMPLE SET")
    print("=" * 62)
    print("Faecal samples analysed (n) : %d" % n_samples)
    print("Piglets sampled             : %d" % df["piglet_id"].nunique())
    print("Study weeks                 : %d (week %d to week %d)"
          % (df["week"].nunique(), df["week"].min(), df["week"].max()))
    print("Rations                     : %s" % ", ".join(sorted(df["ration"].unique())))
    print()

    print("Weekly means across all piglets")
    weekly = df.groupby("week").agg(
        n_samples=("shannon_diversity", "size"),
        shannon_mean=("shannon_diversity", "mean"),
        body_weight_kg_mean=("body_weight_kg", "mean"),
        read_depth_mean=("read_depth", "mean"),
    )
    print(weekly.round(3).to_string())
    print()
    print("Read depth over all samples : mean %.0f, min %d, max %d"
          % (df["read_depth"].mean(), df["read_depth"].min(), df["read_depth"].max()))
    print()
    return n_samples


def summarise_groups(df):
    """Print per-ration sample counts, means and spreads of Shannon diversity."""
    print("=" * 62)
    print("SHANNON DIVERSITY BY RATION")
    print("=" * 62)
    summary = df.groupby("ration")["shannon_diversity"].agg(
        n_samples="size", mean="mean", sd="std", sem="sem", minimum="min", maximum="max"
    )
    print(summary.round(4).to_string())
    print()

    print("Shannon diversity by ration and week")
    by_week = df.pivot_table(
        index="week", columns="ration", values="shannon_diversity", aggfunc="mean"
    )
    print(by_week.round(3).to_string())
    print()
    return summary


def compare_rations(df):
    """Independent two-sample t-test on Shannon diversity, sample by sample."""
    control = df.loc[df["ration"] == "control", "shannon_diversity"]
    supplement = df.loc[df["ration"] == "supplement", "shannon_diversity"]

    t_stat, p_value = stats.ttest_ind(supplement, control, equal_var=True)

    n_c, n_s = len(control), len(supplement)
    df_resid = n_c + n_s - 2
    diff = supplement.mean() - control.mean()
    pooled_sd = (((n_c - 1) * control.var(ddof=1) + (n_s - 1) * supplement.var(ddof=1))
                 / df_resid) ** 0.5
    se_diff = pooled_sd * ((1.0 / n_c + 1.0 / n_s) ** 0.5)
    t_crit = stats.t.ppf(0.975, df_resid)
    ci_low, ci_high = diff - t_crit * se_diff, diff + t_crit * se_diff
    cohens_d = diff / pooled_sd

    print("=" * 62)
    print("INDEPENDENT TWO-SAMPLE T-TEST (supplement vs control)")
    print("=" * 62)
    print("Observations per group      : control %d, supplement %d" % (n_c, n_s))
    print("Total samples in the test   : %d" % (n_c + n_s))
    print("Control mean (SD)           : %.4f (%.4f)" % (control.mean(), control.std(ddof=1)))
    print("Supplement mean (SD)        : %.4f (%.4f)" % (supplement.mean(), supplement.std(ddof=1)))
    print("Mean difference             : %.4f" % diff)
    print("Pooled SD                   : %.4f" % pooled_sd)
    print("SE of the difference        : %.4f" % se_diff)
    print("95%% CI of the difference    : (%.4f, %.4f)" % (ci_low, ci_high))
    print("Cohen's d                   : %.4f" % cohens_d)
    print("t statistic                 : %.4f" % t_stat)
    print("Degrees of freedom          : %d" % df_resid)
    print("p value                     : %.3e" % p_value)
    print()
    return {
        "n_control": n_c,
        "n_supplement": n_s,
        "diff": diff,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "pooled_sd": pooled_sd,
        "cohens_d": cohens_d,
        "t_stat": t_stat,
        "df": df_resid,
        "p_value": p_value,
    }


def main():
    df = load_samples()
    n_samples = describe_samples(df)
    summarise_groups(df)
    result = compare_rations(df)

    print("=" * 62)
    print("CONCLUSION")
    print("=" * 62)
    verdict = "higher" if result["diff"] > 0 else "lower"
    print("Across %d faecal samples, Shannon diversity was %.4f units %s on the"
          % (n_samples, abs(result["diff"]), verdict))
    print("fibre-supplemented ration than on the control ration")
    print("(t(%d) = %.3f, p = %.3e)." % (result["df"], result["t_stat"], result["p_value"]))


if __name__ == "__main__":
    main()
