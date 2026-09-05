# Deficit irrigation in quinoa: five declared outcomes from a single common-garden harvest

## Question and design

I wanted to know what happens to a quinoa crop when it loses about half its water from the
start of flowering onward. Not just to yield, which is the obvious place to look, but to the
grain quality and the plant water status that go with it.

Sixty-four individually potted plants of one quinoa accession were grown outdoors in a common
garden, all on the same substrate and all sown on the same day. Thirty-two pots stayed on full
irrigation and thirty-two went onto deficit irrigation, receiving roughly half the water from
the beginning of flowering. Irrigation regime is the only thing I varied; it is a two-level
grouping factor with 32 plants per level. Every plant was harvested and measured on its own,
so each plant contributes one independent record.

Before flowering I wrote down five outcomes in the experimental plan and fixed their order.
That list did not change afterwards. The five, in the declared order, are seed yield per plant,
thousand-seed weight, plant height at harvest, seed saponin content, and midday leaf water
potential. Because I am asking five questions of one experiment, the chance of at least one
false alarm is higher than the chance for any single test, so all five are judged together
under one family-wise error rate of 0.05. The method is described below.

## Data description

The analysis input is `harvest_records.csv`. It has a header row and 64 data rows, no missing
cells.

**What one row represents:** one individually potted quinoa plant. A row holds that plant's pot
tag, its five measured outcomes, and the irrigation regime its pot was assigned.

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `plant_id` | text | none | Pot tag, `QNA-001` through `QNA-064`. Unique for every row. |
| `seed_yield_g` | number | grams | Total cleaned seed harvested from that plant, to 0.1 g. |
| `thousand_seed_weight_g` | number | grams | Weight of one thousand seeds from that plant's harvest, to 0.01 g. This is the individual-seed size measure. |
| `plant_height_cm` | number | centimetres | Substrate surface to the top of the panicle at harvest, to 0.1 cm. |
| `seed_saponin_mg_g` | number | mg per g | Saponin content of that plant's seed, to 0.01 mg/g. Saponin is the bitter coating on the grain. |
| `midday_leaf_water_potential_mpa` | number | megapascals | Midday leaf water potential, recorded as a positive tension, to 0.01 MPa. A bigger number means the leaf was pulling harder on its water, so the plant was more stressed. |
| `irrigation_regime` | text | none | The watering regime for that pot. Exactly two values, `full` and `deficit`, 32 rows each. |

The five outcome columns appear in the file in the order the outcomes were declared.

## Per-group summary

Spread is the sample standard deviation across the 32 plants in that group.

| Outcome | Group | n | Mean | SD |
| --- | --- | --- | --- | --- |
| `seed_yield_g` | full | 32 | 23.797 | 4.410 |
| `seed_yield_g` | deficit | 32 | 18.159 | 4.147 |
| `thousand_seed_weight_g` | full | 32 | 3.006 | 0.493 |
| `thousand_seed_weight_g` | deficit | 32 | 2.789 | 0.391 |
| `plant_height_cm` | full | 32 | 115.828 | 10.433 |
| `plant_height_cm` | deficit | 32 | 100.575 | 11.022 |
| `seed_saponin_mg_g` | full | 32 | 4.526 | 1.298 |
| `seed_saponin_mg_g` | deficit | 32 | 5.302 | 1.199 |
| `midday_leaf_water_potential_mpa` | full | 32 | 1.177 | 0.342 |
| `midday_leaf_water_potential_mpa` | deficit | 32 | 1.774 | 0.309 |

## How the label-shuffling test works

For each outcome I first computed the observed two-group test statistic, a Welch two-sample
*t* comparing full irrigation with deficit irrigation. I write it as full minus deficit, so a
positive value means the fully watered plants were higher on that measure.

The question is what those numbers would look like if irrigation made no difference at all to
anything. Under that null, the label on a pot is just a tag, and any other assignment of 32
`full` tags and 32 `deficit` tags to the same 64 plants would have been equally likely. So I
build the reference distribution by acting that out. On each round I take the 64 irrigation
labels, shuffle them across the plants, and recompute the *t* statistic for all five outcomes
on the shuffled labels. One shuffle is applied to the whole plant, not a separate shuffle per
outcome, which keeps the natural correlation among the five measures intact: a big vigorous
plant is tall and fills seed at the same time, and that link survives the shuffling exactly as
it exists in the real harvest.

Then comes the step that does the multiplicity work. From each shuffled round I keep only
**the largest of the five statistics in absolute size** and throw the other four away. The
result is a distribution not of "how big is one statistic under the null" but of "how big is
the biggest thing anywhere in this family of five under the null". I did this
**exactly 5,000 times**, a count fixed before the analysis ran, under a fixed random seed so
the whole run reproduces.

Why the maximum controls the family-wise error rate: a family-wise false positive is the event
that *at least one* of my five declared outcomes gets called significant when in truth nothing
is going on. At least one of five exceeding a threshold is the same event as the biggest of the
five exceeding that threshold. So if I set the threshold at the 95th percentile of the
family-maximum distribution, then under a complete null only 5% of experiments would produce
any statistic anywhere in the family big enough to clear it. That 5% is the error rate for the
whole set of five, not for each test separately, which is exactly what I want when five
questions come out of one experiment. Each outcome is judged against this shared family-maximum
reference, never against a reference built from its own outcome alone; an outcome that would
look impressive against its own null has to clear the higher bar set by the noisiest member of
the family. A further point in favour of shuffling here: because the five outcomes are
positively correlated on this dataset, the family maximum is less extreme than it would be for
five unrelated measures, and the shuffling picks that dependence up automatically instead of
assuming the worst as a formula-based correction would.

For this dataset the family-maximum reference had a median of 1.474 and a maximum of 4.419
across the 5,000 shuffles, giving a family-wise critical value of 2.594 at the 95th percentile.
Family-wise p-values use the add-one estimator, counting the observed labelling as one of the
possible assignments, so the smallest value reportable from 5,000 shuffles is 1/5001 = 0.0002.

## Conclusions, in the declared order

**1. Seed yield per plant (`seed_yield_g`): significant.** Observed *t* = +5.268, family-wise
p = 0.0002 (0 of 5,000 family maxima reached it). Deficit-irrigated plants yielded 18.16 g
against 23.80 g under full irrigation, a loss of about 5.6 g per plant, near a quarter of the
crop. Halving the water from flowering costs real grain.

**2. Thousand-seed weight (`thousand_seed_weight_g`): not significant.** Observed *t* = +1.954,
family-wise p = 0.2232 (1,115 of 5,000 family maxima were at least this large). The means were
3.01 g and 2.79 g, a difference of about 0.22 g that this experiment cannot separate from
plant-to-plant variation once the whole family of five is accounted for. Read together with the
yield result, this suggests the yield loss came mostly through fewer seeds rather than through
each seed being lighter, though I did not count seeds and so cannot test that directly here.

**3. Plant height at harvest (`plant_height_cm`): significant.** Observed *t* = +5.686,
family-wise p = 0.0002 (0 of 5,000). Deficit plants finished at 100.6 cm against 115.8 cm,
about 15 cm shorter. The stress shows plainly in the vegetative frame.

**4. Seed saponin content (`seed_saponin_mg_g`): not significant.** Observed *t* = -2.483,
family-wise p = 0.0680 (339 of 5,000). Saponin ran higher under deficit irrigation, 5.30 mg/g
against 4.53 mg/g, and the direction matches the expectation that stressed plants make bitterer
grain. But at 0.068 it sits just outside the 0.05 family-wise threshold. I am not calling this
one. It is the outcome I would target with a larger or repeated trial, because a genuine
bitterness penalty on deficit-irrigated grain would matter commercially.

**5. Midday leaf water potential (`midday_leaf_water_potential_mpa`): significant.** Observed
*t* = -7.327, family-wise p = 0.0002 (0 of 5,000). Deficit plants sat at 1.77 MPa of tension
against 1.18 MPa under full irrigation. This is the strongest signal in the family and it is
the one I would expect to be, since it measures the treatment's immediate physiological effect
rather than a downstream consequence of it. It also confirms the deficit treatment did what it
was supposed to do to the plants.

Three of the five declared outcomes clear the 0.05 family-wise bar: the plants were visibly
more stressed, they grew shorter, and they yielded less. Individual seed weight and seed
saponin did not clear it in this experiment.

## Reproducing the analysis

Run `python analysis.py` from the project root with `harvest_records.csv` beside it. The seed
is fixed in the script, so the 5,000 shuffles and every number above come out identical on a
re-run.
