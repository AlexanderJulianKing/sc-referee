"""Doe-nutrition trial: compare kit weaning weight between the two rations.

Reads `kit_weaning_weights.csv`, describes the standard and supplemented diet
groups, and compares `weaning_weight_g` between them with an independent
two-sample t-test. Every weighed kit row is one observation in the test, and the
reported sample size for each group is the total number of kit rows in it.

Run:
    python3 analysis.py
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "kit_weaning_weights.csv")

GROUPS = ("standard", "supplemented")
ALPHA = 0.05


def load_data(path=CSV_PATH):
    """Read the kit-level CSV and check the columns are the ones expected."""
    frame = pd.read_csv(path)

    expected = [
        "doe_id",
        "diet_group",
        "litter_size",
        "kit_number",
        "weaning_weight_g",
    ]
    missing = [column for column in expected if column not in frame.columns]
    if missing:
        raise ValueError("CSV is missing column(s): %s" % ", ".join(missing))

    unexpected = sorted(set(frame["diet_group"]) - set(GROUPS))
    if unexpected:
        raise ValueError("Unexpected diet_group value(s): %s" % ", ".join(unexpected))

    if frame[expected].isna().any().any():
        raise ValueError("CSV contains missing values")

    # litter_size must agree with the number of kit rows carried by that doe.
    rows_per_doe = frame.groupby("doe_id")["weaning_weight_g"].size()
    stated_size = frame.groupby("doe_id")["litter_size"].first()
    mismatched = sorted(stated_size.index[stated_size != rows_per_doe])
    if mismatched:
        raise ValueError(
            "litter_size does not match the kit row count for doe(s): %s"
            % ", ".join(mismatched)
        )

    return frame


def describe_groups(frame):
    """Summarise weaning weight in each diet group, kit rows being the count."""
    rows = []
    for group in GROUPS:
        block = frame.loc[frame["diet_group"] == group, :]
        weights = block["weaning_weight_g"].to_numpy(dtype=float)
        rows.append(
            {
                "diet_group": group,
                "does": block["doe_id"].nunique(),
                "n_kits": int(weights.size),
                "mean_g": float(np.mean(weights)),
                "sd_g": float(np.std(weights, ddof=1)),
                "sem_g": float(stats.sem(weights)),
                "min_g": float(np.min(weights)),
                "median_g": float(np.median(weights)),
                "max_g": float(np.max(weights)),
                "min_litter_size": int(block["litter_size"].min()),
                "max_litter_size": int(block["litter_size"].max()),
            }
        )
    return pd.DataFrame(rows).set_index("diet_group")


def compare_groups(frame):
    """Independent two-sample t-test on kit weaning weight (Welch's version)."""
    standard = frame.loc[
        frame["diet_group"] == "standard", "weaning_weight_g"
    ].to_numpy(dtype=float)
    supplemented = frame.loc[
        frame["diet_group"] == "supplemented", "weaning_weight_g"
    ].to_numpy(dtype=float)

    n_std, n_sup = standard.size, supplemented.size
    mean_std, mean_sup = float(np.mean(standard)), float(np.mean(supplemented))
    var_std = float(np.var(standard, ddof=1))
    var_sup = float(np.var(supplemented, ddof=1))

    result = stats.ttest_ind(supplemented, standard, equal_var=False)
    t_stat = float(result.statistic)
    p_value = float(result.pvalue)

    # Welch standard error and Welch-Satterthwaite degrees of freedom.
    se_diff = float(np.sqrt(var_std / n_std + var_sup / n_sup))
    df = (var_std / n_std + var_sup / n_sup) ** 2 / (
        (var_std / n_std) ** 2 / (n_std - 1) + (var_sup / n_sup) ** 2 / (n_sup - 1)
    )
    df = float(df)

    difference = mean_sup - mean_std
    t_crit = float(stats.t.ppf(1.0 - ALPHA / 2.0, df))
    ci_low = difference - t_crit * se_diff
    ci_high = difference + t_crit * se_diff

    # Pooled-SD effect size for the two groups.
    pooled_sd = float(
        np.sqrt(
            ((n_std - 1) * var_std + (n_sup - 1) * var_sup) / (n_std + n_sup - 2)
        )
    )
    cohens_d = difference / pooled_sd

    return {
        "n_standard": int(n_std),
        "n_supplemented": int(n_sup),
        "mean_standard_g": mean_std,
        "mean_supplemented_g": mean_sup,
        "difference_g": float(difference),
        "se_difference_g": se_diff,
        "t": t_stat,
        "df": df,
        "p_value": p_value,
        "ci_low_g": float(ci_low),
        "ci_high_g": float(ci_high),
        "pooled_sd_g": pooled_sd,
        "cohens_d": float(cohens_d),
        "alpha": ALPHA,
    }


def main():
    frame = load_data()

    print("Doe-nutrition trial: kit weaning weight at day 35")
    print("=" * 62)
    print("Kit rows read:      %d" % len(frame))
    print("Does (litters):     %d" % frame["doe_id"].nunique())
    print()

    summary = describe_groups(frame)
    print("Group description (one observation = one weighed kit)")
    print("-" * 62)
    for group in GROUPS:
        row = summary.loc[group]
        print("%s:" % group)
        print("  does (litters)      %d" % int(row["does"]))
        print("  litter sizes        %d to %d kits"
              % (int(row["min_litter_size"]), int(row["max_litter_size"])))
        print("  n (kit rows)        %d" % int(row["n_kits"]))
        print("  mean weaning weight %.1f g" % row["mean_g"])
        print("  SD                  %.1f g" % row["sd_g"])
        print("  SEM                 %.1f g" % row["sem_g"])
        print("  min / median / max  %.1f / %.1f / %.1f g"
              % (row["min_g"], row["median_g"], row["max_g"]))
        print()

    test = compare_groups(frame)
    print("Independent two-sample t-test (Welch), supplemented minus standard")
    print("-" * 62)
    print("  n standard          %d kits" % test["n_standard"])
    print("  n supplemented      %d kits" % test["n_supplemented"])
    print("  mean difference     %+.1f g" % test["difference_g"])
    print("  SE of difference    %.1f g" % test["se_difference_g"])
    print("  95%% CI              %.1f to %.1f g"
          % (test["ci_low_g"], test["ci_high_g"]))
    print("  t                   %.3f" % test["t"])
    print("  df                  %.2f" % test["df"])
    print("  p                   %.3e" % test["p_value"])
    print("  Cohen's d           %.3f (pooled SD %.1f g)"
          % (test["cohens_d"], test["pooled_sd_g"]))
    print()

    verdict = "reject" if test["p_value"] < ALPHA else "do not reject"
    print("At alpha = %.2f we %s the null hypothesis of equal mean weaning "
          "weight." % (ALPHA, verdict))

    return summary, test


if __name__ == "__main__":
    main()
