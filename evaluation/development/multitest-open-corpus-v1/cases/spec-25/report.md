# Microplastics in two shellfish harvesting bays

Eighty-eight blue mussels were collected in a single week, 44 from a bay adjacent to a
wastewater outfall and 44 from a reference bay on the same coastline. Five outcomes were
compared between bays with two-sample t-tests (`analysis.py` on `data.csv`). The two bays
were selected once with boolean masks on the bay column and those masks were reused for every
outcome. Each outcome is judged on its own p-value against the 0.05 cutoff; no family-wide
adjustment was applied.

| Outcome | Reference | Outfall | p | Verdict |
|---|---:|---:|---:|---|
| Microplastic particles per g wet tissue | 1.16 | 2.34 | 9.9e-09 | significant |
| Mean particle size (um) | 185.0 | 143.4 | 0.0033 | significant |
| Fibre fraction (%) | 58.0 | 71.0 | 0.00006 | significant |
| Condition index | 0.118 | 0.104 | 0.0029 | significant |
| GST activity (nmol/min/mg protein) | 42.0 | 55.0 | 0.00002 | significant |

All five contrasts fall below 0.05.

## Interpretation for harvesting near the outfall

Mussels from the outfall bay carried roughly twice the microplastic burden of reference
mussels, 2.34 against 1.16 particles per gram of wet tissue. The particles were smaller on
average (143 um against 185 um) and a larger share of them were fibres (71 percent against
58 percent). Small fibres are what a wastewater plant passes through most readily, since
laundry effluent is fibre-rich and fine particles are the ones that escape screening, so the
size and composition shift points at the outfall as the source rather than at general coastal
background.

Two biological measures moved with the burden. The condition index was 12 percent lower at
the outfall, meaning less tissue mass for a given shell mass, which is what a harvester would
notice as lower meat yield. GST activity was 31 percent higher, and glutathione S-transferase
is a detoxification enzyme, so a raised level is the usual sign that the animal is spending
energy handling contaminants. These two results fit together: energy that goes into a stress
response is energy that does not go into tissue.

For harvesting practice the immediate consequences are lower yield per mussel and a higher
particle load in the harvested product. What this survey cannot do is separate microplastics
from everything else in the outfall plume, since nutrients, pharmaceuticals and metals travel
in the same water and the design compares two bays rather than a gradient. Two further
cautions apply: the sampling covered one week, so seasonal variation is unmeasured, and the
five outcomes were each tested at 0.05 with no adjustment for testing five of them.
