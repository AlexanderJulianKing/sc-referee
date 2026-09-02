# data.csv

Bunch-thinning trial on mature Medjool-type date palms in one uniformly managed block at a
date palm research station. Two strand-thinning intensities were applied by the same crew at
the same growth stage, and all palms were harvested and measured at the same maturity.

## What one row represents

One row is one palm: its identifier, the thinning intensity it received, and the eight declared
trial outcomes measured on that palm. There are 56 data rows plus a header row, one row per
palm, 28 palms per thinning intensity. Every palm has a value for every outcome; the file has
no blank cells.

## Columns

Columns appear in this order. The eight outcome columns follow the order in which the trial
plan declared them.

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `palm_id` | text | none | Palm identifier, `P01` through `P56`. One identifier per palm, all unique. |
| `thinning_intensity` | text | none | Group column. Exactly two values: `light` (light strand thinning) and `heavy` (heavy strand thinning). |
| `fruit_weight_g` | number | grams | Declared outcome 1. Mean single fruit weight for that palm. |
| `fruit_length_mm` | number | millimetres | Declared outcome 2. Fruit length. |
| `fruit_width_mm` | number | millimetres | Declared outcome 3. Fruit width. |
| `yield_per_palm_kg` | number | kilograms | Declared outcome 4. Harvested yield for that palm. |
| `total_soluble_solids_brix` | number | degrees Brix | Declared outcome 5. Total soluble solids. |
| `fruit_moisture_pct` | number | percent | Declared outcome 6. Fruit moisture. |
| `flesh_to_seed_ratio` | number | none (unitless ratio) | Declared outcome 7. Flesh mass divided by seed mass. No unit suffix because the quantity is a ratio. |
| `fruit_firmness_n` | number | newtons | Declared outcome 8. Fruit firmness. |

## Value ranges present in the file

| Column | Minimum | Maximum | Decimal places |
| --- | --- | --- | --- |
| `fruit_weight_g` | 8.94 | 14.79 | 2 |
| `fruit_length_mm` | 35.9 | 47.8 | 1 |
| `fruit_width_mm` | 20.2 | 27.1 | 1 |
| `yield_per_palm_kg` | 72.3 | 120.4 | 1 |
| `total_soluble_solids_brix` | 61.3 | 76.8 | 1 |
| `fruit_moisture_pct` | 16.5 | 27.9 | 1 |
| `flesh_to_seed_ratio` | 6.57 | 10.66 | 2 |
| `fruit_firmness_n` | 5.5 | 12.7 | 1 |

## Format notes

Plain comma-separated text, UTF-8, one header row, no quoting needed because no field contains
a comma. Numbers are written as fixed decimals with the decimal places listed above.
