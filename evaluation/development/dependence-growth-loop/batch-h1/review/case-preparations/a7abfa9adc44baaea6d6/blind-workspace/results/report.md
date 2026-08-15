# Chloride exceedance and shoreline zone, Wrack Bay monitoring network

## Data

Source table: data/input.csv (120 sample rows from 30 monitoring wells, 4 visits each).
A sample counts as an exceedance when chloride is at or above 250.0 mg/L.

| Shoreline zone | Samples | Exceedances | Exceedance rate |
| --- | ---: | ---: | ---: |
| Dune ridge | 40 | 10 | 0.250 |
| Back barrier | 40 | 20 | 0.500 |
| Tidal flat | 40 | 30 | 0.750 |

## Analysis

Pearson chi-squared test of independence (scipy.stats.chi2_contingency) applied
to the 3 x 2 table of shoreline zone by exceedance status, with each sample row
entered as one observation.

- chi-squared statistic: 20.0000
- degrees of freedom: 2
- p-value: 4.540e-05
- Cramer's V: 0.408

## Result

[selected-result] Exceedance status is associated with shoreline zone: Pearson chi-squared test of independence on 120 sample rows gives chi-squared = 20.0000, df = 2, p = 4.540e-05 (Cramer's V = 0.408), with the exceedance rate rising from 0.250 on the dune ridge to 0.500 on the back barrier and 0.750 on the tidal flat.
