"""Sunflower biostimulant seed coating trial.

Compares biostimulant-coated seed against untreated seed on each of the five
declared outcomes, one outcome at a time, using a two-sample t-test.
Each outcome is judged on its own against the conventional 0.05 threshold.
"""

import pandas as pd
from scipy import stats

ALPHA = 0.05

data = pd.read_csv("sunflower_trial.csv")

untreated = data[data["seed_treatment"] == "untreated"]
coated = data[data["seed_treatment"] == "coated"]

print("Sunflower biostimulant seed coating trial")
print("n untreated = %d, n coated = %d" % (len(untreated), len(coated)))
print()


# Outcome 1: plant height at flowering (cm)
height_untreated = untreated["plant_height_cm"]
height_coated = coated["plant_height_cm"]
height_t, height_p = stats.ttest_ind(height_coated, height_untreated)
print("Outcome 1: plant_height_cm")
print("  mean untreated = %.2f cm" % height_untreated.mean())
print("  mean coated    = %.2f cm" % height_coated.mean())
print("  t = %.3f" % height_t)
print("  p = %.4f" % height_p)
print("  verdict: %s at alpha = 0.05" % ("significant" if height_p < ALPHA else "not significant"))
print()


# Outcome 2: capitulum diameter at harvest (cm)
diameter_untreated = untreated["head_diameter_cm"]
diameter_coated = coated["head_diameter_cm"]
diameter_t, diameter_p = stats.ttest_ind(diameter_coated, diameter_untreated)
print("Outcome 2: head_diameter_cm")
print("  mean untreated = %.2f cm" % diameter_untreated.mean())
print("  mean coated    = %.2f cm" % diameter_coated.mean())
print("  t = %.3f" % diameter_t)
print("  p = %.4f" % diameter_p)
print("  verdict: %s at alpha = 0.05" % ("significant" if diameter_p < ALPHA else "not significant"))
print()


# Outcome 3: filled seed number per head (count)
seeds_untreated = untreated["filled_seed_number"]
seeds_coated = coated["filled_seed_number"]
seeds_t, seeds_p = stats.ttest_ind(seeds_coated, seeds_untreated)
print("Outcome 3: filled_seed_number")
print("  mean untreated = %.2f seeds" % seeds_untreated.mean())
print("  mean coated    = %.2f seeds" % seeds_coated.mean())
print("  t = %.3f" % seeds_t)
print("  p = %.4f" % seeds_p)
print("  verdict: %s at alpha = 0.05" % ("significant" if seeds_p < ALPHA else "not significant"))
print()


# Outcome 4: thousand-seed mass (g)
mass_untreated = untreated["thousand_seed_mass_g"]
mass_coated = coated["thousand_seed_mass_g"]
mass_t, mass_p = stats.ttest_ind(mass_coated, mass_untreated)
print("Outcome 4: thousand_seed_mass_g")
print("  mean untreated = %.2f g" % mass_untreated.mean())
print("  mean coated    = %.2f g" % mass_coated.mean())
print("  t = %.3f" % mass_t)
print("  p = %.4f" % mass_p)
print("  verdict: %s at alpha = 0.05" % ("significant" if mass_p < ALPHA else "not significant"))
print()


# Outcome 5: seed oil content (percent of seed dry mass)
oil_untreated = untreated["seed_oil_content_pct"]
oil_coated = coated["seed_oil_content_pct"]
oil_t, oil_p = stats.ttest_ind(oil_coated, oil_untreated)
print("Outcome 5: seed_oil_content_pct")
print("  mean untreated = %.2f %%" % oil_untreated.mean())
print("  mean coated    = %.2f %%" % oil_coated.mean())
print("  t = %.3f" % oil_t)
print("  p = %.4f" % oil_p)
print("  verdict: %s at alpha = 0.05" % ("significant" if oil_p < ALPHA else "not significant"))
print()
