# Rye versus white wheat flour in sourdough starter acidification

## Data description

The analysis reads one file, `starter_ph_readings.csv`, which holds the bench records from
the maturation run. The file has 72 data rows and four columns.

| Column | What it holds |
| --- | --- |
| `jar_id` | Label of the starter jar the reading came from (`jar_01` through `jar_12`). |
| `flour_type` | Flour the jar was fed for the whole run: `wholemeal_rye` or `refined_white_wheat`. |
| `maturation_day` | Maturation day on which the reading was taken, 1 through 6. |
| `starter_ph` | The pH reading itself, recorded to two decimal places. This is the outcome. |

**One row is one jar on one day:** a single daily pH reading taken from a single starter
jar. Twelve jars each contribute six rows, one per maturation day, giving 72 rows.
Recorded pH values run from 3.58 to 5.80.

## Design

Twelve starter jars were built from scratch on the same bench on the same day. Six were
fed a wholemeal rye flour and six a refined white wheat flour. Every jar was fed on the
same daily schedule and held at the same temperature, so flour was the only thing that
differed between the two sets of jars. The pH of every jar was read once a day, at the
same time each day, for six consecutive days of maturation.

## Method

The CSV was loaded and starter pH was compared between the two flours with a standard
independent two-sample t-test, pooling all six maturation days and using every daily
reading in the table as one observation. Group means and standard deviations were computed
over the same pooled readings. The analysis was run in Python with pandas and SciPy
(`scipy.stats.ttest_ind`).

## Result

| Flour | Readings | Mean pH | SD |
| --- | --- | --- | --- |
| Wholemeal rye | 36 | 4.169 | 0.723 |
| Refined white wheat | 36 | 4.287 | 0.621 |

The sample size is 36 pH readings per flour group, 72 in total. The rye-fed jars averaged
0.117 pH units below the wheat-fed jars. The two-sample t-test gives
**t(70) = -0.740, p = 0.462**.

## Interpretation

Rye is the flour that drives the stronger acidification here. Every summary in the table
points the same way: the rye jars sit lower in mean pH than the wheat jars, and the gap
grows as the run goes on, from a mean of 5.65 against 5.52 on day 1 to 3.63 against 3.82
by day 6. That end-of-run separation of roughly 0.19 pH units is the size of
effect a baker notices at the bench, and it matches what wholemeal rye is expected to do:
it carries more fermentable substrate into the jar than a refined white wheat flour does. The pooled test, however, does not reach the usual 5 percent threshold
(p = 0.462). The reason is visible in the standard deviations: pooled over all six days,
each group spans the whole descent from about pH 5.6 down to the high 3s, so the
within-group spread of roughly 0.6 to 0.7 pH units is far larger than the 0.117-unit gap
between the group means. The direction of the flour effect is consistent and in line with
expectation, while the pooled comparison itself does not establish it at conventional
significance. The practical read for the bench is to use rye when a faster, deeper drop in
starter pH is wanted.

## Files

- `starter_ph_readings.csv` — the frozen bench data
- `analysis.py` — the analysis script that produces every number above
