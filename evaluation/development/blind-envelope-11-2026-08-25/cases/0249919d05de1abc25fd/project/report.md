# Grafting greenhouse cucumber onto a vigorous squash rootstock: results of one twelve-week production cycle

## Question and design

We wanted to know whether grafting our standard commercial cucumber variety onto
a vigorous interspecific squash rootstock changes how the crop performs, compared
with growing the same variety on its own roots. Sixty plants were raised in a
single glasshouse compartment under one climate and irrigation regime, so the
only thing that differs between the two sets of plants is how they were
propagated. Thirty plants were grafted and thirty were self-rooted. Propagation
method is the two-level grouping factor and it is the only factor in the trial.

Each plant was followed individually through one twelve-week production cycle and
measured on its own. Eight outcomes were declared in the trial plan before
planting, and they are examined here in that declared order. The first three are
the yield outcomes, and those are the headline results of the trial.

## Data description

The data live in one file, `cucumber_grafting_trial.csv`. **One row is one
cucumber plant**, carrying that plant's identifier, its eight declared cycle-end
measurements, and the propagation method it belongs to. There are 60 data rows
plus a header row, 10 columns, and no missing cells. Rows are in bench recording
order, so the two propagation methods are interleaved rather than blocked.

| # | Column | Unit | What it holds |
| --- | --- | --- | --- |
| 1 | `plant_id` | none | Plant label, `CU-001` through `CU-060`, one per row. |
| 2 | `marketable_yield_kg` | kilograms | Total mass of marketable fruit harvested from that plant across the cycle. |
| 3 | `marketable_fruit_count` | count | Number of marketable fruits harvested from that plant across the cycle. |
| 4 | `mean_fruit_mass_g` | grams | Average fresh mass of that plant's marketable fruit. |
| 5 | `stem_diameter_mm` | millimetres | Stem diameter 20 cm above the graft union, or the same height on self-rooted plants. |
| 6 | `leaf_chlorophyll_index` | unitless | Handheld chlorophyll meter reading taken on that plant. |
| 7 | `root_dry_mass_g` | grams | Dry mass of that plant's root system, weighed after the cycle ended. |
| 8 | `soluble_solids_brix` | degrees Brix | Soluble solids content of that plant's fruit. |
| 9 | `days_to_first_harvest` | days | Days from planting to that plant's first harvested fruit. |
| 10 | `propagation_method` | none | Grouping factor with exactly two values, `grafted` or `self_rooted`, 30 rows each. |

Columns 2 through 9 are the eight declared outcomes in their declared order.

## Per-group summary

Thirty plants in each group, with no plant dropped for any outcome. Spread is the
standard deviation across plants within the group.

| Outcome | Grafted n | Grafted mean | Grafted SD | Self-rooted n | Self-rooted mean | Self-rooted SD |
| --- | --- | --- | --- | --- | --- | --- |
| Marketable yield (kg) | 30 | 6.38 | 0.95 | 30 | 5.45 | 0.95 |
| Marketable fruit count | 30 | 22.00 | 2.56 | 30 | 19.23 | 2.99 |
| Mean fruit mass (g) | 30 | 291.19 | 24.69 | 30 | 282.82 | 21.58 |
| Stem diameter (mm) | 30 | 11.80 | 1.19 | 30 | 10.53 | 1.15 |
| Leaf chlorophyll index | 30 | 48.91 | 3.13 | 30 | 44.12 | 4.40 |
| Root dry mass (g) | 30 | 23.52 | 4.84 | 30 | 17.76 | 5.00 |
| Soluble solids (Brix) | 30 | 3.61 | 0.40 | 30 | 3.40 | 0.38 |
| Days to first harvest | 30 | 40.97 | 2.28 | 30 | 43.43 | 2.40 |

## How the comparisons were made

Every declared outcome was compared between grafted and self-rooted plants with a
two-sample t-test, which is the standard test for a continuous measurement
compared across two independent groups. Eight comparisons were run in total, one
per declared outcome.

The first three outcomes, marketable yield, marketable fruit count and mean fruit
mass, are the headline yield results of this trial, so we held them to a stricter
standard. Each of those three p-values was multiplied by the number of
comparisons run, eight, and capped at one, and the resulting corrected value was
judged against the conventional 0.05 threshold. The remaining five declared
outcomes were each judged on their own raw p-value against the same 0.05
threshold.

## Conclusions by outcome, in declared order

**1. Marketable fruit yield per plant (headline yield outcome).** Grafted plants
averaged 6.38 kg against 5.45 kg on own roots, a gain of about 0.94 kg per plant.
Raw p = 0.00032, corrected p = 0.0026. **Grafted plants differ significantly from
self-rooted plants**, and this holds up under the stricter headline standard.

**2. Number of marketable fruits per plant (headline yield outcome).** Grafted
plants set 22.0 fruits on average against 19.2 on own roots. Raw p = 0.00030,
corrected p = 0.0024. **Grafted plants differ significantly from self-rooted
plants**, again under the stricter headline standard.

**3. Mean fruit fresh mass (headline yield outcome).** Grafted fruit averaged
291.2 g against 282.8 g on own roots, a difference of roughly 8 g on fruit of
nearly 290 g. Raw p = 0.167, corrected p = 1.00. **No significant difference
between grafted and self-rooted plants.** The extra yield in outcome 1 therefore
comes from setting more fruits rather than from growing bigger ones.

**4. Stem diameter 20 cm above the graft union.** Grafted stems measured 11.80 mm
against 10.53 mm on own roots. Raw p = 0.000092. **Grafted plants differ
significantly from self-rooted plants.**

**5. Leaf chlorophyll index.** Grafted plants read 48.9 against 44.1 on own roots.
Raw p = 0.0000095. **Grafted plants differ significantly from self-rooted
plants.**

**6. Root system dry mass.** Grafted plants built 23.5 g of root against 17.8 g on
own roots, close to a third more root. Raw p = 0.000030. **Grafted plants differ
significantly from self-rooted plants.**

**7. Fruit soluble solids.** Grafted fruit read 3.61 Brix against 3.40 Brix on own
roots. Raw p = 0.0489. **Grafted plants differ significantly from self-rooted
plants**, though the gap of about 0.2 Brix is small enough that it is unlikely to
be noticed at the point of sale.

**8. Days from planting to first harvest.** Grafted plants reached first harvest
at 41.0 days against 43.4 days on own roots, about two and a half days earlier.
Raw p = 0.00014. **Grafted plants differ significantly from self-rooted plants.**

## What this means for the crop

Grafting onto the squash rootstock gave a clear production benefit in this
compartment. Yield per plant and fruit number, the two headline results that
carried, both moved in favour of the grafted plants, and both are decided on the
stricter corrected values rather than the raw ones. Individual fruit size was
essentially unchanged, so the extra kilograms come from more fruit on the plant
rather than from heavier fruit.

The five remaining declared outcomes each stand on their own and each showed a
difference. The grafted plants carried thicker stems, greener leaves and
substantially more root, and they came into harvest about two and a half days
sooner. Fruit soluble solids were slightly higher on grafted plants, which is
worth noting mainly because a grafted crop is sometimes assumed to lose eating
quality; nothing here suggests that happened.

Taken together, the picture is consistent: a more vigorous root system supporting
a more productive canopy, which sets more fruit, sets it sooner, and does so
without shrinking the fruit or thinning it out.
