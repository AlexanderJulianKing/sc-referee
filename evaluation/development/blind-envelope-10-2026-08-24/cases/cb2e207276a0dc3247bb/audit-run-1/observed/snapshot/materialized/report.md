# Nitrogen rate and sorghum plant performance

## Data description

The analysis reads one file, `sorghum_nitrogen_plants.csv`. **One row is one harvested
sorghum plant.** Seventy-two individually tagged grain sorghum plants were sampled at
physiological maturity on a single uniform field site at one agronomy station: 36 grown
under 60 kg N/ha and 36 under 120 kg N/ha. Each plant was harvested and measured on its
own, and each outcome was measured once on that plant. The file holds 72 data rows plus a
header row, with no empty cells.

The file has six columns:

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `plant_id` | text | none | Tag on the individual plant, `SB001` through `SB072`, unique across the file. |
| `n_rate_group` | text | none | Nitrogen fertiliser rate the plant was grown under. Exactly two values: `n60` (60 kg N/ha, 36 plants) and `n120` (120 kg N/ha, 36 plants). |
| `grain_yield_g` | number | grams per plant | Clean, dried grain harvested from that plant. |
| `panicle_length_cm` | number | centimetres | Length of that plant's panicle, the grain head. |
| `stem_brix_pct` | number | degrees Brix | Sugar content of the juice pressed from that plant's stem. |
| `plant_height_cm` | number | centimetres | Height from the soil surface to the panicle tip. |

## Methods

The protocol declared four outcomes in advance, in this order: grain yield, panicle length,
stem juice sugar, plant height. Each outcome was compared between the two nitrogen rate
groups with an independent two-sample t-test, giving four raw p-values.

All four raw p-values were then passed together, in the declared order, as one family in a
single call to the multiple comparisons adjustment routine of `statsmodels`
(`statsmodels.stats.multitest.multipletests`). No correction method was named or configured,
so the routine applied its own default adjustment. Every significance verdict below is the
verdict that routine returned at a family-wise level of 0.05.

## Group summaries

Mean and standard deviation for each group, with 36 plants per group.

| Outcome | n60 mean (SD) | n120 mean (SD) | Difference (n120 minus n60) |
| --- | --- | --- | --- |
| Grain yield (g/plant) | 64.56 (10.99) | 76.47 (12.82) | +11.91 |
| Panicle length (cm) | 25.00 (2.49) | 26.56 (2.57) | +1.56 |
| Stem juice sugar (degrees Brix) | 13.46 (2.04) | 12.80 (1.74) | -0.66 |
| Plant height (cm) | 162.52 (14.33) | 167.36 (13.84) | +4.83 |

## Test results

Outcomes are listed in the declared order. Each row shows the t-statistic on 70 degrees of
freedom, the raw p-value, the adjusted p-value, and the verdict returned by the adjustment
routine.

| # | Outcome | t (df = 70) | Raw p | Adjusted p | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | Grain yield (g/plant) | -4.234 | 0.000069 | 0.000275 | Significant |
| 2 | Panicle length (cm) | -2.621 | 0.010742 | 0.031881 | Significant |
| 3 | Stem juice sugar (degrees Brix) | 1.478 | 0.143779 | 0.266886 | Not significant |
| 4 | Plant height (cm) | -1.455 | 0.150138 | 0.266886 | Not significant |

All four declared outcomes were adjusted together as one family, in one call, and the
conclusions above rest on the adjusted values rather than on the raw ones. Two outcomes,
grain yield and panicle length, remain significant after adjustment. Stem juice sugar and
plant height do not, and neither was significant before adjustment either.

## Agronomic conclusion

On this site, raising the nitrogen rate from 60 to 120 kg N/ha lifted grain production per
plant. Mean grain yield rose from 64.56 g at the lower rate to 76.47 g at the higher rate,
a gain of 11.91 g per plant, and mean panicle length rose by 1.56 cm. Both differences hold
up once the whole declared family of four outcomes is adjusted together.

The extra nitrogen did not show a detectable effect on the other two outcomes. Stem juice
sugar was 0.66 degrees Brix lower at the higher rate and plant height was 4.83 cm greater,
but neither difference was significant, so this sample gives no evidence that the higher
rate changes stem sugar concentration or overall plant stature. The gain from the higher
rate here is a grain-and-panicle response.

These results come from a single uniform site in one season, with plants as the sampled
units rather than replicated field plots, so they describe this sample and should not be
read as a general nitrogen recommendation across sites or seasons.
