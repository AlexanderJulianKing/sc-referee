"""
Hedgehog overwintering study: analysis of overwinter body-mass change by landscape.

Study question (see PROTOCOL.md): does percentage body-mass change across hibernation
differ between hedgehogs tracked in suburban gardens and hedgehogs tracked on rural
farmland?

Design note that fixes the analysis unit: each tagged hedgehog was weighed once before
hibernation and once after emergence, and that pair of weights was reduced to a single
percentage mass change before the table was written. So one row is one animal, each
animal appears exactly once, and landscape is a property of the animal. The animal and
the row are the same unit here, which makes this an independent two-sample comparison
applied directly to the rows of the table. There is nothing to average within an animal
and no clustering to account for.

Run with:  python3 analysis.py
"""

import sys

import numpy as np
import pandas as pd
from scipy import stats

DATA_FILE = "hedgehog_overwinter_mass.csv"
OUTCOME = "mass_change_percent"
GROUP = "landscape"
UNIT = "hedgehog_id"
COVARIATE = "pre_hibernation_mass_g"

# Reference group is stated up front so the sign of the difference is unambiguous.
GROUP_A = "suburban_garden"
GROUP_B = "rural_farmland"

ALPHA = 0.05


def rule(char="-", width=78):
    print(char * width)


def load_data(path):
    df = pd.read_csv(path)
    expected = [UNIT, GROUP, COVARIATE, OUTCOME]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        sys.exit("Missing expected column(s): %s" % ", ".join(missing))
    return df


def check_structure(df):
    """Confirm the design assumption the analysis rests on: one row per animal."""
    print("DATA AND DESIGN CHECKS")
    rule()
    n_rows = len(df)
    n_animals = df[UNIT].nunique()
    print("Rows in file:                       %d" % n_rows)
    print("Distinct %s values:        %d" % (UNIT, n_animals))
    print("Rows per animal (max):              %d"
          % int(df[UNIT].value_counts().max()))
    one_row_per_animal = (n_rows == n_animals)
    print("One row per animal:                 %s" % one_row_per_animal)
    if not one_row_per_animal:
        dupes = df[UNIT].value_counts()
        dupes = dupes[dupes > 1]
        sys.exit(
            "This script assumes one row per animal, which does not hold. "
            "Repeated animals: %s" % dupes.to_dict()
        )

    # Landscape must be a between-animal grouping: no animal in two landscapes.
    per_animal_groups = df.groupby(UNIT)[GROUP].nunique()
    print("Animals appearing in >1 landscape:  %d" % int((per_animal_groups > 1).sum()))

    print("Missing values in analysis columns: %d"
          % int(df[[UNIT, GROUP, COVARIATE, OUTCOME]].isna().sum().sum()))

    counts = df[GROUP].value_counts()
    print("Animals per landscape:")
    for level in [GROUP_A, GROUP_B]:
        print("    %-16s %d" % (level + ":", int(counts.get(level, 0))))

    unexpected = sorted(set(df[GROUP]) - {GROUP_A, GROUP_B})
    if unexpected:
        sys.exit("Unexpected landscape level(s): %s" % unexpected)
    print()


def describe(df):
    print("DESCRIPTIVE SUMMARY")
    rule()
    print("Outcome: %s (signed; negative = mass lost over the winter)" % OUTCOME)
    print()
    header = "%-16s %4s %8s %7s %8s %8s %8s" % (
        "landscape", "n", "mean", "sd", "median", "min", "max")
    print(header)
    for level in [GROUP_A, GROUP_B]:
        v = df.loc[df[GROUP] == level, OUTCOME]
        print("%-16s %4d %8.2f %7.2f %8.2f %8.2f %8.2f" % (
            level, len(v), v.mean(), v.std(ddof=1), v.median(), v.min(), v.max()))
    print()

    print("Baseline covariate (not the outcome): %s" % COVARIATE)
    print(header)
    for level in [GROUP_A, GROUP_B]:
        v = df.loc[df[GROUP] == level, COVARIATE]
        print("%-16s %4d %8.1f %7.1f %8.1f %8.1f %8.1f" % (
            level, len(v), v.mean(), v.std(ddof=1), v.median(), v.min(), v.max()))
    print()


def assumption_checks(a, b):
    """Reported for transparency; they do not switch the primary test."""
    print("ASSUMPTION CHECKS (reported, not used to select the primary test)")
    rule()
    for name, v in [(GROUP_A, a), (GROUP_B, b)]:
        w_stat, w_p = stats.shapiro(v)
        print("Shapiro-Wilk, %-16s W = %.4f, p = %.4f" % (name + ":", w_stat, w_p))
    lev_stat, lev_p = stats.levene(a, b, center="median")
    print("Levene (Brown-Forsythe) equal variance: W = %.4f, p = %.4f"
          % (lev_stat, lev_p))
    print("SD ratio (larger/smaller):              %.2f"
          % (max(a.std(ddof=1), b.std(ddof=1)) / min(a.std(ddof=1), b.std(ddof=1))))
    print()


def primary_test(a, b):
    """Welch's independent two-sample t-test on the rows (= animals)."""
    n1, n2 = len(a), len(b)
    m1, m2 = a.mean(), b.mean()
    s1, s2 = a.std(ddof=1), b.std(ddof=1)

    t_stat, p_val = stats.ttest_ind(a, b, equal_var=False)

    se = np.sqrt(s1 ** 2 / n1 + s2 ** 2 / n2)
    df_welch = (s1 ** 2 / n1 + s2 ** 2 / n2) ** 2 / (
        (s1 ** 2 / n1) ** 2 / (n1 - 1) + (s2 ** 2 / n2) ** 2 / (n2 - 1))
    diff = m1 - m2
    t_crit = stats.t.ppf(1 - ALPHA / 2, df_welch)
    lo, hi = diff - t_crit * se, diff + t_crit * se

    # Hedges' g (pooled SD, small-sample corrected).
    s_pooled = np.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2))
    d = diff / s_pooled
    j = 1.0 - 3.0 / (4.0 * (n1 + n2) - 9.0)
    g = j * d

    print("PRIMARY ANALYSIS")
    rule()
    print("Welch's independent two-sample t-test on %s by %s." % (OUTCOME, GROUP))
    print("Unit of analysis: the hedgehog. Each animal contributes one row, so the")
    print("test is applied directly to the rows: %d animals, %d per landscape."
          % (n1 + n2, n1))
    print()
    print("Contrast: %s minus %s" % (GROUP_A, GROUP_B))
    print("    mean %-16s %8.3f  (n = %d)" % (GROUP_A, m1, n1))
    print("    mean %-16s %8.3f  (n = %d)" % (GROUP_B, m2, n2))
    print("    difference in means:      %8.3f percentage points" % diff)
    print("    standard error:           %8.3f" % se)
    print("    95%% CI:                   [%.3f, %.3f]" % (lo, hi))
    print("    t = %.4f, df = %.2f, p = %.6f" % (t_stat, df_welch, p_val))
    print("    Hedges' g:                %8.3f" % g)
    print()
    print("Direction: a value closer to zero is a smaller loss. The suburban mean is")
    print("%.3f and the rural mean is %.3f, so suburban animals lost %.1f percentage"
          % (m1, m2, abs(diff)))
    print("points LESS of their pre-hibernation mass than rural animals.")
    print("Decision at alpha = %.2f: %s" % (
        ALPHA, "reject the null of equal means" if p_val < ALPHA
        else "do not reject the null of equal means"))
    print()
    return {"t": t_stat, "df": df_welch, "p": p_val, "diff": diff,
            "lo": lo, "hi": hi, "g": g, "m1": m1, "m2": m2,
            "s1": s1, "s2": s2, "n1": n1, "n2": n2}


def sensitivity(a, b):
    print("SENSITIVITY CHECKS (secondary; the primary result stands on the Welch test)")
    rule()
    t_pool, p_pool = stats.ttest_ind(a, b, equal_var=True)
    print("Student's pooled t-test:  t = %.4f, df = %d, p = %.6f"
          % (t_pool, len(a) + len(b) - 2, p_pool))
    u_stat, p_u = stats.mannwhitneyu(a, b, alternative="two-sided")
    print("Mann-Whitney U:           U = %.1f, p = %.6f" % (u_stat, p_u))
    print()


def main():
    df = load_data(DATA_FILE)

    print()
    rule("=")
    print("HEDGEHOG OVERWINTER MASS CHANGE BY LANDSCAPE")
    rule("=")
    print()

    check_structure(df)
    describe(df)

    a = df.loc[df[GROUP] == GROUP_A, OUTCOME]
    b = df.loc[df[GROUP] == GROUP_B, OUTCOME]

    assumption_checks(a, b)
    primary_test(a, b)
    sensitivity(a, b)

    rule("=")
    print("End of analysis.")
    rule("=")
    print()


if __name__ == "__main__":
    main()
