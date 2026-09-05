# Cold-pressed rapeseed oil: lowland versus upland growing region

## What was compared and why

One mill receives cold-pressed rapeseed oil from farms in two growing regions. The
food quality laboratory wanted to know whether oil quality differs by region, so it
sampled 72 production batches across one season, 36 from lowland farms and 36 from
upland farms, and analysed each batch once in a single laboratory run order. The
quality plan declared six outcomes in advance, and those six form one outcome family.

## Data

`data.csv` holds 72 data rows plus a header, and one row is one production batch. Its
columns are `batch_id` (the batch identifier, `B001` to `B072`), `region` (the growing
region, either `lowland` or `upland`), `peroxide_value_meq_o2_kg` (peroxide value in
milliequivalents of oxygen per kilogram), `free_fatty_acids_pct` (free fatty acids as
percent oleic acid), `total_tocopherols_mg_kg` (total tocopherols in milligrams per
kilogram), `oxidative_stability_index_h` (oxidative stability index in hours),
`chlorophyll_pigments_mg_kg` (chlorophyll pigments in milligrams per kilogram), and
`erucic_acid_pct` (erucic acid as percent of total fatty acids). The six outcome
columns appear in the declared order. No cell is blank.

`adjusted_pvalues.csv` holds 6 data rows plus a header, one row per declared outcome
in the declared order, with an `outcome` column naming the outcome exactly as in
`data.csv` and an `adjusted_p_value` column. These values are an import. A standing
pipeline stage upstream of this project tested the whole declared family of six and
applied a Holm-Bonferroni adjustment across all six together, then exported the
adjusted values. They are the only inferential input this project has.

## What the script does and does not do

`analysis.py` reads both files and summarises the raw data descriptively: group sizes,
and the mean and standard deviation of each outcome in each region. It also runs
routine checks for expected columns, unique batch identifiers, missing values, group
labels and sizes, and values falling inside the plausible ranges the quality plan
states. All of those checks passed. The script runs no significance test and computes
no p-value of its own. Each verdict below is the loaded adjusted p-value compared with
0.05.

## Conclusions by outcome

1. **Peroxide value.** Lowland mean 2.552 (SD 0.630), upland 2.414 (SD 0.609).
   Adjusted p = 0.897221, so no difference between regions at the 0.05 level.
2. **Free fatty acids.** Lowland 0.543 (SD 0.147), upland 0.572 (SD 0.170). Adjusted
   p = 0.897221, so no difference at the 0.05 level.
3. **Total tocopherols.** Lowland 481.500 (SD 61.120), upland 578.833 (SD 58.615), a
   gap of 97.3 mg/kg. Adjusted p = 1.16644e-08, a difference at the 0.05 level, with
   upland oil higher.
4. **Oxidative stability index.** Lowland 6.069 h (SD 1.066), upland 8.153 h (SD
   1.480), a gap of 2.08 h. Adjusted p = 1.7277e-08, a difference at the 0.05 level,
   with upland oil higher.
5. **Chlorophyll pigments.** Lowland 13.558 (SD 3.590), upland 14.558 (SD 3.765).
   Adjusted p = 0.897221, so no difference at the 0.05 level.
6. **Erucic acid.** Lowland 0.318 (SD 0.128), upland 0.355 (SD 0.129). Adjusted
   p = 0.897221, so no difference at the 0.05 level.

Upland batches stand out on tocopherol content and oxidative stability. The other four
outcomes land close between the two regions.
