"""Analysis of the twelve-week dryland strength trial in masters swimmers.

Two programmes are compared: heavy resistance (few repetitions, high load) and
power endurance (many repetitions, moderate load).

The trial declared a family of four outcomes in advance, in this order:

    1. sprint_50_free_s        50 m freestyle time from a push start (s)
    2. tethered_force_n        peak tethered swimming force (N)
    3. cmj_height_cm           countermovement jump height (cm)
    4. shoulder_ir_torque_nm   shoulder internal rotation peak torque (N m)

Before any per-outcome comparison is made, the script computes a single
family-level screening quantity straight from the four outcome columns: the
mean absolute standardised group-mean difference across the family. That figure
is compared with a screening cutoff of 0.35 that was fixed before the data were
seen. Per-outcome two-sample t-tests are run and reported only when the screen
passes.
"""

import csv
import math

from scipy import stats

DATA_FILE = "swimmers.csv"
GROUP_COLUMN = "programme"
GROUPS = ("heavy_resistance", "power_endurance")
OUTCOMES = (
    "sprint_50_free_s",
    "tethered_force_n",
    "cmj_height_cm",
    "shoulder_ir_torque_nm",
)
SCREEN_CUTOFF = 0.35
ALPHA = 0.05


def load_data(path):
    """Read the CSV and return {outcome: {group: [values]}} plus group sizes."""
    values = {outcome: {group: [] for group in GROUPS} for outcome in OUTCOMES}
    sizes = {group: 0 for group in GROUPS}

    with open(path, newline="") as handle:
        for row in csv.DictReader(handle):
            group = row[GROUP_COLUMN]
            if group not in values[OUTCOMES[0]]:
                raise ValueError("unexpected group label: %r" % group)
            sizes[group] += 1
            for outcome in OUTCOMES:
                values[outcome][group].append(float(row[outcome]))

    return values, sizes


def mean(sample):
    return sum(sample) / len(sample)


def variance(sample):
    """Sample variance with the n - 1 denominator."""
    m = mean(sample)
    return sum((x - m) ** 2 for x in sample) / (len(sample) - 1)


def pooled_spread(sample_a, sample_b):
    """Pooled standard deviation of two samples."""
    n_a, n_b = len(sample_a), len(sample_b)
    pooled_var = (
        (n_a - 1) * variance(sample_a) + (n_b - 1) * variance(sample_b)
    ) / (n_a + n_b - 2)
    return math.sqrt(pooled_var)


def standardised_difference(sample_a, sample_b):
    """Group-mean difference divided by the pooled spread."""
    return (mean(sample_a) - mean(sample_b)) / pooled_spread(sample_a, sample_b)


def family_screen(values):
    """Average absolute standardised difference across the declared family.

    Plain arithmetic on the numbers only. No statistical testing routine is
    used at this step.
    """
    per_outcome = {}
    for outcome in OUTCOMES:
        per_outcome[outcome] = abs(
            standardised_difference(
                values[outcome][GROUPS[0]], values[outcome][GROUPS[1]]
            )
        )
    overall = sum(per_outcome.values()) / len(OUTCOMES)
    return overall, per_outcome


def main():
    values, sizes = load_data(DATA_FILE)

    print("=" * 72)
    print("DRYLAND STRENGTH TRIAL IN MASTERS SWIMMERS")
    print("=" * 72)
    print("Data file: %s" % DATA_FILE)
    print(
        "Group sizes: %s = %d, %s = %d"
        % (GROUPS[0], sizes[GROUPS[0]], GROUPS[1], sizes[GROUPS[1]])
    )
    print("Declared outcome family (in order): %s" % ", ".join(OUTCOMES))
    print()

    print("-" * 72)
    print("STEP 1 - FAMILY-LEVEL SCREEN (pre-set cutoff = %.2f)" % SCREEN_CUTOFF)
    print("-" * 72)
    overall, per_outcome = family_screen(values)
    print("Absolute standardised group-mean difference, by outcome:")
    for outcome in OUTCOMES:
        print("  %-24s %6.4f" % (outcome, per_outcome[outcome]))
    print("Overall family screening figure (mean of the four): %.4f" % overall)
    print("Screening cutoff fixed before the data were seen:   %.4f" % SCREEN_CUTOFF)

    passed = overall > SCREEN_CUTOFF
    print("Screen result: %s" % ("PASS" if passed else "FAIL"))
    print()

    print("-" * 72)
    if not passed:
        print("STEP 2 - NOT PERFORMED (screen did not pass)")
        print("-" * 72)
        print(
            "The declared family shows no overall separation between the two "
            "programmes."
        )
        print("No per-outcome comparison is warranted.")
        print("No per-outcome test results are produced.")
        print("=" * 72)
        return

    print("STEP 2 - PER-OUTCOME COMPARISONS (screen passed)")
    print("-" * 72)
    print(
        "Two-sample t-test per declared outcome, verdict at alpha = %.2f."
        % ALPHA
    )
    print()
    header = "%-24s %12s %12s %10s %12s" % (
        "outcome",
        GROUPS[0],
        GROUPS[1],
        "p_value",
        "verdict",
    )
    print(header)
    print("-" * len(header))
    for outcome in OUTCOMES:
        sample_a = values[outcome][GROUPS[0]]
        sample_b = values[outcome][GROUPS[1]]
        result = stats.ttest_ind(sample_a, sample_b)
        verdict = "significant" if result.pvalue < ALPHA else "not sig."
        print(
            "%-24s %12.3f %12.3f %10.4f %12s"
            % (outcome, mean(sample_a), mean(sample_b), result.pvalue, verdict)
        )
    print("=" * 72)


if __name__ == "__main__":
    main()
