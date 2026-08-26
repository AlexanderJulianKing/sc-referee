"""Stone milling versus roller milling of wholegrain wheat flour.

66 sub-samples from the same grain lot, 33 per milling method, milled on
alternating days over three weeks. Five flour properties were measured and the
five together are the family of tests. The per-outcome threshold is the Sidak
threshold for five tests at a family-wide error rate of 5 percent, worked out by
hand below rather than taken from a library, and every p-value is compared with
that threshold instead of with 0.05.
"""

import pandas as pd
from scipy import stats

FAMILY_ALPHA = 0.05
N_TESTS = 5

# Sidak: keeping the family-wide error rate at 5 percent means each of the five
# tests may spend only 1 - (1 - 0.05) ** (1/5) of it.
KEEP_PROBABILITY = 1.0 - FAMILY_ALPHA          # 0.95, chance of no false positive anywhere
EXPONENT = 1.0 / N_TESTS                       # fifth root, one test's share
PER_TEST_KEEP = KEEP_PROBABILITY ** EXPONENT   # 0.95 ** (1/5)
SIDAK_THRESHOLD = 1.0 - PER_TEST_KEEP          # the subtraction

OUTCOMES = [
    ("damaged_starch_pct", "damaged starch (%)", 2),
    ("water_absorption_pct", "water absorption (%)", 1),
    ("particle_size_d50_um", "particle size d50 (um)", 1),
    ("tocopherol_mg_kg", "tocopherols (mg/kg)", 1),
    ("falling_number_s", "falling number (s)", 0),
]


def fmt_p(p):
    return f"{p:.2e}" if p < 1e-4 else f"{p:.6f}"


def main():
    data = pd.read_csv("data.csv")
    roller = data[data["milling"] == "roller"]
    stone = data[data["milling"] == "stone"]

    print(f"Sub-samples: roller n={len(roller)}, stone n={len(stone)}")
    print("Test: two-sample Welch t-test on the difference in means, two sided.\n")

    print("Sidak threshold, computed by hand")
    print(f"  {'number of tests in the family':<30}: {N_TESTS}")
    print(f"  {'family-wide error rate':<30}: {FAMILY_ALPHA:.2f}")
    print(f"  {'1 - ' + format(FAMILY_ALPHA, '.2f'):<30}= {KEEP_PROBABILITY:.6f}")
    print(f"  {'exponent 1/' + str(N_TESTS):<30}= {EXPONENT:.6f}")
    print(f"  {format(KEEP_PROBABILITY, '.2f') + ' ** ' + format(EXPONENT, '.6f'):<30}"
          f"= {PER_TEST_KEEP:.6f}")
    print(f"  {'1 - ' + format(PER_TEST_KEEP, '.6f'):<30}= {SIDAK_THRESHOLD:.6f}")
    print(f"  {'per-outcome threshold':<30}: {SIDAK_THRESHOLD:.6f} "
          f"(assumes {N_TESTS} tests)\n")

    header = f"{'outcome':<24}{'roller':>10}{'stone':>10}{'diff':>10}{'p':>12}  decision"
    print(header)
    print("-" * len(header))
    for column, label, dp in OUTCOMES:
        a = roller[column]
        b = stone[column]
        p = stats.ttest_ind(a, b, equal_var=False).pvalue
        decision = ("below threshold, difference" if p < SIDAK_THRESHOLD
                    else "above threshold, no difference")
        print(f"{label:<24}{a.mean():>10.{dp}f}{b.mean():>10.{dp}f}"
              f"{a.mean() - b.mean():>10.{dp}f}{p:>12.6f}  {decision}")

    print()
    print(f"Every decision above is against {SIDAK_THRESHOLD:.6f}, not against "
          f"{FAMILY_ALPHA:.2f}.")


if __name__ == "__main__":
    main()
