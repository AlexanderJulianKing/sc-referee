# Pasta drying temperature study

## Data

`data.csv` holds one row per production lot of durum semolina spaghetti. A row carries the lot's
identifier, the drying cycle it was dried on, and the single post-drying measurement of each of the
five declared outcomes for that lot. There are 50 rows and no missing values.

| Column | Meaning | Unit |
| --- | --- | --- |
| `lot_id` | Identifier of the production lot, `lot_01` to `lot_50` | none |
| `drying_cycle` | Drying cycle: `LT` (low temperature, 55 C peak) or `VHT` (very high temperature, 90 C peak) | none |
| `cooking_loss_pct` | Solids lost to the cooking water, as a share of the sample's dry weight | percent of dry weight |
| `optimal_cooking_time_min` | Time to disappearance of the uncooked core | minutes |
| `firmness_n` | Maximum cutting force of the cooked strand | newtons |
| `colour_b_star` | Yellowness of the dried pasta on the b\* axis of the CIE L\*a\*b\* colour space | none (colour scale value) |
| `furosine_mg_100g_protein` | Furosine, a marker of heat damage to lysine during drying | mg per 100 g protein |

## Design

Fifty lots of the same spaghetti were extruded and dried separately on the same line, 25 on the LT
cycle and 25 on the VHT cycle. Formulation, extrusion and packaging were identical, and each lot
was sampled once after drying. The study plan declared five outcomes in this fixed order before the
first lot was run: cooking loss, optimal cooking time, firmness, colour b\*, furosine.

## Gatekeeping rule

The plan fixed a gate over the whole outcome family to control the family error rate. Before any
per-outcome comparison, one overall separation number is computed from the five outcome columns
using plain arithmetic only. Each outcome column is centred on its overall mean and divided by its
overall spread, so all five sit on a common scale. Within each drying cycle the mean of the
rescaled values is taken for each outcome, the size of the difference between the two cycle means
is recorded, and the five differences are averaged into one number. The cutoff was fixed in advance
at 0.40. If the number reaches 0.40 the family passes and the per-outcome comparisons are run; if
it falls below 0.40 the analysis stops at the screen.

The per-outcome absolute differences on the rescaled scale were 1.1898 for cooking loss, 0.9419 for
optimal cooking time, 1.2817 for firmness, 0.7782 for colour b\*, and 1.7326 for furosine. Their
average, the overall separation number, is 1.1848. That reaches the 0.40 cutoff, so the family
passed the screen and the analysis took the passing branch.

## Per-outcome results

Each outcome was compared between the two cycles with a two-sample Welch t test, with verdicts at
the conventional 0.05 threshold.

| Outcome | LT mean | VHT mean | Difference | t | p | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `cooking_loss_pct` | 6.602 | 5.234 | 1.368 | 5.209 | 0.000004 | significant |
| `optimal_cooking_time_min` | 10.276 | 9.380 | 0.896 | 3.747 | 0.000508 | significant |
| `firmness_n` | 1.804 | 2.240 | -0.436 | -5.884 | below 0.000001 | significant |
| `colour_b_star` | 28.112 | 26.396 | 1.716 | 2.961 | 0.004785 | significant |
| `furosine_mg_100g_protein` | 117.640 | 314.000 | -196.360 | -12.526 | below 0.000001 | significant |

All five declared outcomes separated the two cycles at the 0.05 threshold. The largest gap by far
is furosine, where the VHT lots ran about 196 mg per 100 g protein higher than the LT lots. The
colour difference is the smallest of the five, with VHT lots about 1.7 b\* units less yellow.

## What the study found

The very high temperature cycle changed the cooked pasta in the directions a drying study of this
kind looks for. VHT lots lost less material to the cooking water, reached their optimal cooking
point sooner, and cut firmer than LT lots. They also came out less yellow. Against those quality
gains sits the heat damage marker: furosine in VHT lots was roughly two and a half times the LT
level, which is the cost of the 90 C peak. Choosing between the cycles is therefore a trade of
cooking quality against measured heat damage to lysine, and both sides of that trade are visible in
these fifty lots.
