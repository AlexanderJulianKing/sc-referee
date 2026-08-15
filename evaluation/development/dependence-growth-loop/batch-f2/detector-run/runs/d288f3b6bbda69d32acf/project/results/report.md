# Net photosynthesis of mangrove seedlings under two salinity regimes

## Data

Input: data/input.csv, 96 leaf-level rows.
Response: anet_umol_m2_s, net CO2 assimilation in umol CO2 m^-2 s^-1.
Design: 12 Avicennia marina seedlings, 8 gas-exchange readings per seedling;
6 seedlings at 15 ppt (ambient_15ppt) and 6 at 35 ppt (elevated_35ppt).

## Group summaries

| salinity_regime | rows | mean | SD |
| --- | ---: | ---: | ---: |
| ambient_15ppt | 48 | 12.700 | 0.816 |
| elevated_35ppt | 48 | 11.700 | 0.818 |

Difference of means (ambient_15ppt - elevated_35ppt): 1.000 umol CO2 m^-2 s^-1.

## Test

Two-sided two-sample Student t-test with pooled variance
(scipy.stats.ttest_ind, equal_var=True). Each row of data/input.csv supplies
one observation, giving 48 observations per regime and 94 degrees of freedom.

[selected-result] Two-sample pooled t-test of anet_umol_m2_s by salinity_regime: t(94) = 5.99, p < 0.0001; ambient_15ppt mean 12.700 vs elevated_35ppt mean 11.700, difference 1.000 umol CO2 m^-2 s^-1.

## Interpretation

Assimilation averages 1.000 umol CO2 m^-2 s^-1 higher under ambient than under
elevated salinity; the pooled t-test rejects equality of the two regime means
at the conventional 5 percent level.
