# Nitrate removal under two external carbon sources

## Data

- Source file: `data/input.csv`
- Measurement rows analysed: 60
- Bioreactors: 10 (5 on methanol, 5 on glycerol)
- Sampling occasions per bioreactor: 6 (run days 7, 14, 21, 28, 35, 42)

| carbon source | rows | mean removal (mg N/L/h) | sd |
| --- | --- | --- | --- |
| methanol | 30 | 3.270 | 0.241 |
| glycerol | 30 | 4.050 | 0.178 |

## Analysis

Each sampling-day measurement in the file was entered as one observation,
and the two carbon-source groups were compared with Welch's two-sample
t test (`scipy.stats.ttest_ind`, `equal_var=False`), two-sided.

## Result

- Mean difference (glycerol minus methanol): 0.780 mg N/L/h
- Welch t = 14.26 on 53.3 degrees of freedom
- p < 1e-12

[selected-result] Welch two-sample t test on the 60 measurement rows: mean nitrate removal is 4.050 mg N/L/h with glycerol versus 3.270 mg N/L/h with methanol, a difference of 0.780 mg N/L/h (t = 14.26, df = 53.3, p < 1e-12); the difference is significant at alpha = 0.05.
