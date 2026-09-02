# Seven-day duckweed growth assay: reference medium vs 10% treated effluent

## What was tested and why

Treated municipal wastewater effluent is released into surface water, so the
laboratory asked whether water that has already been through treatment still
slows the growth of a sensitive aquatic plant. Forty-eight duckweed culture
vessels were started from one clonal stock. Twenty-four received standard
reference growth medium and twenty-four received the same medium made up with
ten percent treated municipal effluent. All vessels sat in the same growth
cabinet and were measured once, at day seven. The assay plan declared five
outcomes in advance, so the question for each outcome is whether the two media
differ.

## The data

`data.csv` holds 48 data rows plus a header. **One row is one culture vessel**,
carrying its medium assignment and its day-seven value for each declared
outcome. There are no missing values. The columns are:

- `vessel_id`: vessel label, `V01` through `V48`.
- `medium`: growth medium, either `reference_medium` or `effluent_10pct`, with
  24 vessels in each.
- `frond_number_increase`: increase in frond number over the seven days, a count.
- `total_frond_area_mm2`: total frond area at day seven, in mm².
- `chlorophyll_a_ug_per_g`: chlorophyll a at day seven, in µg per g fresh mass.
- `mean_root_length_mm`: mean root length at day seven, in mm.
- `dry_biomass_mg`: dry biomass at day seven, in mg.

## What the analysis did

`analysis.py` reads `data.csv` and runs an independent two-sample t-test on each
of the five declared outcomes, comparing the reference vessels against the
effluent vessels.

Testing five outcomes gives five chances to call a difference real by accident,
so the family-wise level is held at 0.05: that 5% is the chance of at least one
false call across the whole declared family, not per outcome. To get there, the
script computes the Sidak per-comparison threshold from the family size of
m = 5, as 1 - (1 - 0.05)^(1/5) = 0.010206. Every p-value is judged against
0.010206 rather than against 0.05.

## Conclusions by outcome

1. **Frond number increase.** Reference 71.46 (SD 9.03), effluent 37.63
   (SD 8.59), p = 2.23e-17. Below the threshold, so effluent vessels added far
   fewer fronds.
2. **Total frond area.** Reference 387.36 mm² (SD 80.04), effluent 411.41 mm²
   (SD 83.34), p = 0.313. Above the threshold, so no difference was shown.
3. **Chlorophyll a.** Reference 597.11 µg/g (SD 95.98), effluent 596.19 µg/g
   (SD 139.99), p = 0.979. Above the threshold, so no difference was shown.
4. **Mean root length.** Reference 18.22 mm (SD 3.08), effluent 9.23 mm
   (SD 2.25), p = 3.44e-15. Below the threshold, so effluent roots were about
   half as long.
5. **Dry biomass.** Reference 18.44 mg (SD 5.22), effluent 19.69 mg (SD 3.91),
   p = 0.352. Above the threshold, so no difference was shown.

Two of the five declared outcomes, frond number increase and root length, show
a clear effect of the 10% effluent medium at the Sidak threshold. The other
three do not.
