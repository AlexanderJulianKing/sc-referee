# Leaf critical temperature in two coffee cultivars

## Data

Each row of `data/input.csv` is one leaf sampled for a chlorophyll-fluorescence
temperature ramp; `tcrit_c` is the critical temperature (C) at which the rapid
rise in basal fluorescence begins. The file contains 48 leaf measurements
collected from field-grown shrubs of the cultivars Catuai and Obata.

## Analysis

Every leaf measurement in the file was entered as a single observation, and the
two cultivars were compared with Welch's two-sample t-test (unequal variances,
two-sided) on `tcrit_c`.

## Group summaries

| cultivar | leaf measurements | shrubs sampled | mean tcrit_c (C) | SD (C) |
| --- | --- | --- | --- | --- |
| Catuai | 24 | 6 | 48.000 | 0.862 |
| Obata | 24 | 6 | 46.500 | 1.059 |

## Result

[selected-result] Welch two-sample t-test on 48 leaf measurements: t = 5.382, df = 44.17, two-sided p < 0.0001; mean tcrit_c is 1.500 C higher in Catuai (48.000 C, n = 24) than in Obata (46.500 C, n = 24).

The test statistic above spends one degree of freedom per leaf measurement, so
the reported df of 44.17 comes from the 48 rows in the file.
