# Thermal stress and particle clearance in the duck mussel Anodonta anatina

## Design and data

`data/input.csv` stores one row per clearance run: 72 runs recorded from 12 individually
tagged mussels, each held in its own flow-through chamber. Every animal contributed three
runs during the pre-exposure baseline (days 0-4) and three more after a 10-day warming
exposure (days 16-20). Runs from the same animal are repeated measurements of one
individual, so the 72 rows are not 72 independent observations.

## Analysis

Clearance rates were averaged within animal and phase, which leaves one pre-exposure mean
and one post-exposure mean per mussel and therefore exactly one analysed row per
independent unit (`mussel_id`). The 12 within-animal changes (post minus pre) were tested
against zero with a two-sided paired t-test (`scipy.stats.ttest_rel`); the 95% interval
uses the Student t quantile on 11 degrees of freedom.

## Per-animal clearance means (L/h)

| mussel_id | runs | pre-exposure | post-exposure | change |
| --- | ---: | ---: | ---: | ---: |
| MU-01 | 6 | 3.400 | 2.500 | -0.900 |
| MU-02 | 6 | 2.900 | 2.200 | -0.700 |
| MU-03 | 6 | 4.100 | 2.900 | -1.200 |
| MU-04 | 6 | 3.600 | 2.800 | -0.800 |
| MU-05 | 6 | 3.000 | 2.000 | -1.000 |
| MU-06 | 6 | 2.700 | 2.100 | -0.600 |
| MU-07 | 6 | 3.800 | 2.700 | -1.100 |
| MU-08 | 6 | 3.300 | 2.400 | -0.900 |
| MU-09 | 6 | 4.400 | 3.100 | -1.300 |
| MU-10 | 6 | 3.100 | 2.300 | -0.800 |
| MU-11 | 6 | 3.500 | 2.500 | -1.000 |
| MU-12 | 6 | 2.800 | 2.100 | -0.700 |

## Result

- Independent units analysed: 12 mussels (72 clearance runs collapsed to 12 paired rows)
- Mean pre-exposure clearance: 3.383 L/h
- Mean post-exposure clearance: 2.467 L/h
- Mean within-animal change: -0.917 L/h (SD 0.212, 95% CI -1.052 to -0.782)
- Paired t-test: t(11) = -14.944, p < 0.0001

[selected-result] Particle clearance fell after the 10-day warming exposure: mean within-animal change -0.917 L/h (95% CI -1.052 to -0.782), two-sided paired t(11) = -14.944, p < 0.0001, n = 12 mussels.

## Note on the unit of analysis

The test statistic rests on 12 numbers, one per mussel. Individual clearance runs enter
only through those per-animal means, so no animal contributes more than one row to the
comparison.
