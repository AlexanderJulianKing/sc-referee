# Infiltration gain in compost-amended rain gardens

## Data

Source table: `data/input.csv`

The file holds 60 infiltrometer survey sessions recorded at 16 rain gardens, with 3 to 4 sessions per garden (mean 3.75). Each session pairs one measurement in the compost-amended cell with one measurement in the untreated reference cell of the same garden; the session gain is amended minus reference, in mm/h.

Sessions repeated at the same garden are not independent of one another, so the session gains are averaged within each garden before testing. The reported test therefore uses 16 garden means, one analysed value per independent garden.

## Per-garden means

| garden_id | sessions | mean gain (mm/h) |
| --- | --- | --- |
| RG-01 | 4 | 3.80 |
| RG-02 | 4 | 5.20 |
| RG-03 | 4 | 1.90 |
| RG-04 | 3 | 6.10 |
| RG-05 | 4 | 4.40 |
| RG-06 | 3 | 2.70 |
| RG-07 | 4 | 5.50 |
| RG-08 | 4 | 1.20 |
| RG-09 | 4 | 4.80 |
| RG-10 | 3 | 3.30 |
| RG-11 | 4 | 7.00 |
| RG-12 | 4 | -0.60 |
| RG-13 | 4 | 4.10 |
| RG-14 | 3 | 5.80 |
| RG-15 | 4 | 2.40 |
| RG-16 | 4 | 3.60 |

## Test

Two-sided one-sample t-test of the 16 garden mean gains against a null gain of 0.0 mm/h.

- Mean garden gain: 3.825 mm/h
- SD across gardens: 1.983 mm/h
- Standard error of the mean: 0.496 mm/h
- 95% confidence interval: 2.768 to 4.882 mm/h
- t(15) = 7.714, p < 0.0001

[selected-result] Compost-amended cells infiltrated faster than their paired reference cells by 3.825 mm/h on average (95% CI 2.768 to 4.882 mm/h; two-sided one-sample t-test on 16 garden means, t(15) = 7.714, p < 0.0001).

## Reading note

The 60 rows are repeated visits rather than 60 independent gardens. The sample size for the reported test is 16 gardens, which fixes the degrees of freedom at 15.
