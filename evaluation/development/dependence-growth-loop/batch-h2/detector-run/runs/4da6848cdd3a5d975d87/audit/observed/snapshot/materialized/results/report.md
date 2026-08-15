# Late-season carbon enrichment in proglacial streams

## Design

24 proglacial streams draining separate glaciated headwater catchments were each sampled once in June and once in September of the same melt year. No catchment appears twice in the file and no stream drains into another.

The June and September values belonging to a stream are collapsed into one signed change before anything is tested, so each catchment supplies exactly one analysed observation and the sample size of the test is the number of catchments rather than the number of water samples.

## Per-stream direction of change

| stream_code | delta_doc_mg_per_l | direction |
|---|---|---|
| PG01 | +0.49 | increase |
| PG02 | +0.28 | increase |
| PG03 | +0.46 | increase |
| PG04 | +0.26 | increase |
| PG05 | -0.39 | decrease |
| PG06 | +0.39 | increase |
| PG07 | +0.48 | increase |
| PG08 | +0.28 | increase |
| PG09 | -0.36 | decrease |
| PG10 | +0.53 | increase |
| PG11 | +0.31 | increase |
| PG12 | +0.43 | increase |
| PG13 | +0.33 | increase |
| PG14 | -0.32 | decrease |
| PG15 | +0.49 | increase |
| PG16 | +0.44 | increase |
| PG17 | +0.26 | increase |
| PG18 | -0.37 | decrease |
| PG19 | +0.49 | increase |
| PG20 | +0.41 | increase |
| PG21 | -0.34 | decrease |
| PG22 | +0.43 | increase |
| PG23 | +0.32 | increase |
| PG24 | -0.38 | decrease |

## Test

The null hypothesis is that a stream is as likely to fall as to rise between June and September, that is, that the probability of an increase equals one half. The number of rising streams is compared with that null by an exact two-sided binomial test, the sign test for these paired changes, which assumes only that the per-stream changes are mutually independent.

- independent catchments analysed: 24
- streams with higher September DOC: 18
- streams with lower September DOC: 6
- ties excluded: 0
- proportion of streams increasing: 0.750
- exact two-sided p-value: 0.0227

[selected-result] Exact two-sided sign test (binomial test, null probability 0.5) on 24 independent proglacial catchments, one paired June-to-September change each: 18 of 24 streams had higher September dissolved organic carbon, proportion 0.750, p = 0.0227, so the 50/50 null is rejected at the 0.05 level.

## Interpretation

Late-season enrichment is the prevailing pattern: three quarters of the catchments carried more dissolved organic carbon in September than in June, and a split this lopsided would arise under the 50/50 null in about two studies in a hundred. The inference rests on 24 independent units because the two visits to a stream were reduced to a single change; counting both visits as separate observations would have doubled the apparent sample size without adding any independent information.
