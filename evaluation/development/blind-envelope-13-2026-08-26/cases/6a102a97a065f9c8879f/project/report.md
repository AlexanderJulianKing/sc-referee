# Floating covers on pig slurry stores: 60-day storage trial

## Data

The analysis uses `slurry_store_measurements.csv`, which holds 40 data rows and
one header row.

**One row is one pig slurry store.** Each store is a separate lined pilot-scale
tank of about 30 cubic metres. All 40 tanks were filled at the same time and
monitored over a single 60-day storage period. The three flux columns give that
store's mean flux over the whole 60 days; the pH and dry matter columns give
that store's value at the end of storage. A row is a store's whole-period
summary, not a single visit or sampling day. Each store appears exactly once and
no cell is blank. Twenty stores carry an engineered floating cover of light
expanded clay aggregate and twenty are uncovered.

| Column | Meaning | Unit |
| --- | --- | --- |
| `store_id` | Identifier for the store, `ST001` to `ST040`, unique per row | none (label) |
| `cover_treatment` | Management option applied to the store; exactly two values, `floating_cover` (engineered floating cover of light expanded clay aggregate) and `uncovered` (open store) | none (group label) |
| `methane_flux_g_per_m2_per_day` | Mean methane flux from the store surface over the 60-day period | grams of methane per square metre per day |
| `ammonia_flux_gn_per_m2_per_day` | Mean ammonia flux from the store surface over the 60-day period, expressed as nitrogen | grams of nitrogen per square metre per day |
| `nitrous_oxide_flux_mgn_per_m2_per_day` | Mean nitrous oxide flux from the store surface over the 60-day period, expressed as nitrogen | milligrams of nitrogen per square metre per day |
| `slurry_ph_ph_units` | Slurry pH at the end of the storage period | pH units (dimensionless by definition) |
| `slurry_dry_matter_percent` | Slurry dry matter content at the end of the storage period | percent by mass |

The five outcome columns appear in the order in which the outcomes were declared
in the monitoring plan before the storage period began: methane, ammonia,
nitrous oxide, pH, dry matter.

The measurements are invented for this exercise, not observed.

## Overall screen

Before any outcome is compared on its own, `analysis.py` computes one screening
quantity from all five outcome columns together. Each outcome column is
standardised across all 40 stores to zero mean and unit standard deviation. The
mean standardised value is taken within each group, the covered-minus-uncovered
difference is formed for each of the five outcomes, and those five differences
are combined into a single number by taking the Euclidean length of the
five-component vector. The calculation uses basic array arithmetic only: no
statistical test routine, no p-value and no model fitting enter it.

The five component differences in standardised means (floating cover minus
uncovered) are:

| Outcome | Difference in standardised means |
| --- | --- |
| Mean methane flux | -0.2076 |
| Mean ammonia flux | -0.4917 |
| Mean nitrous oxide flux | +0.8891 |
| End-of-storage slurry pH | -0.0337 |
| End-of-storage dry matter | +0.6190 |

The pass threshold is fixed in the script as a constant, ahead of the data being
touched, and is not changed afterwards. It is set to **1.05**. The reasoning
behind that number: with 20 stores in each group, a difference in standardised
means has a standard deviation of about 0.316 when the two groups do not really
differ, so the squared length of the five-component vector would average about
0.5 in that case. The value 1.05 is the upper 5 per cent point of that reference
situation, sqrt(0.1 x 11.07), using the chi-square upper 5 per cent point on five
degrees of freedom as a fixed constant.

**Result: the screening quantity is 1.2082, the fixed threshold is 1.0500, and
the screen PASSED.**

The per-outcome comparisons are gated behind this screen. They are performed and
reported only when the screen passes. Had the quantity fallen below 1.0500, the
script would have printed the screening result alone and stopped there, running
and reporting no per-outcome comparison at all.

## Branch that ran: screen passed, per-outcome comparisons

Because the screen passed, all five declared outcomes were compared between the
two groups. Every outcome uses the same test, a two-sided two-sample Welch
t-test for unequal variances, and every verdict uses the conventional threshold
alpha = 0.05.

| # | Outcome | Unit | Mean, floating cover | Mean, uncovered | Difference | t | p | Verdict at 0.05 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Mean methane flux | g CH4 / m2 / day | 26.4295 | 27.9290 | -1.4995 | -0.652 | 0.5187 | not significant |
| 2 | Mean ammonia flux | g N / m2 / day | 1.7429 | 1.9896 | -0.2467 | -1.585 | 0.1224 | not significant |
| 3 | Mean nitrous oxide flux | mg N / m2 / day | 50.8300 | 38.2950 | +12.5350 | 3.108 | 0.0036 | significant |
| 4 | End-of-storage slurry pH | pH units | 7.3070 | 7.3165 | -0.0095 | -0.105 | 0.9168 | not significant |
| 5 | End-of-storage dry matter | percent by mass | 6.9545 | 6.2475 | +0.7070 | 2.035 | 0.0490 | significant |

The difference column is the covered-group mean minus the uncovered-group mean,
so a positive value means the covered stores read higher.

Two of the five outcomes cross the 0.05 threshold. Covered stores show a higher
mean nitrous oxide flux, 50.83 against 38.30 mg N per square metre per day, a
difference of 12.54. Covered stores also end the period with higher dry matter,
6.95 per cent against 6.25 per cent, a difference of 0.71 percentage points, and
that result sits just under the threshold at p = 0.0490. Methane flux, ammonia
flux and end-of-storage pH do not reach the threshold. The methane and pH
differences are small relative to the spread between stores; the ammonia
difference is larger in relative terms, with covered stores lower by 0.25 g N per
square metre per day, but does not reach the threshold at this sample size.

Each p-value in the table is the p-value from that outcome's own test. Five tests
were run on one declared outcome family, and no adjustment for the number of
comparisons is applied to these p-values or to the verdicts.

## Conclusion

In this 60-day pilot-scale trial, the light expanded clay aggregate floating
cover did not lower methane flux, ammonia flux or end-of-storage pH by an amount
that the data separate from store-to-store variation. The two differences that do
stand out point the other way on greenhouse gases: covered stores gave off more
nitrous oxide, and they retained more dry matter, which is consistent with a
covered surface holding a drier crust and less evaporative and gaseous loss of
material.

The practical reading is that a floating cover cannot be assumed to cut emissions
across the board from a storage period of this length. In this dataset its
clearest effect is on nitrous oxide, and it is an increase. Any programme
decision would need the emissions traded off across gases rather than judged on
one of them, and would need confirmation at full store scale and over a longer
storage period than 60 days. With 20 stores per group, the trial can only pick
out fairly large differences, so the three outcomes that did not reach the
threshold are not thereby shown to be equal between the two management options.
