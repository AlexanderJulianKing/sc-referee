# Metabolic rate of Baetis nymphs across two elevation bands

## Data

Source: data/input.csv, 12 rows. Each row is one closed-chamber
respirometry run. 6 nymphs were collected and each was run twice on
consecutive mornings.

| elevation band | runs | nymphs | mean rate (uL O2 per h per mg) |
| --- | --- | --- | --- |
| lowland | 6 | 3 | 41.60 |
| highland | 6 | 3 | 45.40 |

## Analysis

All 12 runs were entered as individual observations in a two-sample
Student t-test (equal variances assumed, scipy.stats.ttest_ind) comparing
highland runs with lowland runs. Pooled standard deviation 2.517 uL O2 per h per mg
on 10 degrees of freedom.

## Result

Mean difference (highland minus lowland): 3.80 uL O2 per h per mg.
t(10) = 2.6152, two-sided p = 0.0258.

[selected-result] Two-sample Student t-test on 12 respirometry runs: highland nymphs have a higher mass-specific metabolic rate than lowland nymphs by 3.80 uL O2 per h per mg (t(10) = 2.6152, two-sided p = 0.0258).
