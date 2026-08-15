# Overwinter wrapping and spring cluster mass in honey bee colonies

## Design

16 overwintered colonies were weighed once each at the first spring
inspection. Every colony (hive_id) appears in exactly one row, so the
analysed values are 16 independent units with no repeated measurements.

| wrap_treatment | colonies | mean mass (kg) | median mass (kg) |
| --- | --- | --- | --- |
| bare | 8 | 1.27 | 1.27 |
| wrapped | 8 | 1.81 | 1.69 |

## Test

Two-sided Mann-Whitney U test on spring cluster mass, exact null
distribution, 8 bare colonies versus 8 wrapped colonies (one value per
colony).

- U = 3.0, computed with the bare colonies as the first sample
- p = 0.001088
- wrapped colony heavier in 0.953 of the 64 cross-treatment pairs
- mean difference (wrapped minus bare) = 0.54 kg

## Interpretation

Spring cluster mass was higher in wrapped colonies than in bare colonies.
Because each colony supplies a single value, the rank test's independence
assumption is met by the design and the p-value needs no clustering
correction. With 8 colonies per arm the size of the gap is still
estimated coarsely.

[selected-result] Wrapped colonies had higher spring cluster mass than bare colonies: exact two-sided Mann-Whitney U = 3.0 with 8 versus 8 independent colonies, p = 0.001088 (mean difference 0.54 kg).
