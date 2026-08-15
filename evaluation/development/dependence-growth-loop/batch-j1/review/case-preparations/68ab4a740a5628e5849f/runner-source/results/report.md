# Thermal regime and net calcification in Acropora nubbins

## Data

Source file: `data/input.csv` (12 measurement rows).

- ambient: n = 6, mean = 15.000 mg CaCO3 g^-1 d^-1, sd = 1.897
- heated: n = 6, mean = 12.000 mg CaCO3 g^-1 d^-1, sd = 1.549
- 6 parent colonies contributed 2 measurements each.

## Analysis

Each measurement row in the file was entered as one observation in a
two-sample Student t-test with pooled variance (two-sided), comparing net
calcification under the ambient regime with net calcification under the
heated regime (scipy.stats.ttest_ind, equal_var=True).

## Result

- Mean difference (ambient - heated): 3.000 mg CaCO3 g^-1 d^-1
- 95% confidence interval: 0.7719 to 5.2281
- Test statistic: t(10) = 3.0000
- Two-sided p-value: 0.0133

[selected-result] Two-sample Student t-test comparing the 12 nubbin calcification measurements between thermal regimes: ambient nubbins calcified 3.000 mg CaCO3 g^-1 d^-1 faster than heated nubbins, t(10) = 3.0000, p = 0.0133 (two-sided, 95% CI 0.7719 to 5.2281).

## Interpretation

At the 0.05 level the ambient-heated difference in net calcification is
statistically significant. The 12 analysed rows are the 2 nubbins measured
on each of the 6 parent colonies, and the test used all 12 rows as its
observations, which is where its 10 degrees of freedom come from.
