# Chitin accumulation in strain MX-7 on two substrate blends

## Data

- Source file: `data/input.csv`
- Harvest samples analysed: 60
- Bioreactor vessels: 12
- Harvest samples per vessel: 5
- Harvest days present: 3, 6, 9, 12, 15

## Method

Chitin content (mg per g dry biomass) is compared between the two substrate
blends with a two-sided Welch two-sample t-test. Each harvest sample in the
file supplies one observation, so the test runs on 30 observations per blend.

## Summary statistics

| Substrate blend | Observations | Mean chitin (mg/g) | SD |
| --- | --- | --- | --- |
| lignin_blend | 30 | 22.00 | 1.63 |
| starch_blend | 30 | 23.50 | 1.58 |

## Result

Mean difference (starch_blend minus lignin_blend): 1.50 mg/g
95% confidence interval: 0.67 to 2.33 mg/g
Welch t = 3.62, df = 57.9, p < 0.001

[selected-result] Welch two-sample t-test of chitin content, starch_blend vs lignin_blend: mean difference 1.50 mg/g (95% CI 0.67 to 2.33), t = 3.62, df = 57.9, p < 0.001; chitin content is significantly higher on the starch blend.
