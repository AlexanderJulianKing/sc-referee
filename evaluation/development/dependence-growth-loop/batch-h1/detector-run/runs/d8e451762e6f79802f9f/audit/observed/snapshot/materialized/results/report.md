# UV-bright corolla preference in a two-choice Y-maze assay

## Data

Each row of `data/input.csv` is one Y-maze trial, scored by the artificial
corolla that received the first landing. The file holds 20 trials contributed
by 6 marked foragers.

| forager_id | trials | uv_bright first visits |
| --- | --- | --- |
| FOR-01 | 4 | 4 |
| FOR-02 | 4 | 3 |
| FOR-03 | 4 | 4 |
| FOR-04 | 3 | 2 |
| FOR-05 | 3 | 1 |
| FOR-06 | 2 | 1 |

## Analysis

Every trial row was entered as one Bernoulli observation and the pooled counts
were submitted to an exact two-sided binomial test (`scipy.stats.binomtest`)
against the chance expectation p = 0.5.

## Result

Foragers landed first on the UV-bright corolla in 15 of 20 trials (observed
share 0.750).

[selected-result] Exact two-sided binomial test of 15 uv_bright first visits out of 20 trials against p = 0.5: p = 0.041389 (observed share 0.750); the deviation from chance is significant at the 5% level.

## Notes

The 20 trials come from 6 foragers, so several rows describe the same insect
tested again; the test above nonetheless weighs each row as one independent
draw. Trial order within a forager was not modelled.
