"""Street tree pit soil monitoring: two-group comparison of the four declared outcomes.

Reads data.csv and compares the engineered structural pit soil group against the
standard site backfill group on each declared outcome, in the declared order.
Each outcome is treated as its own question and judged on its own p-value at the
conventional 0.05 threshold.

Run with no arguments from the project root:

    python analysis.py
"""

import pandas as pd
from scipy import stats

ALPHA = 0.05
GROUP_COL = "pit_soil_type"
GROUP_A = "engineered_structural_soil"
GROUP_B = "standard_backfill"

data = pd.read_csv("data.csv")

engineered = data[data[GROUP_COL] == GROUP_A]
backfill = data[data[GROUP_COL] == GROUP_B]

print("Street tree pit soil monitoring")
print("Engineered structural soil vs standard backfill")
print("Two-sample t test (Welch), alpha = {:.2f}".format(ALPHA))
print("Rows read from data.csv: {}".format(len(data)))
print()


# ---------------------------------------------------------------------------
# Declared outcome 1: trunk diameter increment (mm)
# ---------------------------------------------------------------------------
outcome_1 = "trunk_diameter_increment_mm"
eng_1 = engineered[outcome_1]
bak_1 = backfill[outcome_1]

n_eng_1 = len(eng_1)
n_bak_1 = len(bak_1)
mean_eng_1 = eng_1.mean()
mean_bak_1 = bak_1.mean()
sd_eng_1 = eng_1.std(ddof=1)
sd_bak_1 = bak_1.std(ddof=1)
t_1, p_1 = stats.ttest_ind(eng_1, bak_1, equal_var=False)

print("Outcome 1: trunk diameter increment (mm)")
print("  engineered structural soil: n = {}, mean = {:.3f}, sd = {:.3f}".format(
    n_eng_1, mean_eng_1, sd_eng_1))
print("  standard backfill:          n = {}, mean = {:.3f}, sd = {:.3f}".format(
    n_bak_1, mean_bak_1, sd_bak_1))
print("  difference (engineered - backfill) = {:.3f}".format(mean_eng_1 - mean_bak_1))
print("  t = {:.3f}, p = {:.4f}".format(t_1, p_1))
if p_1 < ALPHA:
    print("  Verdict: significant difference between the pit soil groups at p < 0.05.")
else:
    print("  Verdict: no significant difference between the pit soil groups at p < 0.05.")
print()


# ---------------------------------------------------------------------------
# Declared outcome 2: projected canopy area (m2)
# ---------------------------------------------------------------------------
outcome_2 = "canopy_area_m2"
eng_2 = engineered[outcome_2]
bak_2 = backfill[outcome_2]

n_eng_2 = len(eng_2)
n_bak_2 = len(bak_2)
mean_eng_2 = eng_2.mean()
mean_bak_2 = bak_2.mean()
sd_eng_2 = eng_2.std(ddof=1)
sd_bak_2 = bak_2.std(ddof=1)
t_2, p_2 = stats.ttest_ind(eng_2, bak_2, equal_var=False)

print("Outcome 2: projected canopy area (m2)")
print("  engineered structural soil: n = {}, mean = {:.3f}, sd = {:.3f}".format(
    n_eng_2, mean_eng_2, sd_eng_2))
print("  standard backfill:          n = {}, mean = {:.3f}, sd = {:.3f}".format(
    n_bak_2, mean_bak_2, sd_bak_2))
print("  difference (engineered - backfill) = {:.3f}".format(mean_eng_2 - mean_bak_2))
print("  t = {:.3f}, p = {:.4f}".format(t_2, p_2))
if p_2 < ALPHA:
    print("  Verdict: significant difference between the pit soil groups at p < 0.05.")
else:
    print("  Verdict: no significant difference between the pit soil groups at p < 0.05.")
print()


# ---------------------------------------------------------------------------
# Declared outcome 3: leaf chlorophyll index (relative units)
# ---------------------------------------------------------------------------
outcome_3 = "leaf_chlorophyll_index"
eng_3 = engineered[outcome_3]
bak_3 = backfill[outcome_3]

n_eng_3 = len(eng_3)
n_bak_3 = len(bak_3)
mean_eng_3 = eng_3.mean()
mean_bak_3 = bak_3.mean()
sd_eng_3 = eng_3.std(ddof=1)
sd_bak_3 = bak_3.std(ddof=1)
t_3, p_3 = stats.ttest_ind(eng_3, bak_3, equal_var=False)

print("Outcome 3: leaf chlorophyll index (relative units)")
print("  engineered structural soil: n = {}, mean = {:.3f}, sd = {:.3f}".format(
    n_eng_3, mean_eng_3, sd_eng_3))
print("  standard backfill:          n = {}, mean = {:.3f}, sd = {:.3f}".format(
    n_bak_3, mean_bak_3, sd_bak_3))
print("  difference (engineered - backfill) = {:.3f}".format(mean_eng_3 - mean_bak_3))
print("  t = {:.3f}, p = {:.4f}".format(t_3, p_3))
if p_3 < ALPHA:
    print("  Verdict: significant difference between the pit soil groups at p < 0.05.")
else:
    print("  Verdict: no significant difference between the pit soil groups at p < 0.05.")
print()


# ---------------------------------------------------------------------------
# Declared outcome 4: midday stem water potential (MPa)
# ---------------------------------------------------------------------------
outcome_4 = "midday_stem_water_potential_mpa"
eng_4 = engineered[outcome_4]
bak_4 = backfill[outcome_4]

n_eng_4 = len(eng_4)
n_bak_4 = len(bak_4)
mean_eng_4 = eng_4.mean()
mean_bak_4 = bak_4.mean()
sd_eng_4 = eng_4.std(ddof=1)
sd_bak_4 = bak_4.std(ddof=1)
t_4, p_4 = stats.ttest_ind(eng_4, bak_4, equal_var=False)

print("Outcome 4: midday stem water potential (MPa)")
print("  engineered structural soil: n = {}, mean = {:.3f}, sd = {:.3f}".format(
    n_eng_4, mean_eng_4, sd_eng_4))
print("  standard backfill:          n = {}, mean = {:.3f}, sd = {:.3f}".format(
    n_bak_4, mean_bak_4, sd_bak_4))
print("  difference (engineered - backfill) = {:.3f}".format(mean_eng_4 - mean_bak_4))
print("  t = {:.3f}, p = {:.4f}".format(t_4, p_4))
if p_4 < ALPHA:
    print("  Verdict: significant difference between the pit soil groups at p < 0.05.")
else:
    print("  Verdict: no significant difference between the pit soil groups at p < 0.05.")
print()
