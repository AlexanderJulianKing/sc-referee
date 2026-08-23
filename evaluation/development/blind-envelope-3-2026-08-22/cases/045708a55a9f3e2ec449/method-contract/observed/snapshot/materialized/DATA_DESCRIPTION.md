# Data description

## File

`cortisol_transport.csv` — 60 data rows plus one header row, comma separated, UTF-8.

## What one row represents

One row is a single serum cortisol reading from the assay plate. Each horse gave one blood sample,
and that one sample was measured three separate times on the same plate, so each horse appears on
three rows. The three rows for a horse carry the same `horse_id`, the same `transport_condition` and
the same `age_years`, and differ only in `replicate` and in `cortisol_nmol_l`.

## Units and counts

- 20 horses, all from a single riding centre.
- 1 blood sample per horse, drawn two hours after the transported group returned.
- 3 assay readings per sample.
- 20 x 3 = 60 rows of data.

## The two groups

`transport_condition` splits the animals into two groups of ten:

| Group | Horses | Rows | What the animals did |
| --- | --- | --- | --- |
| `transported` | 10 (H01–H10) | 30 | Completed a four-hour road journey and returned to the centre |
| `stayed` | 10 (H11–H20) | 30 | Remained in the home yard for the same period |

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `horse_id` | text | Identifier of the animal, `H01` through `H20`. Repeats three times, once per assay reading of that horse's sample. |
| `transport_condition` | text | Group label, either `transported` or `stayed`. Fixed for a horse. |
| `replicate` | integer | Which of the three assay readings of that horse's sample the row holds: 1, 2 or 3. Replicate numbers refer only within a horse, so `replicate` 1 for H01 and `replicate` 1 for H02 are unrelated measurements. |
| `cortisol_nmol_l` | number | Serum cortisol for that reading, in nanomoles per litre, recorded to one decimal place. |
| `age_years` | integer | Age of the horse in whole years at the time of sampling. Fixed for a horse. |

## Observed values

| Group | Mean cortisol (nmol/L) | Range (nmol/L) |
| --- | --- | --- |
| `transported` | 119.2 | 81.5 to 153.1 |
| `stayed` | 74.3 | 42.6 to 117.1 |

Animals differ from one another by roughly 22 nmol/L. The three assay readings taken from one tube of
serum sit much closer together, roughly 6 nmol/L apart.

Ages run from 4 to 17 years, with a mean of 11.4 years.

## Provenance

The file was produced by `make_data.py` in this folder, run under Python 3 with a fixed random seed
(57704). Re-running that script rewrites `cortisol_transport.csv` with identical contents.
