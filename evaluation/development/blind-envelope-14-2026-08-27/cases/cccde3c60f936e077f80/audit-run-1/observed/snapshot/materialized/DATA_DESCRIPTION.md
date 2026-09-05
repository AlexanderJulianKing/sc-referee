# Data description: `deer_condition.csv`

## What the file holds

Condition measurements from an autumn cull of roe deer (*Capreolus capreolus*)
yearlings in two neighbouring hunting districts. Ninety-six animals were
sampled, forty-eight from the northern district and forty-eight from the
southern district.

**One row is one deer.** Each animal was weighed and sampled once at the game
larder, and the same set of measurements was taken on every animal. No animal
appears twice, and there are no repeated visits or follow-up measurements.

The file has a header row plus 96 data rows. Every cell is filled; there are no
blanks and no missing-value codes.

## Columns

| # | Column | Type | Units | Description |
|---|--------|------|-------|-------------|
| 1 | `deer_id` | text | none | Animal identifier, `RD-001` through `RD-096`, assigned in larder processing order. Unique across the file. |
| 2 | `district` | text | none | Group label. Exactly two values: `north` and `south`. 48 rows each. |
| 3 | `carcass_mass_kg` | number | kg | Dressed carcass mass, recorded to 0.1 kg on the larder scale. |
| 4 | `kidney_fat_index` | number | ratio (unitless) | Kidney fat index: mass of perirenal fat divided by mass of the trimmed kidney. Recorded to two decimals. |
| 5 | `back_fat_mm` | number | mm | Subcutaneous back fat depth at the rump, measured with callipers to 0.1 mm. `0.0` means no measurable fat layer. |
| 6 | `jaw_length_mm` | number | mm | Lower jaw (mandible) length, measured to 0.1 mm. |
| 7 | `haemoglobin_g_per_dl` | number | g/dL | Blood haemoglobin concentration, recorded to 0.1 g/dL. |
| 8 | `serum_urea_mmol_per_l` | number | mmol/L | Serum urea concentration, recorded to 0.1 mmol/L. |
| 9 | `faecal_egg_count_epg` | integer | eggs per gram | Faecal strongyle egg count from a rectal sample, read by the McMaster method. Whole numbers in steps of 25 eggs per gram, the resolution of the counting chamber. `0` means no eggs seen. The distribution is right-skewed: most animals are low, a few are very high. |

Columns 3 through 9 are the seven condition outcomes declared before the season,
and they appear in the file in that declared order.

## Observed value ranges (all 96 animals pooled)

| Column | Minimum | Maximum |
|--------|---------|---------|
| `carcass_mass_kg` | 11.3 | 20.6 |
| `kidney_fat_index` | 0.20 | 2.48 |
| `back_fat_mm` | 0.0 | 11.0 |
| `jaw_length_mm` | 141.2 | 161.4 |
| `haemoglobin_g_per_dl` | 10.6 | 17.2 |
| `serum_urea_mmol_per_l` | 2.8 | 8.6 |
| `faecal_egg_count_epg` | 0 | 900 |

## Provenance

The values are simulated field data, produced by `generate_data.py` with a fixed
random seed. They are realistic in scale, spread and rounding, but they are not
records of real animals.
