# Sediment condition in a restored mangrove stand and an adjacent natural stand

## What was surveyed and why

Twelve years after planting, we wanted to know how far the sediment in a restored mangrove stand
has come toward matching undisturbed conditions. The restored stand sits on the same shoreline as
an undisturbed natural stand of the same species, which gives us a local reference for what the
sediment should look like once recovery is complete.

We took forty-eight sediment cores to 30 centimetres depth during a single survey: twenty-four
spread across the restored stand and twenty-four across the natural stand. Each core was analysed
once in the laboratory. Before any core was analysed we declared three outcomes, in this order:
sediment organic carbon, dry bulk density, and total nitrogen. Each one is its own question about
restoration progress, so each is reported on its own terms.

## The data

`data.csv` holds one row per sediment core, forty-eight rows plus a header, with no blanks. The
columns are:

- `core_id` - the identifier for that core (`R01`-`R24` in the restored stand, `N01`-`N24` in the
  natural stand).
- `stand_type` - which stand the core came from, either `restored` or `natural`.
- `organic_carbon_pct` - sediment organic carbon, as a percent of dry mass.
- `bulk_density_g_cm3` - dry bulk density, in grams per cubic centimetre.
- `total_nitrogen_mg_g` - total nitrogen, in milligrams per gram of dry sediment.

One row is one core: its label, its stand, and the three laboratory measurements made on it.

## What the analysis did

`analysis.py` reads `data.csv` and compares the two stand types on each declared outcome with an
independent two-sample t-test, which is the standard comparison for continuous measurements on
separate cores. The per-outcome testing is handled by one reusable step in the script that takes
the loaded data and the declared outcome list and returns the collected results; the main part of
the script prints from those results. For each outcome the script prints the number of cores in
each stand, the mean and standard deviation in each stand, the p-value, and a verdict at the
conventional 0.05 threshold based on that outcome's own p-value.

## Results

**Organic carbon.** Restored 2.004 percent (SD 0.276, n = 24) against natural 3.518 percent
(SD 0.360, n = 24), p = 8.60e-21. The stands differ significantly. The restored sediment holds
well under two thirds of the carbon the natural stand holds.

**Bulk density.** Restored 0.897 g/cm3 (SD 0.101, n = 24) against natural 0.907 g/cm3 (SD 0.095,
n = 24), p = 0.7148. No significant difference. Compaction in the restored stand already looks
like the natural stand.

**Total nitrogen.** Restored 1.341 mg/g (SD 0.223, n = 24) against natural 1.487 mg/g (SD 0.210,
n = 24), p = 0.0243. The stands differ significantly, with the restored stand lower, though the
gap is far smaller than the carbon gap.
