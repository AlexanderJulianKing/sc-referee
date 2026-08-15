# Dissolved zinc in constructed wetland mesocosm outflow

## Data

Bench-scale constructed treatment wetlands were run for eight weeks and
their outflow was assayed for dissolved zinc on four sampling weeks.

- Outflow water samples analysed: 48
- Sampling weeks represented: 2, 4, 6, 8
- Samples with substrate biochar_amended: 24
- Samples with substrate gravel_control: 24

## Mean outflow zinc by mesocosm

| mesocosm_id | substrate | samples | mean zinc (mg/L) |
| --- | --- | --- | --- |
| MC-01 | biochar_amended | 4 | 0.620 |
| MC-02 | biochar_amended | 4 | 0.580 |
| MC-03 | biochar_amended | 4 | 0.710 |
| MC-04 | biochar_amended | 4 | 0.550 |
| MC-05 | biochar_amended | 4 | 0.660 |
| MC-06 | biochar_amended | 4 | 0.600 |
| MC-07 | gravel_control | 4 | 0.940 |
| MC-08 | gravel_control | 4 | 1.020 |
| MC-09 | gravel_control | 4 | 0.920 |
| MC-10 | gravel_control | 4 | 1.100 |
| MC-11 | gravel_control | 4 | 0.970 |
| MC-12 | gravel_control | 4 | 1.050 |

## Substrate group summary

| substrate | samples | mean (mg/L) | SD (mg/L) |
| --- | --- | --- | --- |
| biochar_amended | 24 | 0.6200 | 0.0601 |
| gravel_control | 24 | 1.0000 | 0.0697 |

## Analysis

Welch's two-sample t-test (two-sided, unequal variances) compares the
dissolved zinc concentration of the two substrate builds. Each outflow
water sample in data/input.csv enters the test as one observation.

- Mean difference (biochar_amended - gravel_control): -0.3800 mg/L
- Welch t = -20.228 on df = 45.02
- p < 1e-06
- Significance threshold: alpha = 0.05

## Conclusion

[selected-result] Welch's two-sample t-test on 48 outflow water samples: mean dissolved zinc is 0.3800 mg/L lower under biochar_amended (0.6200 mg/L) than under gravel_control (1.0000 mg/L), t = -20.228, df = 45.02, p < 1e-06, significant at alpha = 0.05.
