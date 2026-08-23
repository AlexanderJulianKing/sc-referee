"""Larval crowding and adult body size in Anopheles.

Reads the measured wing lengths, summarises each larval density treatment, and
compares adult female wing length between the low and high density treatments
with an independent two-sample t test. Each measured female contributes one
wing measurement to the comparison.

Run:  /usr/local/bin/python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

CSV_FILE = "wing_lengths.csv"
MEASURE = "wing.length.mm"
GROUP = "density.treatment"
LEVELS = ("low", "high")


def load_measurements():
    """Read the wing measurements."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_FILE)
    data = pd.read_csv(path)
    return data


def describe_treatment(values):
    """Summary statistics for one density treatment."""
    n = int(values.size)
    mean = float(values.mean())
    sd = float(values.std(ddof=1))
    return {
        "n": n,
        "mean": mean,
        "sd": sd,
        "sem": sd / (n ** 0.5),
        "min": float(values.min()),
        "max": float(values.max()),
        "median": float(values.median()),
    }


def main():
    data = load_measurements()

    print("Wing length of adult female Anopheles reared at two larval densities")
    print("=" * 70)
    print("Wing measurements read: {}".format(len(data)))
    print("Emergence days spanned: {} to {}".format(
        int(data["emergence.day"].min()), int(data["emergence.day"].max())
    ))
    print()

    wing = {level: data.loc[data[GROUP] == level, MEASURE] for level in LEVELS}
    summary = {level: describe_treatment(wing[level]) for level in LEVELS}

    print("Summary by larval density treatment")
    print("-" * 70)
    header = "{:<8}{:>6}{:>10}{:>10}{:>10}{:>10}{:>10}"
    print(header.format("density", "n", "mean", "sd", "sem", "min", "max"))
    for level in LEVELS:
        s = summary[level]
        print("{:<8}{:>6d}{:>10.3f}{:>10.3f}{:>10.3f}{:>10.2f}{:>10.2f}".format(
            level, s["n"], s["mean"], s["sd"], s["sem"], s["min"], s["max"]
        ))
    print()
    print("n is the number of measured adult females in the treatment.")
    print()

    # Independent two-sample t test (Welch), each measured female one observation.
    t_stat, p_value = stats.ttest_ind(
        wing["low"], wing["high"], equal_var=False
    )

    n_low = summary["low"]["n"]
    n_high = summary["high"]["n"]
    sd_low = summary["low"]["sd"]
    sd_high = summary["high"]["sd"]

    # Welch-Satterthwaite degrees of freedom.
    v_low = sd_low ** 2 / n_low
    v_high = sd_high ** 2 / n_high
    df = (v_low + v_high) ** 2 / (
        v_low ** 2 / (n_low - 1) + v_high ** 2 / (n_high - 1)
    )

    diff = summary["low"]["mean"] - summary["high"]["mean"]
    se_diff = (v_low + v_high) ** 0.5
    t_crit = stats.t.ppf(0.975, df)
    ci_low = diff - t_crit * se_diff
    ci_high = diff + t_crit * se_diff

    # Standardised effect size (Hedges' g) on the measured females.
    pooled_sd = (
        ((n_low - 1) * sd_low ** 2 + (n_high - 1) * sd_high ** 2)
        / (n_low + n_high - 2)
    ) ** 0.5
    cohens_d = diff / pooled_sd
    correction = 1.0 - 3.0 / (4.0 * (n_low + n_high) - 9.0)
    hedges_g = cohens_d * correction

    print("Independent two-sample t test (Welch), low vs high larval density")
    print("-" * 70)
    print("n (low density)          : {}".format(n_low))
    print("n (high density)         : {}".format(n_high))
    print("mean difference (low - high) : {:.4f} mm".format(diff))
    print("95% CI of the difference     : {:.4f} to {:.4f} mm".format(ci_low, ci_high))
    print("t statistic              : {:.4f}".format(t_stat))
    print("degrees of freedom       : {:.2f}".format(df))
    print("p value                  : {:.3e}".format(p_value))
    print("Cohen's d                : {:.3f}".format(cohens_d))
    print("Hedges' g                : {:.3f}".format(hedges_g))
    print()

    pct = 100.0 * diff / summary["low"]["mean"]
    print("Wing length at high larval density is {:.2f}% shorter than at low".format(pct))
    print("larval density.")


if __name__ == "__main__":
    main()
