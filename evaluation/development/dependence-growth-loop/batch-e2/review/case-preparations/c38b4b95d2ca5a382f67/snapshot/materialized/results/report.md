# Perforated shade screens and daily water use in rooftop planter modules

## Design

Fourteen modular rooftop planters (module_id P01-P14) were logged on six
consecutive days in July 2025. Each module spent three of those days under a
perforated shade screen and three days with an open top; the day order was
counterbalanced, so half the array was screened on the even-numbered days and
half on the odd-numbered days. Daily evapotranspiration was metered once per
module-day, giving 84 session rows in total.

## Analysis

The 84 session rows are repeated measurements rather than 84 independent
observations: six of them belong to each planter. Every module's three
screened days and three open days were therefore averaged first, and the
module-level contrast (screened mean minus open mean) was what entered the
test. That leaves exactly one analysed row per planter module, so the units
in the reported comparison are the 14 modules, not the 84 daily logs.

The 14 module-level pairs were compared with a two-sided paired t-test
(scipy.stats.ttest_rel), which is equivalent to a one-sample t-test on the 14
contrasts.

## Module-level summary (mm/day)

| module_id | logged days | screened mean | open mean | contrast |
| --- | --- | --- | --- | --- |
| P01 | 6 | 4.390 | 4.860 | -0.470 |
| P02 | 6 | 4.920 | 5.120 | -0.200 |
| P03 | 6 | 3.780 | 4.400 | -0.620 |
| P04 | 6 | 5.560 | 5.550 | +0.010 |
| P05 | 6 | 4.660 | 4.980 | -0.320 |
| P06 | 6 | 3.540 | 4.250 | -0.710 |
| P07 | 6 | 5.160 | 5.300 | -0.140 |
| P08 | 6 | 4.220 | 4.720 | -0.500 |
| P09 | 6 | 4.750 | 5.040 | -0.290 |
| P10 | 6 | 5.330 | 5.410 | -0.080 |
| P11 | 6 | 4.050 | 4.610 | -0.560 |
| P12 | 6 | 4.520 | 4.900 | -0.380 |
| P13 | 6 | 4.950 | 5.180 | -0.230 |
| P14 | 6 | 4.380 | 4.790 | -0.410 |

## Result

- Grand mean, screened days: 4.586 mm/day
- Grand mean, open days: 4.936 mm/day
- Mean contrast: -0.350 mm/day (SD 0.210, n = 14 modules)
- Paired t-test: t(13) = -6.22, p < 0.001

[selected-result] Averaging each planter's repeated days into one analysed row per module (n = 14 independent modules from 84 session rows), a two-sided paired t-test shows that screened days use less water than open days: mean contrast -0.350 mm/day (SD 0.210), t(13) = -6.22, p < 0.001.

## Notes

13 of the 14 modules had a negative contrast; module P04 was the single
exception (+0.010 mm/day). The within-module spread across logging days is
not treated as replication, and no claim is made about individual days.
