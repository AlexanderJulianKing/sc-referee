# Diet supplementation and song tempo in hand-raised zebra finches

## Question

Do juvenile male zebra finches raised on a protein-supplemented diet sing
faster motifs than controls once each bird is summarised by a single value?

## Data and unit of analysis

`data/input.csv` is stored in long format: 48 rows, one row per bird per
recording night. Each of the 12 birds contributes 4 nights, so individual
rows are not independent. Diet was assigned to birds rather than to nights,
so the independent unit is the bird (`bird_id`). Every bird is collapsed
to its mean syllable rate across its own nights before any test is run,
leaving 12 analysed values -- 6 supplemented and 6 control -- that is,
exactly one analysed value per independent unit.

## Per-bird summaries

| bird_id | diet_group | nights | mean syllable rate (syl/s) |
| --- | --- | --- | --- |
| ZF-03 | control | 4 | 6.95 |
| ZF-06 | control | 4 | 6.60 |
| ZF-08 | control | 4 | 6.44 |
| ZF-11 | control | 4 | 6.28 |
| ZF-14 | control | 4 | 6.10 |
| ZF-17 | control | 4 | 5.90 |
| ZF-01 | supplemented | 4 | 7.85 |
| ZF-04 | supplemented | 4 | 7.62 |
| ZF-05 | supplemented | 4 | 7.48 |
| ZF-09 | supplemented | 4 | 7.30 |
| ZF-12 | supplemented | 4 | 7.05 |
| ZF-16 | supplemented | 4 | 6.72 |

## Group summaries

| diet_group | birds | mean of bird means | median of bird means |
| --- | --- | --- | --- |
| supplemented | 6 | 7.34 | 7.39 |
| control | 6 | 6.38 | 6.36 |

Median difference (supplemented minus control): 1.03 syl/s.

## Test

Exact two-sided Mann-Whitney U test (scipy.stats.mannwhitneyu with
method="exact") on the 12 bird-level mean syllable rates, supplemented
against control. The bird means contain no ties, so the exact null
distribution applies.

U = 35, p = 0.0043, rank-biserial correlation = 0.944.

[selected-result] Supplemented birds sang faster than controls: exact two-sided Mann-Whitney U test on 12 bird-level mean syllable rates (6 supplemented, 6 control, one value per bird), U = 35, p = 0.0043, rank-biserial correlation = 0.944, median difference 1.03 syl/s.

## Notes

The 48 session rows never enter the test as separate observations; each
bird contributes exactly one value, so the row-independence assumption of
the rank test is met at the level of the analysed units. Session-to-session
spread within a bird is visible in the raw file but is absorbed by the
per-bird mean.
