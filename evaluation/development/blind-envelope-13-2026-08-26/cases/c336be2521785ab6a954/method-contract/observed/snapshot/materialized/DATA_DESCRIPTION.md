# Data description

## File

`cotton_density_plants.csv` — 48 data rows plus one header row.

## What one row represents

One row is one sampled cotton plant, measured once at harvest. Each plant was
grown at one of two within-row planting densities at a single research farm and
belongs to exactly one density group. Twenty-four plants were sampled at the
conventional density and twenty-four at the high density. There are no repeated
measures: a plant appears in exactly one row, and every cell is filled.

## Columns

Columns appear in the file in the order listed below. The six outcome columns
follow the order in which the outcomes were declared in the trial protocol.

| Column | Meaning | Unit | Type |
| --- | --- | --- | --- |
| `plant_id` | Identifier for the sampled plant (`P001` through `P048`), unique across the file | none | text |
| `planting_density` | Within-row planting density group the plant was grown at. Exactly two values: `conventional` (about 10 plants per metre of row) and `high` (about 15 plants per metre of row) | none | text |
| `bolls_per_plant` | Declared outcome 1: number of harvestable bolls counted on the plant | count of bolls | integer |
| `lint_yield_g` | Declared outcome 2: lint yield of the plant after ginning | grams | decimal (1 place) |
| `upper_half_mean_length_mm` | Declared outcome 3: upper half mean fibre length, the average length of the longer half of the fibres in the sample | millimetres | decimal (2 places) |
| `micronaire` | Declared outcome 4: micronaire reading, an air-flow measure of fibre fineness and maturity | unitless | decimal (2 places) |
| `plant_height_cm` | Declared outcome 5: height of the plant from the soil surface to the terminal | centimetres | decimal (1 place) |
| `first_fruiting_branch_node` | Declared outcome 6: node number on the main stem carrying the first fruiting branch, counted upward from the cotyledonary node | node number (count) | integer |

## Provenance

The values are invented for this exercise, not measured. They were produced by
`generate_data.py` in this directory, which draws each outcome from a normal
distribution with an agronomically plausible mean and spread per density group
and clips the draws to a realistic range. The generator uses a fixed random seed
(20260826), so rerunning it reproduces the same file.
