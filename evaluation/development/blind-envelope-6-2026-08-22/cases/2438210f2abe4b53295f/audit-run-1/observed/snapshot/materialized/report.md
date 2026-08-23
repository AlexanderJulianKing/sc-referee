# Added dietary calcium and snail live weight

## Aim

To find out whether feed with added calcium carbonate changes the live weight of growing
edible garden snails after twelve weeks, compared with the standard feed.

## Enclosure design

Fourteen outdoor mesh enclosures were stocked at equal density. Seven enclosures were given
the standard feed and seven were given the same feed with added calcium carbonate. Feed was
assigned to the enclosure: every snail in a pen ate the same feed, and no snail was assigned
to a feed on its own.

After twelve weeks, twenty snails were collected from each enclosure and weighed
individually, along with their greatest shell diameter. That gives 14 x 20 = 280 weighed
snails in `snail_weights.csv`.

## The aggregation step, and why the enclosure is the unit of replication

The feed was applied to a pen, not to a snail. Everything a pen does to its snails, such as
its patch of shade, its damp corners, or how the food ended up spread around, is shared by
all twenty snails inside it. So the twenty rows from one enclosure are twenty repeated
measurements of one treated unit, not twenty independent replicates of the feed. Treating
them as independent would count the same pen twenty times over and make the study look far
more precise than it is. The study has 14 independent units, 7 per feed group.

`analysis.py` therefore keeps the aggregation in its own step, `aggregate_to_enclosures`.
That step is separate from `load_snail_rows`, which only reads the CSV, and separate from
`compare_groups`, which only runs the test. It collapses the 280 snail rows into one row per
enclosure and hands back a table of 14 rows holding, for each enclosure, its identifier, its
feed group, its mean live weight, and how many snails it contributed. Every enclosure
contributed 20 snails.

The test function receives that aggregated 14-row table and nothing else. No inferential
test is run on the individual snail rows anywhere in the script.

## Method

The comparison is an independent two-sample t-test (Welch's version, which does not assume
the two groups share the same variance) on the enclosure mean live weights. The two samples
are the 7 standard-feed enclosures and the 7 added-calcium enclosures. The sample size is
14 enclosures, 7 per group. A 95% confidence interval for the difference in group means is
reported alongside the test.

## Results

Aggregated enclosure table produced by the aggregation step (mean live weight in grams,
rounded to 3 decimal places):

| enclosure_ref | calcium_level | mean_live_weight_g | n_snails |
| --- | --- | --- | --- |
| ENC-01 | standard | 8.997 | 20 |
| ENC-02 | added_calcium | 9.052 | 20 |
| ENC-03 | standard | 8.517 | 20 |
| ENC-04 | added_calcium | 11.817 | 20 |
| ENC-05 | standard | 7.334 | 20 |
| ENC-06 | added_calcium | 10.598 | 20 |
| ENC-07 | standard | 10.761 | 20 |
| ENC-08 | added_calcium | 9.896 | 20 |
| ENC-09 | standard | 9.096 | 20 |
| ENC-10 | added_calcium | 11.312 | 20 |
| ENC-11 | standard | 10.744 | 20 |
| ENC-12 | added_calcium | 10.658 | 20 |
| ENC-13 | standard | 11.532 | 20 |
| ENC-14 | added_calcium | 11.256 | 20 |

Two-group comparison on those 14 enclosure means:

| Quantity | Value |
| --- | --- |
| Sample size | 14 enclosures (7 standard, 7 added calcium) |
| Standard feed | mean 9.569 g, SD 1.489 g |
| Added calcium | mean 10.656 g, SD 0.939 g |
| Difference (added calcium - standard) | 1.087 g |
| 95% confidence interval for the difference | -0.394 g to 2.567 g |
| Test statistic | t = 1.633, df = 10.12 |
| p-value | 0.133 |

Enclosure means ranged from 7.334 g (ENC-05, standard) to 11.817 g (ENC-04, added calcium).
Pens within the same feed group differ a lot from each other, which is the between-enclosure
variation that the enclosure-level analysis correctly carries into the test.

## Conclusion

The enclosures on added calcium carbonate averaged 1.087 g heavier than the enclosures on
standard feed. With 7 enclosures per group, that difference is not statistically significant
(Welch's t-test on enclosure means, t = 1.633, df = 10.12, p = 0.133), and the 95%
confidence interval runs from -0.394 g to 2.567 g. The interval includes zero, so this study
does not establish that the calcium supplement raises live weight.

It also does not rule out a worthwhile benefit. The interval is wide, and most of it sits
above zero, so an increase of around 2.5 g remains as consistent with these data as no
change at all. Pens varied enough among themselves that 7 per group cannot separate a
moderate feed effect from ordinary pen-to-pen differences. Weighing more snails per pen
would not fix this, because the sample size that matters is the number of enclosures. A
farm that wants a decision on this supplement should run the trial again with more
enclosures per feed group.

## Data description

### Files

| File | Level | Rows (excluding header) |
| --- | --- | --- |
| `snail_weights.csv` | one weighed snail | 280 |

There is no stored per-enclosure file. The 14-row enclosure table is produced inside
`analysis.py` by the aggregation step.

### What one row represents

One row is one individual snail, weighed once at the end of the twelve-week feeding period.
Each snail belongs to exactly one enclosure, and each enclosure belongs to exactly one feed
group. Every weighed snail is kept as its own row; nothing is averaged or de-duplicated in
the file. The 20 rows that share an `enclosure_ref` are repeated measurements from the same
pen, not 20 independent replicates of the feed.

### Columns of `snail_weights.csv`

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `enclosure_ref` | text | none | Identifier of the outdoor mesh enclosure the snail came from, `ENC-01` to `ENC-14`. Exactly 20 rows carry each value. This is the level at which feed was assigned, and the unit of replication for the analysis. |
| `calcium_level` | text | none | Feed group of the enclosure: `standard` (standard feed) or `added_calcium` (standard feed plus calcium carbonate). Constant within an enclosure. `ENC-01, 03, 05, 07, 09, 11, 13` are `standard`; `ENC-02, 04, 06, 08, 10, 12, 14` are `added_calcium`. |
| `snail_no` | integer | none | Sequence number of the snail within its enclosure, 1 to 20. A within-enclosure label only, not a farm-wide snail ID; the same number appears once in every enclosure. |
| `live_weight_g` | number | grams (g) | Live weight of the individual snail at the end of week twelve, rounded to 2 decimal places. Observed range in this file: 3.56 to 16.36 g. This is the response variable. |
| `shell_diameter_mm` | number | millimetres (mm) | Greatest shell diameter of the same snail, rounded to 1 decimal place, recorded in the same session as the weight. It tracks live weight, so heavier snails have wider shells. Recorded only within the measurable range 26.0 to 38.0 mm; 5 of the 280 snails fell outside that range and are recorded at the nearest limit (3 at 26.0 mm, 2 at 38.0 mm). It is not used in the two-group comparison. |

### Completeness

All 280 rows have all five fields populated. There are no missing values, no blank cells,
and no duplicate `enclosure_ref` + `snail_no` pairs. All 14 enclosures contributed exactly
20 snails.
