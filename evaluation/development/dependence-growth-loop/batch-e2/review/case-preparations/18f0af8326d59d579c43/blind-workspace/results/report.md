# Vickers Microhardness of Ti-6Al-4V Coupons: As-Built vs Stress-Relieved

Source table: `data/input.csv` (48 microhardness indentations).

## Group summary

| condition | indentations | mean HV0.5 | SD HV0.5 |
| --- | --- | --- | --- |
| as_built | 24 | 370.00 | 7.34 |
| stress_relieved | 24 | 350.00 | 7.59 |

## Test

Welch's unequal-variance two-sample t-test, two-sided, compares mean Vickers
hardness between the two heat-treatment conditions. Every indentation in the
table enters the test as one independent observation.

- Mean difference (as_built minus stress_relieved): 20.00 HV0.5
- t = 9.280
- df = 45.95
- p < 1e-06

[selected-result] Welch's two-sample t-test treating each of the 48 indentations as an independent observation: as-built coupons average 370.00 HV0.5 versus 350.00 HV0.5 for stress-relieved coupons, a difference of 20.00 HV0.5 (t = 9.280, df = 45.95, p < 1e-06).

## Reading

The stress-relief anneal at 730 C is associated with roughly a 20 HV0.5 drop
in surface microhardness, consistent with partial decomposition of the
martensitic alpha-prime structure retained after printing.
