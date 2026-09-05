# Enrichment housing for laboratory rabbits

Fifty-six New Zealand White rabbits were housed for eight weeks either in standard cages
(n = 28) or in enriched pens with platforms, hay racks and gnawing blocks (n = 28). Six
welfare and physiology outcomes were measured at the end of the period and compared
between housing types with two-sample t-tests (`analysis.py`, run on `data.csv`).

Faecal corticosterone and stereotypy bouts were named in the protocol as the two
welfare-critical outcomes. Those two were treated as their own small family and corrected
with the Holm procedure at a family alpha of 0.05. The other four outcomes were read
against the plain 0.05 level with no adjustment, so the table below mixes adjusted and
unadjusted p-values in a single column.

| Outcome | Standard | Enriched | p | Basis |
|---|---:|---:|---:|---|
| Final body weight (g) | 3119.9 | 3244.9 | 0.107 | raw, not significant |
| Faecal corticosterone (ng/g) | 148.0 | 112.0 | 0.0026 | Holm-adjusted, significant |
| Stereotypy bouts (per h) | 2.82 | 1.15 | 0.0000012 | Holm-adjusted, significant |
| Femoral bone density (mg/cm3) | 412.0 | 455.0 | 0.0018 | raw, significant |
| Sole lesion score (0-6) | 2.14 | 1.36 | 0.014 | raw, significant |
| Latency to novel food (s) | 88.5 | 55.0 | 0.00065 | raw, significant |

Corrected outcomes: faecal corticosterone (raw p = 0.0026, Holm p = 0.0026) and stereotypy
bouts (raw p = 6.2e-07, Holm p = 1.2e-06). Both remain significant after correction.

## Welfare case for enriched housing

The two welfare-critical outcomes both moved in the expected direction and both survived
correction. Corticosterone metabolites fell by about 24 percent and stereotypic behaviour
by about 60 percent in the enriched pens, which is the pattern expected if the pens reduce
chronic stress and give the animals something to do besides bar-gnawing and pawing.

The secondary outcomes point the same way. Bone density was 43 mg/cm3 higher in enriched
pens, consistent with the extra locomotion that platforms allow, and sole lesion scores were
lower, which fits softer and more varied standing surfaces. Latency to approach novel food
was cut roughly in half, usually read as reduced fearfulness. Final body weight was 125 g
higher in the enriched group but did not reach significance (p = 0.107), so growth is best
described as unaffected.

Read together, enriched pens improved every outcome that moved, with no cost detected in
growth. The four secondary outcomes carry no multiplicity control, so they should be treated
as supporting rather than confirmatory evidence.
