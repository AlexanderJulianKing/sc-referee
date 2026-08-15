# Headspace methane fraction under two digester feed blends

## Design and data

Twelve 5 L lab-scale anaerobic digesters were started in parallel from a single inoculum batch. Six vessels were assigned to the standard maize-silage feed and six to the enriched feed (maize silage plus mineral-supplemented cattle manure and biochar fines). Headspace gas was drawn once per week during run weeks 3 to 7, after the acclimation phase, and the methane fraction was read on a benchtop analyser.

The stored table holds 60 vessel-week rows for 12 vessels, 5 weekly samples per vessel.

## Analysis

The weekly readings from one vessel are repeated measures on the same reactor and are not independent of each other: the vessel, not the weekly sample, is the unit that received a feed blend. Each vessel's weekly series was therefore averaged into a single vessel-level methane fraction, and the blend contrast was tested on those 12 independent vessel values with an exact two-sided Mann-Whitney U test (6 standard vessels versus 6 enriched vessels, no ties among the vessel means).

## Vessel-level values

| vessel | feed blend | weekly samples | mean CH4 (%) |
| --- | --- | ---: | ---: |
| D01 | standard | 5 | 58.68 |
| D02 | enriched | 5 | 60.96 |
| D03 | standard | 5 | 59.02 |
| D04 | enriched | 5 | 61.58 |
| D05 | standard | 5 | 59.30 |
| D06 | enriched | 5 | 62.04 |
| D07 | standard | 5 | 59.86 |
| D08 | enriched | 5 | 62.40 |
| D09 | standard | 5 | 60.14 |
| D10 | enriched | 5 | 62.86 |
| D11 | standard | 5 | 61.22 |
| D12 | enriched | 5 | 63.52 |

## Result

- median vessel mean, standard feed: 59.58 % CH4 (n = 6 vessels)
- median vessel mean, enriched feed: 62.22 % CH4 (n = 6 vessels)
- shift (enriched minus standard): +2.64 percentage points
- exact two-sided Mann-Whitney U = 35, p = 0.0043

[selected-result] Enriched-feed digesters held a higher headspace methane fraction than standard-feed digesters: median vessel mean 62.22 % versus 59.58 % (+2.64 percentage points), exact two-sided Mann-Whitney U = 35, p = 0.0043, computed from one averaged value per vessel for 6 enriched and 6 standard vessels.

## Caveats

The vessels were not blinded to the operator and the window covers a single loading rate over five steady-state weeks, so the contrast speaks to that phase only. The exact rank test assumes nothing about the shape of the vessel-mean distribution but has coarse resolution at six vessels per blend: with this design no arrangement of the data could have returned a two-sided p-value below about 0.002. Averaging within a vessel deliberately discards the week-to-week variation visible in the source table, which is small next to the spread between vessels.
