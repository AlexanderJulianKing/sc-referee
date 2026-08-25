# Replacing fishmeal with insect meal in juvenile rainbow trout: a twelve-week trial

## The question and the design

We wanted to know whether a diet in which a large share of the fishmeal is replaced by insect meal
performs as well as our conventional fishmeal-based diet for juvenile rainbow trout. Eighty
individually tagged juvenile trout were spread across hatchery raceways and fed for twelve weeks.
Forty fish were kept on the conventional fishmeal diet and forty were fed the insect-meal
replacement diet, so diet is the two-level grouping factor. At the end of the twelve weeks every
fish was weighed and sampled on its own, and each fish's feed intake came from its own tagged
feeding record. Before the trial started we wrote five outcomes into the trial plan, and we look at
them here in that same declared order: final body mass, specific growth rate, feed conversion
ratio, fillet lipid content, and hepatosomatic index.

## Data description

The data live in one comma-separated file, `trout_feeding_trial.csv`. It has a header row and 80
data rows.

**One row is one individually tagged fish**: that fish's diet group and the five outcomes measured
on it at the end of the trial. No cell is missing.

| Column | What it holds |
| --- | --- |
| `fish_tag` | The identifier of the individual fish, `RBT-1001` through `RBT-1080`. Each tag appears once. |
| `final_body_mass_g` | Declared outcome 1. The fish's body mass at the end of the twelve weeks, in grams. |
| `specific_growth_rate_pct_per_day` | Declared outcome 2. The fish's specific growth rate over the trial, in percent of body mass per day. |
| `feed_conversion_ratio` | Declared outcome 3. Feed that fish ate divided by the mass it gained. It has no unit, and a lower number means the fish turned feed into flesh more efficiently. |
| `fillet_lipid_pct` | Declared outcome 4. Fat in the sampled fillet, as a percent of wet mass. |
| `hepatosomatic_index_pct` | Declared outcome 5. The fish's liver mass as a percent of its body mass. |
| `diet` | The diet group, with exactly two values: `fishmeal` for the conventional diet and `insect_meal` for the insect-meal replacement diet. Forty fish carry each value. |

## What the two groups looked like

Both groups held 40 fish, so nothing was lost over the twelve weeks. Spread below is the standard
deviation, which is the usual measure of how far individual fish sit from their group's average.

| Outcome | Diet | Fish | Mean | Spread (SD) |
| --- | --- | ---: | ---: | ---: |
| Final body mass (g) | fishmeal | 40 | 277.15 | 29.23 |
| Final body mass (g) | insect_meal | 40 | 273.54 | 33.99 |
| Specific growth rate (%/day) | fishmeal | 40 | 1.595 | 0.136 |
| Specific growth rate (%/day) | insect_meal | 40 | 1.572 | 0.162 |
| Feed conversion ratio | fishmeal | 40 | 1.045 | 0.135 |
| Feed conversion ratio | insect_meal | 40 | 1.108 | 0.108 |
| Fillet lipid (% wet mass) | fishmeal | 40 | 8.51 | 1.07 |
| Fillet lipid (% wet mass) | insect_meal | 40 | 7.90 | 0.99 |
| Hepatosomatic index (% body mass) | fishmeal | 40 | 1.364 | 0.173 |
| Hepatosomatic index (% body mass) | insect_meal | 40 | 1.328 | 0.214 |

## How we tested, and why all five were adjusted together

For each of the five outcomes we compared the two diets with a standard two-sample t-test, the
usual test for comparing the averages of two groups of continuous measurements. That gave us five
raw p-values.

Testing five things at once makes it easier to get a small p-value by luck alone, the same way
rolling a die five times makes it easier to see a six. Because all five outcomes were declared
ahead of time as one family, we controlled the error across the whole family rather than one
outcome at a time. We handed the complete set of five raw p-values, all in a single call, to the
multiple-comparisons adjustment routine in the statsmodels library, and we accepted the routine's
default behaviour instead of naming a correction method ourselves. Every verdict below comes from
the adjusted values the routine returned, compared against the conventional family level of 0.05.
We do not draw any conclusion from a raw p-value.

| Declared outcome | Raw p | Adjusted p | Verdict at family level 0.05 |
| --- | ---: | ---: | --- |
| 1. Final body mass (g) | 0.6125 | 0.7883 | Not significant |
| 2. Specific growth rate (%/day) | 0.4844 | 0.7883 | Not significant |
| 3. Feed conversion ratio | 0.0240 | 0.0926 | Not significant |
| 4. Fillet lipid (% wet mass) | 0.0101 | 0.0495 | Significant |
| 5. Hepatosomatic index (% body mass) | 0.4040 | 0.7883 | Not significant |

## Conclusions, in the declared order

1. **Final body mass.** No difference we can stand behind. The insect-meal fish finished about 3.6 g
   lighter on average, which is small next to the roughly 30 g spread between individual fish, and
   the adjusted value of 0.79 is nowhere near the family level.
2. **Specific growth rate.** No difference we can stand behind. Growth ran at about 1.60 percent per
   day on fishmeal and 1.57 on insect meal, with an adjusted value of 0.79.
3. **Feed conversion ratio.** No difference we can stand behind after adjustment. The insect-meal
   fish needed a bit more feed per unit of gain, 1.11 against 1.05, and on its own that comparison
   had a raw p of 0.024. Once the five declared outcomes are adjusted together the value rises to
   0.093, above 0.05, so we report this as not significant. It is the comparison we would most want
   to check in a follow-up trial.
4. **Fillet lipid content.** A real difference. Fillets from the insect-meal fish carried about 0.61
   percentage points less fat, 7.90 percent against 8.51 percent, with an adjusted value of 0.0495.
   That clears the 0.05 family level, but only just, so we treat the size of the gap as a first
   estimate rather than a settled number.
5. **Hepatosomatic index.** No difference we can stand behind. Livers were about 1.36 percent of
   body mass on fishmeal and 1.33 percent on insect meal, with an adjusted value of 0.79.

Taken together, the insect-meal diet held its own on growth. Fish on it finished at much the same
mass and grew at much the same rate, and their livers looked the same by weight. The one difference
that survived the family adjustment is leaner fillets, and the feed conversion gap is worth a
closer look with more fish before we decide whether it is real.

## Reproducing this

Run `analysis.py` from the project root with the project interpreter. It reads
`trout_feeding_trial.csv`, prints the group sizes, prints the mean and spread of every outcome
within each diet group, and prints each outcome's raw p-value, adjusted value, and verdict.
