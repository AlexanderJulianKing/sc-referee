# Final ethanol titer of an engineered Zymomonas strain in pilot fermenters

## Design

Twelve independent 20 L pilot fermenters were taken to harvest, six seeded with the
wild-type strain and six with the engineered strain. Each vessel received its own
inoculum lot and contributes exactly one harvest titer, so the twelve rows of
data/input.csv are twelve independent units and no vessel is measured more than once.

## Vessel-level summary

| Arm | Vessels | Mean (g/L) | SD (g/L) | Median (g/L) | Min (g/L) | Max (g/L) |
| --- | --- | --- | --- | --- | --- | --- |
| wild-type | 6 | 42.00 | 1.86 | 41.65 | 39.60 | 44.50 |
| engineered | 6 | 49.25 | 2.07 | 48.95 | 46.90 | 52.20 |

## Test

With six vessels per arm the two arms were compared with an exact two-sided
Mann-Whitney U test on the twelve vessel-level titers (no ties are present, so the
exact null distribution applies). The engineered vessels occupy the six highest ranks,
giving U = 36.0 with an exact two-sided p-value of 0.00216. The rank-biserial
correlation is 1.000, the Hodges-Lehmann shift estimate is 7.25 g/L, and the gap
between arm means is 7.25 g/L.

[selected-result] Exact two-sided Mann-Whitney U test on 12 independent pilot fermenters (6 engineered vs 6 wild-type, one harvest titer per vessel): U = 36.0, p = 0.00216, Hodges-Lehmann shift +7.25 g/L, so the engineered strain reaches the higher final titer.

## Reading

The strains were assigned to whole vessels and the comparison is made at the vessel
level, so the independence assumption of the exact test is satisfied by construction
rather than by argument. Complete separation of the two arms yields the smallest
p-value this design can return, so the result is best read as evidence that is as
strong as twelve runs allow, not as a finely resolved probability.
