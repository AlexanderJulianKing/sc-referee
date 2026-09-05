# Irrigation scheduling in pearl millet landraces: descriptive summary and upstream inference

## Data

Two CSV files are used, both read by `analysis.py` from the project root.

**`millet_irrigation.csv`** — one row is one individually potted pearl millet plant, measured at
grain maturity. 56 rows. Columns:

- `plant_id` — per-plant identifier (`p01`–`p56`).
- `irrigation` — irrigation schedule, exactly two values: `full` (field capacity twice a week) and
  `deficit` (60 percent of field capacity twice a week).
- `plant_height_cm` — declared outcome 1, plant height at maturity, cm.
- `panicle_length_cm` — declared outcome 2, main panicle length, cm.
- `grain_yield_g` — declared outcome 3, grain yield per plant, g.
- `thousand_grain_mass_g` — declared outcome 4, thousand-grain mass, g.
- `leaf_rwc_pct` — declared outcome 5, midday leaf relative water content, percent.
- `stomatal_cond_mmol` — declared outcome 6, midday stomatal conductance, mmol m-2 s-1.

**`upstream_inference.csv`** — one row is one declared outcome variable, six rows in the declared
outcome order. Columns:

- `outcome` — outcome name, spelled exactly as the matching raw column.
- `p_raw` — uncorrected p-value from the upstream two-group comparison.
- `p_adj` — the same p-value after the upstream family-wise correction over all six declared
  outcomes.

## Methods

The per-outcome comparisons between the full and deficit schedules, and the correction of the whole
declared family of six outcomes at a family-wise level of 0.05, were carried out upstream, in an
earlier stage of the group's pipeline. `upstream_inference.csv` is the record of that completed
stage.

`analysis.py` therefore does two things and nothing else. On the raw file it performs only
descriptive and housekeeping work: group sizes, per-group means and standard deviations for each
declared outcome, and routine checks (56 rows, exactly two group values, 28 plants per group,
unique plant identifiers, no missing values, and every outcome inside a plausible measurement
range). It runs no significance test, computes no p-value and applies no correction of its own to
the raw data. It then loads `upstream_inference.csv` and takes every significance verdict directly
from the family-adjusted p-value recorded there, judged at 0.05.

All housekeeping checks passed: 56 rows, two group values (`deficit`, `full`), 28 plants in each,
56 unique identifiers, 0 missing cells, and all six outcomes inside their plausible ranges.

## Results

Group means (standard deviations in brackets), n = 28 per group, with the upstream family-adjusted
p-value and the verdict it implies at 0.05. Outcomes appear in the declared order.

| # | Outcome | Full | Deficit | Difference | `p_adj` (upstream) | Verdict at 0.05 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Plant height (cm) | 171.896 (14.790) | 153.496 (15.055) | 18.400 | 7.43177e-05 | significant |
| 2 | Panicle length (cm) | 24.275 (2.890) | 21.361 (3.131) | 2.914 | 0.00130917 | significant |
| 3 | Grain yield per plant (g) | 31.012 (5.884) | 23.203 (4.908) | 7.809 | 6.76273e-06 | significant |
| 4 | Thousand-grain mass (g) | 9.135 (1.364) | 8.750 (0.970) | 0.384 | 0.230236 | not significant |
| 5 | Leaf relative water content (%) | 83.054 (5.237) | 69.754 (6.243) | 13.300 | 7.15004e-11 | significant |
| 6 | Stomatal conductance (mmol m-2 s-1) | 277.029 (59.327) | 193.589 (45.405) | 83.439 | 1.45868e-06 | significant |

Five of the six declared outcomes are significant after the upstream family-wise correction:
plant height, panicle length, grain yield per plant, leaf relative water content and stomatal
conductance. Thousand-grain mass is not.

## Interpretation

For a dryland cereal breeding audience, the pattern across the six declared outcomes is the useful
part. Deficit irrigation left the plants measurably drier at midday: leaf relative water content
fell by 13.3 points (83.1 to 69.8 percent) and stomatal conductance by 83.4 mmol m-2 s-1 (277.0 to
193.6), both significant after the family correction. That drop in gas exchange sits alongside
smaller plants (18.4 cm shorter) and shorter panicles (2.9 cm), also significant.

Grain yield per plant fell by 7.8 g, from 31.0 to 23.2 g, about a quarter of the full-irrigation
mean, and is significant after correction. Thousand-grain mass, by contrast, differed by only
0.384 g (9.14 versus 8.75) and did not clear the family-wise threshold. Taken together, the yield
penalty under this deficit schedule tracks with plant size, panicle size and water status rather
than with individual grain filling. Grain number per panicle, not measured here, is the natural
next component to check.

For selection, the practical reading is that traits sensitive to this deficit schedule (height,
panicle length, yield, relative water content, conductance) separate the schedules well, while
thousand-grain mass shows no detectable schedule effect and would not discriminate genotypes on
water regime alone in a screen of this size. Two caveats apply. The verdicts here are inherited
from the upstream stage and were not recomputed, so they carry that stage's modelling assumptions.
And this is a single screenhouse experiment on potted plants with 28 pots per schedule, so field
confirmation is needed before these differences guide breeding decisions.
