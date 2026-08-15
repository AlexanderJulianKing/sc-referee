# Right-arm bias at a darkened T-junction

## Data

The file `data/input.csv` records 36 T-junction trials from 6 whip spiders,
6 trials per animal. Each row is one trial and stores the arm the animal
entered and its latency to the choice point in seconds.

## Analysis

Every trial in the file was treated as one Bernoulli observation. The pooled
count of right-arm entries was compared against a chance rate of 0.5 with an
exact two-sided binomial test (scipy.stats.binomtest).

## Per-animal tallies

| animal_id | trials | right-arm entries | share |
| --- | --- | --- | --- |
| AMB-01 | 6 | 6 | 1.000 |
| AMB-02 | 6 | 5 | 0.833 |
| AMB-03 | 6 | 5 | 0.833 |
| AMB-04 | 6 | 4 | 0.667 |
| AMB-05 | 6 | 3 | 0.500 |
| AMB-06 | 6 | 2 | 0.333 |

## Result

Right-arm entries: 25 of 36 trials (pooled share 0.694).
Exact two-sided binomial test against 0.5: p = 0.0288.
Mean latency to the choice point: 41.9 s.

[selected-result] Exact two-sided binomial test on 36 pooled trials with 25 right-arm entries against a chance rate of 0.5 gives p = 0.0288 (pooled share 0.694), a departure from chance at the 0.05 level.

## Notes

The 36 trials come from 6 animals, 6 trials each, and the
per-animal shares span 0.333 to 1.000. Each trial contributes
one observation to the test above.
