"""Generate harvest_titer.csv for the fed-batch CHO feed-strategy comparison.

Design intent encoded here:
  * 12 independent 2 L bioreactor runs (6 standard feed, 6 enriched feed).
    The run is the experimental unit: separate inoculation, vessel, 14-day campaign.
  * Each run has its own TRUE harvest titer. Run-to-run variability is large
    (inoculum age, pH excursions, feed timing).
  * Each run is sampled 5 times from the same harvest pool and each sample is
    assayed on protein A HPLC. Those 5 rows are analytical replicates, so they
    scatter only by assay noise (~2% CV), not by process variability.
  * harvest_viability_pct is a run-level measurement, so it is repeated
    identically across the 5 rows of a run.

Fixed seed so the CSV is reproducible.
"""

import csv
import numpy as np

SEED = 20260821
rng = np.random.default_rng(SEED)

N_RUNS_PER_GROUP = 6
N_REPLICATES = 5

# Process-level (run-to-run) parameters, g/L.
GROUP_PARAMS = {
    "standard": {"prefix": "RUN-A", "true_mean": 2.85, "true_sd": 0.30,
                 "viab_mean": 74.0, "viab_sd": 4.0},
    "enriched": {"prefix": "RUN-B", "true_mean": 3.75, "true_sd": 0.38,
                 "viab_mean": 79.0, "viab_sd": 4.0},
}

# Analytical (within-run) assay noise, as a coefficient of variation.
ASSAY_CV = 0.022

REPLICATE_LABELS = [f"S{i}" for i in range(1, N_REPLICATES + 1)]

rows = []
for strategy in ("standard", "enriched"):
    p = GROUP_PARAMS[strategy]
    for i in range(1, N_RUNS_PER_GROUP + 1):
        run_id = f"{p['prefix']}{i}"

        # One true titer per run: this is the process signal.
        true_titer = rng.normal(p["true_mean"], p["true_sd"])
        true_titer = float(np.clip(true_titer, 2.0, 5.0))

        # One viability reading per run, repeated on every replicate row.
        viability = rng.normal(p["viab_mean"], p["viab_sd"])
        viability = float(np.clip(viability, 65.0, 88.0))

        for label in REPLICATE_LABELS:
            # Assay noise only: repeat measurements of the same harvest pool.
            measured = rng.normal(true_titer, ASSAY_CV * true_titer)
            rows.append({
                "fermenter_run": run_id,
                "feed_strategy": strategy,
                "sample_replicate": label,
                "harvest_viability_pct": f"{viability:.1f}",
                "titer_g_per_l": f"{measured:.3f}",
            })

OUT = "harvest_titer.csv"
with open(OUT, "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=[
        "fermenter_run", "feed_strategy", "sample_replicate",
        "harvest_viability_pct", "titer_g_per_l",
    ])
    writer.writeheader()
    writer.writerows(rows)

print(f"wrote {OUT}: {len(rows)} data rows, "
      f"{len({r['fermenter_run'] for r in rows})} runs")
