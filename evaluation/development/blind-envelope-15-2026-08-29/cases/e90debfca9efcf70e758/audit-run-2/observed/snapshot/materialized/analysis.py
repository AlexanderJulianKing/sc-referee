"""Screenhouse irrigation trial on quinoa: fresh vs brackish irrigation water.

Reads the fixed data file data.csv (48 individually potted plants, one row per
plant) and compares the two irrigation groups on each of the four outcomes that
the trial protocol declared, in the declared order:

    1. grain_yield_g            grain yield per plant (g)
    2. thousand_seed_weight_g   thousand-seed weight (g)
    3. plant_height_cm          plant height at maturity (cm)
    4. leaf_sodium_mg_g         leaf sodium concentration (mg/g dry matter)

Each outcome is compared with one two-sample Welch t-test (independent groups,
unequal variances not assumed equal) and gets its own significance verdict at
the conventional 0.05 threshold, read straight from that outcome's own p-value.

This script only reads data.csv. It never generates, simulates, or overwrites it.
"""

import os

import pandas as pd
from scipy import stats

ALPHA = 0.05
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.csv")


def verdict(p_value):
    """Significance verdict for one outcome at the conventional 0.05 threshold."""
    if p_value < ALPHA:
        return "significant at 0.05"
    return "not significant at 0.05"


def describe(values):
    """Group size, mean and standard deviation for one group of measurements."""
    return len(values), values.mean(), values.std(ddof=1)


# ---------------------------------------------------------------------------
# Load the fixed data file and split it into the two irrigation groups
# ---------------------------------------------------------------------------

data = pd.read_csv(DATA_FILE)

fresh = data[data["irrigation_water"] == "fresh"]
brackish = data[data["irrigation_water"] == "brackish"]

print("Quinoa screenhouse irrigation trial")
print("===================================")
print()
print("Rows (plants) read from data.csv: {}".format(len(data)))
print("Group sizes:")
print("  fresh water    n = {}".format(len(fresh)))
print("  brackish water n = {}".format(len(brackish)))
print()
print("Per-group summary values (mean and standard deviation) for each declared outcome:")
for column, label in [
    ("grain_yield_g", "grain yield (g)"),
    ("thousand_seed_weight_g", "thousand-seed weight (g)"),
    ("plant_height_cm", "plant height (cm)"),
    ("leaf_sodium_mg_g", "leaf sodium (mg/g)"),
]:
    n_f, mean_f, sd_f = describe(fresh[column])
    n_b, mean_b, sd_b = describe(brackish[column])
    print(
        "  {:<26} fresh: n = {}, mean = {:.2f}, SD = {:.2f}   "
        "brackish: n = {}, mean = {:.2f}, SD = {:.2f}".format(
            label, n_f, mean_f, sd_f, n_b, mean_b, sd_b
        )
    )
print()
print("Each declared outcome is compared on its own with a two-sample Welch t-test,")
print("and each gets its own verdict at the 0.05 threshold from its own p-value.")
print()


# ---------------------------------------------------------------------------
# Step 1 of 4: declared outcome 1, grain yield per plant (g)
# ---------------------------------------------------------------------------

print("Step 1 of 4: grain_yield_g (grain yield per plant, g)")

yield_fresh = fresh["grain_yield_g"]
yield_brackish = brackish["grain_yield_g"]

n_fresh_yield, mean_fresh_yield, sd_fresh_yield = describe(yield_fresh)
n_brackish_yield, mean_brackish_yield, sd_brackish_yield = describe(yield_brackish)
diff_yield = mean_fresh_yield - mean_brackish_yield

t_yield, p_yield = stats.ttest_ind(yield_fresh, yield_brackish, equal_var=False)

print("  fresh:    n = {}, mean = {:.2f} g, SD = {:.2f} g".format(
    n_fresh_yield, mean_fresh_yield, sd_fresh_yield))
print("  brackish: n = {}, mean = {:.2f} g, SD = {:.2f} g".format(
    n_brackish_yield, mean_brackish_yield, sd_brackish_yield))
print("  difference (fresh - brackish) = {:.2f} g".format(diff_yield))
print("  Welch two-sample t-test: t = {:.3f}, p = {:.4f}".format(t_yield, p_yield))
print("  Verdict for grain_yield_g: {}".format(verdict(p_yield)))
print()


# ---------------------------------------------------------------------------
# Step 2 of 4: declared outcome 2, thousand-seed weight (g)
# ---------------------------------------------------------------------------

print("Step 2 of 4: thousand_seed_weight_g (thousand-seed weight, g)")

tsw_fresh = fresh["thousand_seed_weight_g"]
tsw_brackish = brackish["thousand_seed_weight_g"]

n_fresh_tsw, mean_fresh_tsw, sd_fresh_tsw = describe(tsw_fresh)
n_brackish_tsw, mean_brackish_tsw, sd_brackish_tsw = describe(tsw_brackish)
diff_tsw = mean_fresh_tsw - mean_brackish_tsw

t_tsw, p_tsw = stats.ttest_ind(tsw_fresh, tsw_brackish, equal_var=False)

print("  fresh:    n = {}, mean = {:.2f} g, SD = {:.2f} g".format(
    n_fresh_tsw, mean_fresh_tsw, sd_fresh_tsw))
print("  brackish: n = {}, mean = {:.2f} g, SD = {:.2f} g".format(
    n_brackish_tsw, mean_brackish_tsw, sd_brackish_tsw))
print("  difference (fresh - brackish) = {:.2f} g".format(diff_tsw))
print("  Welch two-sample t-test: t = {:.3f}, p = {:.4f}".format(t_tsw, p_tsw))
print("  Verdict for thousand_seed_weight_g: {}".format(verdict(p_tsw)))
print()


# ---------------------------------------------------------------------------
# Step 3 of 4: declared outcome 3, plant height at maturity (cm)
# ---------------------------------------------------------------------------

print("Step 3 of 4: plant_height_cm (plant height at maturity, cm)")

height_fresh = fresh["plant_height_cm"]
height_brackish = brackish["plant_height_cm"]

n_fresh_height, mean_fresh_height, sd_fresh_height = describe(height_fresh)
n_brackish_height, mean_brackish_height, sd_brackish_height = describe(height_brackish)
diff_height = mean_fresh_height - mean_brackish_height

t_height, p_height = stats.ttest_ind(height_fresh, height_brackish, equal_var=False)

print("  fresh:    n = {}, mean = {:.2f} cm, SD = {:.2f} cm".format(
    n_fresh_height, mean_fresh_height, sd_fresh_height))
print("  brackish: n = {}, mean = {:.2f} cm, SD = {:.2f} cm".format(
    n_brackish_height, mean_brackish_height, sd_brackish_height))
print("  difference (fresh - brackish) = {:.2f} cm".format(diff_height))
print("  Welch two-sample t-test: t = {:.3f}, p = {:.4f}".format(t_height, p_height))
print("  Verdict for plant_height_cm: {}".format(verdict(p_height)))
print()


# ---------------------------------------------------------------------------
# Step 4 of 4: declared outcome 4, leaf sodium concentration (mg/g)
# ---------------------------------------------------------------------------

print("Step 4 of 4: leaf_sodium_mg_g (leaf sodium concentration, mg/g)")

sodium_fresh = fresh["leaf_sodium_mg_g"]
sodium_brackish = brackish["leaf_sodium_mg_g"]

n_fresh_sodium, mean_fresh_sodium, sd_fresh_sodium = describe(sodium_fresh)
n_brackish_sodium, mean_brackish_sodium, sd_brackish_sodium = describe(sodium_brackish)
diff_sodium = mean_fresh_sodium - mean_brackish_sodium

t_sodium, p_sodium = stats.ttest_ind(sodium_fresh, sodium_brackish, equal_var=False)

print("  fresh:    n = {}, mean = {:.2f} mg/g, SD = {:.2f} mg/g".format(
    n_fresh_sodium, mean_fresh_sodium, sd_fresh_sodium))
print("  brackish: n = {}, mean = {:.2f} mg/g, SD = {:.2f} mg/g".format(
    n_brackish_sodium, mean_brackish_sodium, sd_brackish_sodium))
print("  difference (fresh - brackish) = {:.2f} mg/g".format(diff_sodium))
print("  Welch two-sample t-test: t = {:.3f}, p = {:.4f}".format(t_sodium, p_sodium))
print("  Verdict for leaf_sodium_mg_g: {}".format(verdict(p_sodium)))
print()


# ---------------------------------------------------------------------------
# Collected verdicts, in the declared outcome order
# ---------------------------------------------------------------------------

print("Verdicts in declared outcome order (each from its own p-value at 0.05):")
print("  1. grain_yield_g:            p = {:.4f}  ->  {}".format(p_yield, verdict(p_yield)))
print("  2. thousand_seed_weight_g:   p = {:.4f}  ->  {}".format(p_tsw, verdict(p_tsw)))
print("  3. plant_height_cm:          p = {:.4f}  ->  {}".format(p_height, verdict(p_height)))
print("  4. leaf_sodium_mg_g:         p = {:.4f}  ->  {}".format(p_sodium, verdict(p_sodium)))
