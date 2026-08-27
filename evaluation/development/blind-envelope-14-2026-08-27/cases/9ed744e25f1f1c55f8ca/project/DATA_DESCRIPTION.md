# Data description

## File

`malting_lots.csv` — 48 data rows plus one header row, comma separated, no missing cells.

## What one row represents

One row is one micro-malting lot: a single 5 kg lot of spring malting barley (one variety, one
harvest year, all lots drawn from the same grain bulk), steeped under the regime named in that
row, then germinated and kilned under conditions identical for every lot, then analysed in the
laboratory. Each lot appears exactly once. The five outcome columns are the laboratory results
for that one lot.

## Design

Forty-eight lots were randomly allocated to two steeping regimes, 24 lots per regime:

| steep_regime | lots |
|---|---|
| `two_step` | 24 |
| `extended_air_rest` | 24 |

## Columns

| Column | Type | Units | Rounding | Description |
|---|---|---|---|---|
| `lot_id` | text | — | — | Lot identifier, `LOT-001` through `LOT-048`. Unique; one per row. |
| `steep_regime` | text | — | — | Group column. Exactly two values: `two_step` (conventional two-step steep) and `extended_air_rest` (extended air-rest steep). |
| `friability_pct` | number | percent | 0.1 | Friability of the finished malt, declared outcome 1. |
| `fine_extract_pct_dry` | number | percent, dry basis | 0.1 | Fine grind extract on a dry basis, declared outcome 2. |
| `fan_mg_per_l` | number | mg/L | whole number | Free amino nitrogen in the laboratory wort, declared outcome 3. |
| `diastatic_power_wk` | number | degrees Windisch-Kolbach | whole number | Diastatic power, declared outcome 4. |
| `beta_glucan_mg_per_l` | number | mg/L | whole number | Beta-glucan in the laboratory wort, declared outcome 5. |

The outcome columns appear in the declared order: friability, fine extract, FAN, diastatic power,
beta-glucan.

## Observed value ranges

| Column | Minimum | Maximum |
|---|---|---|
| `friability_pct` | 75.9 | 91.7 |
| `fine_extract_pct_dry` | 80.0 | 83.1 |
| `fan_mg_per_l` | 131 | 196 |
| `diastatic_power_wk` | 213 | 328 |
| `beta_glucan_mg_per_l` | 65 | 243 |

## Provenance

The values are synthetic, authored for this project rather than measured. `make_data.py` in this
directory produced the CSV from a fixed random seed; its docstring records the authored
within-regime means and standard deviations for every outcome.
