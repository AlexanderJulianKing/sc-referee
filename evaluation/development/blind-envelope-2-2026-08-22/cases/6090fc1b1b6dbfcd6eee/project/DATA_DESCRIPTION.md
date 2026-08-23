# Data description

River restoration monitoring programme: sensitive stream invertebrate richness in restored versus
channelised reaches.

## Study units and groups

* **Experimental unit: the stream reach.** Restoration was carried out along whole reaches of
  roughly 200 m, so every kick-net sample taken inside a reach shares the same treatment, the same
  channel form, and the same upstream catchment.
* **20 reaches** in total, labelled `R01` through `R20`.
* **Two groups, 10 reaches each.**
  * `restored` (10 reaches): R01, R03, R05, R07, R09, R11, R13, R15, R17, R19
  * `channelised` (10 reaches): R02, R04, R06, R08, R10, R12, R14, R16, R18, R20
* **12 replicate kick-net samples per reach**, all taken on a single summer survey, giving
  **240 samples overall** (120 per group). The kick-nets are subsamples of the reach, not
  independently treated sites.

## File 1: `kicknet_samples_raw.csv` (raw, sample level)

**One row = one kick-net sample.** 240 data rows plus a header row. Twelve rows per reach.

| Column | Type | Description |
| --- | --- | --- |
| `reach_id` | text | Reach the sample came from, `R01`–`R20`. 20 distinct values, each appearing 12 times. |
| `restoration_group` | text | Treatment of the whole reach: `restored` or `channelised`. Constant within a reach. |
| `sample_id` | text | Identifier of the sample within its reach, formed as `<reach_id>_S01` … `<reach_id>_S12`. Unique across the file. |
| `distance_m` | number, 1 decimal | Distance in metres upstream of the reach start where the kick-net was taken. Kick-nets are spread along the ~200 m reach. Observed range 5.6–194.4. |
| `mean_depth_cm` | number, 1 decimal | Mean water depth in centimetres at the sampling point. Observed range 12.1–45.9. |
| `sensitive_taxa_count` | whole number | Count of mayfly, stonefly, and caddisfly (EPT) taxa found in that kick-net sample. Observed range 2–18. |

## File 2: `reach_summary.csv` (per-reach summary)

**One row = one reach.** Exactly 20 data rows plus a header row. One row per reach.

| Column | Type | Description |
| --- | --- | --- |
| `reach_id` | text | Reach identifier, `R01`–`R20`. Same labels and same meaning as in the raw file. |
| `restoration_group` | text | `restored` or `channelised`. Same labels and same meaning as in the raw file. |
| `n_samples` | whole number | Number of kick-net samples the reach contributed. 12 for every reach. |
| `mean_sensitive_taxa` | number, 2 decimals | The reach's mean `sensitive_taxa_count` across its 12 raw rows, rounded to two decimal places. |

## Consistency between the two files

The summary file is computed from the raw file, so the two agree by construction:

* Every `reach_id` in the summary appears in the raw file, and vice versa (20 reaches both ways).
* `restoration_group` for a reach is identical in both files.
* `n_samples` equals the number of raw rows carrying that `reach_id` (12 in every case; 240 in
  total).
* `mean_sensitive_taxa` equals the mean of that reach's `sensitive_taxa_count` values in the raw
  file, rounded to two decimals. This was checked for all 20 reaches with no mismatches.

## How the values were generated

`make_data.py` (standard library only, fixed seed `2039`, run with `/usr/local/bin/python3`)
produces both CSVs. Each reach gets its own level drawn around its group mean, and each kick-net
varies around its reach's level:

    sensitive_taxa_count = group mean + reach effect + kick-net noise

with target group means of 7.1 taxa (channelised) and 11.3 taxa (restored), a between-reach standard
deviation of 1.8 taxa, and a within-reach standard deviation of 2.2 taxa. Values are rounded to
whole taxa counts and held inside the plausible field range 2–18.

Realised values in the delivered files: channelised sample mean 7.03 taxa, restored sample mean
11.24 taxa; between-reach standard deviation of the 20 reach means 1.87 (channelised) and 1.77
(restored); pooled within-reach standard deviation 2.21. The nesting is therefore visible in the
data: reach means range from 4.25 to 14.58 taxa, well beyond what kick-net noise alone would
produce.
