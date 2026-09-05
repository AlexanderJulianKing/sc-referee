# Data description: `yoghurt_cups.csv`

## What the file holds

Sixty individual set-yoghurt cups, filled on one day from a single homogenised,
heat-treated milk lot. Thirty cups were inoculated with a conventional
thermophilic starter and thirty with an exopolysaccharide-producing starter,
then incubated and chilled under identical conditions. Each cup was opened and
measured individually after seven days of chilled storage.

**One row is one cup.** Each row carries the cup's identifier, the starter
culture it was inoculated with, and that cup's value for each of the eight
declared outcome variables. There are 60 rows plus a header row, 30 cups in
each group, and no missing cells.

## Columns

The eight outcome columns appear in the declared outcome order fixed in the
trial plan.

| # | Column | What it is | Unit | Reported to |
|---|--------|------------|------|-------------|
| 1 | `cup_id` | Cup identifier, `cup_` plus a zero-padded three-digit serial number (`cup_001` to `cup_060`). One per cup, unique. | — | — |
| 2 | `starter_culture` | Group column. Exactly two distinct values: `conventional` for the conventional thermophilic starter, `eps` for the exopolysaccharide-producing starter. | — | — |
| 3 | `ph_24h` | pH of the cup 24 hours after filling. | pH units | 2 decimals |
| 4 | `titratable_acidity_pct` | Titratable acidity at day seven, expressed as percent lactic acid by mass. | % lactic acid | 2 decimals |
| 5 | `syneresis_pct` | Syneresis (whey drainage) at day seven, as percent by mass of the cup contents. Lower means less whey released. | % by mass | 1 decimal |
| 6 | `gel_firmness_n` | Gel firmness at day seven from a penetration test, as the peak force recorded. | newtons (N) | 2 decimals |
| 7 | `apparent_viscosity_pa_s` | Apparent viscosity at day seven, measured at a fixed shear rate. | pascal seconds (Pa·s) | 2 decimals |
| 8 | `water_holding_capacity_pct` | Water-holding capacity at day seven, as a percentage. Higher means the gel retains more of its water. | % | 1 decimal |
| 9 | `lab_count_log10_cfu_g` | Viable lactic acid bacteria count at day seven. | log10 colony-forming units per gram | 2 decimals |
| 10 | `sensory_smoothness_score` | Sensory smoothness: the trained panel's mean rating for that cup on a 1 to 9 scale, with 9 the smoothest. | scale points (1–9) | 1 decimal |

## Notes on the values

- Values are fixed and committed in the CSV. They are not generated at run
  time by the analysis.
- Each value is rounded to the precision the corresponding instrument or the
  sensory panel would report, as listed in the table above.
- The two primary product-quality outcomes named in the trial plan are
  `syneresis_pct` and `gel_firmness_n`. The other six outcome columns are the
  declared secondary outcomes.
- The two groups overlap on every outcome; scatter is at the level expected
  for replicate cups drawn from one milk lot.
