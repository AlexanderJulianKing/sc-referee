# data.csv

Faba bean sowing-time trial: autumn sowing compared with spring sowing of the same
cultivar on one uniform experimental field, same seed rate and same management
otherwise. Sixty field plots of equal size, thirty per sowing time. Each plot was
harvested and assessed once at maturity.

## What one row represents

One row is one field plot: the plot's identifier, the sowing time it was assigned,
and that plot's single end-of-season measurement for each of the six outcomes the
trial plan declared in advance. There are 60 data rows plus a header row, and no
blank cells: every plot has a value for every outcome.

## Columns

Columns appear in this order. The six outcome columns follow the order the trial
plan declared.

| # | Column | Type | Unit | Description |
|---|--------|------|------|-------------|
| 1 | `plot_id` | text | none | Plot identifier, `P01` through `P60`. Unique; one per row. |
| 2 | `sowing_time` | text | none | Group column. Exactly two possible values: `autumn` and `spring`. Thirty rows carry each value. |
| 3 | `grain_yield_t_ha` | number | tonnes per hectare | Declared outcome 1. Grain yield of the plot. Two decimal places. |
| 4 | `pods_per_plant` | number | none (a count) | Declared outcome 2. Pods per plant, averaged over the plot. One decimal place. |
| 5 | `thousand_seed_weight_g` | number | grams | Declared outcome 3. Weight of one thousand seeds. One decimal place. |
| 6 | `plant_height_cm` | number | centimetres | Declared outcome 4. Plant height at maturity, averaged over the plot. One decimal place. |
| 7 | `seed_protein_pct` | number | percent | Declared outcome 5. Seed protein content as a percentage of dry matter. One decimal place. |
| 8 | `chocolate_spot_severity_pct` | number | percent | Declared outcome 6. Chocolate spot leaf disease severity, as percent of leaf area affected. One decimal place. |

## Ranges present in the file

These are the smallest and largest values in each outcome column across all sixty
plots. They are descriptive of the file as written; they are not group summaries.

| Column | Minimum | Maximum |
|--------|---------|---------|
| `grain_yield_t_ha` | 3.08 | 5.87 |
| `pods_per_plant` | 7.9 | 23.2 |
| `thousand_seed_weight_g` | 401.7 | 599.6 |
| `plant_height_cm` | 81.0 | 128.4 |
| `seed_protein_pct` | 24.9 | 31.5 |
| `chocolate_spot_severity_pct` | 2.2 | 25.8 |

## Format notes

- Comma separated, UTF-8, one header row, Unix line endings.
- No quoting is needed; no field contains a comma.
- Rows are ordered by `plot_id`. Sowing times are interleaved through the plot
  numbers, not blocked, because sowing time was assigned at random across the
  sixty plots.
