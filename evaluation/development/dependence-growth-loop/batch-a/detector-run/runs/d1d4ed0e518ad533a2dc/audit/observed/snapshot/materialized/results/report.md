# Free chlorine residual by reservoir liner type

## Data

Twelve municipal service reservoirs in the North Ridge distribution zone were
sampled during a single spring flushing window. Six carry an epoxy liner and
six carry a cement-mortar liner. Each reservoir was tapped at four fixed port
depths (1.5, 3.0, 4.5 and 6.0 m), giving 48 free chlorine readings in
`data/input.csv`.

## Analysis

Each reading was entered as one observation and the two liner groups were
compared with a two-sided Welch two-sample t-test (unequal variances).

| liner | samples | mean free chlorine (mg/L) | SD (mg/L) |
| --- | ---: | ---: | ---: |
| epoxy | 24 | 0.850 | 0.112 |
| cement-mortar | 24 | 0.650 | 0.111 |

Mean difference (epoxy minus cement-mortar): 0.200 mg/L

Welch t = 6.226, df = 46.0, p < 0.001

## Result

[selected-result] Epoxy-lined reservoirs carried 0.200 mg/L more free chlorine than cement-mortar-lined reservoirs (two-sided Welch two-sample t-test over 48 readings, 24 per liner: t = 6.226, df = 46.0, p < 0.001).
