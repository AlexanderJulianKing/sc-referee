# Data description

## File

`piglet_shannon.csv` — the single data file for this project, comma separated, with a header row.
It is produced by `make_data.py` (fixed random seed, standard library only), which writes the file
next to itself. Re-running the generator reproduces the file exactly.

## What one row is

One row is **one faecal sample**: a single weekly collection from a single piglet. Each piglet
contributes five rows, one per study week, so the rows for a given `piglet_id` are five successive
time points on that same animal.

## Units and counts

- Animals: **22 weaned piglets**, each housed in its own pen.
- Groups: **2** — 11 piglets on the control starter ration (`control`, ids P01–P11) and 11 piglets on
  the same ration plus a fibre supplement (`supplement`, ids P12–P22).
- Sampling: **5 consecutive weeks**, one faecal sample per piglet per week.
- Rows: **110** data rows (22 piglets x 5 weeks), plus 1 header row. 55 rows per ration group.
- No missing values; every piglet has all five weeks.

## Columns

| column | type | description |
| --- | --- | --- |
| `piglet_id` | text | Identifier of the animal the sample came from, `P01` through `P22`. Appears five times, once per week. |
| `ration` | text | Diet group of that piglet, either `control` (starter ration alone) or `supplement` (same ration plus the fibre supplement). Constant within a piglet. |
| `week` | integer | Study week the sample was collected in, 1 to 5. |
| `shannon_diversity` | number | Shannon diversity index of the gut microbial community in that faecal sample, rounded to 3 decimals. Observed range 2.744 to 4.263. |
| `body_weight_kg` | number | Body weight of the piglet in kilograms on the day of that sampling, rounded to 2 decimals. Weekly means climb from about 7.2 kg in week 1 to about 14.1 kg in week 5. |
| `read_depth` | integer | Number of sequencing reads obtained for that sample, in the tens of thousands. Observed range 27,101 to 62,697, mean about 45,700. |

Column headers are lowercase words joined by underscores. Rows are ordered by piglet id, then by week.

## How the values were generated

`make_data.py` builds each Shannon value as

```
shannon = group mean + piglet effect + week trend + residual
```

- group mean: 3.21 for `control`, 3.58 for `supplement`
- piglet effect: Normal(0, 0.22), one draw per animal, giving the between-animal spread
- week trend: +0.03 per week, centred on week 3, the slight upward creep over the study
- residual: Normal(0, 0.15), one draw per sample, the week-to-week movement within one piglet

Realised values in the file: control mean 3.214 (SD 0.212), supplement mean 3.569 (SD 0.293);
between-piglet SD 0.15 in the control group and 0.27 in the supplemented group; mean within-piglet
SD 0.155 and 0.141.

Body weight is `7.0 + 1.75 x (week - 1)` plus a per-piglet offset (SD 0.55) and per-sample noise
(SD 0.25). Read depth is drawn from Normal(45,000, 9,000) per sample and held inside 22,000–78,000.
