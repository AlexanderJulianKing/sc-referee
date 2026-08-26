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
print("milk_yield_kg_d: control %.3f, methionine %.3f, diff %+.3f, p = %.4f"
      % (ctl1.mean(), met1.mean(), met1.mean() - ctl1.mean(), p1))
if p1 < 0.05:
    print("  significant")
else:
    print("  not significant")


# --- milk fat -------------------------------------------------------------
ctl2 = control["milk_fat_pct"]
met2 = methionine["milk_fat_pct"]
t2, p2 = stats.ttest_ind(ctl2, met2, equal_var=False)
print("milk_fat_pct: control %.3f, methionine %.3f, diff %+.3f, p = %.4f"
      % (ctl2.mean(), met2.mean(), met2.mean() - ctl2.mean(), p2))
if p2 < 0.05:
    print("  significant")
else:
    print("  not significant")


# --- milk true protein ----------------------------------------------------
ctl3 = control["milk_protein_pct"]
met3 = methionine["milk_protein_pct"]
t3, p3 = stats.ttest_ind(ctl3, met3, equal_var=False)
print("milk_protein_pct: control %.3f, methionine %.3f, diff %+.3f, p = %.4f"
      % (ctl3.mean(), met3.mean(), met3.mean() - ctl3.mean(), p3))
if p3 < 0.05:
    print("  significant")
else:
    print("  not significant")


# --- somatic cell score ---------------------------------------------------
ctl4 = control["somatic_cell_score"]
met4 = methionine["somatic_cell_score"]
t4, p4 = stats.ttest_ind(ctl4, met4, equal_var=False)
print("somatic_cell_score: control %.3f, methionine %.3f, diff %+.3f, p = %.4f"
      % (ctl4.mean(), met4.mean(), met4.mean() - ctl4.mean(), p4))
if p4 < 0.05:
    print("  significant")
else:
    print("  not significant")


# --- afternoon rectal temperature -----------------------------------------
ctl5 = control["rectal_temp_c"]
met5 = methionine["rectal_temp_c"]
t5, p5 = stats.ttest_ind(ctl5, met5, equal_var=False)
print("rectal_temp_c: control %.3f, methionine %.3f, diff %+.3f, p = %.4f"
      % (ctl5.mean(), met5.mean(), met5.mean() - ctl5.mean(), p5))
if p5 < 0.05:
    print("  significant")
else:
    print("  not significant")


# --- plasma NEFA ----------------------------------------------------------
ctl6 = control["plasma_nefa_mmol_l"]
met6 = methionine["plasma_nefa_mmol_l"]
t6, p6 = stats.ttest_ind(ctl6, met6, equal_var=False)
print("plasma_nefa_mmol_l: control %.4f, methionine %.4f, diff %+.4f, p = %.4f"
      % (ctl6.mean(), met6.mean(), met6.mean() - ctl6.mean(), p6))
if p6 < 0.05:
    print("  significant")
else:
    print("  not significant")
