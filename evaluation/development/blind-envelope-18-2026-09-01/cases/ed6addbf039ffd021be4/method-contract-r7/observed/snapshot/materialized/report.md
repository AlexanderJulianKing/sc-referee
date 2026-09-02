# Harvest timing in lavender: early bloom against full bloom

## What was compared, and why

An essential oil farm needed to know which harvest timing gives the better crop. Sixty-four
lavender bushes of the same cultivar and age grew in one uniform field. Thirty-two were cut at
early bloom and thirty-two at full bloom, on the same two mornings, and every bush was distilled
and analysed on its own. The trial plan named six outcomes in advance, and the
comparison covers those six only.

## The data

`data.csv` has 64 data rows plus a header. One row is one harvested bush: its group and its six
measurements. No value is blank. The columns are:

- `bush_id`: bush identifier, `LAV-001` through `LAV-064`.
- `harvest_stage`: `early_bloom` or `full_bloom`, 32 bushes each.
- `fresh_inflorescence_biomass_g`: fresh weight of the cut inflorescences, in grams.
- `oil_yield_pct`: oil recovered, as a percent by weight of dry inflorescence.
- `linalool_pct`: linalool, as a percent of that bush's oil.
- `linalyl_acetate_pct`: linalyl acetate, as a percent of that bush's oil.
- `camphor_pct`: camphor, as a percent of that bush's oil.
- `cineole_1_8_pct`: 1,8-cineole, as a percent of that bush's oil.

## Keeping the six tests honest together

For each outcome `analysis.py` computes a two-sample Welch t statistic, early bloom minus full
bloom. It then shuffles the harvest-stage labels across all 64 bushes 5000 times, from a fixed
seed so the run repeats. On each shuffle it recomputes all six statistics and keeps one number,
the largest absolute value in the family. That gives 5000 family-maximum values. Each outcome's
p-value is the share of those 5000 maxima that reach or exceed its own observed absolute
statistic, judged at 0.05.

Shuffling labels breaks any real link between timing and measurement, so a shuffled family shows
only what chance produces. Keeping the biggest of six each time asks how large the largest of six
chance results usually gets. That is the bar an outcome must clear, so the risk of any of the six
clearing it when nothing truly differs stays near 5 percent for the whole set rather than per
test. Shuffling whole bush rows also preserves the real correlations among the six measurements.
Here the bar, the 95th percentile of the family maxima, was 2.7191.

## Conclusion for each declared outcome

1. **Fresh inflorescence biomass.** Early 449.70 g (sd 72.67), full 682.38 g (sd 100.53),
   t = -10.6111, p = 0.0000. Full bloom bushes are clearly heavier.
2. **Oil yield.** Early 2.2575 (sd 0.4631), full 2.1453 (sd 0.5270), t = 0.9046, p = 0.9216.
   No difference.
3. **Linalool.** Early 30.4819 (sd 2.9422), full 28.6897 (sd 3.5250), t = 2.2080, p = 0.1702.
   The nearest miss, and still short of the family bar.
4. **Linalyl acetate.** Early 30.8347 (sd 2.6758), full 37.7134 (sd 2.4545), t = -10.7165,
   p = 0.0000. Full bloom oil is clearly richer.
5. **Camphor.** Early 0.6778 (sd 0.2190), full 0.7709 (sd 0.2596), t = -1.5512, p = 0.5226.
   No difference.
6. **1,8-cineole.** Early 1.6428 (sd 0.4404), full 1.4531 (sd 0.4618), t = 1.6816, p = 0.4324.
   No difference.

Two outcomes are significant after family-wise control, biomass and linalyl acetate, both
favouring full bloom. A p of 0.0000 means no shuffle of the 5000 matched the observed statistic,
so the value is below 0.0002.
