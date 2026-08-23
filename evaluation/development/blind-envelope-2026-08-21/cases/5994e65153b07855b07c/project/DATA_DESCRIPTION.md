# Data description

## File

`harvest_titer.csv` — 60 data rows plus one header row.

## What one row represents

One row is **one protein A HPLC assay of one harvest sample**. It is *not* one bioreactor run.
At the end of each 14-day campaign the operator drew five separate samples from that reactor's
harvest pool and assayed each sample once. Each of those five assays gets its own row, so every
run contributes five rows that describe the same harvested material.

## Units and counts

- **Experimental unit:** the fermenter run. Each run is a separate inoculation, a separate 2 L
  vessel setup, and a separate 14-day fed-batch campaign.
- **Number of runs:** 12 (6 standard feed, 6 enriched feed).
- **Assays per run:** 5 analytical replicates from the same harvest pool.
- **Total rows:** 12 x 5 = 60.

Because the five rows within a run are repeat measurements of the same harvest, they are not
independent observations of the feeding strategy. The 60 rows carry only 12 independent process
observations.

## Groups

| Group | `feed_strategy` value | Run labels | Runs | Rows |
|---|---|---|---|---|
| Standard fed-batch feed schedule | `standard` | RUN-A1 … RUN-A6 | 6 | 30 |
| Enriched fed-batch feed schedule | `enriched` | RUN-B1 … RUN-B6 | 6 | 30 |

## Columns

| Column | Type | Level | Description |
|---|---|---|---|
| `fermenter_run` | string | run | Identifier of the bioreactor run the sample came from. Twelve distinct labels: `RUN-A1`–`RUN-A6` (standard feed) and `RUN-B1`–`RUN-B6` (enriched feed). Repeats across the five rows of a run. |
| `feed_strategy` | string | run | Feeding strategy used for that run. Exactly two values: `standard` or `enriched`. Constant within a run. |
| `sample_replicate` | string | assay | Which of the five harvest samples this row reports: `S1`, `S2`, `S3`, `S4`, or `S5`. Labels are within-run only, so `S1` in one run has no relationship to `S1` in another. |
| `harvest_viability_pct` | float, one decimal | run | Viable cell percentage measured at harvest, range 65–88 in this data set. This is a single run-level reading, so it is identical on all five rows of a run and must not be treated as five observations. |
| `titer_g_per_l` | float, three decimals | assay | Measured monoclonal antibody titer in grams per litre for that one assay. This is the outcome of interest and the only column that varies from row to row within a run. |

## Structure of the variation

Two sources of spread sit in `titer_g_per_l`, and they are very different in size:

- **Between runs:** large. Runs differ because of inoculum age, pH excursions, and feed timing.
  Run-level mean titers in this data set span roughly 2.55 to 3.97 g/L.
- **Within a run:** small. The five replicates differ only by protein A HPLC assay noise, about
  2% of the value, giving within-run standard deviations of roughly 0.03 to 0.14 g/L.

Any comparison of the two feed strategies has to work at the run level, because that is where the
independent replication is.
