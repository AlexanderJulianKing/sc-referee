"""Novel-object recognition: does environmental enrichment improve recognition memory?

Design. 18 adult male rats, assigned as whole animals to enriched (9) or standard (9)
housing. Each rat was run through 8 novel-object recognition tests on separate days, so
`data.csv` holds 144 rows: one row per test run, eight rows per rat.

Experimental unit. Housing was assigned to the animal, not to the test run, so the rat is
the independent experimental unit. The eight runs belonging to one rat are not independent
of each other. This script therefore reduces each rat's eight runs to that rat's single
mean discrimination index FIRST, and only then compares the two housing groups. The test
is run on 18 per-animal values, not on 144 run-level rows, and the reported sample size is
the number of rats.

Test. Welch's independent two-sample t-test on the difference in group means of the
per-animal mean discrimination index. Welch's version does not assume the two groups share
a variance.

The data file is left untouched at run level; the reduction happens here only.
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = "data.csv"
OUTCOME = "discrimination_index"
UNIT = "rat_id"
GROUP = "housing"
GROUP_LEVELS = ("enriched", "standard")


def load_runs():
    """Read the run-level data file that sits next to this script."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
    return pd.read_csv(path)


def reduce_to_animals(runs):
    """Collapse each rat's runs to one row: that rat's mean discrimination index.

    Housing is constant within a rat (it was assigned to the whole animal), so carrying it
    through the groupby is safe; the assertion below checks that rather than assuming it.
    """
    per_rat_housing = runs.groupby(UNIT)[GROUP].nunique()
    assert (per_rat_housing == 1).all(), "a rat_id carries more than one housing label"

    animals = (
        runs.groupby([UNIT, GROUP], as_index=False)
        .agg(n_runs=(OUTCOME, "size"), mean_di=(OUTCOME, "mean"))
        .sort_values(UNIT)
        .reset_index(drop=True)
    )
    return animals


def describe(values):
    """Mean, standard deviation (sample, n-1) and count for one group of animals."""
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def main():
    runs = load_runs()

    print("=" * 72)
    print("Environmental enrichment and novel-object recognition memory")
    print("=" * 72)

    print("\n--- Data as read (run level) ---")
    print("rows (test runs)        : %d" % len(runs))
    print("distinct rats           : %d" % runs[UNIT].nunique())
    print("runs per rat            : %s" % sorted(runs.groupby(UNIT).size().unique()))
    print("missing values          : %d" % int(runs.isna().sum().sum()))
    print(
        "duplicate rat+run pairs : %d"
        % int(runs.duplicated(subset=[UNIT, "run_number"]).sum())
    )
    print(
        "exploration_time_s      : mean %.2f s, range %.1f-%.1f s"
        % (
            runs["exploration_time_s"].mean(),
            runs["exploration_time_s"].min(),
            runs["exploration_time_s"].max(),
        )
    )

    animals = reduce_to_animals(runs)

    print("\n--- Reduction to the experimental unit ---")
    print("The rat is the unit that was assigned to a housing condition, so each rat's")
    print("eight runs are averaged into one value before any group comparison.")
    print("animals after reduction : %d" % len(animals))
    print("\nPer-animal mean discrimination index:")
    print(
        animals.rename(columns={"mean_di": "mean_discrimination_index"}).to_string(
            index=False, float_format=lambda v: "%.4f" % v
        )
    )

    enriched = animals.loc[animals[GROUP] == GROUP_LEVELS[0], "mean_di"].to_numpy()
    standard = animals.loc[animals[GROUP] == GROUP_LEVELS[1], "mean_di"].to_numpy()

    enr = describe(enriched)
    std = describe(standard)

    print("\n--- Group summaries (unit = rat) ---")
    print("group      n(rats)     mean       SD      min      max")
    for name, s in (("enriched", enr), ("standard", std)):
        print(
            "%-9s %7d   %.4f   %.4f   %.4f   %.4f"
            % (name, s["n"], s["mean"], s["sd"], s["min"], s["max"])
        )

    diff = enr["mean"] - std["mean"]

    result = stats.ttest_ind(enriched, standard, equal_var=False)
    t_stat = float(result.statistic)
    p_value = float(result.pvalue)

    # Welch-Satterthwaite degrees of freedom and the 95% CI for the difference in means.
    se_enr_sq = enr["sd"] ** 2 / enr["n"]
    se_std_sq = std["sd"] ** 2 / std["n"]
    se_diff = (se_enr_sq + se_std_sq) ** 0.5
    df = (se_enr_sq + se_std_sq) ** 2 / (
        se_enr_sq**2 / (enr["n"] - 1) + se_std_sq**2 / (std["n"] - 1)
    )
    t_crit = stats.t.ppf(0.975, df)
    ci_low = diff - t_crit * se_diff
    ci_high = diff + t_crit * se_diff

    print("\n--- Welch's independent two-sample t-test on per-animal means ---")
    print("sample size             : %d rats (%d enriched, %d standard)"
          % (enr["n"] + std["n"], enr["n"], std["n"]))
    print("difference in means     : %.4f (enriched minus standard)" % diff)
    print("standard error of diff  : %.4f" % se_diff)
    print("95%% CI for difference   : [%.4f, %.4f]" % (ci_low, ci_high))
    print("t statistic             : %.4f" % t_stat)
    print("degrees of freedom      : %.3f" % df)
    print("p-value                 : %.6g" % p_value)

    print("\n--- Interpretation ---")
    direction = "higher" if diff > 0 else "lower"
    print(
        "Enriched-housed rats had a mean discrimination index %.4f %s than"
        % (abs(diff), direction)
    )
    print(
        "standard-housed rats. With 18 animals the test gives p = %.6g." % p_value
    )
    print(
        "%s at the 0.05 level."
        % ("Difference is statistically significant" if p_value < 0.05
           else "Difference is not statistically significant")
    )
    print(
        "Note: the p-value describes the 18 animals, not the 144 runs. Treating each run"
    )
    print(
        "as independent would overstate the sample size, because runs within a rat share"
    )
    print("the same animal.")


if __name__ == "__main__":
    main()
