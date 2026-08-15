# Canopy shading and Daphnia persistence in outdoor mesocosms

## Design

Each of the 24 outdoor mesocosm ponds was stocked once with a founder
Daphnia pulex population, assigned to one canopy treatment, and scored once
at the end of the season as either persisted or collapsed. The pond is both
the unit of assignment and the unit of analysis: every pond_id value appears
in exactly one row, so no pond contributes more than a single outcome to the
table below.

## Counts

| canopy | persisted | collapsed | ponds | persistence rate |
| --- | --- | --- | --- | --- |
| shaded | 9 | 3 | 12 | 75.0% |
| open | 3 | 9 | 12 | 25.0% |

## Test

Two-sided Fisher exact test on the 2x2 table of independent ponds, one trial
per pond.

- sample odds ratio: 9.000
- two-sided p-value: 0.039126
- difference in persistence rate (shaded - open): 0.500

[selected-result] Two-sided Fisher exact test on 24 independent mesocosm ponds: shaded ponds persisted in 9 of 12 cases versus 3 of 12 open ponds (sample odds ratio 9.000, p = 0.039126), so canopy shading is associated with higher persistence at the 5% level.

## Reading the result

The exact p-value is the sum of hypergeometric probabilities no larger than
that of the observed table under fixed row and column margins. Each pond
enters the table once, so the fixed margins refer to independent ponds and no
within-pond replication inflates the counts. Volume, stocking density and
mean surface temperature were recorded but not used as strata, so the
association is unadjusted, and with 24 ponds in total the odds ratio is
imprecise.
