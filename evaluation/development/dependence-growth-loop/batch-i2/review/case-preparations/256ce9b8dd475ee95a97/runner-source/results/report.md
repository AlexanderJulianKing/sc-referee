# Natal-tube homing accuracy in tagged Osmia females

## Data

- Source table: `data/input.csv`
- Provisioning trips scored: 24
- Tagged females contributing trips: 8
- Trips ending in the natal tube: 18
- Pooled accuracy: 0.750

## Procedure

Every provisioning trip in the table was treated as one Bernoulli trial, scored
1 when the female re-entered her own tube and 0 when she entered a different
tube. The 24 trips were pooled into a single count and compared with the chance
expectation of 0.500 using an exact two-sided binomial test
(`scipy.stats.binomtest`, alternative "two-sided").

## Result

[selected-result] Exact two-sided binomial test of 18 natal-tube returns in 24 pooled trips against p0 = 0.500: accuracy = 0.750, p = 0.022656, significant at alpha = 0.05.

## Per-female tallies

| bee_tag | trips | natal returns | accuracy |
| --- | --- | --- | --- |
| B-01 | 4 | 3 | 0.750 |
| B-02 | 3 | 3 | 1.000 |
| B-03 | 3 | 1 | 0.333 |
| B-04 | 4 | 4 | 1.000 |
| B-05 | 2 | 2 | 1.000 |
| B-06 | 3 | 3 | 1.000 |
| B-07 | 3 | 0 | 0.000 |
| B-08 | 2 | 2 | 1.000 |

Trip counts per female range from 2 to 4.
