"""Grazing intensity and grassland birds: reporting script.

Descriptive statistics come from data.csv. Inference comes from
pvalues_adjusted.csv, the upstream preparation step's output: it tested the
whole family of five outcomes and applied the Holm-Bonferroni correction at
the five percent family-wide level. Significance here is read off the adjusted
p-value column only; this script does not run any test of its own.
"""

import pandas as pd

ALPHA = 0.05

paddocks = pd.read_csv("data.csv")
adjusted = pd.read_csv("pvalues_adjusted.csv")

light = paddocks[paddocks["grazing"] == "light"]
heavy = paddocks[paddocks["grazing"] == "heavy"]

print("Grazing intensity and grassland bird response")
print(f"paddocks: {len(light)} light, {len(heavy)} heavy, {len(paddocks)} total")
print()

print("Descriptive statistics (mean, SD)")
print(f"{'outcome':<24}{'light':>20}{'heavy':>20}")
for outcome in adjusted["outcome"]:
    l_mean, l_sd = light[outcome].mean(), light[outcome].std()
    h_mean, h_sd = heavy[outcome].mean(), heavy[outcome].std()
    print(f"{outcome:<24}{l_mean:>11.2f} ({l_sd:4.2f}){h_mean:>11.2f} ({h_sd:4.2f})")
print()

method = adjusted["correction_method"].unique()
assert len(method) == 1, "mixed correction methods in pvalues_adjusted.csv"
method = method[0]

print(f"Inference from pvalues_adjusted.csv, correction: {method}, alpha = {ALPHA}")
print(f"{'outcome':<24}{'difference':>12}{'p_adjusted':>13}  verdict")
for row in adjusted.itertuples(index=False):
    difference = row.mean_light - row.mean_heavy
    significant = row.p_adjusted < ALPHA
    verdict = "significant" if significant else "not significant"
    print(f"{row.outcome:<24}{difference:>12.3f}{row.p_adjusted:>13.3g}  {verdict}")
print()

n_significant = int((adjusted["p_adjusted"] < ALPHA).sum())
print(f"{n_significant} of {len(adjusted)} outcomes significant after {method} correction")
