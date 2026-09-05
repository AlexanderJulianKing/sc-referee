# Road salt runoff and roadside soil

Sixty-four composite soil cores were taken at the end of winter, 32 along a heavily salted
arterial route and 32 along a comparable unsalted rural route in the same county. Five soil
outcomes were compared between route types with two-sample t-tests (`analysis.py` on
`data.csv`). Each p-value was rounded to three decimal places on the way out of the test, and
the rounded value is what the script compares to the 0.05 cutoff and prints. No family-wide
adjustment was applied, so each outcome is judged on its own.

| Outcome | Unsalted | Salted | p (3 dp) | Verdict |
|---|---:|---:|---:|---|
| Soil chloride (mg/kg) | 42.0 | 168.0 | 0.000 | significant |
| Electrical conductivity (dS/m) | 0.280 | 0.660 | 0.000 | significant |
| Sodium adsorption ratio | 0.900 | 2.601 | 0.000 | significant |
| Soil pH | 6.35 | 6.62 | 0.010 | significant |
| Earthworms per core | 11.5 | 7.3 | 0.000 | significant |

All five outcomes clear the cutoff. Four of them sit far below it, and three decimal places
is not enough resolution to show how far: the chloride, conductivity and sodium adsorption
ratio p-values all print as 0.000.

## What this means for winter maintenance

Chloride along the salted route is four times the rural background, and conductivity and the
sodium adsorption ratio track it closely. That combination is the signature of de-icing salt
rather than of a general difference in soil type, since all three respond to the same ions.
A sodium adsorption ratio of 2.6 is still below the level at which soil structure is usually
considered at risk, but it is approaching the range where repeated seasons would matter,
particularly in fine-textured verge soils that drain slowly.

The earthworm result is the one with direct ecological weight. Counts were down by roughly
37 percent along the salted route. Earthworms are osmotically sensitive and do not move far,
so verge populations cannot escape a salted season, and slower litter breakdown along the
verge follows from losing them.

The pH difference of 0.27 units is significant but small, and on its own it would not change
management. Practical implications are the familiar ones: calibrate spreaders to road
conditions rather than to a fixed rate, prefer pre-wetted salt or brine to reduce bounce and
scatter beyond the carriageway, and where verge drainage allows it, direct runoff away from
the first metre or two of soil. Because no correction was applied across the five outcomes,
the marginal pH result in particular should be read with that in mind.
