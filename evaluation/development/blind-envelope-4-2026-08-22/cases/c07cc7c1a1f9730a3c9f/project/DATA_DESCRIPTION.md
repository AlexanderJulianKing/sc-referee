# Data description: interleukin-6 assay table

## File

`il6_assay.csv` — the single data file for this project. It holds a header row and 90 data rows.

The file is produced by `make_data.py` (Python standard library only, fixed random seed 20260851).
Re-running the generator rewrites exactly the same file.

## What one row is

One row is one assay run on one serum sample: the interleukin-6 concentration returned by a single
run of the immunoassay for a single banked sample.

## Units and counts

- 30 people, one banked serum sample per person, referenced `S-101` through `S-130`.
- Each sample was assayed 3 times on the same plate, so the three rows that share a `sample_ref`
  are repeat assay runs on the same aliquot of that person's serum.
- 30 samples x 3 runs = 90 data rows.

## The two groups

| Cohort value | Meaning | People | Rows |
| --- | --- | --- | --- |
| `control` | Matched healthy volunteers | 15 (`S-101` to `S-115`) | 45 |
| `RA` | Adults with newly diagnosed rheumatoid arthritis | 15 (`S-116` to `S-130`) | 45 |

The two groups are matched and each contributes half the samples and half the rows.

## Columns

Columns appear in this order.

| # | Column | Type | Values | Meaning |
| --- | --- | --- | --- | --- |
| 1 | `sample_ref` | text | `S-101` … `S-130` | Identifier of the banked serum sample. One sample per person, so this also identifies the person. Appears on 3 rows, once per assay run. |
| 2 | `cohort` | text | `control`, `RA` | Study group the person belongs to. Constant across the 3 rows of a sample. |
| 3 | `replicate_run` | integer | `1`, `2`, `3` | Which of the three assay runs of that sample this row reports. Numbering restarts at 1 for every sample. |
| 4 | `il6_pg_ml` | number | 2 decimal places, always above zero | Interleukin-6 concentration measured on that run, in picograms per millilitre. |

## Observed values

Figures below describe the delivered file.

- `control`: sample concentrations average 4.18 pg/mL, person-to-person standard deviation
  2.24 pg/mL, rows spanning 1.26 to 8.81 pg/mL.
- `RA`: sample concentrations average 7.79 pg/mL, person-to-person standard deviation
  2.09 pg/mL, rows spanning 5.10 to 12.52 pg/mL.
- The distribution in each group is right-skewed, and a few patients reach the low teens.
- Within a sample, the highest and lowest of the three runs differ by 4.9 to 7.1 percent of that
  sample's own concentration.
