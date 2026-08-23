# Data description

## File

`harvest_weights.csv` — one data file, plain text, comma separated, 300 data rows plus one
header row (301 lines total).

## What one row is

One row is one individual shrimp that was weighed at harvest. Every row carries the pond that
shrimp came from, the feed treatment that pond received, an identifier for that shrimp, and its
body weight in grams.

## Units and counts

- 10 earthen grow-out ponds, stocked with Pacific white shrimp postlarvae at the same density
  on the same day.
- 30 shrimp dip-netted at random from each pond at harvest and weighed individually.
- 10 ponds x 30 shrimp = 300 weighed shrimp, so 300 rows.

## The two groups

The feed treatment is assigned at the pond level, five ponds per treatment.

| Feed treatment | Ponds | Ponds in file | Shrimp weighed |
|---|---|---|---|
| `standard` | 5 | P01, P02, P03, P04, P05 | 150 |
| `supplemented` | 5 | P06, P07, P08, P09, P10 | 150 |

`standard` ponds received the farm's standard commercial grow-out diet. `supplemented` ponds
received that same diet with a fermented soy by-product added.

## Columns

| Column | Type | Description |
|---|---|---|
| `pond_id` | text | Identifier of the earthen pond the shrimp was harvested from. Values `P01` through `P10`. Ten distinct values, 30 rows each. |
| `feed_treatment` | text | Diet the pond received for the whole grow-out. Two values: `standard` (standard commercial diet) and `supplemented` (standard diet plus fermented soy by-product). Constant within a pond. |
| `shrimp_id` | text | Identifier of the individual shrimp, formed as the pond id plus a within-pond sequence number, e.g. `P03-S17`. Unique across the file, so it also serves as the row key. |
| `body_weight_g` | number | Individual whole body weight of that shrimp at harvest, in grams, recorded to one decimal place. Observed range 9.2 g to 29.2 g. |

## How the file was produced

`make_data.py` writes `harvest_weights.csv` using the Python standard library only, with a fixed
random seed (`SEED = 20260823`), so the file is reproducible. Each pond gets its own mean harvest
weight drawn around its treatment mean (18.5 g standard, 20.2 g supplemented) with a pond-to-pond
spread of 1.6 g, and each shrimp is drawn around its own pond's mean with a within-pond spread of
3.2 g. Draws are kept inside a plausible harvest window of 9 g to 31 g. The CSV is committed as
plain text and is the input to the analysis; the analysis does not regenerate it.

Observed in the committed file: `standard` mean 18.53 g (SD 3.36 g, n = 150), `supplemented`
mean 20.60 g (SD 3.38 g, n = 150).
