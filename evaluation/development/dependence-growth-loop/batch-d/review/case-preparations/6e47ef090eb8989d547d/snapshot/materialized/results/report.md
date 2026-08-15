# Leaf-level carbon assimilation in two quinoa cultivars

## Data

Source table: `data/input.csv` (48 measurement rows).

Measured variable: net CO2 assimilation rate (assimilation_umol_m2_s), recorded on
individually tagged leaves of greenhouse-grown quinoa plants.

| Cultivar | Rows | Mean | SD |
| --- | ---: | ---: | ---: |
| Pasankalla | 24 | 18.000 | 1.732 |
| Titicaca | 24 | 21.000 | 1.732 |

## Analysis

Each measured leaf was entered as one observation and the two cultivar groups were
compared with Welch's two-sample t-test (scipy.stats.ttest_ind, equal_var=False),
two-sided, alpha = 0.05.

## Result

Mean difference (Titicaca minus Pasankalla): 3.000 umol m-2 s-1
t = 6.000, df = 46.0, p < 0.0001

[selected-result] Welch's two-sample t-test over 48 leaf observations gives t = 6.000, df = 46.0, p < 0.0001: mean net assimilation is higher in Titicaca (21.000) than in Pasankalla (18.000) umol m-2 s-1.
