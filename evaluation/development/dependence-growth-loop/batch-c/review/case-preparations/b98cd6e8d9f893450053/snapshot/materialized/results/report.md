# Sourdough acidification: rye versus wheat starter builds

## Data

`data/input.csv` holds 32 pH readings taken 36 hours after the final build.
Each vessel was sampled at four separate points in the dough, and every
reading enters the comparison as one observation.

| Flour | Vessels | Readings | Mean pH | Median pH |
| --- | ---: | ---: | ---: | ---: |
| rye | 4 | 16 | 3.689 | 3.6850 |
| wheat | 4 | 16 | 3.941 | 3.9450 |

Median difference (wheat minus rye): 0.260 pH units.

## Analysis

A two-sided Mann-Whitney U test with the exact null distribution over the
601080390 equally likely rank assignments compares the 16 rye readings with the
16 wheat readings.

## Result

[selected-result] Mann-Whitney U = 0.0 for rye versus wheat (16 vs 16 readings), two-sided exact p = 3.327e-09.

No rye reading exceeds any wheat reading, so U sits at the boundary of its
exact null distribution and the p-value is the smallest the test can return
at these sample sizes.
