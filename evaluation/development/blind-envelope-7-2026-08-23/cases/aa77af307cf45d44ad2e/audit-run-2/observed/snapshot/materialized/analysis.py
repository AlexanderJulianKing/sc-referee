"""Rearing condition and cortical response threshold in gerbil A1.

Compares the response threshold at characteristic frequency between
quiet-reared and noise-reared animals, using every recorded single unit
as one observation in a standard independent two-sample t-test.

Run:  python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "unit_thresholds.csv")

OUTCOME = "cf_threshold_db_spl"
GROUP = "rearing_condition"


def load():
    df = pd.read_csv(DATA)
    expected = ["animal_id", "rearing_condition", "unit_id", "cf_threshold_db_spl"]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise SystemExit("missing column(s) in %s: %s" % (DATA, ", ".join(missing)))
    if df[OUTCOME].isna().any():
        raise SystemExit("missing threshold values in %s" % DATA)
    return df


def describe(values):
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def main():
    df = load()

    quiet = df.loc[df[GROUP] == "quiet", OUTCOME]
    noise = df.loc[df[GROUP] == "noise", OUTCOME]

    q = describe(quiet)
    n = describe(noise)

    t_stat, p_value = stats.ttest_ind(noise, quiet, equal_var=True)
    df_resid = q["n"] + n["n"] - 2
    diff = n["mean"] - q["mean"]

    print("Single-unit thresholds at characteristic frequency (dB SPL)")
    print("Data file: %s" % os.path.basename(DATA))
    print("Total units recorded: %d" % len(df))
    print("Animals contributing units: %d" % df["animal_id"].nunique())
    print()

    header = "%-8s %5s %8s %8s %8s %8s" % ("group", "n", "mean", "sd", "min", "max")
    print(header)
    print("-" * len(header))
    for name, s in (("quiet", q), ("noise", n)):
        print("%-8s %5d %8.2f %8.2f %8.1f %8.1f"
              % (name, s["n"], s["mean"], s["sd"], s["min"], s["max"]))
    print()

    print("Difference in mean threshold (noise - quiet): %.2f dB SPL" % diff)
    print("Independent two-sample t-test (equal variances assumed):")
    print("  t(%d) = %.3f" % (df_resid, t_stat))
    print("  p = %.3e" % p_value)
    print("  sample size = %d quiet units, %d noise units" % (q["n"], n["n"]))


if __name__ == "__main__":
    main()
