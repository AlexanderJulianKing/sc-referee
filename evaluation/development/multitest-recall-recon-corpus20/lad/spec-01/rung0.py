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
ctl = control["milk_yield_kg_d"]
met = methionine["milk_yield_kg_d"]
t, p = stats.ttest_ind(ctl, met, equal_var=False)
print("milk_yield_kg_d: control %.3f, methionine %.3f, diff %+.3f, p = %.4f"
      % (ctl.mean(), met.mean(), met.mean() - ctl.mean(), p))
if p < 0.05:
    print("  significant")
else:
    print("  not significant")


# --- milk fat -------------------------------------------------------------
ctl = control["milk_fat_pct"]
met = methionine["milk_fat_pct"]
t, p = stats.ttest_ind(ctl, met, equal_var=False)
print("milk_fat_pct: control %.3f, methionine %.3f, diff %+.3f, p = %.4f"
      % (ctl.mean(), met.mean(), met.mean() - ctl.mean(), p))
if p < 0.05:
    print("  significant")
else:
    print("  not significant")


# --- milk true protein ----------------------------------------------------
ctl = control["milk_protein_pct"]
met = methionine["milk_protein_pct"]
t, p = stats.ttest_ind(ctl, met, equal_var=False)
print("milk_protein_pct: control %.3f, methionine %.3f, diff %+.3f, p = %.4f"
      % (ctl.mean(), met.mean(), met.mean() - ctl.mean(), p))
if p < 0.05:
    print("  significant")
else:
    print("  not significant")


# --- somatic cell score ---------------------------------------------------
ctl = control["somatic_cell_score"]
met = methionine["somatic_cell_score"]
t, p = stats.ttest_ind(ctl, met, equal_var=False)
print("somatic_cell_score: control %.3f, methionine %.3f, diff %+.3f, p = %.4f"
      % (ctl.mean(), met.mean(), met.mean() - ctl.mean(), p))
if p < 0.05:
    print("  significant")
else:
    print("  not significant")


# --- afternoon rectal temperature -----------------------------------------
ctl = control["rectal_temp_c"]
met = methionine["rectal_temp_c"]
t, p = stats.ttest_ind(ctl, met, equal_var=False)
print("rectal_temp_c: control %.3f, methionine %.3f, diff %+.3f, p = %.4f"
      % (ctl.mean(), met.mean(), met.mean() - ctl.mean(), p))
if p < 0.05:
    print("  significant")
else:
    print("  not significant")


# --- plasma NEFA ----------------------------------------------------------
ctl = control["plasma_nefa_mmol_l"]
met = methionine["plasma_nefa_mmol_l"]
t, p = stats.ttest_ind(ctl, met, equal_var=False)
print("plasma_nefa_mmol_l: control %.4f, methionine %.4f, diff %+.4f, p = %.4f"
      % (ctl.mean(), met.mean(), met.mean() - ctl.mean(), p))
if p < 0.05:
    print("  significant")
else:
    print("  not significant")
