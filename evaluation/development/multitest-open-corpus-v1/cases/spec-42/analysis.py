# Composting system evaluation, protocol MWA-COMPOST-2024-03, registered with the
# waste management authority before the first batch was sampled. The protocol fixes
# the outcome family and sets the per-outcome decision threshold at 0.010; report.md
# gives the derivation of that number.

import pandas as pd
from scipy import stats

OUTCOMES = [
    ("process_days", "Days to maturity"),
    ("final_c_to_n", "Final C:N ratio"),
    ("germination_index_pct", "Germination index (%)"),
    ("e_coli_log_cfu_g", "E. coli (log10 CFU/g)"),
    ("ammonia_emission_g_t", "Ammonia (g/tonne feedstock)"),
]

df = pd.read_csv("data.csv")
static = df[df["system"] == "static_pile"]
vessel = df[df["system"] == "in_vessel"]

print("In-vessel composting vs static aerated pile")
print("%d batches per system, one feedstock stream, one year" % len(static))
print("Decision threshold per outcome: 0.010")
print()
print("%-32s %14s %14s %12s  %s" % ("Outcome", "static pile", "in-vessel", "p-value", "Decision"))
print("-" * 88)

for column, label in OUTCOMES:
    a = static[column]
    b = vessel[column]
    _, p = stats.ttest_ind(a, b)
    decision = "difference" if p < 0.010 else "no difference"
    p_text = "<0.0001" if p < 0.0001 else "%.4f" % p
    print("%-32s %14.2f %14.2f %12s  %s" % (label, a.mean(), b.mean(), p_text, decision))
