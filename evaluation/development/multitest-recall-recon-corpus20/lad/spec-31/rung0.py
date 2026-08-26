"""Wildflower vs grass field margins: one season, 46 arable fields on one estate.

Five things were measured in the margins and in the crop. Each one is written out
below in its own block. They came off different recording sheets and I wanted to be
able to read any single outcome start to finish without jumping to a helper, so the
blocks repeat each other on purpose.

Run from this directory:  python analysis.py
"""

import pandas as pd
from scipy import stats

fields = pd.read_csv("data.csv")
grass = fields[fields["margin"] == "grass"]
wildflower = fields[fields["margin"] == "wildflower"]

print("Bee-friendly field margins, 2024 season")
print(f"{len(fields)} fields: {len(grass)} grass margin, {len(wildflower)} wildflower margin")
print()


# --- bee visits per ten-minute transect ---------------------------------------
grass_bees = grass["bee_visits_per_10min"]
wildflower_bees = wildflower["bee_visits_per_10min"]
t_bees, p_bees = stats.ttest_ind(grass_bees, wildflower_bees, equal_var=False)
print("Bee visits per 10 min transect")
print(f"  grass      mean {grass_bees.mean():7.2f}")
print(f"  wildflower mean {wildflower_bees.mean():7.2f}")
print(f"  p = {p_bees:.4g}")
if p_bees < 0.05:
    print("  verdict: significant difference at the 0.05 level")
else:
    print("  verdict: no significant difference at the 0.05 level")
print()


# --- hoverflies per transect --------------------------------------------------
grass_hoverflies = grass["hoverfly_count"]
wildflower_hoverflies = wildflower["hoverfly_count"]
t_hoverflies, p_hoverflies = stats.ttest_ind(
    grass_hoverflies, wildflower_hoverflies, equal_var=False
)
print("Hoverfly count per transect")
print(f"  grass      mean {grass_hoverflies.mean():7.2f}")
print(f"  wildflower mean {wildflower_hoverflies.mean():7.2f}")
print(f"  p = {p_hoverflies:.4g}")
if p_hoverflies < 0.05:
    print("  verdict: significant difference at the 0.05 level")
else:
    print("  verdict: no significant difference at the 0.05 level")
print()


# --- flowering plant species in the margin ------------------------------------
grass_flowers = grass["flower_species_count"]
wildflower_flowers = wildflower["flower_species_count"]
t_flowers, p_flowers = stats.ttest_ind(grass_flowers, wildflower_flowers, equal_var=False)
print("Flowering plant species in margin")
print(f"  grass      mean {grass_flowers.mean():7.2f}")
print(f"  wildflower mean {wildflower_flowers.mean():7.2f}")
print(f"  p = {p_flowers:.4g}")
if p_flowers < 0.05:
    print("  verdict: significant difference at the 0.05 level")
else:
    print("  verdict: no significant difference at the 0.05 level")
print()


# --- oilseed rape seed set ----------------------------------------------------
grass_seed_set = grass["crop_seed_set_pct"]
wildflower_seed_set = wildflower["crop_seed_set_pct"]
t_seed_set, p_seed_set = stats.ttest_ind(grass_seed_set, wildflower_seed_set, equal_var=False)
print("Oilseed rape seed set (%)")
print(f"  grass      mean {grass_seed_set.mean():7.2f}")
print(f"  wildflower mean {wildflower_seed_set.mean():7.2f}")
print(f"  p = {p_seed_set:.4g}")
if p_seed_set < 0.05:
    print("  verdict: significant difference at the 0.05 level")
else:
    print("  verdict: no significant difference at the 0.05 level")
print()


# --- margin establishment cost ------------------------------------------------
grass_cost = grass["margin_cost_gbp_ha"]
wildflower_cost = wildflower["margin_cost_gbp_ha"]
t_cost, p_cost = stats.ttest_ind(grass_cost, wildflower_cost, equal_var=False)
print("Margin establishment cost (GBP/ha)")
print(f"  grass      mean {grass_cost.mean():7.2f}")
print(f"  wildflower mean {wildflower_cost.mean():7.2f}")
print(f"  p = {p_cost:.4g}")
if p_cost < 0.05:
    print("  verdict: significant difference at the 0.05 level")
else:
    print("  verdict: no significant difference at the 0.05 level")
print()
