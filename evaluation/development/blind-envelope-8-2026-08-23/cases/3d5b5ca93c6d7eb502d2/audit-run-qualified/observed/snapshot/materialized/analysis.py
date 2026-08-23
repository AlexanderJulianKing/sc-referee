"""Evolved fitness cost of efflux-pump-inhibitor selection.

Compares maximum growth rate between the two selection regimes of a 30-day
experimental evolution study in a bacterial pathogen. Every assay run in
growth_rates.csv enters the comparison as one observation.

Run:  python3 analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "growth_rates.csv"

INHIBITOR = "inhibitor"
PLAIN = "plain"
RESPONSE = "growth_rate_per_h"
GROUP = "selection_regime"


def load_data(path=DATA_FILE):
    """Read the assay table and check it has the shape the study describes."""
    df = pd.read_csv(path)

    expected_columns = [
        "lineage_id",
        "selection_regime",
        "replicate_run",
        "growth_rate_per_h",
        "plate_id",
        "well",
        "final_od600",
    ]
    missing = [c for c in expected_columns if c not in df.columns]
    if missing:
        raise ValueError(f"growth_rates.csv is missing columns: {missing}")

    if df[RESPONSE].isna().any():
        raise ValueError("growth_rates.csv has missing growth-rate values")

    regimes = set(df[GROUP].unique())
    if regimes != {INHIBITOR, PLAIN}:
        raise ValueError(f"unexpected selection_regime values: {sorted(regimes)}")

    return df


def describe_group(values):
    """Mean, standard deviation and count for one regime."""
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "sem": float(values.std(ddof=1) / (values.size ** 0.5)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def compare_regimes(df):
    """Independent two-sample t-test on maximum growth rate.

    Each assay run in the table is one observation entering the test, so the
    sample size is the total number of rows in each regime.
    """
    inhibitor = df.loc[df[GROUP] == INHIBITOR, RESPONSE]
    plain = df.loc[df[GROUP] == PLAIN, RESPONSE]

    # Welch's version, which does not assume the two regimes share a variance.
    t_stat, p_value = stats.ttest_ind(inhibitor, plain, equal_var=False)

    inh = describe_group(inhibitor)
    pln = describe_group(plain)

    # Welch-Satterthwaite degrees of freedom, reported alongside the statistic.
    v_i = inh["sd"] ** 2 / inh["n"]
    v_p = pln["sd"] ** 2 / pln["n"]
    df_welch = (v_i + v_p) ** 2 / (
        v_i ** 2 / (inh["n"] - 1) + v_p ** 2 / (pln["n"] - 1)
    )

    diff = inh["mean"] - pln["mean"]
    se_diff = (v_i + v_p) ** 0.5
    crit = stats.t.ppf(0.975, df_welch)
    ci = (diff - crit * se_diff, diff + crit * se_diff)

    # Hedges-corrected standardised difference, on the pooled standard deviation.
    pooled_sd = (
        ((inh["n"] - 1) * inh["sd"] ** 2 + (pln["n"] - 1) * pln["sd"] ** 2)
        / (inh["n"] + pln["n"] - 2)
    ) ** 0.5
    cohens_d = diff / pooled_sd

    return {
        "inhibitor": inh,
        "plain": pln,
        "n_total": inh["n"] + pln["n"],
        "difference": diff,
        "percent_change": 100.0 * diff / pln["mean"],
        "ci95": ci,
        "t_stat": float(t_stat),
        "df": float(df_welch),
        "p_value": float(p_value),
        "cohens_d": float(cohens_d),
    }


def main():
    df = load_data()
    result = compare_regimes(df)

    inh = result["inhibitor"]
    pln = result["plain"]

    print("Maximum growth rate by selection regime")
    print("=" * 62)
    print(f"rows in table                 : {len(df)}")
    print(f"lineages assayed              : {df['lineage_id'].nunique()}")
    print(f"assay plates                  : {df['plate_id'].nunique()}")
    print(f"observations entering the test: {result['n_total']}")
    print()
    print(f"{'regime':<12}{'n':>5}{'mean':>10}{'sd':>10}{'sem':>10}{'min':>9}{'max':>9}")
    for name, g in (("inhibitor", inh), ("plain", pln)):
        print(
            f"{name:<12}{g['n']:>5}{g['mean']:>10.4f}{g['sd']:>10.4f}"
            f"{g['sem']:>10.4f}{g['min']:>9.4f}{g['max']:>9.4f}"
        )
    print()
    print(f"difference (inhibitor - plain): {result['difference']:+.4f} per hour")
    print(
        f"95% CI of the difference      : "
        f"[{result['ci95'][0]:.4f}, {result['ci95'][1]:.4f}] per hour"
    )
    print(f"change relative to plain      : {result['percent_change']:+.1f} %")
    print()
    print("Independent two-sample t-test (Welch)")
    print(f"  t         = {result['t_stat']:.4f}")
    print(f"  df        = {result['df']:.2f}")
    print(f"  p         = {result['p_value']:.6g}")
    print(f"  Cohen's d = {result['cohens_d']:.3f}")
    print()
    print("Final OD600 by regime (context measure, not tested)")
    for name in (INHIBITOR, PLAIN):
        od = df.loc[df[GROUP] == name, "final_od600"]
        print(f"  {name:<10} mean {od.mean():.3f}   sd {od.std(ddof=1):.3f}")


if __name__ == "__main__":
    main()
