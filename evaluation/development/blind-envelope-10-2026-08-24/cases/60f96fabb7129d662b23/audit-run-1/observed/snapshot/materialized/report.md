# Urban and rural red foxes: comparison of four declared outcomes

## Data description

The analysis uses one file, `fox_habitat_measurements.csv`. It has a header row and 68 data rows.

**One row represents one adult red fox**: the animal's identifier, the area where it was trapped, and
the four outcomes measured for that animal during the study season. Each fox was live-trapped,
collared, sampled and released once, and each fox appears exactly once. Thirty-four foxes were trapped
in the city and thirty-four in the surrounding farmland. Every cell is filled; there are no missing
values.

| Column | Units | What it holds |
| --- | --- | --- |
| `fox_id` | none | Unique animal identifier, `FOX001` through `FOX068`, numbered in trapping order. |
| `habitat_group` | none | Trapping area for the animal. Exactly two values appear, `urban` and `rural`, with 34 rows each. |
| `body_condition_index` | unitless | Mass-for-length body condition score at capture. |
| `home_range_km2` | square kilometres | Home range area estimated from six months of collar fixes. |
| `faecal_cortisol_ng_per_g` | nanograms per gram | Faecal cortisol metabolite concentration in the scat sample taken at capture. |
| `diet_shannon_index` | unitless | Shannon diversity index of the food categories identified in the scat contents. |

All numbers below were produced by `analysis.py`, which reads this file.

## Group summaries

Mean and standard deviation for each habitat group, for each of the four declared outcomes.

| Outcome | Urban mean (SD), n = 34 | Rural mean (SD), n = 34 |
| --- | --- | --- |
| Body condition index | 1.0238 (0.1071) | 1.0132 (0.1262) |
| Home range (km^2) | 0.8682 (0.4239) | 3.0744 (3.5083) |
| Faecal cortisol (ng/g) | 122.7206 (38.2704) | 93.2353 (35.9670) |
| Diet Shannon index | 1.5829 (0.3365) | 1.5491 (0.3485) |

## Declared family of four outcomes

Each outcome was compared between the two habitat groups with Welch's two-sample t-test for
independent samples. The four outcomes were declared in advance, in the order shown below, so they
form one family of tests. All four raw p-values were collected and adjusted together as that complete
family, using the Holm-Bonferroni procedure at a family-wise level of 0.05. Every verdict in the last
column comes from the adjusted p-value, not the raw one.

| # | Outcome | Welch t | df | Raw p | Adjusted p | Verdict at family-wise 0.05 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `body_condition_index` | 0.373 | 64.30 | 0.71044 | 1.00000 | Not significant |
| 2 | `home_range_km2` | -3.640 | 33.96 | 0.00090 | 0.00359 | Significant |
| 3 | `faecal_cortisol_ng_per_g` | 3.274 | 65.75 | 0.00170 | 0.00509 | Significant |
| 4 | `diet_shannon_index` | 0.407 | 65.92 | 0.68524 | 1.00000 | Not significant |

Positive t values mean the urban mean is the larger one. Urban foxes held smaller home ranges than
rural foxes and had higher faecal cortisol concentrations. Body condition and diet diversity did not
differ between the two areas once the family was adjusted together.

## Sensitivity check on the home range comparison (robustness only)

One rural animal, `FOX013`, has a recorded home range of 22.14 square kilometres. Every other fox in
the table falls between 0.20 and 4.63 square kilometres. That animal dispersed out of the study area
during the collar period, so its fixes cover far more ground than a resident territory. The value is
kept in the data file as recorded, and it is included in the test reported above.

As a robustness check, the home range comparison was re-run exactly once with that single fox removed:

| Group | n | Mean (km^2) | SD |
| --- | --- | --- | --- |
| Urban | 34 | 0.8682 | 0.4239 |
| Rural | 33 | 2.4967 | 0.9948 |

Welch t = -8.671, df = 42.98, unadjusted p = 5.46e-11.

This re-run is a robustness check on one questionable recorded value. It is not an inferential result.
It is not part of the declared family, it was not adjusted for multiplicity, and it does not replace or
alter any of the four adjusted verdicts in the table above. Its only purpose is to show that the home
range difference does not depend on that single large value: the gap between the groups is in the same
direction with the animal in the data and with it removed.

## Ecological conclusion

In this fox population, city living goes with a much smaller area to patrol and a higher faecal
cortisol level, while body size for length and the variety of food in the scat look about the same as
in the farmland. A plausible reading is that urban food is dense and predictable enough that a fox can
meet its needs on roughly a third of the ground a farmland fox covers, and that it can do so without
paying a cost in condition or in a narrower diet. The higher cortisol fits the idea that the city
brings its own pressures, such as traffic, people, dogs and crowding, even where food is easy. These
are observational comparisons between two trapping areas, not an experiment, so they describe a
difference between city and farmland foxes rather than proving that the city caused it.
