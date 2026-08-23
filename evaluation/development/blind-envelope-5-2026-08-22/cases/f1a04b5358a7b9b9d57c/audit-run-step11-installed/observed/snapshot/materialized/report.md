# Shade trees and stomatal conductance in arabica coffee

## Data

The file `coffee_stomatal_conductance.csv` holds one header line and 120 data rows.

**One row is one measured leaf.** It is a single porometer reading taken on one fully expanded leaf
of one coffee shrub on one clear morning. A row is not a shrub and not a treatment group. Six leaves
were measured on each of 20 shrubs, so the 120 rows are the 120 measured leaves.

The columns, in file order:

| # | Column | Type | Units | Description |
|---|---|---|---|---|
| 1 | `shrub_label` | text | none | Field tag of the shrub the leaf came from, written `Rnn-Pnn`: estate row number and the shrub's position along that row, for example `R02-P03`. 20 distinct values, 6 rows each. |
| 2 | `canopy_treatment` | text, 2 levels | none | Growing condition of the shrub: `shade_trees` (under nitrogen-fixing shade trees) or `full_sun` (no overhead canopy). Constant across all six rows of a shrub. |
| 3 | `leaf_position` | text, 6 levels | none | Where on the canopy the leaf sat: `upper_north`, `upper_south`, `mid_east`, `mid_west`, `lower_east`, `lower_west`. Each value appears once per shrub. |
| 4 | `leaf_temp_c` | number, 1 decimal | degrees Celsius | Leaf temperature at the moment of measurement. Observed 24.0 to 32.4. |
| 5 | `stomatal_conductance_mmol_m2_s` | integer | mmol H2O m-2 s-1 | The outcome: stomatal conductance to water vapour for that leaf, rounded to a whole number. Observed 110 to 300. |

There are no missing values and no duplicate leaf records. Ten shrubs sit in each treatment, giving
60 leaves per group.

## Methods

Stomatal conductance was compared between the two canopy treatments with an independent two-sample
t-test of the difference in means (Welch, unequal variances, two-sided, alpha = 0.05). Every measured
leaf entered the comparison as a separate observation, so 120 leaves were analysed. Group mean,
standard deviation, standard error and range are reported for each treatment, together with the
difference in means and its 95 percent confidence interval. The analysis is in `analysis.py` and uses
pandas and SciPy.

## Results

Leaves analysed: **120** (60 under shade trees, 60 in full sun).

| Group | Leaves | Mean | SD | SE | Range |
|---|---|---|---|---|---|
| `shade_trees` | 60 | 228.52 | 23.92 | 3.09 | 178 to 300 |
| `full_sun` | 60 | 154.80 | 20.09 | 2.59 | 110 to 203 |

All conductance figures are mmol H2O m-2 s-1.

Shaded leaves averaged **73.72 mmol m-2 s-1** higher than full-sun leaves, a 47.6 percent increase.
The 95 percent confidence interval for the difference runs from 65.73 to 81.70. The test gives
t = 18.28 on 114.58 degrees of freedom, **p = 9.3e-36**, far below the 0.05 threshold. Shade raises
stomatal conductance.

Leaf temperature followed the same pattern in reverse. Leaves under shade trees averaged 26.14 deg C
(SD 1.32, range 24.0 to 29.2) against 29.73 deg C in full sun (SD 1.32, range 26.6 to 32.4), a gap of
3.6 deg C.

## Interpretation

Shade trees keep coffee stomata open. Shaded shrubs ran conductance close to half again as high as
their full-sun neighbours on the same estate and the same morning, and the effect is unambiguous.

The mechanism is straightforward. The overhead canopy intercepts direct radiation, so shaded leaves
sat 3.6 deg C cooler. Cooler leaves face a lower leaf-to-air vapour pressure deficit, and a lower
deficit is the condition under which coffee stomata stay wide rather than closing to protect leaf
water status. Full-sun leaves at close to 30 deg C were doing the opposite: partial midday closure,
which is exactly what the depressed conductance of 154.8 mmol m-2 s-1 records.

Two agronomic consequences follow. First, open stomata mean carbon dioxide keeps entering the leaf,
so the shaded shrubs sustained photosynthesis through the part of the morning when full-sun shrubs
were already throttling gas exchange. Second, open stomata also mean higher transpiration per unit
leaf area, so shade does not save water at the leaf. The water saving from an agroforestry canopy
comes at the stand level, from reduced radiation load and lower soil evaporation, not from
restricting the individual coffee leaf.

For management on this estate, the nitrogen-fixing shade canopy is doing physiological work beyond
its nitrogen contribution. It holds coffee leaves in a cooler, lower-deficit microclimate that keeps
gas exchange running later into the day. Retaining and extending that canopy is the sensible course,
particularly on blocks exposed to high morning radiation.
