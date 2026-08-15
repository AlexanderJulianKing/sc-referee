# Methane flux from drained versus intact peatland

## Data

Static-chamber closures read from `data/input.csv`: 60 flux measurements (drained = 30, intact = 30).

| Peat condition | n | Mean CH4 flux (mg m^-2 h^-1) | SD |
| --- | --- | --- | --- |
| drained | 30 | 12.400 | 0.652 |
| intact | 30 | 10.000 | 0.597 |

## Analysis

Welch's two-sample t-test (unequal variances) comparing the methane flux of drained and intact peat. Every chamber closure in `data/input.csv` is entered as one observation.

- Difference in means (drained - intact): 2.400 mg m^-2 h^-1
- Welch t = 14.876
- Welch degrees of freedom = 57.55
- Two-sided p < 1e-06

## Conclusion

[selected-result] Drained peat emits more methane than intact peat: mean difference 2.400 mg m^-2 h^-1 (drained 12.400, intact 10.000), Welch t = 14.876, df = 57.55, two-sided p < 1e-06.
