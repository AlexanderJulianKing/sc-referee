# Data description

Screenhouse irrigation-scheduling experiment on pearl millet landraces. Fifty-six pearl millet
plants were grown in individual pots and harvested at grain maturity. Twenty-eight pots were kept
on a full irrigation schedule (watered to field capacity twice a week) and twenty-eight on a
deficit schedule (watered to 60 percent of field capacity twice a week). Every plant was measured
for all six declared outcomes, so there are no missing values.

Two files are supplied: the raw per-plant measurements, and the inference table handed down by the
group's upstream statistics stage.

## `millet_irrigation.csv`

One row is one potted pearl millet plant, measured at grain maturity. 56 data rows plus a header
row.

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `plant_id` | text | none | Per-plant identifier, `p01` through `p56`. Unique across the file. |
| `irrigation` | text | none | Irrigation schedule the pot was assigned to. Exactly two distinct values: `full` (field capacity twice a week, 28 plants) and `deficit` (60 percent of field capacity twice a week, 28 plants). |
| `plant_height_cm` | number | cm | Declared outcome 1. Plant height at maturity, from soil surface to the tip of the panicle. |
| `panicle_length_cm` | number | cm | Declared outcome 2. Length of the main panicle. |
| `grain_yield_g` | number | g | Declared outcome 3. Grain yield per plant, threshed and air-dried. |
| `thousand_grain_mass_g` | number | g | Declared outcome 4. Mass of one thousand grains. |
| `leaf_rwc_pct` | number | percent | Declared outcome 5. Leaf relative water content of the youngest fully expanded leaf, sampled at midday. |
| `stomatal_cond_mmol` | number | mmol m-2 s-1 | Declared outcome 6. Stomatal conductance of the same leaf, measured at midday. |

The six outcome columns appear in the order the family of outcomes was declared in advance.

## `upstream_inference.csv`

One row is one declared outcome variable. Six data rows plus a header row, in the declared outcome
order used by the raw file.

| Column | Type | Description |
| --- | --- | --- |
| `outcome` | text | Name of the declared outcome, spelled exactly as the matching column name in `millet_irrigation.csv`. |
| `p_raw` | number | The uncorrected p-value for that outcome, from the upstream stage's two-sample comparison of the full and deficit schedules. |
| `p_adj` | number | The same p-value after the upstream stage corrected the whole family of six declared outcomes together, controlling the family-wise error rate at 0.05 by the Holm step-down procedure. This is the value a downstream consumer should judge against 0.05. |

Both p-value columns are written in general numeric format, so very small values appear in
scientific notation (for example `1.19167e-11`).

## Provenance

The per-outcome tests and the family-wise correction were carried out upstream, before these files
were handed over. `upstream_inference.csv` is a record of that completed stage, not something to be
recomputed from the raw file.
