# Autumn versus spring sowing of faba bean

## What was compared, and why

An agronomy institute asked whether autumn-sown faba bean differs from the same
cultivar sown the following spring. Sixty plots of equal size were laid out on
one uniform experimental field. Thirty were sown in autumn and thirty in spring,
with the same seed rate and the same management otherwise. Every plot was
harvested and assessed once at maturity. The trial plan named six outcomes in
advance, so all six are reported here in that declared order.

## The data

`data.csv` has one header row and 60 data rows. One row is one field plot: its
identifier, the sowing time it was assigned, and that plot's single
end-of-season measurement for each of the six declared outcomes. No cell is
blank. The columns are:

- `plot_id`: plot identifier, `P01` to `P60`, one per row.
- `sowing_time`: the group column, either `autumn` or `spring`, 30 rows each.
- `grain_yield_t_ha`: grain yield in tonnes per hectare.
- `pods_per_plant`: pods per plant, plot average.
- `thousand_seed_weight_g`: weight of one thousand seeds, in grams.
- `plant_height_cm`: plant height at maturity in centimetres, plot average.
- `seed_protein_pct`: seed protein as a percentage of dry matter.
- `chocolate_spot_severity_pct`: chocolate spot leaf disease, as percent of leaf
  area affected.

## What the analysis did

`analysis.py` reads `data.csv`, splits the plots by `sowing_time`, and compares
autumn against spring on each outcome with an independent two-sample t-test.
Every outcome had 30 plots per group. That gives six raw p-values. Testing six
outcomes raises the chance that at least one looks impressive by luck alone, so
all six were passed together, as one complete family, to `pingouin.multicomp`,
the multiple-comparison adjustment in the pingouin statistics package. Pingouin
is a specialist third-party package, installed separately and listed in
`requirements.txt`. The adjustment used the Holm method at a family-wise level of
0.05. Every verdict below rests on the adjusted value pingouin returned. No
outcome is judged on its raw p-value.

## Conclusion for each declared outcome

1. **Grain yield.** Autumn 5.228 t/ha (sd 0.366), spring 4.030 t/ha (sd 0.451).
   Adjusted value 1.4e-15: autumn sowing yielded about 1.2 t/ha more grain.
2. **Pods per plant.** Autumn 15.72 (sd 3.49), spring 15.50 (sd 3.57). Adjusted
   value 1.000: no difference was shown.
3. **Thousand-seed weight.** Autumn 499.1 g (sd 46.6), spring 508.9 g (sd 49.5).
   Adjusted value 1.000: no difference was shown.
4. **Plant height.** Autumn 100.9 cm (sd 10.4), spring 102.5 cm (sd 12.7).
   Adjusted value 1.000: no difference was shown.
5. **Seed protein.** Autumn 27.83 % (sd 1.47), spring 28.17 % (sd 1.46).
   Adjusted value 1.000: no difference was shown.
6. **Chocolate spot severity.** Autumn 17.59 % leaf area (sd 4.17), spring
   6.36 % (sd 2.20). Adjusted value 3.9e-18: autumn sowing carried much more
   disease.

Two of the six declared outcomes cleared the 0.05 family-wise level: the autumn
yield gain came with a heavier chocolate spot burden, and the other four
outcomes landed close between the sowing times.
