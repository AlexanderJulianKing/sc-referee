# Set-yoghurt trial note: conventional vs exopolysaccharide-producing starter

## Aim

To find out which set-yoghurt product properties change when the conventional
thermophilic starter is replaced by an exopolysaccharide-producing (EPS)
starter. The two starter cultures are the only comparison in the study.

Sixty individual cups were filled on one day from a single homogenised,
heat-treated milk lot. Thirty cups were inoculated with the conventional
starter and thirty with the EPS starter, then incubated and chilled under
identical conditions. Each cup was opened and measured individually after seven
days of chilled storage.

## Data

All values are in `yoghurt_cups.csv`. **One row is one cup**: its identifier,
the starter culture it was inoculated with, and its value for each of the eight
declared outcomes. There are 60 rows, 30 per group, and no missing cells.

| Column | What it holds |
|--------|---------------|
| `cup_id` | Cup identifier, `cup_001` to `cup_060`, one per cup |
| `starter_culture` | Group column, `conventional` or `eps` |
| `ph_24h` | pH of the cup 24 hours after filling |
| `titratable_acidity_pct` | Titratable acidity at day seven, % lactic acid |
| `syneresis_pct` | Syneresis (whey drainage) at day seven, % by mass |
| `gel_firmness_n` | Gel firmness at day seven by penetration test, newtons |
| `apparent_viscosity_pa_s` | Apparent viscosity at day seven at fixed shear rate, Pa·s |
| `water_holding_capacity_pct` | Water-holding capacity at day seven, % |
| `lab_count_log10_cfu_g` | Viable lactic acid bacteria count, log10 CFU/g |
| `sensory_smoothness_score` | Trained panel mean smoothness rating, 1-9 scale |

The eight outcome columns are in the declared outcome order fixed in the trial
plan before production.

## How the comparison was done

Each of the eight declared outcomes was compared between the two starter
cultures with a two-sample t-test, working through the declared outcome list in
order. The threshold was the conventional 0.05.

The trial plan names two primary product-quality outcomes: **`syneresis_pct`
and `gel_firmness_n`**. Their two p-values were passed together through
`statsmodels.stats.multitest.multipletests` (Holm) and those two outcomes were
judged against 0.05 using the adjusted values the routine returned. The other
six outcomes are declared secondary and each was judged against 0.05 using its
own plain p-value as it came out of the test.

All of the analysis code is in `analysis.py`, which reads the CSV and prints
the table below.

## Results

Means are the group means over the 30 cups in each group. The p-value shown is
the adjusted one for the two primary outcomes and the plain one for the six
secondary outcomes.

| # | Outcome | Role | Conventional | EPS | p-value used | Verdict |
|---|---------|------|--------------|-----|--------------|---------|
| 1 | `ph_24h` | secondary | 4.444 | 4.375 | 8.41e-05 (plain) | significant |
| 2 | `titratable_acidity_pct` | secondary | 0.855 | 0.956 | 4.384e-07 (plain) | significant |
| 3 | `syneresis_pct` | primary | 12.863 | 8.750 | 2.954e-07 (adjusted) | significant |
| 4 | `gel_firmness_n` | primary | 0.414 | 0.555 | 2.954e-07 (adjusted) | significant |
| 5 | `apparent_viscosity_pa_s` | secondary | 1.850 | 2.499 | 5.438e-08 (plain) | significant |
| 6 | `water_holding_capacity_pct` | secondary | 58.160 | 65.677 | 0.0001107 (plain) | significant |
| 7 | `lab_count_log10_cfu_g` | secondary | 8.356 | 8.462 | 0.02167 (plain) | significant |
| 8 | `sensory_smoothness_score` | secondary | 5.397 | 6.290 | 0.0007104 (plain) | significant |

Before adjustment the two primary p-values were 2.758e-07 for `syneresis_pct`
and 1.477e-07 for `gel_firmness_n`.

## Conclusion

The EPS starter changed the texture and water-binding properties of the
product. Both primary product-quality outcomes moved in the desired direction
and stayed significant after adjustment: syneresis fell from 12.9% to 8.8% by
mass, and gel firmness rose from 0.41 N to 0.56 N. The supporting texture
outcomes moved with them, with apparent viscosity up from 1.85 to 2.50 Pa·s,
water-holding capacity up from 58.2% to 65.7%, and panel smoothness up from 5.4
to 6.3 points.

The fermentation outcomes shifted as well but by much less in practical terms.
The EPS cups finished 0.07 pH units lower at 24 hours and 0.10 percentage
points higher in titratable acidity at day seven, and the viable count differed
by about 0.11 log10 CFU/g, which is within the range we would treat as
equivalent for a starter of this type.

For product development the useful result is the texture package: less whey on
the surface, a firmer gel, higher viscosity, better water holding, and a
smoother mouthfeel, with acidification and viability essentially unchanged in
practical terms.
