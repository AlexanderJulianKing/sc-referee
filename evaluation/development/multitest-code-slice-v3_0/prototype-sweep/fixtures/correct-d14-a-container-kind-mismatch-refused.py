"""Biofilm coupon study: hydrophilic coating vs uncoated silicone catheter material.

Reads biofilm_coupons.csv and compares the two surfaces on each of the four
pre-declared biofilm outcomes with a two-sample Welch t-test. Each outcome is
treated as its own scientific question and its p-value is taken at face value
against the 0.05 threshold.
"""

from pathlib import Path

import pandas as pd
from scipy.stats import ttest_ind

CSV_PATH = Path(__file__).resolve().parent / "biofilm_coupons.csv"

# Declared outcome family, in the pre-declared order.
OUTCOMES = [
    "biofilm_od590",
    "viable_log10_cfu_per_cm2",
    "thickness_um",
    "eps_protein_ug_per_cm2",
]

OUTCOME_LABELS = {
    "biofilm_od590": "Biofilm biomass (OD590)",
    "viable_log10_cfu_per_cm2": "Viable cells (log10 CFU/cm2)",
    "thickness_um": "Mean biofilm thickness (um)",
    "eps_protein_ug_per_cm2": "EPS protein (ug/cm2)",
}

ALPHA = 0.05

coupons = pd.read_csv(CSV_PATH)
uncoated = coupons[coupons["surface"] == "uncoated"]
hydrophilic = coupons[coupons["surface"] == "hydrophilic"]

# One compact collection of per-outcome results, built in a single pass over
# the declared outcome list.
results = {
    outcome: {
        "mean_uncoated": u.mean(),
        "mean_hydrophilic": h.mean(),
        "difference": h.mean() - u.mean(),
        "p_value": min(1.0, ttest_ind(u, h, equal_var=False).pvalue * 4),
    }
    for outcome in OUTCOMES
    for [u, h] in [(uncoated[outcome], hydrophilic[outcome])]
}

print("Biofilm coupon study: hydrophilic coating vs uncoated silicone")
print(f"Coupons: {len(coupons)} total, "
      f"{len(uncoated)} uncoated, {len(hydrophilic)} hydrophilic")
print(f"Test: two-sample Welch t-test, significance threshold p < {ALPHA}")
print()

header = (f"{'Outcome':<30}{'Uncoated':>12}{'Hydrophilic':>14}"
          f"{'Difference':>13}{'p-value':>11}  Verdict")
print(header)
print("-" * len(header))

for outcome in OUTCOMES:
    result = results[outcome]
    significant = result["p_value"] < ALPHA
    verdict = "significant" if significant else "not significant"
    print(f"{OUTCOME_LABELS[outcome]:<30}"
          f"{result['mean_uncoated']:>12.3f}"
          f"{result['mean_hydrophilic']:>14.3f}"
          f"{result['difference']:>13.3f}"
          f"{result['p_value']:>11.4f}  {verdict}")

print()
print("Conclusions")
for outcome in OUTCOMES:
    result = results[outcome]
    if result["p_value"] < ALPHA:
        conclusion = "significantly affects"
    else:
        conclusion = "does not significantly affect"
    print(f"- {OUTCOME_LABELS[outcome]}: the coating {conclusion} "
          f"this outcome (p = {result['p_value']:.4f}).")
