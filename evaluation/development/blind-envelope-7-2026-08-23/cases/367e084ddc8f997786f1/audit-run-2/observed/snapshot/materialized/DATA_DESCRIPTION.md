# Data description

## File

`cistern_faecal_indicator.csv` — one plain-text CSV, comma separated, with a header row and
36 data rows.

## What one row represents

One row is **one assay replicate**: a single run of the faecal indicator gene assay on one
laboratory extract. It is not an independent water sample and it is not a cistern.

## Sampling units and counts

- **12 household rainwater storage cisterns** in one district, each sampled **once** during
  the wet season.
- Each water sample was split in the laboratory, and the same molecular assay for a faecal
  indicator gene was run **3 times on the same extract** as instrument triplicates.
- 12 cisterns x 3 assay replicates = **36 rows**.
- Total assay measurements per roof-material group: **18** (6 cisterns x 3 replicates).

## The two groups

The grouping variable is the roof catchment material feeding the cistern.

| Group value | Meaning | Cisterns | Rows |
| --- | --- | --- | --- |
| `coated_metal` | Cistern fed by a coated-metal roof catchment | 6 (`CIS-01`–`CIS-06`) | 18 |
| `asphalt_shingle` | Cistern fed by an asphalt-shingle roof catchment | 6 (`CIS-07`–`CIS-12`) | 18 |

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `cistern_id` | text | Identifier of the household rainwater storage cistern the sample came from. Format `CIS-NN`, values `CIS-01` through `CIS-12`. Each identifier appears on exactly 3 rows, one per assay replicate. |
| `roof_catchment_material` | text (category) | Material of the roof catchment feeding that cistern. Two values: `coated_metal` and `asphalt_shingle`. Constant within a cistern. |
| `assay_replicate` | integer | Which of the three instrument replicates on that cistern's extract the row reports. Values 1, 2, 3. |
| `log10_gene_copies_per_100ml` | decimal number, 2 places | Measured faecal indicator gene concentration for that assay replicate, as the base-ten logarithm of gene copies per 100 mL of water. |

## Observed ranges

| Group | Rows | Mean | SD | Min | Max |
| --- | --- | --- | --- | --- | --- |
| `coated_metal` | 18 | 2.82 | 0.28 | 2.41 | 3.29 |
| `asphalt_shingle` | 18 | 3.63 | 0.25 | 3.28 | 4.05 |

All values fall between 1.8 and 4.6 log copies per 100 mL.

## How the file was made

`make_data.py` (Python standard library only, fixed seed `20260823`) draws a true mean log
concentration for each cistern around its roof-material group mean (2.90 for coated metal,
3.60 for asphalt shingle) with a cistern-to-cistern spread of 0.45 log units, then draws the
three replicate measurements around that cistern mean with a within-extract spread of 0.12
log units. Values are clamped to the 1.8–4.6 range and rounded to two decimals. The CSV is
committed as plain text; the analysis reads the file and does not regenerate it.
