# Sawdust vs woven plastic mulch, mature highbush blueberry, one season, 78 bushes.

import pandas as pd
from scipy import stats

df = pd.read_csv("data.csv")
plastic = df[df["mulch"] == "plastic"]
sawdust = df[df["mulch"] == "sawdust"]

outcomes = ["yield_kg_bush", "berry_weight_g", "brix_pct",
            "soil_moisture_pct", "weed_biomass_g_m2", "soil_ph"]

pvals = [stats.ttest_ind(plastic[c], sawdust[c]).pvalue for c in outcomes]


print("%-20s %10s %10s %10s  %s" % ("Outcome", "plastic", "sawdust", "p", "Verdict"))
for c, p in zip(outcomes, pvals):
    v = "significant" if p < 0.05 else "not significant"
    print("%-20s %10.2f %10.2f %10.3g  %s"
          % (c, plastic[c].mean(), sawdust[c].mean(), p, v))
