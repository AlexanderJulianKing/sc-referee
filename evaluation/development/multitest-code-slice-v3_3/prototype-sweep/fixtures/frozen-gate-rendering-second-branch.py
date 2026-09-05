READY = True
import pandas as pd
from scipy import stats
df = pd.read_csv("calves.csv")
r0 = stats.ttest_ind(df.loc[df["feed_group"] == "pellet_established", "daily_gain_g_per_day"], df.loc[df["feed_group"] == "pellet_new", "daily_gain_g_per_day"])
r1 = stats.ttest_ind(df.loc[df["feed_group"] == "pellet_established", "serum_urea_mmol_l"], df.loc[df["feed_group"] == "pellet_new", "serum_urea_mmol_l"])
r2 = stats.ttest_ind(df.loc[df["feed_group"] == "pellet_established", "haematocrit_pct"], df.loc[df["feed_group"] == "pellet_new", "haematocrit_pct"])
s0 = "yes" if r0.pvalue < 0.05 else "no"
s1 = "yes" if r1.pvalue < 0.05 else "no"
s2 = "yes" if r2.pvalue < 0.05 else "no"
if READY:
    print(s0)
print(s1); print(s2)
