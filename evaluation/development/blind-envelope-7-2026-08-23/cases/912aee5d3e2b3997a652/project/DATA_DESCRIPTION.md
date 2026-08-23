# Data description

## File

`sugar_beet_field_yields.csv` — one data file, plain text, comma separated, with a header row.
It holds the harvest record for the on-farm sugar beet seed treatment trial run over a single
growing season in one region.

The file was written once by `make_data.py` (Python standard library, fixed random seed) and is
stored as a committed text file. Nothing regenerates it at analysis time.

## What one row represents

One row is one whole commercial sugar beet field. Each field sits on a different farm, was drilled
with one seed treatment, and was harvested whole by the contractor. The delivered clean root
weight for that field was read once off the weighbridge tickets and turned into a yield per
hectare. So each field appears exactly once and contributes exactly one yield figure. The field is
the experimental unit.

## Units and row count

- 34 fields, on 34 different farms.
- 34 rows, plus one header row (35 lines in the file).
- No repeated measurements, no subsamples, no split plots. Rows and fields are one to one.

## The two groups

The `seed_treatment` column splits the fields into two groups of equal size:

| Group value  | Meaning                                                            | Fields |
|--------------|--------------------------------------------------------------------|--------|
| `standard`   | Seed carrying the standard fungicidal seed treatment only           | 17     |
| `biological` | Seed carrying the standard fungicidal treatment plus an added biological seed coating | 17 |

Seventeen fields per group, 34 in total. Each field belongs to exactly one group.

## Columns

| Column                  | Type              | Units    | Description |
|-------------------------|-------------------|----------|-------------|
| `field_id`              | text              | none     | Identifier for the field in the regional trial numbering, `SB-101` through `SB-134`. Unique across the file; one identifier per farm. |
| `seed_treatment`        | text (2 levels)   | none     | The seed treatment that field was drilled with: `standard` or `biological`. See the group table above. |
| `field_area_ha`         | number, 1 decimal | hectares | Drilled area of the field. An agronomic covariate recorded for context; it ranges from 6.0 to 26.6 ha. |
| `clean_root_yield_t_ha` | number, 1 decimal | tonnes per hectare | The outcome. Delivered clean root yield for the whole field, from the weighbridge tickets, divided by the drilled area. Values run from 51.7 to 79.9 t/ha. |

There are no missing values in any column.

## Rough shape of the outcome

Field to field variation is large, as expected on farm, and comes from soil type, drilling date and
in-season rainfall.

| Group        | Fields | Mean yield (t/ha) | SD (t/ha) | Min  | Max  |
|--------------|--------|-------------------|-----------|------|------|
| `standard`   | 17     | 61.1              | 7.3       | 51.7 | 75.5 |
| `biological` | 17     | 66.9              | 7.1       | 55.5 | 79.9 |

These figures are given here only to describe the file. The trial result is worked out in the
analysis script.
