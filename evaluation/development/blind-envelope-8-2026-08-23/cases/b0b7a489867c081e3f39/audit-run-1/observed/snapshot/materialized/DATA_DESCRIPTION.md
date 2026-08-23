# Data description

## File

`seagrass_survey.csv` — one file, comma separated, with a header row and 96 data rows.

The file was produced by `make_data.py` (Python standard library only, fixed random seed
`20260040`). Rerunning `python3 make_data.py` recreates the same file exactly.

## What one row represents

One row is **one sampled dive point inside one seagrass meadow**: the single shoot measured at that
point, plus the water depth and sediment type recorded at that same point.

## Survey units and layout

- 12 seagrass meadows were surveyed. Each meadow is a separate location on the coast.
- Divers placed 8 haphazard sampling points inside each meadow and measured the longest leaf on one
  shoot at each point.
- 12 meadows x 8 points = **96 rows**. Every meadow contributes exactly 8 rows, and the 8 rows of a
  meadow are spatial subsamples taken inside that same meadow.
- Meadow identifiers run `MDW01` through `MDW12`.

## The two groups

The `zone` column splits the meadows into two groups of six:

| zone value  | meadows       | meaning                                                        | rows |
|-------------|---------------|----------------------------------------------------------------|------|
| `protected` | MDW01–MDW06   | inside the boat-mooring exclusion zone, where anchoring is banned | 48 |
| `open`      | MDW07–MDW12   | adjacent water open to mooring                                   | 48 |

Zone is a property of the meadow, so all 8 rows of a given meadow carry the same zone value.

## Columns

| column | type | units | description |
|--------|------|-------|-------------|
| `meadow_id` | text | — | Identifier of the surveyed meadow, `MDW01` to `MDW12`. Repeats 8 times, once per sampled point in that meadow. |
| `zone` | text | — | Mooring status of the meadow. Exactly two values: `protected` (inside the exclusion zone) or `open` (open to mooring). |
| `point_number` | integer | — | Which of the 8 sampling points inside the meadow this row is, numbered 1 to 8. Point numbers restart at 1 in every meadow, so `meadow_id` plus `point_number` identifies a row uniquely. |
| `leaf_length_cm` | number | centimetres | Maximum leaf length: the length of the longest leaf on the one shoot measured at this point. Recorded to 0.1 cm. Observed range 25.0 to 84.3 cm. |
| `depth_m` | number | metres | Water depth at the sampling point. Recorded to 0.01 m. Observed range 1.50 to 6.00 m. |
| `sediment_type` | text | — | Sediment recorded at the sampling point. Five values appear: `fine_sand` (15 rows), `medium_sand` (24), `muddy_sand` (24), `shell_gravel` (15), `silt` (18). Sediment mix varies from meadow to meadow, so it can change between points inside one meadow. |

There are no missing values in any column.

## Summary of the response variable

Maximum leaf length (`leaf_length_cm`), all 96 rows:

| group | rows | mean (cm) | sd (cm) |
|-------|------|-----------|---------|
| `protected` | 48 | 63.43 | 10.25 |
| `open` | 48 | 48.01 | 10.16 |

Per-meadow mean leaf length ranges from 35.7 cm (MDW08, open) to 74.7 cm (MDW05, protected), and
the standard deviation of points inside a meadow runs from about 5.6 to 10.2 cm.
