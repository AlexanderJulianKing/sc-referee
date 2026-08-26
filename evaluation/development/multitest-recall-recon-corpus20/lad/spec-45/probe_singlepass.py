# Sawdust vs woven plastic mulch, mature highbush blueberry, one season, 78 bushes.

import pandas as pd
from scipy import stats

df = pd.read_csv("data.csv")
plastic = df[df["mulch"] == "plastic"]
sawdust = df[df["mulch"] == "sawdust"]

outcomes = ["yield_kg_bush", "berry_weight_g", "brix_pct",
            "soil_moisture_pct", "weed_biomass_g_m2", "soil_ph"]

print(f"{'Outcome':-20s} {'plastic':10s} {'sawdust':10s} {'p':10s}  Verdict")
for c in outcomes:
    p = stats.ttest_ind(plastic[c], sawdust[c]).pvalue
    v = "significant" if p < 0.05 else "not significant"
    print(f"{c:-20s} {plastic[c].mean():10.2f} {sawdust[c].mean():10.2f} {p:10.3g}  {v}")
