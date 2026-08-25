# Urban heat and emergency department visits by neighbourhood

## What we did

We compared 60 city neighbourhoods, 30 in the lowest tree-canopy tertile and 30 in
the highest, over one summer. Air temperature and PM2.5 came from the monitoring
network interpolated to neighbourhood centroids; emergency department visits came
from routine hospital records, expressed per 1000 residents. Each neighbourhood
contributes one summary row. `analysis.py` computes all five comparisons first
(Welch two-sample t-tests) and stores them, then formats the table in a separate
reporting pass.

## Results

| Outcome | Low canopy | High canopy | Difference | p | Verdict |
|---|---|---|---|---|---|
| Mean summer temp (C) | 27.68 | 26.36 | +1.31 | 0.00044 | significant |
| Heat ED visits /1000 | 3.86 | 2.82 | +1.04 | 0.0039 | significant |
| Asthma ED visits /1000 | 10.17 | 7.31 | +2.85 | 0.00030 | significant |
| Night minimum temp (C) | 20.52 | 19.01 | +1.51 | 2.4e-06 | significant |
| Annual PM2.5 (ug/m3) | 11.62 | 10.20 | +1.42 | 0.0035 | significant |

Differences are low canopy minus high canopy. All five point the same way: low-canopy
neighbourhoods are hotter by day, hotter at night, dirtier, and send more people to
emergency departments for both heat and asthma.

The night-time gap is the largest relative to its scatter (p = 2.4e-06) and is the
one we would emphasise. Daytime heat is partly a matter of shade at the moment of
measurement; night minimum temperature reflects how much heat the neighbourhood
stored during the day and is the exposure most closely tied to heat illness, because
it determines whether people get a chance to cool down overnight.

## What this means for the tree-planting programme

The programme should prioritise low-canopy neighbourhoods, and the case for doing so
is stronger than the raw effect sizes suggest: an extra 1.0 heat visit and 2.9 asthma
visits per 1000 residents, across a summer, is a large absolute number of attendances
in neighbourhoods of 5,000 to 20,000 people.

Three limits on how far this can be pushed:

- **This is a cross-sectional comparison of neighbourhoods, not a planting trial.**
  Low-canopy neighbourhoods in this city are also the denser, poorer, more
  traffic-exposed ones. Canopy, temperature, PM2.5 and deprivation move together, and
  nothing in these five tests separates them. We cannot say from this data how much of
  the ED gap planting alone would close.
- **PM2.5 is unlikely to be a tree effect.** The 1.4 ug/m3 gap almost certainly
  reflects proximity to arterial roads rather than the trees themselves, and the
  asthma result should be read with that in mind.
- **Five outcomes were each tested against the same 0.05 cutoff**, and they are not
  independent of each other: temperature, night temperature and heat visits are three
  views of the same underlying exposure. The consistent direction across all five is
  the finding, more than any single p-value.

A useful next step is to track the neighbourhoods that receive planting in the coming
two years and compare their night-time temperatures before and after, which would turn
this into a before-and-after comparison rather than a snapshot.
