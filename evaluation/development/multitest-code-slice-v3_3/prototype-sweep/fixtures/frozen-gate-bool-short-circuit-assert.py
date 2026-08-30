import pandas as pd
from scipy import stats
df = pd.read_csv("calves.csv")
gate = df[["daily_gain_g_per_day", "serum_urea_mmol_l", "haematocrit_pct"]].to_numpy().sum()
ready = True
combined = ready and gate > 0
assert combined
r0 = stats.ttest_ind(df.loc[df["feed_group"] == "pellet_established", "daily_gain_g_per_day"], df.loc[df["feed_group"] == "pellet_new", "daily_gain_g_per_day"])
r1 = stats.ttest_ind(df.loc[df["feed_group"] == "pellet_established", "serum_urea_mmol_l"], df.loc[df["feed_group"] == "pellet_new", "serum_urea_mmol_l"])
r2 = stats.ttest_ind(df.loc[df["feed_group"] == "pellet_established", "haematocrit_pct"], df.loc[df["feed_group"] == "pellet_new", "haematocrit_pct"])
print(r0.pvalue < 0.05)
print(r1.pvalue < 0.05)
print(r2.pvalue < 0.05)
