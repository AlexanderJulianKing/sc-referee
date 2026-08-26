# Cotton within-row planting density: plant-level outcomes at harvest

## Data

The analysis uses `cotton_density_plants.csv`, which holds 48 data rows and one
header row. **One row is one sampled cotton plant, measured once at harvest.**
Each plant was grown at a single research farm at one of two within-row planting
densities and belongs to exactly one density group: 24 plants at the
conventional density (about 10 plants per metre of row) and 24 at the high
density (about 15 plants per metre of row). No plant is measured twice, and
every cell is filled.

| Column | Meaning | Unit |
| --- | --- | --- |
| `plant_id` | Identifier for the sampled plant (`P001`-`P048`), unique across the file | none |
| `planting_density` | Density group the plant was grown at: `conventional` (~10 plants/m of row) or `high` (~15 plants/m of row) | none |
| `bolls_per_plant` | Declared outcome 1: harvestable bolls counted on the plant | count of bolls |
| `lint_yield_g` | Declared outcome 2: lint yield of the plant after ginning | grams |
| `upper_half_mean_length_mm` | Declared outcome 3: upper half mean fibre length, the average length of the longer half of the fibres | millimetres |
| `micronaire` | Declared outcome 4: micronaire, an air-flow reading of fibre fineness and maturity | unitless |
| `plant_height_cm` | Declared outcome 5: height from the soil surface to the terminal | centimetres |
| `first_fruiting_branch_node` | Declared outcome 6: node on the main stem carrying the first fruiting branch, counted up from the cotyledonary node | node number (count) |

## Method

`analysis.py` reads the CSV and works through the six declared outcomes in the
order they were declared in the trial protocol. Every outcome gets the same
comparison: a Welch two-sample t-test between the conventional and the high
density group. For each outcome the script prints the two group sizes, the two
group means, the t statistic and the p-value. Each declared outcome is a
separate agronomic question, so each one is judged on its own at the
conventional threshold of p < 0.05.

## Results

Both groups have n = 24 for every outcome.

| Declared outcome | Mean, conventional | Mean, high | Difference (high - conv.) | t | p | Verdict at 0.05 |
| --- | --- | --- | --- | --- | --- | --- |
| 1. `bolls_per_plant` | 17.125 | 15.583 | -1.542 | 2.7267 | 0.0091 | significant |
| 2. `lint_yield_g` | 33.083 | 29.246 | -3.838 | 3.9178 | 0.0003 | significant |
| 3. `upper_half_mean_length_mm` | 29.088 | 29.090 | +0.002 | -0.0096 | 0.9924 | not significant |
| 4. `micronaire` | 4.532 | 4.366 | -0.166 | 2.5209 | 0.0153 | significant |
| 5. `plant_height_cm` | 105.458 | 111.875 | +6.417 | -4.7500 | 0.0000 | significant |
| 6. `first_fruiting_branch_node` | 7.125 | 7.375 | +0.250 | -1.5560 | 0.1266 | not significant |

The p-value for plant height rounds to 0.0000 in the printed table; its full
value is 2.08e-05. The p-value for lint yield is 0.000295.

### Outcome 1: bolls per plant

Plants at the high density carried 1.54 fewer harvestable bolls on average
(17.13 versus 15.58 bolls), and the difference is significant at 0.05
(p = 0.0091). Agronomically this is the expected crowding response: with 15
plants per metre of row instead of 10, each plant has less light and less room,
so it sets and keeps fewer bolls. This is a per-plant loss, not a per-hectare
loss, because there are half again as many plants in the same length of row.

### Outcome 2: lint yield per plant

Lint yield per plant fell by 3.84 g at the high density (33.08 g versus
29.25 g), a significant difference (p = 0.0003). This is the yield consequence
of the boll count above, and it is the largest relative drop among the six
outcomes at about 12 percent of the conventional mean. Whether it costs the
grower anything depends on stand count: the extra plants in a row can more than
repay a 12 percent per-plant deficit, but this trial measured plants, not plots,
so it cannot settle that on its own.

### Outcome 3: upper half mean fibre length

The two densities are indistinguishable on fibre length (29.088 mm versus
29.090 mm, p = 0.9924). The verdict at 0.05 is not significant, and the observed
gap of 0.002 mm is far below anything a classing office or a spinner would act
on. Fibre length in cotton is strongly variety-driven, so a density change of
this size leaving it untouched is agronomically unsurprising, and it is good
news: crowding the crop did not cost fibre length.

### Outcome 4: micronaire

Micronaire was lower at the high density (4.53 versus 4.37, p = 0.0153),
a significant difference. Lower micronaire means finer or less mature fibre,
consistent with more plants competing for the assimilate that fills the fibre
wall late in the season. Both group means sit in the range mills accept, and
readings well above 4.5 are the ones that attract discounts, so the shift here
runs in a favourable direction rather than a harmful one. The concern at still
higher densities, or in a shorter season, would be micronaire falling far enough
to be discounted for immaturity instead.

### Outcome 5: plant height

High-density plants were 6.42 cm taller (105.46 cm versus 111.88 cm), the
strongest result in the family (p = 2.08e-05). This is a classic shade-avoidance
response: crowded plants detect their neighbours and put growth into stem
elongation. Taller, more slender plants matter for management, because they
raise the risk of lodging and usually mean a heavier or better-timed plant
growth regulator programme is needed at the high density.

### Outcome 6: node of the first fruiting branch

The first fruiting branch sat 0.25 nodes higher on average at the high density
(7.13 versus 7.38 nodes), and the difference is not significant at 0.05
(p = 0.1266). A quarter of a node is also below what field scouting can reliably
resolve. The practical reading is that the higher density did not delay the
start of fruiting up the main stem: the crop began setting fruit at effectively
the same node in both treatments.

## Conclusion and recommendation

Four of the six declared outcomes separated the two densities at the 0.05
threshold. The high density produced fewer bolls and less lint per plant, finer
fibre by micronaire, and noticeably taller plants. Fibre length and the node of
the first fruiting branch were unchanged.

The picture is coherent. Crowding shifts each individual plant toward more stem
and less fruit, without harming the fibre quality traits that determine grade.

**Recommendation for growers.** On fields resembling this one, the conventional
density of about 10 plants per metre of row remains the sound default, and it is
what we recommend for growers who cannot add a plant growth regulator pass or
who farm ground prone to rank growth and lodging. Moving to about 15 plants per
metre is worth trialling where the extra stand can be managed, since the
per-plant penalties here are moderate and quality was not degraded. This trial
measured individual plants rather than plot yield, so it cannot show whether the
extra plants pay for the per-plant loss. Growers considering the high density
should budget for a stronger growth regulator programme to hold plant height,
and should confirm the economics with a plot-level yield trial before changing
seeding rate across a whole farm.
