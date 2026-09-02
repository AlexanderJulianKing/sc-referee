# Bunch thinning on Medjool-type date palms: light versus heavy strand thinning

## What was compared and why

Strand thinning sets how many fruit a bunch carries, so we need to know what harder thinning
buys and what it costs. Fifty-six mature palms in one uniformly managed block were used.
Twenty-eight received light strand thinning and twenty-eight received heavy strand thinning,
applied by the same crew at the same growth stage, and every palm was harvested and measured at
the same maturity. The trial plan declared eight outcomes in advance.

## Data

`data.csv` holds one row per palm, 56 rows plus a header, with 28 palms in each thinning
intensity. One row is one palm: its identifier, the thinning intensity it received, and its value
for each of the eight declared outcomes. No cell is blank. The columns are:

- `palm_id`: palm identifier, `P01` through `P56`.
- `thinning_intensity`: the group, either `light` or `heavy`.
- `fruit_weight_g`: mean single fruit weight in grams.
- `fruit_length_mm`: fruit length in millimetres.
- `fruit_width_mm`: fruit width in millimetres.
- `yield_per_palm_kg`: harvested yield for that palm in kilograms.
- `total_soluble_solids_brix`: total soluble solids in degrees Brix.
- `fruit_moisture_pct`: fruit moisture as a percentage.
- `flesh_to_seed_ratio`: flesh mass divided by seed mass, a unitless ratio.
- `fruit_firmness_n`: fruit firmness in newtons.

## What the analysis did

`analysis.py` reads `data.csv` and compares light against heavy on each of the eight declared
outcomes with an independent two-sample t-test, which fits continuous measurements taken on
separate palms. Eight comparisons were run in total.

Three outcomes decide the commercial value of the crop: mean single fruit weight, yield per palm,
and total soluble solids. Their p-values were corrected by hand inside the script, each multiplied
by eight and capped at one, then judged against 0.05. The other five outcomes, namely fruit
length, fruit width, fruit moisture, flesh-to-seed ratio, and fruit firmness, were each judged
against 0.05 on the raw unadjusted p-value.

## Conclusions, in the declared order

1. **Mean single fruit weight (g).** Light 10.351 (SD 0.936), heavy 12.931 (SD 0.859). Corrected
   p = 4.03e-14. Heavy thinning produced heavier fruit, by about 2.6 g.
2. **Fruit length (mm).** Light 39.329 (SD 1.543), heavy 44.936 (SD 1.664). Raw p = 2.31e-18.
   Heavy thinning produced longer fruit, by about 5.6 mm.
3. **Fruit width (mm).** Light 23.343 (SD 1.344), heavy 24.082 (SD 1.266). Raw p = 0.0387. Fruit
   from heavily thinned palms was wider, by about 0.7 mm.
4. **Yield per palm (kg).** Light 109.264 (SD 6.515), heavy 82.289 (SD 6.572). Corrected
   p = 1.56e-20. Light thinning yielded about 27 kg more per palm.
5. **Total soluble solids (Brix).** Light 69.636 (SD 2.823), heavy 69.029 (SD 3.302). Corrected
   p = 1. No significant difference between the intensities.
6. **Fruit moisture (%).** Light 21.646 (SD 2.299), heavy 22.139 (SD 2.747). Raw p = 0.470. No
   significant difference.
7. **Flesh-to-seed ratio.** Light 9.091 (SD 0.829), heavy 9.103 (SD 0.811). Raw p = 0.957. No
   significant difference.
8. **Fruit firmness (N).** Light 8.579 (SD 1.283), heavy 9.036 (SD 1.619). Raw p = 0.247. No
   significant difference.

Heavier thinning gives larger fruit and lower tonnage per palm, and the four quality measures
came out much the same under both intensities.
