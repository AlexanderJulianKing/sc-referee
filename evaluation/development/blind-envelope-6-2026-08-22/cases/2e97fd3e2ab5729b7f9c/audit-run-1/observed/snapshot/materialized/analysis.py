"""Sugar kelp seeding-density trial: compare blade length between two seeding densities.

The raw file holds one row per measured blade, ten blades per dropper line.
Blades on the same dropper line are not independent of one another: the whole
line received one seeding density, and the blades on it share that line's
growing conditions. The dropper line is therefore the unit of replication.

This script:
  1. reads the raw blade file,
  2. reduces it to one mean blade length per dropper line (14 values),
  3. runs one independent two-sample test on those 14 per-line averages,
     7 per seeding density.

No inferential test is run on individual blades. The blade count is printed
only to describe the sampling effort.
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "kelp_blades.csv")

UNIT_COLUMN = "dropper_line"
GROUP_COLUMN = "seeding_density"
RESPONSE_COLUMN = "blade_length_cm"
GROUPS = ("standard", "reduced")


def load_blades(path):
    """Read the raw blade-level file."""
    return pd.read_csv(path)


def per_line_means(blades):
    """Collapse the blade rows to one mean blade length per dropper line.

    Returns one row per dropper line with its seeding density and its mean
    blade length. This is the averaging step that makes the dropper line, not
    the blade, the row that enters the test.
    """
    lines = (
        blades.groupby([UNIT_COLUMN, GROUP_COLUMN], as_index=False)
        .agg(
            mean_blade_length_cm=(RESPONSE_COLUMN, "mean"),
            n_blades=(RESPONSE_COLUMN, "size"),
        )
        .sort_values(UNIT_COLUMN)
        .reset_index(drop=True)
    )
    return lines


def describe_group(lines, group):
    values = lines.loc[lines[GROUP_COLUMN] == group, "mean_blade_length_cm"].to_numpy()
    return {
        "group": group,
        "n_lines": int(values.size),
        "mean": float(np.mean(values)),
        "sd": float(np.std(values, ddof=1)),
        "sem": float(stats.sem(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "values": values,
    }


def main():
    blades = load_blades(CSV_PATH)

    n_blade_rows = int(len(blades))
    blades_per_line = blades.groupby(UNIT_COLUMN).size()

    lines = per_line_means(blades)
    n_lines = int(len(lines))

    print("Sugar kelp seeding-density trial")
    print("=" * 64)
    print()
    print("Sampling effort (description only, not the sample size of the test)")
    print("-" * 64)
    lo, hi = int(blades_per_line.min()), int(blades_per_line.max())
    per_line_text = "%d" % lo if lo == hi else "%d-%d" % (lo, hi)
    print("Measured blades in the raw file : %d" % n_blade_rows)
    print("Blades measured per dropper line: %s" % per_line_text)
    print("Longlines                       : 1 (all dropper lines hang from it)")
    print()

    print("Averaging step: blades -> dropper lines")
    print("-" * 64)
    print("Each dropper line's ten blade lengths are averaged into one value.")
    print("Per-line mean blade length (cm):")
    for _, row in lines.iterrows():
        print("  %-4s  %-9s  %7.2f cm  (from %d blades)"
              % (row[UNIT_COLUMN], row[GROUP_COLUMN],
                 row["mean_blade_length_cm"], int(row["n_blades"])))
    print()
    print("Dropper lines entering the test (the sample size): %d" % n_lines)
    print()

    summaries = {g: describe_group(lines, g) for g in GROUPS}

    print("Group summaries of the per-line averages")
    print("-" * 64)
    print("%-10s %7s %10s %9s %9s %9s %9s"
          % ("density", "n_lines", "mean_cm", "sd_cm", "sem_cm", "min_cm", "max_cm"))
    for g in GROUPS:
        s = summaries[g]
        print("%-10s %7d %10.2f %9.2f %9.2f %9.2f %9.2f"
              % (s["group"], s["n_lines"], s["mean"], s["sd"], s["sem"],
                 s["min"], s["max"]))
    print()

    standard = summaries["standard"]["values"]
    reduced = summaries["reduced"]["values"]

    # One inferential test, on the 14 per-line averages only.
    # Welch's independent two-sample t-test (does not assume equal variances).
    t_stat, p_value = stats.ttest_ind(reduced, standard, equal_var=False)
    n1, n2 = reduced.size, standard.size
    v1 = np.var(reduced, ddof=1)
    v2 = np.var(standard, ddof=1)
    se_diff = float(np.sqrt(v1 / n1 + v2 / n2))
    df = (v1 / n1 + v2 / n2) ** 2 / (
        (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    )
    diff = float(np.mean(reduced) - np.mean(standard))
    crit = float(stats.t.ppf(0.975, df))
    ci_low = diff - crit * se_diff
    ci_high = diff + crit * se_diff

    # Pooled-SD standardised effect size (Hedges-corrected Cohen's d).
    pooled_sd = float(np.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2)))
    cohens_d = diff / pooled_sd
    hedges_g = cohens_d * (1.0 - 3.0 / (4.0 * (n1 + n2) - 9.0))

    print("Independent two-sample test on the per-line averages")
    print("-" * 64)
    print("Test                : Welch's independent two-sample t-test")
    print("Unit of replication : dropper line")
    print("Response            : mean blade length of a dropper line (cm)")
    print("n (dropper lines)   : %d reduced vs %d standard, %d total"
          % (n1, n2, n_lines))
    print("Mean difference     : %+.2f cm (reduced minus standard)" % diff)
    print("95%% CI of difference: [%+.2f, %+.2f] cm" % (ci_low, ci_high))
    print("Standard error      : %.2f cm" % se_diff)
    print("t                   : %.3f" % float(t_stat))
    print("df (Welch)          : %.2f" % float(df))
    print("p                   : %.3e" % float(p_value))
    print("Hedges' g           : %.3f" % float(hedges_g))
    print()

    print("Conclusion")
    print("-" * 64)
    direction = "longer" if diff > 0 else "shorter"
    if p_value < 0.05:
        verdict = ("At the 5%% level the two seeding densities differ: blades on\n"
                   "reduced-density lines averaged %s by %.2f cm."
                   % (direction, abs(diff)))
    else:
        verdict = ("At the 5%% level the two seeding densities are not distinguished\n"
                   "by this test (observed difference %+.2f cm)." % diff)
    print(verdict)
    print()
    print("The %d measured blades describe the sampling effort only. The test's"
          % n_blade_rows)
    print("sample size is %d dropper lines, %d per seeding density."
          % (n_lines, n1))


if __name__ == "__main__":
    main()
