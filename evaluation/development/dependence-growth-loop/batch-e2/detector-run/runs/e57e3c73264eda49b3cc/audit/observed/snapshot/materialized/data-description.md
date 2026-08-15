# What is in data/input.csv

Ten separate seagrass meadows along one coastline were mapped from aerial
imagery in 2015 and mapped again in 2025. Each meadow occupies its own named
stretch of coast, was surveyed once, and yields a single number: the percentage
change in its mapped area across the decade. Five of the meadows lie inside
voluntary no-anchoring zones; the other five are open to boat anchoring.

Columns:

- meadow_id: unique label for the meadow; a label appears on one row only
- coast_sector: the named stretch of coast the meadow occupies
- anchoring_regime: either no_anchor_zone or open_access
- chart_depth_m: charted water depth at the meadow centre, in metres
- baseline_area_ha: mapped meadow area in 2015, in hectares
- area_change_pct_2015_2025: percentage change in mapped area, 2015 to 2025

One row is: one seagrass meadow surveyed once, with its single decadal change in mapped area
Independent unit column: meadow_id

No meadow is measured twice and no two rows come from the same meadow, so the
values compared between the two anchoring regimes are independent observations.
The depth and baseline-area columns are background context and are not used by
the test.
