# Street tree pit soil monitoring: end-of-season report

## What was monitored and why

Some new street tree pits are filled with an engineered structural soil, which costs more than the
standard backfill taken from the site itself. This monitoring round asks whether the extra cost buys
better tree performance. Sixty young small-leaved lime trees were planted three years ago in tree
pits along comparable inner-city streets: thirty into engineered structural soil, thirty into
standard backfill. Every tree was measured once, at the end of the same growing season, by the same
surveying crew. The monitoring plan declared four outcomes before measurement: trunk diameter
increment, projected canopy area, leaf chlorophyll index, and midday stem water potential.

## The data

`data.csv` holds sixty data rows plus a header. One row is one tree: its identifier, the pit soil it
was planted into, and its four end-of-season measurements. Each tree appears once and no cell is
blank. The columns are:

- `tree_id`: tree identifier, `T001` through `T060`.
- `pit_soil_type`: group column, either `engineered_structural_soil` or `standard_backfill`.
- `trunk_diameter_increment_mm`: trunk diameter increment over the season, in millimetres.
- `canopy_area_m2`: projected canopy area, in square metres.
- `leaf_chlorophyll_index`: leaf chlorophyll index, in relative units of a handheld leaf meter.
- `midday_stem_water_potential_mpa`: midday stem water potential in megapascals, a negative quantity.

## What the analysis did

`analysis.py` reads `data.csv` and splits the rows into the two pit soil groups. It then works
through the four declared outcomes in their declared order, giving each outcome its own section of
the script. Each section runs a two-sample t test for independent samples on that outcome, in the
Welch version, which does not assume the two groups share the same spread. Each section prints the
group sizes, means, standard deviations, difference in means, t statistic, p-value, and a verdict on
whether that outcome differs at the conventional 0.05 threshold, judged on its own p-value.

## Conclusions by outcome

1. **Trunk diameter increment (mm).** Engineered soil 13.097 (sd 1.542, n = 30), standard backfill
   9.690 (sd 1.535, n = 30), a gap of 3.407 mm favouring the engineered soil. t = 8.577,
   p < 0.0001. Significantly different at the 0.05 threshold.
2. **Projected canopy area (m2).** Engineered soil 8.702 (sd 1.079, n = 30), standard backfill 6.371
   (sd 0.816, n = 30), a gap of 2.331 m2 favouring the engineered soil. t = 9.439, p < 0.0001.
   Significantly different at the 0.05 threshold.
3. **Leaf chlorophyll index.** Engineered soil 36.973 (sd 3.178, n = 30), standard backfill 36.983
   (sd 3.536, n = 30), a gap of -0.010 index units. t = -0.012, p = 0.9908. Not significantly
   different at the 0.05 threshold.
4. **Midday stem water potential (MPa).** Engineered soil -1.246 (sd 0.151, n = 30), standard
   backfill -1.313 (sd 0.198, n = 30), a gap of 0.068 MPa, the engineered soil trees being the less
   negative. t = 1.492, p = 0.1416. Not significantly different at the 0.05 threshold.

The trees in engineered structural soil are clearly ahead on the two growth outcomes, while the
leaf-level and water-status outcomes came out close between the groups this season.
