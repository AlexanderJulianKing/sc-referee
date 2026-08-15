# Aerial seeding and pine regeneration in burned compartments

## Design

Twenty-six burn compartments were surveyed once each by drone
photogrammetry three growing seasons after the fire. Thirteen
compartments received aerial seeding of pine seed; thirteen were left to
recover naturally. The compartment is both the unit that received the
treatment and the unit that was measured, and each compartment
contributes exactly one row to the analysis.

## Independence check

- Rows read: 26
- Distinct compartments: 26
- Rows per compartment: 1 (no compartment appears more than once)

## Group summaries

| aerial_seeding | compartments | mean pine_stems_per_ha | sd | mean elevation_m |
| --- | --- | --- | --- | --- |
| yes | 13 | 1492.3 | 276.3 | 1213.8 |
| no | 13 | 1046.9 | 238.6 | 1204.2 |

## Test

Welch's two-sample t-test (unequal variances, two-sided) comparing
pine_stems_per_ha between seeded and naturally recovering compartments,
seeded minus naturally recovering.

- Mean difference: 445.4 stems per hectare
- t = 4.40, df = 23.5, p < 0.001

[selected-result] Welch's two-sample t-test across 26 independent burn compartments (13 seeded, 13 naturally recovering, one row per compartment): seeded compartments held 445.4 more pine stems per hectare than naturally recovering compartments (1492.3 vs 1046.9), t = 4.40, df = 23.5, p < 0.001, a statistically significant increase.

## Notes

Elevation was recorded as context; the two groups are closely matched on it
(1213.8 m versus 1204.2 m) and the reported test is unadjusted. No
sub-compartment plot, transect, or repeat visit enters the test: the 26 rows
are 26 independent compartments, so the row count and the number of
independent units are the same.
