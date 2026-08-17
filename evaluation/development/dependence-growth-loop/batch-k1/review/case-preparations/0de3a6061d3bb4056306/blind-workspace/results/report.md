# Methane flux in restored versus drained peatland chambers

## Data

The file `data/input.csv` records 40 static-chamber measurements of methane flux (mg CH4 m^-2 h^-1) from a lowland peatland restoration trial, together with the management class of the chamber's plot, the survey visit, and the water-table depth logged at sampling.

## Analysis

Flux readings were summarised per management class and compared with a two-sample Student t-test (scipy.stats.ttest_ind, equal variances assumed) in which each of the 40 measurement rows entered the test as one observation. Cohen's d was computed from the pooled standard deviation.

## Summary statistics

| management | measurements | mean flux (mg CH4 m^-2 h^-1) | SD |
| --- | --- | --- | --- |
| restored | 20 | 12.00 | 2.94 |
| drained | 20 | 4.00 | 1.47 |

## Result

[selected-result] Restored chambers released more methane than drained chambers: mean difference 8.00 mg CH4 m^-2 h^-1 (restored 12.00, drained 4.00), two-sample t-test t(38) = 10.89, p < 0.001, Cohen's d = 3.44.
