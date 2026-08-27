# Data description

## File

`mango_coating_shelf_life.csv`

## Study and design

A fresh-cut produce laboratory tested an edible coating on ready-to-eat mango slices.
Sixty retail packs were prepared on the same day from the same fruit batch. Thirty packs
were dipped in a chitosan and ascorbic acid edible coating before packing. Thirty packs
were packed uncoated. All sixty packs were stored at 5 degrees Celsius and assessed
individually on day eight. The same five measurements were taken on every pack.

Group sizes: 30 coated packs and 30 uncoated packs, 60 packs in total.

## What one row represents

One row is one retail pack of mango slices, measured once on day eight of storage.
Each pack appears exactly once. There are 60 data rows plus a header row, and no
blank cells.

## Columns

The file has 7 columns, in this order.

| # | Column | Type | Units | Description |
|---|--------|------|-------|-------------|
| 1 | `pack_id` | text | none | Pack identifier, `PK-01` through `PK-60`. Unique for each row. |
| 2 | `coating` | text | none | Group label. Exactly two values: `coated` (dipped in the chitosan and ascorbic acid coating) or `uncoated` (packed without coating). |
| 3 | `firmness_n` | number | newtons (N) | Slice firmness measured by penetrometer. Reported to 1 decimal place. |
| 4 | `browning_index` | number | unitless, 0 to 100 | Surface browning index from image analysis. Higher means more browning. Reported to 1 decimal place. |
| 5 | `tss_brix` | number | degrees Brix | Total soluble solids in the expressed juice. Reported to 1 decimal place. |
| 6 | `weight_loss_pct` | number | percent | Pack weight loss over the storage period, as a percent of the starting pack weight. Reported to 2 decimal places. |
| 7 | `aerobic_count_log10_cfu_per_g` | number | log10 CFU/g | Mesophilic aerobic plate count, on a base-10 log scale of colony-forming units per gram. Reported to 2 decimal places. |

Columns 3 through 7 are the five pack-level outcomes the laboratory declared before the
trial, listed here in that declared order.

## Value ranges

Each outcome falls inside the plausible range the laboratory specified for it.

| Column | Plausible range | Observed minimum | Observed maximum |
|--------|-----------------|------------------|------------------|
| `firmness_n` | 7 to 26 | 7.50 | 23.60 |
| `browning_index` | 8 to 50 | 10.60 | 48.40 |
| `tss_brix` | 11.5 to 18.5 | 12.20 | 17.30 |
| `weight_loss_pct` | 0.8 to 8.5 | 2.04 | 7.22 |
| `aerobic_count_log10_cfu_per_g` | 1.8 to 6.5 | 2.30 | 5.90 |

## Provenance

These are simulated values, not measurements from a real laboratory. They were produced by
`make_data.py` in this directory with a fixed random seed, so rerunning that script
reproduces the file exactly. Each outcome was drawn from a normal distribution with a
per-group mean and spread, resampled when a draw fell outside the plausible range for that
outcome, then rounded to the number of decimal places the instrument would report.
