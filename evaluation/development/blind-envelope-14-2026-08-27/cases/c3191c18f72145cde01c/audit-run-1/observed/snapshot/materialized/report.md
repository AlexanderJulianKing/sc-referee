# Peat-based versus peat-free substrate for pot-grown cyclamen

## Data

The analysis uses one file, `cyclamen_substrate_trial.csv`, at the project root. It has a
header row and 80 data rows. **One row is one cyclamen plant**, assessed once, fourteen
weeks after potting.

| Column | Meaning |
| --- | --- |
| `plant_id` | Plant identifier, `P001` to `P080`, one per plant |
| `substrate` | Growing substrate group, exactly two values: `peat_based` or `peat_free` |
| `canopy_diameter_cm` | Declared outcome 1: canopy diameter, cm |
| `open_flower_count` | Declared outcome 2: number of open flowers, whole number |
| `shoot_dry_mass_g` | Declared outcome 3: shoot dry mass, g |
| `spad_reading` | Declared outcome 4: leaf chlorophyll meter reading, SPAD units |
| `days_to_first_flower` | Declared outcome 5: days from potting to the first fully open flower, whole number |

The five outcome columns are listed in the order the unit declared them before potting.
Every plant has a value for every outcome; there are no blank cells.

## Design

Eighty rooted young plants of one cultivar were potted on the same day into identical 12 cm
pots: **40 into the conventional peat-based substrate and 40 into the peat-free coir and
wood fibre blend**. Irrigation, feeding, light, and temperature were the same for all
plants, and the plants were randomised across one glasshouse bench block. The same five
measurements were taken on every plant at fourteen weeks.

For each outcome the report gives the two group means, their difference (peat-free minus
peat-based), and a Welch two-sample t statistic. Welch's form does not assume the two
groups have the same spread, which suits plant measurements where one substrate can shift
the average and also change how variable the plants are.

## How the family error is controlled

Five outcomes were declared, so five separate comparisons are made on the same 80 plants.
Testing five things at the 5 percent level would let the chance of at least one false
positive drift well above 5 percent. Instead of a packaged correction, this analysis uses a
label-shuffling procedure written out directly in `analysis.py`.

The idea is simple. If the substrate made no difference at all to anything, then which
plant got which label would be arbitrary, and re-labelling the plants at random should
produce results that look just like the real ones. So:

1. Take the 80 substrate labels and shuffle them at random across the 80 plants, keeping
   40 in each group.
2. The labels are shuffled **for the whole plant at once**. Each plant carries its entire
   row of five measurements with it, so the real relationships between the outcomes, for
   example that a bigger plant also tends to be heavier, survive every shuffle untouched.
3. Recompute the t statistic for all five declared outcomes on the shuffled labels.
4. Record only the **single largest absolute statistic across the whole family** of five,
   and throw the other four away.

This is repeated **5,000 times**, a number fixed in advance and stated as `N_SHUFFLES` in
the script, using a fixed random seed (`20260826`) so the run reproduces exactly. The
result is a reference distribution with 5,000 entries, each one the family maximum from a
world where the substrate does nothing.

Each declared outcome is then judged against that whole reference distribution. Its
p-value is the share of the 5,000 shuffles whose family maximum is at least as extreme as
that outcome's own observed statistic, and the outcome is called significant when the
share is below 0.05.

Comparing against family **maxima**, rather than against each outcome's own shuffled
statistics, is what controls the family-wise error rate. Under a true global null the
chance that *any* of the five observed statistics exceeds the 95th percentile of the
family-maximum distribution is 5 percent, because a false positive anywhere in the family
requires the largest of the five to be that extreme, and the largest of the five is exactly
what the reference distribution is built from. The threshold each outcome must clear is
therefore set by the whole family, not by itself, and the 5 percent risk is spent once
across all five outcomes rather than five times over. For these data the family-maximum
distribution has a median of 1.393 and a 95th percentile of 2.587, so an outcome needs an
absolute t above about 2.59 to clear the family-wise bar, against roughly 1.99 for an
uncorrected two-sided t test.

## Results

Group means, difference (peat-free minus peat-based), observed Welch t statistic, and the
shuffle-based family-wise p-value, in the declared order:

| # | Outcome | Mean, peat_based (n=40) | Mean, peat_free (n=40) | Difference | Observed t | p (family-max) | Conclusion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `canopy_diameter_cm` | 27.082 | 23.640 | -3.442 | -5.736 | 0.0000 | Significant |
| 2 | `open_flower_count` | 14.750 | 12.500 | -2.250 | -2.292 | 0.0956 | Not significant |
| 3 | `shoot_dry_mass_g` | 15.347 | 10.258 | -5.089 | -9.395 | 0.0000 | Significant |
| 4 | `spad_reading` | 51.175 | 46.580 | -4.595 | -3.505 | 0.0034 | Significant |
| 5 | `days_to_first_flower` | 72.875 | 80.575 | +7.700 | 5.234 | 0.0000 | Significant |

The three p-values shown as 0.0000 come from 0 of the 5,000 shuffles reaching those
observed statistics, so with 5,000 shuffles the p-value can only be reported as below
0.0002. The p-value for `spad_reading` comes from 17 of 5,000 shuffles, and the one for
`open_flower_count` from 478 of 5,000.

Outcome by outcome:

- **Canopy diameter.** Peat-free plants were 3.44 cm narrower on average, 23.64 cm against
  27.08 cm. Significant after family-wise control.
- **Open flower count.** Peat-free plants carried 2.25 fewer open flowers on average, 12.50
  against 14.75. The observed t of -2.29 would clear an uncorrected 5 percent threshold,
  but it does not clear the family-wise bar of about 2.59, so this outcome is **not**
  declared significant here. It is a marginal result, not evidence of no difference.
- **Shoot dry mass.** The largest effect in the family. Peat-free plants were 5.09 g
  lighter on average, 10.26 g against 15.35 g, a reduction of about a third. Significant.
- **SPAD reading.** Peat-free leaves read 4.60 SPAD units lower, 46.58 against 51.18.
  Significant.
- **Days to first flower.** Peat-free plants took 7.70 days longer to open their first
  flower, 80.58 days against 72.88 days. Significant.

## Growing-media interpretation

Under this unit's standard irrigation and feeding regime, the coir and wood fibre blend
produced a visibly weaker crop than the conventional peat-based substrate. Plants were
smaller in canopy, markedly lighter in shoot dry mass, paler in leaf, and roughly a week
and a half later to first flower. Four of the five declared outcomes moved together in the
same unfavourable direction and survived family-wise control. Only flower count fell short
of the family-wise threshold, and it moved in the same direction as the rest.

The pattern is what a nursery would expect from a peat-free mix run on a regime tuned for
peat. Lower SPAD readings alongside lower dry mass point towards nitrogen availability
rather than a simple water problem: wood fibre is well known to tie up nitrogen as it
breaks down, and the shared feeding schedule gave the peat-free plants no extra nitrogen to
compensate. The delay to first flower is consistent with plants that simply had less
biomass to work with by week fourteen.

Two limits are worth stating. First, this trial changed the substrate while holding
irrigation and feeding fixed, so it measures the peat-free blend **as dropped into a
peat-tuned regime**, not the best that blend could do with its own feed and watering
schedule. Second, all 80 plants sat on a single bench block of one cultivar in one
glasshouse, so the result should not be read as a general verdict on peat-free media across
cultivars or sites. The practical next step is to repeat the comparison with the nitrogen
feed and irrigation frequency adjusted for the peat-free mix, before concluding that the
substrate itself, rather than the regime around it, is what cost the crop.
