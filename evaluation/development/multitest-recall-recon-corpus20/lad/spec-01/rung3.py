"""Heat-stress methionine trial: control vs supplemented cows, final week measures.

One two-sample comparison per outcome. Each outcome is written out as its own
block so the milk people and the metabolism people can read the part they care
about without untangling a loop.
"""

import pandas as pd
from scipy import stats

cows = pd.read_csv("data.csv")

control = cows[cows["treatment"] == "control"]
methionine = cows[cows["treatment"] == "methionine"]

print("cows read: %d (control %d, methionine %d)"
      % (len(cows), len(control), len(methionine)))
print()


# --- milk yield -----------------------------------------------------------
ctl1 = control["milk_yield_kg_d"]
met1 = methionine["milk_yield_kg_d"]
t1, p1 = stats.ttest_ind(ctl1, met1, equal_var=False)
print(f"milk_yield_kg_d: control {ctl1.mean():.3f}, methionine {met1.mean():.3f}, diff {met1.mean() - ctl1.mean():+.3f}, p = {p1:.4f}")
print("  significant" if p1 < 0.05 else "  not significant")


# --- milk fat -------------------------------------------------------------
ctl2 = control["milk_fat_pct"]
met2 = methionine["milk_fat_pct"]
t2, p2 = stats.ttest_ind(ctl2, met2, equal_var=False)
print(f"milk_fat_pct: control {ctl2.mean():.3f}, methionine {met2.mean():.3f}, diff {met2.mean() - ctl2.mean():+.3f}, p = {p2:.4f}")
print("  significant" if p2 < 0.05 else "  not significant")


# --- milk true protein ----------------------------------------------------
ctl3 = control["milk_protein_pct"]
met3 = methionine["milk_protein_pct"]
t3, p3 = stats.ttest_ind(ctl3, met3, equal_var=False)
print(f"milk_protein_pct: control {ctl3.mean():.3f}, methionine {met3.mean():.3f}, diff {met3.mean() - ctl3.mean():+.3f}, p = {p3:.4f}")
print("  significant" if p3 < 0.05 else "  not significant")


# --- somatic cell score ---------------------------------------------------
ctl4 = control["somatic_cell_score"]
met4 = methionine["somatic_cell_score"]
t4, p4 = stats.ttest_ind(ctl4, met4, equal_var=False)
print(f"somatic_cell_score: control {ctl4.mean():.3f}, methionine {met4.mean():.3f}, diff {met4.mean() - ctl4.mean():+.3f}, p = {p4:.4f}")
print("  significant" if p4 < 0.05 else "  not significant")


# --- afternoon rectal temperature -----------------------------------------
ctl5 = control["rectal_temp_c"]
met5 = methionine["rectal_temp_c"]
t5, p5 = stats.ttest_ind(ctl5, met5, equal_var=False)
print(f"rectal_temp_c: control {ctl5.mean():.3f}, methionine {met5.mean():.3f}, diff {met5.mean() - ctl5.mean():+.3f}, p = {p5:.4f}")
print("  significant" if p5 < 0.05 else "  not significant")


# --- plasma NEFA ----------------------------------------------------------
ctl6 = control["plasma_nefa_mmol_l"]
met6 = methionine["plasma_nefa_mmol_l"]
t6, p6 = stats.ttest_ind(ctl6, met6, equal_var=False)
print(f"plasma_nefa_mmol_l: control {ctl6.mean():.4f}, methionine {met6.mean():.4f}, diff {met6.mean() - ctl6.mean():+.4f}, p = {p6:.4f}")
print("  significant" if p6 < 0.05 else "  not significant")
