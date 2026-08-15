# Bedrock lithology and downslope creep of alpine rock glaciers

## Design

Each row of `data/input.csv` is one rock glacier, surveyed once. No landform
contributes more than one row, so the 25 velocity values are 25 independent
observations.

## Groups

| bedrock_class | n | mean creep (cm/yr) | SD (cm/yr) |
| --- | --- | --- | --- |
| micaschist | 12 | 24.00 | 5.63 |
| orthogneiss | 13 | 16.00 | 4.01 |

## Test

Welch's two-sample t-test (unequal variances, two-sided) on
creep_velocity_cm_yr by bedrock_class.

Difference in means (micaschist - orthogneiss): 8.00 cm/yr
t = 4.06, Welch-Satterthwaite df = 19.8, p < 0.001
Cohen's d (pooled SD) = 1.65

[selected-result] Welch two-sided t-test: micaschist-hosted rock glaciers creep 8.00 cm/yr faster than orthogneiss-hosted ones (24.00 vs 16.00 cm/yr; t = 4.06, df = 19.8, p < 0.001, Cohen's d = 1.65), one row per landform.
