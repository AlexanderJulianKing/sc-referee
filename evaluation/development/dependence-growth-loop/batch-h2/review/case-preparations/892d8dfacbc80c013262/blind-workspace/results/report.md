# Inoculum pretreatment and specific methane yield in bench-scale digesters

## Data

The file data/input.csv stores 48 monitoring records collected from 12 bench-scale
anaerobic digesters. Each digester was sampled on four monitoring sessions (run days
6, 10, 14 and 18), so the records are repeated measurements nested within vessels
rather than 48 independent observations. Six digesters were run on untreated
inoculum (control) and six on thermally pretreated inoculum (thermal).

## Analysis

Each digester is collapsed to a single analysed value, the mean specific methane
yield across its four sessions. The resulting 12 digester means, one per
independent vessel, are compared between the two pretreatment arms with a
two-sided exact Mann-Whitney U test (6 vessels vs 6 vessels).

## Digester-level values

| digester | pretreatment | sessions | mean yield (mL CH4 / g VS) |
| --- | --- | --- | --- |
| DG01 | control | 4 | 262.3 |
| DG02 | thermal | 4 | 305.4 |
| DG03 | control | 4 | 248.3 |
| DG04 | thermal | 4 | 291.3 |
| DG05 | control | 4 | 271.4 |
| DG06 | thermal | 4 | 318.4 |
| DG07 | thermal | 4 | 297.2 |
| DG08 | control | 4 | 255.2 |
| DG09 | control | 4 | 239.5 |
| DG10 | thermal | 4 | 283.3 |
| DG11 | thermal | 4 | 311.3 |
| DG12 | control | 4 | 266.3 |

## Results

Monitoring records read: 48
Independent digesters analysed: 12
Control arm: n = 6 digesters, mean of digester means = 257.17 mL CH4 / g VS, median = 258.75
Thermal arm: n = 6 digesters, mean of digester means = 301.15 mL CH4 / g VS, median = 301.30
Difference in medians (thermal - control): 42.55 mL CH4 / g VS
Mann-Whitney U (thermal vs control): 36.0
Exact two-sided p-value: 0.002165

[selected-result] Thermally pretreated digesters produced higher specific methane yield than control digesters (Mann-Whitney U = 36.0, n = 6 vs 6 digester means, exact two-sided p = 0.002165); the median digester mean was 42.55 mL CH4 / g VS higher in the thermal arm.

## Unit of analysis

The 48 stored rows are four repeated sessions from each of 12 vessels. The reported
comparison is run on the 12 vessel-level means, so every independent digester enters
the test exactly once and the repeated sessions contribute only to the precision of
each vessel's own value.
