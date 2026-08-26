# Data description

Tea shading trial: 48 mature tea bushes in the field, 24 under 40 percent shade netting over the
plucking table and 24 in full sun with no netting. Each bush was sampled once at the third plucking
round. Five outcomes were declared in the trial protocol before sampling, in the order listed below.

## `tea_shading_measurements.csv`

Raw measurement file. **One row is one tea bush**, carrying that bush's identifier, its shading
regime, and its single measurement of each of the five declared outcomes. 48 data rows plus a
header. There are no blank cells.

| Column | Meaning | Unit |
| --- | --- | --- |
| `bush_id` | Bush identifier, `TB001` through `TB048`, unique across the file | none (text label) |
| `shading_regime` | Shading treatment the bush received. Exactly two distinct values: `shade_net_40pct` (40 percent shade netting) and `full_sun` (no netting) | none (group label) |
| `total_catechins_mg_g` | Declared outcome 1: total catechins in the sampled shoots | milligrams per gram dry weight |
| `caffeine_mg_g` | Declared outcome 2: caffeine in the sampled shoots | milligrams per gram dry weight |
| `theanine_mg_g` | Declared outcome 3: theanine in the sampled shoots | milligrams per gram dry weight |
| `leaf_nitrogen_pct` | Declared outcome 4: leaf nitrogen content | percent of dry weight |
| `young_shoot_yield_g` | Declared outcome 5: young shoot yield harvested from the bush at the round | grams per bush |

Bush identifiers run in field-layout order, so the two regimes are interleaved rather than blocked
into the first and second halves of the file.

## `upstream_adjusted_pvalues.csv`

Results file released by the shared upstream testing stage, which sits outside this project. **One
row is one declared outcome**, carrying the p-value that the upstream stage released for the
comparison of the two shading regimes on that outcome. 5 data rows plus a header, one per declared
outcome, in the protocol order.

| Column | Meaning | Unit |
| --- | --- | --- |
| `outcome` | Name of the declared outcome, written exactly as the matching column name in `tea_shading_measurements.csv` | none (text label) |
| `adjusted_p_value` | The outcome's p-value **after** the upstream stage adjusted the whole family of five together for multiple comparisons. This is not a raw per-outcome p-value and must not be adjusted again | probability, 0 to 1 |
| `adjustment_method` | Multiple-comparison procedure the upstream stage applied across the family, `holm_bonferroni` for every row | none (text label) |
| `family_size` | Number of declared outcomes adjusted together, 5 for every row | count |

The values in `adjusted_p_value` are already family-adjusted across all five declared outcomes.
The testing and the adjustment happened upstream of this project.
