"""Streetlight orb-weaver study: pre-declared gatekeeping analysis.

Reads the fixed authored file data.csv and runs the plan the field group fixed
in advance:

  Step 1 (overall screen).  A single screening quantity is computed directly
  from all five declared outcome columns at once, with plain arithmetic and no
  statistical test routine of any kind: for each outcome take the absolute
  difference between the two group means divided by that outcome's pooled
  standard deviation, then average those five numbers into one value.  That one
  value is compared with a screening cut-off fixed before the analysis.

  Step 2 (per-outcome comparisons).  Only if the overall screen passes are the
  five per-outcome two-group comparisons performed, in the declared order, each
  judged at the conventional 0.05 threshold.  If the screen does not pass, no
  per-outcome comparison is performed at all.

The script runs top to bottom with no arguments and prints its results.
"""

import csv
import math

from scipy import stats

DATA_FILE = "data.csv"

GROUP_COLUMN = "site_lighting"
GROUP_A = "lit"
GROUP_B = "unlit"

# The five outcomes, in the order the field plan declared them in advance.
OUTCOMES = [
    "body_mass_mg",
    "cephalothorax_width_mm",
    "web_capture_area_cm2",
    "mesh_width_mm",
    "prey_items",
]

# Screening cut-off fixed before the analysis.  The averaged standardised group
# difference across the five declared outcomes must reach this value for the
# outcome family to be pursued.
SCREEN_CUTOFF = 0.40

# Conventional threshold for the per-outcome comparisons.
ALPHA = 0.05


def read_data(path):
    """Return {column: [values]} for each group, reading the CSV by name."""
    groups = {GROUP_A: {name: [] for name in OUTCOMES},
              GROUP_B: {name: [] for name in OUTCOMES}}
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            group = row[GROUP_COLUMN]
            for name in OUTCOMES:
                groups[group][name].append(float(row[name]))
    return groups


def mean(values):
    return sum(values) / len(values)


def sample_sd(values):
    """Sample standard deviation, denominator n - 1."""
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def pooled_sd(a, b):
    """Pooled standard deviation of two independent samples."""
    na, nb = len(a), len(b)
    sa, sb = sample_sd(a), sample_sd(b)
    return math.sqrt(((na - 1) * sa ** 2 + (nb - 1) * sb ** 2) / (na + nb - 2))


def standardised_difference(a, b):
    """|mean difference| divided by the pooled standard deviation."""
    return abs(mean(a) - mean(b)) / pooled_sd(a, b)


def overall_screen(groups):
    """Average the five per-outcome standardised differences into one number.

    Plain arithmetic on the numeric outcome columns only; no test routine.
    """
    per_outcome = {}
    for name in OUTCOMES:
        per_outcome[name] = standardised_difference(groups[GROUP_A][name],
                                                    groups[GROUP_B][name])
    screen_value = sum(per_outcome[name] for name in OUTCOMES) / len(OUTCOMES)
    return screen_value, per_outcome


def main():
    groups = read_data(DATA_FILE)
    screen_value, per_outcome = overall_screen(groups)

    print("=" * 72)
    print("STEP 1 - OVERALL SCREEN OVER THE DECLARED OUTCOME FAMILY")
    print("=" * 72)
    print("Screening quantity: mean over the five declared outcomes of")
    print("|mean(lit) - mean(unlit)| / pooled SD, computed by plain arithmetic.")
    print()
    for name in OUTCOMES:
        print(f"  {name:<26} standardised difference = {per_outcome[name]:.4f}")
    print()
    print(f"Overall screening quantity : {screen_value:.4f}")
    print(f"Pre-fixed screening cut-off: {SCREEN_CUTOFF:.4f}")
    print()

    if screen_value < SCREEN_CUTOFF:
        print("SCREEN RESULT: DID NOT PASS")
        print(f"The screening quantity {screen_value:.4f} is below the cut-off "
              f"{SCREEN_CUTOFF:.4f}.")
        print("The outcome family was not pursued. No per-outcome comparison "
              "was performed.")
        print("=" * 72)
        return

    print("SCREEN RESULT: PASSED")
    print(f"The screening quantity {screen_value:.4f} reaches the cut-off "
          f"{SCREEN_CUTOFF:.4f}.")
    print("The outcome family is pursued; the per-outcome comparisons follow.")
    print()

    print("=" * 72)
    print("STEP 2 - PER-OUTCOME TWO-GROUP COMPARISONS (DECLARED ORDER)")
    print("=" * 72)
    print(f"Two-sample t-test, judged at the conventional {ALPHA:.2f} threshold.")
    print()

    for index, name in enumerate(OUTCOMES, start=1):
        a = groups[GROUP_A][name]
        b = groups[GROUP_B][name]
        result = stats.ttest_ind(a, b)
        verdict = ("significant at 0.05" if result.pvalue < ALPHA
                   else "not significant at 0.05")
        print(f"Outcome {index}: {name}")
        print(f"  {GROUP_A:<6} n = {len(a):<3} mean = {mean(a):10.4f} "
              f"SD = {sample_sd(a):9.4f}")
        print(f"  {GROUP_B:<6} n = {len(b):<3} mean = {mean(b):10.4f} "
              f"SD = {sample_sd(b):9.4f}")
        print(f"  p-value = {result.pvalue:.6g}")
        print(f"  Verdict: {verdict}")
        print()

    print("=" * 72)


if __name__ == "__main__":
    main()
