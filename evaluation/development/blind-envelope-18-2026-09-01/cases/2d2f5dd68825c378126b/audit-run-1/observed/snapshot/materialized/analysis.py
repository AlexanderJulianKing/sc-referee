"""Bunch-thinning trial on Medjool-type date palms: light vs heavy strand thinning.

Reads data.csv and compares the two thinning intensities on each of the eight
outcomes declared in the trial plan, in the declared order.

Each outcome is compared with an independent two-sample t-test (Student's,
equal variances), which suits continuous measurements taken on independent
palms.

Three outcomes are commercially decisive for the station: mean single fruit
weight, yield per palm and total soluble solids. Their p-values are corrected
by hand in this script: each is multiplied by the number of comparisons run
(eight) and capped at one, then judged at 0.05. The other five declared
outcomes are judged at 0.05 on their own raw unadjusted p-values.
"""

import csv

from scipy import stats

DATA_FILE = "data.csv"
GROUP_COLUMN = "thinning_intensity"
GROUPS = ("light", "heavy")

# The eight outcomes in the order the trial plan declared them.
OUTCOMES = [
    ("fruit_weight_g", "Mean single fruit weight (g)"),
    ("fruit_length_mm", "Fruit length (mm)"),
    ("fruit_width_mm", "Fruit width (mm)"),
    ("yield_per_palm_kg", "Yield per palm (kg)"),
    ("total_soluble_solids_brix", "Total soluble solids (degrees Brix)"),
    ("fruit_moisture_pct", "Fruit moisture (%)"),
    ("flesh_to_seed_ratio", "Flesh-to-seed ratio (unitless)"),
    ("fruit_firmness_n", "Fruit firmness (N)"),
]

# The three commercially decisive outcomes whose p-values are corrected by hand.
HAND_CORRECTED = {
    "fruit_weight_g",
    "yield_per_palm_kg",
    "total_soluble_solids_brix",
}

N_COMPARISONS = len(OUTCOMES)  # eight comparisons are run
ALPHA = 0.05


def read_data(path):
    """Return the rows of the authored data file as a list of dicts."""
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def group_values(rows, group, column):
    """Return the values of one outcome column for one thinning intensity."""
    return [float(row[column]) for row in rows if row[GROUP_COLUMN] == group]


def mean(values):
    return sum(values) / len(values)


def sd(values):
    """Sample standard deviation (n - 1 in the denominator)."""
    m = mean(values)
    return (sum((v - m) ** 2 for v in values) / (len(values) - 1)) ** 0.5


def main():
    rows = read_data(DATA_FILE)

    print("Bunch-thinning trial: light vs heavy strand thinning")
    print(f"Palms in file: {len(rows)}")
    print(f"Comparisons run: {N_COMPARISONS}")
    print(f"Threshold: {ALPHA}")
    print(
        "Hand-corrected outcomes (p x 8, capped at 1): "
        + ", ".join(name for name, _ in OUTCOMES if name in HAND_CORRECTED)
    )
    print()

    for column, label in OUTCOMES:
        light = group_values(rows, "light", column)
        heavy = group_values(rows, "heavy", column)

        raw_p = stats.ttest_ind(light, heavy).pvalue

        if column in HAND_CORRECTED:
            p_used = min(raw_p * N_COMPARISONS, 1.0)
            p_kind = "corrected by hand (raw x 8, capped at 1)"
        else:
            p_used = raw_p
            p_kind = "raw unadjusted"

        verdict = (
            "significant difference between intensities"
            if p_used < ALPHA
            else "no significant difference between intensities"
        )

        print(label)
        print(f"  column: {column}")
        print(f"  light: n = {len(light)}, mean = {mean(light):.3f}, sd = {sd(light):.3f}")
        print(f"  heavy: n = {len(heavy)}, mean = {mean(heavy):.3f}, sd = {sd(heavy):.3f}")
        print(f"  raw p-value: {raw_p:.6g}")
        print(f"  p-value used for the verdict ({p_kind}): {p_used:.6g}")
        print(f"  verdict at {ALPHA}: {verdict}")
        print()


if __name__ == "__main__":
    main()
