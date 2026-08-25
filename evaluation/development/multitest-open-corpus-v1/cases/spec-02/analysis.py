"""Cereal rye cover crop vs winter fallow: five soil health outcomes, 48 plots.

The five outcomes are one family of tests, so the five raw p-values are held
together and corrected in a single call rather than one at a time.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

ALPHA = 0.05

OUTCOMES = [
    "soil_organic_c_pct",
    "bulk_density_g_cm3",
    "aggregate_stability_pct",
    "microbial_biomass_c_mg_kg",
    "nitrate_n_mg_kg",
]

plots = pd.read_csv("data.csv")
fallow = plots[plots["system"] == "fallow"]
rye = plots[plots["system"] == "rye"]

print("plots: %d (fallow %d, rye %d)" % (len(plots), len(fallow), len(rye)))
print()

raw_p = []
means = []
for name in OUTCOMES:
    a = fallow[name]
    b = rye[name]
    t, p = stats.ttest_ind(a, b, equal_var=False)
    raw_p.append(p)
    means.append((a.mean(), b.mean()))

# One correction over the whole family of five, using the library default method.
reject, p_adj, alpha_sidak, alpha_bonf = multipletests(raw_p, alpha=ALPHA)

print("family size: %d outcomes, corrected together at alpha = %.2f"
      % (len(raw_p), ALPHA))
print()
print("%-28s %10s %10s %10s %10s  %s"
      % ("outcome", "fallow", "rye", "raw p", "adj p", "decision"))
for i, name in enumerate(OUTCOMES):
    fallow_mean, rye_mean = means[i]
    decision = "reject H0" if reject[i] else "keep H0"
    print("%-28s %10.3f %10.3f %10.4f %10.4f  %s"
          % (name, fallow_mean, rye_mean, raw_p[i], p_adj[i], decision))

print()
print("outcomes called significant after correction: %d of %d"
      % (sum(bool(r) for r in reject), len(OUTCOMES)))
