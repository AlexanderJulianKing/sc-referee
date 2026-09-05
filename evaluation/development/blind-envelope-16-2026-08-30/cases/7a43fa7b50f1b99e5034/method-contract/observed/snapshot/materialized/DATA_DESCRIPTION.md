# Data description

## File

`quail_flooring.csv` — 48 data rows plus one header row, comma separated, no missing values.

## What one row represents

One row is **one Japanese quail chick**. Each chick was housed on its own from hatch to 21 days of
age, reared on one of the two brooder floor types, and measured once at the end of the 21-day
rearing period. Every chick contributes exactly one row and has a value for all six outcomes, so
there are 48 rows for the 48 chicks: 24 on plastic mesh flooring and 24 on chopped straw litter.

## Columns

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `chick_id` | text | — | Per-chick identifier, `q01` through `q48`. Unique, one per row. |
| `floor_type` | text | — | Brooder floor the chick was reared on. Exactly two values: `mesh` (plastic mesh flooring, 24 chicks) and `straw` (chopped straw litter, 24 chicks). |
| `body_weight_g` | number | g | Body weight at 21 days of age. |
| `feed_intake_g_d` | number | g/day | Average daily feed intake over the whole rearing period. |
| `footpad_score_pts` | integer | points | Foot-pad lesion score at 21 days on a 0 to 4 scale, where 0 is no visible lesion and 4 is the most severe. Whole numbers only. |
| `tibia_strength_n` | number | N | Tibia breaking strength (newtons). |
| `corticosterone_ng_ml` | number | ng/mL | Plasma corticosterone concentration. Right-skewed across birds. |
| `tonic_immobility_s` | number | s | Duration of tonic immobility (seconds), a behavioural fear measure. Right-skewed across birds. |

The six outcome columns appear in the order the trial declared them in advance: body weight, feed
intake, foot-pad lesion score, tibia breaking strength, plasma corticosterone, tonic immobility.

## Observed ranges (both floor types pooled)

| Column | Minimum | Maximum |
| --- | --- | --- |
| `body_weight_g` | 76.3 | 108.3 |
| `feed_intake_g_d` | 9.94 | 14.31 |
| `footpad_score_pts` | 0 | 4 |
| `tibia_strength_n` | 18.2 | 37.8 |
| `corticosterone_ng_ml` | 2.15 | 9.26 |
| `tonic_immobility_s` | 42 | 251 |
