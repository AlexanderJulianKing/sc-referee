"""Compare harvest titer between the standard and enriched fed-batch feed schedules.

The CSV holds 60 rows, but it does NOT hold 60 independent observations. Each
bioreactor run was sampled five times from the same harvest pool and each sample
was assayed once on the protein A HPLC, so the five rows of a run are repeat
measurements of one piece of material. Feed strategy was assigned to the run,
not to the sample, so the run is the experimental unit.

That is why this script aggregates first and tests second: we collapse the five
assays of each run to a single per-run mean titer, and only then hand the data to
the t-test. The test therefore sees 6 runs against 6 runs. Testing the raw 60
rows would count analytical noise as if it were independent process replication
and would inflate the apparent sample size five-fold.
"""

import pandas as pd
from scipy import stats

CSV = "harvest_titer.csv"

df = pd.read_csv(CSV)

print("=" * 68)
print("Raw file")
print("=" * 68)
print(f"assay rows in file          : {len(df)}")
print(f"distinct fermenter runs     : {df['fermenter_run'].nunique()}")
print(f"assays per run              : {len(df) // df['fermenter_run'].nunique()}")

# --- Step 1: within-run assay noise -------------------------------------
# Spread of the five replicates about their own run mean. This is pure
# analytical noise, and it is reported so the reader can see how small it is
# next to the run-to-run spread.
within_run_sd = df.groupby("fermenter_run")["titer_g_per_l"].std(ddof=1)
pooled_within_sd = (within_run_sd.pow(2).mean()) ** 0.5

# --- Step 2: collapse to one value per run ------------------------------
# One row per fermenter run: the mean of that run's five assays, carrying the
# run's feed strategy along. This is the aggregation step that makes the rows
# independent of one another before any test is run.
per_run = (
    df.groupby(["fermenter_run", "feed_strategy"], as_index=False)
      .agg(mean_titer_g_per_l=("titer_g_per_l", "mean"),
           n_assays=("titer_g_per_l", "size"))
)
per_run["within_run_sd"] = per_run["fermenter_run"].map(within_run_sd)

print()
print("=" * 68)
print("Per-run mean titer (one row per fermenter run)")
print("=" * 68)
print(per_run.to_string(index=False,
                        float_format=lambda v: f"{v:.3f}"))

# --- Step 3: group summaries on the run-level values --------------------
standard = per_run.loc[per_run["feed_strategy"] == "standard",
                       "mean_titer_g_per_l"]
enriched = per_run.loc[per_run["feed_strategy"] == "enriched",
                       "mean_titer_g_per_l"]

print()
print("=" * 68)
print("Group summaries (computed on run-level means, not on assay rows)")
print("=" * 68)
for name, values in (("standard", standard), ("enriched", enriched)):
    print(f"{name:>9}: n_runs = {len(values)}  "
          f"mean = {values.mean():.3f} g/L  "
          f"SD = {values.std(ddof=1):.3f} g/L  "
          f"assay rows behind it = {len(values) * 5}")

print()
print(f"difference (enriched - standard) : "
      f"{enriched.mean() - standard.mean():.3f} g/L")

print()
print("Within-run assay noise (analytical replicates only):")
print(f"  pooled within-run SD          : {pooled_within_sd:.4f} g/L")
print(f"  smallest within-run SD        : {within_run_sd.min():.4f} g/L")
print(f"  largest within-run SD         : {within_run_sd.max():.4f} g/L")
print(f"  SD of the 12 run-level means  : "
      f"{per_run['mean_titer_g_per_l'].std(ddof=1):.4f} g/L")

# --- Step 4: the test, on 6 values against 6 ----------------------------
t_stat, p_value = stats.ttest_ind(enriched, standard)

print()
print("=" * 68)
print("Two-sample t-test on per-run mean titer")
print("=" * 68)
print(f"units entering the test : fermenter runs (not assay rows)")
print(f"N per group             : enriched = {len(enriched)}, "
      f"standard = {len(standard)}")
print(f"degrees of freedom      : {len(enriched) + len(standard) - 2}")
print(f"t statistic             : {t_stat:.4f}")
print(f"p-value                 : {p_value:.6f}")
