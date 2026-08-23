# Archerfish two-choice shooting assay: pooled hit-rate test

## Data

Input file: `data/input.csv`
Rows read: 20
Fish tags present: 5

| fish_tag | trials | hits |
| --- | --- | --- |
| AR-11 | 4 | 4 |
| AR-14 | 4 | 4 |
| AR-22 | 4 | 3 |
| AR-27 | 4 | 3 |
| AR-31 | 4 | 1 |

## Analysis

Each row of the input file is one two-choice shooting trial, scored 1 when the
fish knocked down the rewarded target and 0 otherwise. All 20 rows were pooled
into a single sequence and entered into an exact two-sided binomial test, one
observation per row, of the null hypothesis that the hit probability of a trial
equals 0.500 (scipy.stats.binomtest, alternative "two-sided"). No grouping or
weighting of rows was applied before the test.

## Result

Hits: 15 of 20
Observed hit rate: 0.750
Exact two-sided binomial p-value: 0.0414

[selected-result] Pooling all 20 trials as independent observations, the fish hit the rewarded target in 15 of 20 trials (hit rate 0.750); an exact two-sided binomial test against a chance rate of 0.500 gives p = 0.0414, so chance performance is rejected at the 0.05 level.
