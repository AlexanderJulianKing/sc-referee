# Reduced-rate and full-rate fungicide programmes for black scurf in seed potatoes

One field was divided into 64 plots, 32 given the standard full-rate soil fungicide programme and
32 given the reduced-rate programme. Each plot was lifted and graded separately. Six outcomes were
recorded: marketable yield, black scurf incidence, stem canker index, tubers per plant, mean tuber
weight, and programme cost.

## How multiplicity was handled

Six comparisons on one field give six chances to turn ordinary plot-to-plot variation into a
result, so the p-values here are adjusted rather than raw. The adjustment is a label-shuffling
procedure done by hand in the analysis script rather than a packaged routine, and it works like
this. First, the Welch t statistic is computed for each of the six outcomes using the true
programme labels. Then the programme labels are shuffled across the 64 plots 4000 times. Each
shuffle is a field in which the programme means nothing, and for each one only the largest
absolute t statistic among the six outcomes is kept. That gives 4000 draws of "the biggest thing
six outcomes throw up by chance alone". An outcome's adjusted p-value is the fraction of those
4000 maxima that reach or exceed its observed statistic. An outcome is called significant only if
that adjusted value falls below 0.05.

The random seed was 71042 and the shuffle count was 4000. For reference, the largest shuffle
maximum seen was 4.51 and the 95th percentile of the 4000 maxima was 2.71, so an observed
statistic has to clear roughly 2.7 in absolute value to be called.

| Outcome | Full rate | Reduced rate | t | Adjusted p | Verdict |
|---|---|---|---|---|---|
| Marketable yield (t/ha) | 42.5 | 40.1 | -1.70 | 0.423 | not significant |
| Black scurf incidence (%) | 12.4 | 18.9 | 4.07 | 0.0008 | significant |
| Stem canker index | 14.2 | 21.5 | 4.14 | 0.0008 | significant |
| Tubers per plant | 11.81 | 11.20 | -1.07 | 0.856 | not significant |
| Mean tuber weight (g) | 118.0 | 113.9 | -0.79 | 0.965 | not significant |
| Programme cost (GBP/ha) | 285 | 168 | -34.43 | <0.00025 | significant |

Statistics are reduced rate minus full rate. No adjusted p-value came out at exactly zero; the
cost figure is reported as below one over the shuffle count because no shuffle maximum reached it.

## Advice on the reduced-rate programme

The reduced-rate programme saves GBP 117/ha and loses disease control. Black scurf incidence rises
by 6.5 percentage points and the stem canker index by 7.3 points, both established after the
adjustment. Neither yield nor either yield component was established as different, and the yield
gap of 2.4 t/ha is the one number worth thinking about carefully. It is not demonstrated here, but
it is not ruled out either, and a shortfall that size would have to be worth less than about
GBP 49/t for the cost saving to come out ahead. In seed potatoes it is worth considerably more.

For seed crops the disease results settle it on their own. Black scurf is a grading and
certification problem before it is a yield problem, and an incidence rising from 12 to 19 percent
moves tonnage from the seed grade into ware. We do not recommend the reduced-rate programme for
seed production. It may still be worth testing in ware crops where skin blemish carries less
penalty, but that needs its own trial, and this one is a single field in a single season, so
neither the soil inoculum level nor the season's weather is represented more than once.
