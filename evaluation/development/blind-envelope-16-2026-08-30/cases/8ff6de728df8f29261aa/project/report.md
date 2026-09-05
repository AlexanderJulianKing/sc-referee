# Vacuum versus atmospheric frying of plantain crisps

## Data

`plantain_frying_batches.csv` holds 40 data rows and one header row. One row is one
independently prepared frying batch of plantain crisps, made from its own lot of sliced
green plantain and fried by one of the two methods. Each batch was measured once for each
of the five outcomes, so a row is the complete outcome record for that batch. There are no
missing values.

Columns:

| Column | Units | Meaning |
| --- | --- | --- |
| `batch_id` | none | Per-batch identifier, `b01` to `b40`, in processing run order |
| `frying_method` | none | `vacuum` (120 C under vacuum, 20 batches) or `atmospheric` (170 C at atmospheric pressure, 20 batches) |
| `oil_content_g100g` | g per 100 g product | Oil content of the finished crisps |
| `acrylamide_ug_kg` | ug per kg | Acrylamide content of the finished crisps |
| `breaking_force_n` | N | Maximum breaking force, three-point bend test |
| `colour_b_cielab` | CIELAB units | Colour b* value of the ground crisps |
| `crispness_score_pts` | points, 0 to 10 | Trained panel crispness score |

The five outcome columns appear in the order in which the outcome family was declared in
advance.

## Methods

The two frying methods were compared on each of the five pre-declared outcomes with an
independent two-sample t-test (`scipy.stats.ttest_ind`), one test per outcome, 20 batches
per group. Group means, the t statistic and the p-value are reported for every outcome.

Oil content and acrylamide are the nutritional and safety endpoints and were given a
conservative reading. Their p-values were corrected by hand: each raw p-value was
multiplied by the number of comparisons made (5) and capped at 1, and the verdict for those
two outcomes was taken from the corrected value at the conventional 0.05 threshold.

Breaking force, colour b* and crispness are quality endpoints, each treated as its own
separate pre-declared question, so each raw p-value was compared with the 0.05 threshold
directly.

## Results

| Outcome | Mean, vacuum | Mean, atmospheric | t | Raw p | p used for the verdict | Conclusion |
| --- | --- | --- | --- | --- | --- | --- |
| `oil_content_g100g` | 22.800 | 29.885 | -10.826 | 3.59151e-13 | 1.79576e-12 (corrected by hand) | Difference between methods |
| `acrylamide_ug_kg` | 152.850 | 420.900 | -10.537 | 7.82042e-13 | 3.91021e-12 (corrected by hand) | Difference between methods |
| `breaking_force_n` | 12.445 | 12.340 | 0.192 | 0.848653 | 0.848653 (raw) | No difference detected |
| `colour_b_cielab` | 31.515 | 32.565 | -1.430 | 0.160924 | 0.160924 (raw) | No difference detected |
| `crispness_score_pts` | 7.280 | 6.900 | 1.579 | 0.122656 | 0.122656 (raw) | No difference detected |

The hand correction, shown openly:

- oil content: 3.59151e-13 x 5 = 1.79576e-12, below the cap of 1, so the corrected p-value
  is 1.79576e-12.
- acrylamide: 7.82042e-13 x 5 = 3.91021e-12, below the cap of 1, so the corrected p-value
  is 3.91021e-12.

Both corrected p-values stay far under 0.05, so the conservative reading of the two
safety-related endpoints does not change their verdicts.

The three quality outcomes were read from their raw p-values and none reached the 0.05
threshold.

## Interpretation for a snack manufacturer

Vacuum frying at 120 C cut oil content from 29.9 to 22.8 g per 100 g, a drop of about 7.1 g
per 100 g, or roughly a quarter of the oil in the atmospheric product. It also cut
acrylamide from 421 to 153 ug per kg, a drop of about 268 ug per kg, roughly a two-thirds
reduction. Both differences survive the conservative hand-corrected reading, and both are
large enough to matter on a nutrition panel and in a contaminant specification.

The product quality endpoints did not separate. Mean breaking force differed by 0.1 N, mean
colour b* by 1.05 CIELAB units, and mean panel crispness by 0.4 points, and no quality
p-value fell below 0.05 in this 20-batch-per-group trial. On this evidence a switch to
vacuum frying buys a substantially leaner and lower-acrylamide crisp without a measured
penalty in texture, colour or sensory crispness.
