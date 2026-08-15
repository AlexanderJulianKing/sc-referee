# Littoral shelf restoration and great crested newt eDNA detection

## Design

Each row of `data/input.csv` is one abandoned quarry pond. Every pond was
visited once and contributed exactly one pooled water sample, screened for
great crested newt eDNA. Pond identifiers are unique, so the 24 ponds
supply 24 mutually independent observations with no repeated measures.

## Analysis

Two-sided Fisher exact test on the 2 x 2 table of shelf status by eDNA result.

| Shelf status | Detected | Not detected | Ponds | Detection rate |
| --- | --- | --- | --- | --- |
| restored | 9 | 3 | 12 | 0.750 |
| unrestored | 3 | 9 | 12 | 0.250 |

## Result

- Sample odds ratio: 9.00
- Two-sided exact p-value: 0.0391
- Detection-rate difference (restored minus unrestored): 0.500

[selected-result] A two-sided Fisher exact test on 24 independently surveyed quarry ponds returns p = 0.0391 with a sample odds ratio of 9.00; great crested newt eDNA was detected in 9 of 12 restored-shelf ponds (0.750) against 3 of 12 unrestored ponds (0.250).

## Reading note

Fisher's exact test treats each row as an independent trial. That assumption
matches the sampling frame used here, which allocates one and only one survey
to each pond, so no pond is counted more than once.
