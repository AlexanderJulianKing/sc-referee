"""Bakery flour dust survey: compare the open and enclosed dough lines.

The study declared four outcomes in advance, in this order:
    1. dust_mg_m3        shift-average inhalable flour dust (mg/m3)
    2. fev1_drop_ml      cross-shift fall in FEV1 (mL)
    3. ige_wheat_ku_l    serum wheat-specific IgE (kU/L)
    4. nasal_symptom_pts work-related nasal symptom score (points, 0-12)

Each outcome is compared between the two production lines with a two-sample
(Student's) t-test and judged at the conventional 0.05 threshold.
"""

import pandas as pd
from scipy import stats

ALPHA = 0.05

data = pd.read_csv("bakery_flour_dust.csv")

open_line = data[data["dough_line"] == "open"]
enclosed_line = data[data["dough_line"] == "enclosed"]

print("Bakery flour dust survey: open vs enclosed dough line")
print(f"Workers on the open line:     {len(open_line)}")
print(f"Workers on the enclosed line: {len(enclosed_line)}")
print(f"Significance threshold: {ALPHA}")


def verdict(p_value):
    return "SIGNIFICANT" if p_value < ALPHA else "not significant"


def fmt_p(p_value):
    """Print small p-values in scientific notation instead of rounding to 0."""
    return f"{p_value:.3e}" if p_value < 0.0001 else f"{p_value:.4f}"


# ---------------------------------------------------------------------------
# Step 1 of 4 - Outcome 1: inhalable flour dust concentration (mg/m3)
# ---------------------------------------------------------------------------
print("\nStep 1 of 4 - dust_mg_m3 (inhalable flour dust, mg/m3)")

dust_open = open_line["dust_mg_m3"]
dust_enclosed = enclosed_line["dust_mg_m3"]

dust_t, dust_p = stats.ttest_ind(dust_open, dust_enclosed)

print(f"  mean, open line:     {dust_open.mean():.3f} mg/m3")
print(f"  mean, enclosed line: {dust_enclosed.mean():.3f} mg/m3")
print(f"  difference (open - enclosed): {dust_open.mean() - dust_enclosed.mean():.3f} mg/m3")
print(f"  two-sample t = {dust_t:.3f}")
print(f"  p-value      = {fmt_p(dust_p)}")
print(f"  verdict at {ALPHA}: {verdict(dust_p)}")


# ---------------------------------------------------------------------------
# Step 2 of 4 - Outcome 2: cross-shift fall in FEV1 (mL)
# ---------------------------------------------------------------------------
print("\nStep 2 of 4 - fev1_drop_ml (cross-shift fall in FEV1, mL)")

fev1_open = open_line["fev1_drop_ml"]
fev1_enclosed = enclosed_line["fev1_drop_ml"]

fev1_t, fev1_p = stats.ttest_ind(fev1_open, fev1_enclosed)

print(f"  mean, open line:     {fev1_open.mean():.3f} mL")
print(f"  mean, enclosed line: {fev1_enclosed.mean():.3f} mL")
print(f"  difference (open - enclosed): {fev1_open.mean() - fev1_enclosed.mean():.3f} mL")
print(f"  two-sample t = {fev1_t:.3f}")
print(f"  p-value      = {fmt_p(fev1_p)}")
print(f"  verdict at {ALPHA}: {verdict(fev1_p)}")


# ---------------------------------------------------------------------------
# Step 3 of 4 - Outcome 3: serum wheat-specific IgE (kU/L)
# ---------------------------------------------------------------------------
print("\nStep 3 of 4 - ige_wheat_ku_l (serum wheat-specific IgE, kU/L)")

ige_open = open_line["ige_wheat_ku_l"]
ige_enclosed = enclosed_line["ige_wheat_ku_l"]

ige_t, ige_p = stats.ttest_ind(ige_open, ige_enclosed)

print(f"  mean, open line:     {ige_open.mean():.3f} kU/L")
print(f"  mean, enclosed line: {ige_enclosed.mean():.3f} kU/L")
print(f"  difference (open - enclosed): {ige_open.mean() - ige_enclosed.mean():.3f} kU/L")
print(f"  two-sample t = {ige_t:.3f}")
print(f"  p-value      = {fmt_p(ige_p)}")
print(f"  verdict at {ALPHA}: {verdict(ige_p)}")


# ---------------------------------------------------------------------------
# Step 4 of 4 - Outcome 4: work-related nasal symptom score (points)
# ---------------------------------------------------------------------------
print("\nStep 4 of 4 - nasal_symptom_pts (nasal symptom score, points)")

nasal_open = open_line["nasal_symptom_pts"]
nasal_enclosed = enclosed_line["nasal_symptom_pts"]

nasal_t, nasal_p = stats.ttest_ind(nasal_open, nasal_enclosed)

print(f"  mean, open line:     {nasal_open.mean():.3f} points")
print(f"  mean, enclosed line: {nasal_enclosed.mean():.3f} points")
print(f"  difference (open - enclosed): {nasal_open.mean() - nasal_enclosed.mean():.3f} points")
print(f"  two-sample t = {nasal_t:.3f}")
print(f"  p-value      = {fmt_p(nasal_p)}")
print(f"  verdict at {ALPHA}: {verdict(nasal_p)}")
