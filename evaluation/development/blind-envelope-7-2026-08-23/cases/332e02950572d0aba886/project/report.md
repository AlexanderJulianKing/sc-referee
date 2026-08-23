# Harvest weight of Pacific white shrimp fed a fermented soy by-product supplement

Trial biologist's report, grow-out season 2026.

## Design

Ten earthen grow-out ponds on the farm were stocked with Pacific white shrimp postlarvae on the
same day at the same stocking density. Five ponds were fed the farm's standard commercial
grow-out diet. The other five were fed that same diet with a fermented soy by-product added.
Feeding ran for the whole grow-out.

At harvest, 30 shrimp were dip-netted at random from each pond and weighed individually on the
farm's bench scale, to one decimal place in grams. That gives 300 weighed shrimp in total, 150 per
diet.

## Data description

The trial data are in one plain text file, `harvest_weights.csv`, with a header row and 300 data
rows. **One row is one individual shrimp that was weighed at harvest.** The file has four columns:

| Column | What it holds |
|---|---|
| `pond_id` | The earthen pond the shrimp was harvested from. Text, values `P01` through `P10`. |
| `feed_treatment` | The diet that pond was fed. Text, either `standard` or `supplemented`. |
| `shrimp_id` | Identifier of the individual shrimp, the pond id plus a within-pond number, e.g. `P03-S17`. Unique across the file. |
| `body_weight_g` | Whole body weight of that shrimp at harvest, in grams, to one decimal place. |

Weights in the file run from 9.2 g to 29.2 g, which is the normal spread we see on this farm at
harvest size.

## Method

The analysis script `analysis.py` reads the committed CSV and compares harvest body weight between
the two diets with a standard independent two-sample t-test. Every weighed shrimp in the table
enters the test as one observation, so the sample size is 150 shrimp in the standard group and 150
shrimp in the supplemented group. Group means and standard deviations are reported alongside the
test.

## Result

| Feed treatment | n (shrimp) | Mean harvest weight | SD |
|---|---|---|---|
| `standard` | 150 | 18.53 g | 3.36 g |
| `supplemented` | 150 | 20.60 g | 3.38 g |

Shrimp on the supplemented diet were 2.07 g heavier on average than shrimp on the standard diet.
The independent two-sample t-test gives **t = 5.32 on 298 degrees of freedom, p = 2.0 x 10^-7**.

## Interpretation

The supplemented diet produced heavier shrimp at harvest. Average individual weight rose from
18.53 g to 20.60 g, a gain of 2.07 g, or about 11 percent over the standard diet, and the
difference is highly significant at p = 2.0 x 10^-7. The two diets gave nearly identical spread in
individual weight (SD 3.36 g versus 3.38 g), so the supplement shifted the whole size distribution
upward rather than only lifting the largest animals or stretching the size grade. For the farm,
11 percent more weight per animal at the same stocking density and the same grow-out period is a
meaningful gain in yield per pond, and it comes from an inexpensive by-product added to a diet the
farm already buys. On the strength of these results I recommend the fermented soy by-product be
carried into the next grow-out cycle, with feed cost per kilogram harvested tracked so the weight
gain can be weighed against the added feed cost.
