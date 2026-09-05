# Data description

## File

`data.csv` — 64 data rows plus one header row, comma separated.

## What one row represents

One row is one harvested lavender bush. All 64 bushes are the same cultivar and age and
grew in one uniform field. Each bush was cut whole, then distilled and analysed on its
own, so the six outcome columns in a row all come from that single bush's inflorescences.
Thirty-two bushes were cut at early bloom and thirty-two at full bloom, on the same two
mornings. Every bush has a value in every column; there are no blanks.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `bush_id` | text | Identifier for the bush, `LAV-001` through `LAV-064`. One per row, no repeats. |
| `harvest_stage` | text | Harvest timing group for that bush. Exactly two values: `early_bloom` or `full_bloom`. 32 rows carry each value. |
| `fresh_inflorescence_biomass_g` | number, 1 decimal | Fresh weight of the inflorescences cut from the bush, in grams, weighed before distillation. |
| `oil_yield_pct` | number, 2 decimals | Essential oil recovered from that bush, as a percent by weight of its dry inflorescence. |
| `linalool_pct` | number, 2 decimals | Linalool content of that bush's oil, as a percent of the oil. |
| `linalyl_acetate_pct` | number, 2 decimals | Linalyl acetate content of that bush's oil, as a percent of the oil. |
| `camphor_pct` | number, 2 decimals | Camphor content of that bush's oil, as a percent of the oil. |
| `cineole_1_8_pct` | number, 2 decimals | 1,8-cineole content of that bush's oil, as a percent of the oil. |

The six outcome columns appear in the order the trial plan declared them: fresh
inflorescence biomass, oil yield, linalool, linalyl acetate, camphor, 1,8-cineole.

## Observed ranges in the file

| Column | Minimum | Maximum |
| --- | --- | --- |
| `fresh_inflorescence_biomass_g` | 270.8 | 915.5 |
| `oil_yield_pct` | 1.05 | 3.15 |
| `linalool_pct` | 23.32 | 37.93 |
| `linalyl_acetate_pct` | 27.25 | 42.46 |
| `camphor_pct` | 0.23 | 1.42 |
| `cineole_1_8_pct` | 0.43 | 2.37 |

`data.csv` is a fixed authored file. It is written once and then read as-is.
