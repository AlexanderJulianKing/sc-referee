# Data description: estate tap-water survey

## Files

| File | Role |
| --- | --- |
| `make_data.py` | Seeded generator (`SEED = 20260825`, NumPy `default_rng`). Running it rewrites `tap_water_survey.csv` byte-for-byte. |
| `tap_water_survey.csv` | The study data file. This is the analysis input. |

## `tap_water_survey.csv`

44 data rows plus one header row. One row per occupied household sampled on the
estate. Each row holds the tap-water measurements taken at that household's
kitchen tap on the single sampling morning, together with the household's
identifier and whether a certified point-of-use filter was fitted. Every cell is
filled; there are no missing values and no negative values.

22 rows have `filter_status = filtered` (`HH-001` through `HH-022`) and 22 have
`filter_status = unfiltered` (`HH-023` through `HH-044`).

### Columns, in file order

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `household_id` | text | none | Household label, `HH-001` to `HH-044`. Unique; one per row. |
| `first_draw_lead_ug_l` | number | micrograms per litre | Lead in the first draw drawn from the kitchen tap after the standing-time protocol. Reported to 0.1. Range in this file 0.7 to 16.6. |
| `flushed_lead_ug_l` | number | micrograms per litre | Lead in the sample taken after the tap ran for two minutes. Reported to 0.1. Range 0.2 to 5.6. |
| `first_draw_copper_mg_l` | number | milligrams per litre | Copper in the same first draw as `first_draw_lead_ug_l`. Reported to 0.001. Range 0.103 to 0.810. |
| `first_draw_turbidity_ntu` | number | nephelometric turbidity units | Turbidity of the same first draw. Reported to 0.01. Range 0.12 to 0.97. |
| `filter_status` | text | none | Grouping factor with exactly two values: `filtered` (certified point-of-use filter fitted at the kitchen tap the previous year) and `unfiltered` (no filter). |

The four measurement columns appear in the order the sampling plan declared
them: first-draw lead, flushed lead, first-draw copper, first-draw turbidity.

## How the values were generated

`make_data.py` draws each outcome from a right-skewed (lognormal) distribution
whose mean and spread match the levels in the sampling plan, then reports every
reading at the laboratory's rounding resolution. Within a household the four
outcomes share a latent "plumbing condition" term, so a household with a bad
service pipe tends to read high on more than one outcome. Readings below the
laboratory reporting limit would be written at the limit; in this file no
reading falls that low.

Two filtered households (`HH-004` at 0.83 NTU and `HH-019` at 0.97 NTU) were
sampled where disturbed sediment left the first draw visibly cloudy, so their
turbidity readings sit well above the rest of their group. They are genuine
measured values, not data errors, and they are included as measured.
