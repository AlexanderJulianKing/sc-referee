# Trellis system and berry skin anthocyanin in Syrah

## Data

The file records 24 Syrah vineyard blocks, each at a different estate and each trained on a single trellis system. Each block contributes exactly one analyzed row: a 100-berry composite drawn across the block at harvest and assayed once. Rows therefore correspond one-to-one with independent blocks, and no block appears twice.

| trellis system | blocks | mean anthocyanin (mg/g skin) | SD |
| --- | ---: | ---: | ---: |
| vertical shoot positioning | 12 | 1.514 | 0.152 |
| sprawl | 12 | 1.236 | 0.120 |

## Analysis

Welch's two-sided two-sample t-test (unequal variances, Welch-Satterthwaite degrees of freedom) comparing block-level composite anthocyanin concentration between the two trellis systems. The block is the unit of assignment, the unit of measurement, and the unit of analysis, so the 24 values entering the test are mutually independent.

## Result

[selected-result] Welch two-sample t-test on 24 independent vineyard blocks (12 vertical shoot positioning, 12 sprawl): mean berry skin anthocyanin was 1.514 mg/g under vertical shoot positioning versus 1.236 mg/g under sprawl, a difference of 0.278 mg/g (t = 4.99, df = 20.86, p < 0.001); anthocyanin was higher under vertical shoot positioning.

## Notes

- Group sizes are balanced (12 and 12); the unequal-variance (Welch) form of the test was used because the two sample standard deviations differ.
- The columns vine_age_years and canopy_leaf_layers are recorded for context and take no part in the reported test.
- A single pre-specified two-sided comparison was made, so no adjustment for multiplicity applies.
