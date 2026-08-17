# Warming and methane release in a subarctic fen: mesocosm-level test

## Design and data

`data/input.csv` holds 96 static-chamber records from the Kaldbekk fen
warming array: 24 peat mesocosms, each measured on 4 flux campaigns
(thaw-season weeks 3, 6, 9 and 12 of 2025). Half of the mesocosms carry an open-top
warming chamber and half are ambient controls; the treatment was assigned once, to the
whole mesocosm, and did not change between campaigns.

## Analysis

The four campaign records of a mesocosm are repeated measurements of the same randomised
unit, so they were averaged before any test was run. Collapsing the long-format file gives
24 mesocosm mean CH4 fluxes, exactly one per mesocosm, so no mesocosm contributes more
than one value. The 12 warmed mesocosm means were then compared with the 12 ambient
mesocosm means using a two-sided exact Mann-Whitney U test.

## Result

| Treatment | Mesocosms | Campaigns per mesocosm | Mean of mesocosm means | Median mesocosm mean |
| --- | --- | --- | --- | --- |
| Ambient | 12 | 4 | 2.07 | 1.97 |
| Warmed | 12 | 4 | 3.83 | 3.82 |

Fluxes are in mg CH4 per square metre per hour. The warmed median mesocosm mean exceeds
the ambient median by 1.85 mg CH4 per square metre per hour.

[selected-result] Exact two-sided Mann-Whitney U test on 24 mesocosm-level mean CH4 fluxes (12 warmed vs 12 ambient, one analysed value per mesocosm): U = 141.0, p = 5.177e-06; warmed mesocosms released more methane (median mesocosm mean 3.82 vs 1.97 mg CH4 per square metre per hour).

## Caveats

The comparison is between mesocosms, so it supports a claim about mesocosms rather than
about individual chamber campaigns; the 96 campaign records were used only to estimate
each mesocosm's seasonal mean flux. Within-season variation is folded into that mean and
is not modelled separately, and the array covers one thaw season at a single fen.
