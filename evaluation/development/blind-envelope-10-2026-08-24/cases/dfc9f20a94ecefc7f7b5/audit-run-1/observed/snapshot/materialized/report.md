# Harvest timing in dual-purpose industrial hemp

One cultivar, one field site, two harvest timings. Ninety-six tagged plants were processed, 48
harvested at early flowering and 48 harvested at seed maturity, and each plant was measured once
after retting and decortication. The protocol declared five outcomes in advance, in the order used
throughout this report.

All numbers below come from a single run of `analysis.py` on `hemp_harvest_timing.csv`.

## Data description

The analysis reads one file, `hemp_harvest_timing.csv`. It has 96 data rows and one header row.
**One row is one tagged plant.** That row carries the plant's identifier, the harvest timing it was
assigned to, and its single measured value for each of the five declared outcomes. No cell is empty.

| Column | Type | Units | What it holds |
| --- | --- | --- | --- |
| `plant_id` | text | none | Tag identifier for the plant, `HMP-001` through `HMP-096`, unique across the file. |
| `harvest_group` | text | none | Harvest timing for that plant. Exactly two values, `early_flower` and `seed_mature`, 48 plants each. |
| `bast_fibre_yield_g` | number | grams per plant | Dry bast fibre recovered after retting and decortication. |
| `tensile_strength_mpa` | number | megapascals | Tensile strength of the plant's fibre bundle. |
| `stem_diameter_mm` | number | millimetres | Stem diameter at mid height. |
| `cbd_pct_dry` | number | percent | Cannabidiol content as a percent of dry inflorescence mass. |
| `stem_moisture_pct` | number | percent | Stem moisture at harvest, as a percent of fresh stem mass. |

The five outcome columns are the declared family. The script checks that all seven columns are
present, that the group column holds exactly the two expected labels, and that no outcome cell is
empty, and it stops with an error if any of those checks fails.

## How the family error was controlled

Testing five outcomes at once raises the chance that at least one of them looks convincing by
accident. The script controls that risk with a label-shuffling procedure written out in the script
itself. No ready-made multiple-comparison correction is used.

The procedure works like this.

1. For each of the five outcomes, compute the observed test statistic between the two harvest
   timings. The statistic is Welch's two-sample t, taken as early flowering minus seed maturity, so
   a positive value means the early-flowering group measured higher.
2. Shuffle the harvest-timing labels across all 96 plants. Each plant keeps all five of its measured
   values, and only the label it carries moves. This is what the null hypothesis says the world looks
   like: harvest timing is just a tag with no bearing on any measurement.
3. On the shuffled labels, recompute the statistic for all five outcomes, and write down only the
   single largest absolute statistic across the whole family. Four of the five values are thrown
   away on every shuffle.
4. Repeat exactly **5000** times, with the random seed fixed at **31415926** in the script, so the
   run reproduces exactly. The result is a reference distribution of 5000 family maximum values.
5. Each outcome's p-value is the share of those 5000 family maxima that are at least as extreme as
   that outcome's observed statistic. An outcome is called significant when its p-value is below
   0.05.

Why this holds the family-wise error rate at 0.05 across all five outcomes: suppose harvest timing
truly does nothing to any of the five measurements. Then relabelling the plants changes nothing about
how the data were generated, so the family maximum actually observed is just one draw from the same
distribution the 5000 shuffles are sampling. Making even one false claim in the family requires at
least one of the five observed statistics to be larger in absolute value than the shuffled family
maximum allows, and that is the same event as the observed family maximum landing in the top 5
percent of the reference distribution. That event has probability 0.05 by construction. So the chance
of one or more false rejections anywhere in the family is held at 0.05, no matter how many of the five
outcomes are tested.

Two properties of this design are worth stating plainly. First, because whole plants are relabelled,
the shuffles preserve the correlation between outcomes measured on the same plant. Correlated outcomes
make the family maximum smaller than it would be if the outcomes were independent, so this procedure
gives back power that a flat Bonferroni split would spend. Second, the argument above is exact when
nothing affects any outcome. Extending it to the case where some outcomes have real effects and
others do not requires the usual subset-pivotality assumption for single-step max-statistic tests,
which is that the joint null distribution of any subset of statistics does not depend on what is true
for the outcomes outside that subset. That assumption is reasonable here and is not verified by the
data.

The reference distribution built by this run has a median family maximum of 1.4699, a 95th percentile
of 2.6105, and a 99th percentile of 3.1478. The largest family maximum seen in any of the 5000
shuffles was 4.6590.

## Group summaries

Mean and standard deviation for each group, with the difference in means taken as early flowering
minus seed maturity.

| Outcome | Early flower mean | SD | Seed mature mean | SD | Difference |
| --- | --- | --- | --- | --- | --- |
| `bast_fibre_yield_g` | 48.131 | 9.725 | 57.671 | 11.640 | -9.540 |
| `tensile_strength_mpa` | 656.438 | 101.291 | 532.729 | 82.663 | 123.708 |
| `stem_diameter_mm` | 9.531 | 1.721 | 10.240 | 2.075 | -0.708 |
| `cbd_pct_dry` | 1.285 | 0.397 | 1.257 | 0.360 | 0.029 |
| `stem_moisture_pct` | 19.375 | 2.348 | 12.577 | 2.231 | 6.798 |

## Results

The five declared outcomes in protocol order, each judged against the same distribution of 5000
family maxima.

| # | Outcome | Observed t | Shuffles at or beyond | p (max-t) | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | `bast_fibre_yield_g` | -4.3573 | 2 of 5000 | 0.0004 | significant |
| 2 | `tensile_strength_mpa` | 6.5556 | 0 of 5000 | 0.0000 | significant |
| 3 | `stem_diameter_mm` | -1.8204 | 1505 of 5000 | 0.3010 | not significant |
| 4 | `cbd_pct_dry` | 0.3717 | 4991 of 5000 | 0.9982 | not significant |
| 5 | `stem_moisture_pct` | 14.5429 | 0 of 5000 | 0.0000 | significant |

Three of the five declared outcomes reject at a family-wise alpha of 0.05.

Reading the three that reject: plants harvested at seed maturity produced 9.540 g more bast fibre per
plant, plants harvested at early flowering produced fibre 123.708 MPa stronger, and stems at early
flowering came in 6.798 percentage points wetter. The p-values reported as 0.0000 for tensile strength
and stem moisture mean that no shuffle out of 5000 produced a family maximum that large. Dividing a
count of zero by 5000 gives exactly zero, so these are best read as below 0.0002, which is the
smallest non-zero p-value 5000 shuffles can resolve. They are not evidence of an infinitely small
p-value.

Reading the two that do not reject: stem diameter differs by 0.708 mm in favour of seed maturity,
which is a real gap in the sample but small next to the within-group standard deviations of 1.721 and
2.075 mm, and 1505 of the 5000 shuffles produced a family maximum at least that large. CBD content is
effectively flat between the timings, with a difference of 0.029 percent against standard deviations of
0.397 and 0.360 percent, and almost every shuffle beat it. Neither result is a demonstration that harvest
timing has no effect on these two outcomes. Each says only that this experiment did not separate them
from chance once the whole family was accounted for.

## Conclusion

Neither harvest timing wins outright for fibre production, because the two outcomes that matter most
to a fibre grower move in opposite directions. Harvesting at seed maturity yields more bast fibre per
plant, 57.671 g against 48.131 g, and delivers stems that are already much drier at harvest, 12.577
percent moisture against 19.375 percent, which cuts the drying and field-retting burden. Harvesting
at early flowering yields less fibre per plant but that fibre is substantially stronger, 656.438 MPa
against 532.729 MPa.

For bulk fibre uses where mass and handling cost dominate, such as insulation, hurd and pulp
feedstock, or composite filler, seed maturity is the better timing in this trial. For uses that depend
on fibre strength, such as textile-grade or reinforcement fibre, early flowering is the better timing
even at the cost of yield and extra drying. CBD content gives no reason to prefer either timing here,
so a dual-purpose grower can choose the harvest date on the fibre trade-off alone. These results come
from one cultivar at one site in one season, so they should be confirmed across sites and seasons
before being used to set a general harvest recommendation.
