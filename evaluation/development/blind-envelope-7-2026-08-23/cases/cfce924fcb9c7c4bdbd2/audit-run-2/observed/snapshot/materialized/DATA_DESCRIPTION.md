# Data description

## File

`rnfl_sector_thickness.csv` — the single raw data file for this study. Plain text, comma
separated, one header line followed by 144 data lines. It is committed as a fixed file; it is
not regenerated when the analysis runs.

`make_data.py` is the generator that produced it (Python standard library only, fixed random
seed `20260823`). It is kept for reproducibility of the dataset and is not part of the analysis.

## What one row represents

One row is **one clock-hour sector of one patient's designated study eye**, measured by optical
coherence tomography at the final visit of the one-year treatment period.

Each patient appears on six rows, one per sector. A row is therefore not an independent patient:
the six rows belonging to a patient are repeated measurements on the same eye.

## Units and counts

| Quantity | Value |
| --- | --- |
| Patients (units of randomisation and of analysis) | 24 |
| Sectors per patient study eye | 6 |
| Rows in the CSV | 144 |
| Patients on `timolol` (older regimen) | 12 |
| Patients on `latanoprost` (newer regimen) | 12 |
| Rows per regimen | 72 |

Each patient contributes exactly six rows, and every patient has a complete set of six sectors.
There are no missing values.

## The two groups

The grouping variable is `drop_regimen`, with two levels:

- **`timolol`** — the older topical pressure-lowering drop regimen. 12 patients, 72 rows.
- **`latanoprost`** — the newer topical pressure-lowering drop regimen. 12 patients, 72 rows.

Every patient stays in one regimen for the whole year, so the regimen label is constant across a
patient's six rows. The comparison of interest is between these two groups of 12 patients.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `patient_id` | text | Patient identifier, `pt_01` through `pt_24`. Repeats across the six rows belonging to that patient. This is the column that marks which rows share an eye. |
| `drop_regimen` | text | The topical pressure-lowering drop regimen the patient was treated with for one year. Exactly two values: `timolol` (older) or `latanoprost` (newer). Constant within a patient. |
| `clock_hour_sector` | text | Which peripapillary clock-hour sector of the study eye the thickness value comes from. Exactly six values: `temporal`, `superotemporal`, `superonasal`, `nasal`, `inferonasal`, `inferotemporal`. Each value occurs once per patient. |
| `rnfl_thickness_um` | number | Retinal nerve fibre layer thickness for that sector of that patient's study eye, in micrometres, recorded to one decimal place. This is the study outcome. |

## Ranges actually observed in the file

- `rnfl_thickness_um`: minimum 53.2 um, maximum 114.8 um. No value sits on the 45 um or 130 um
  guard bounds used during generation, so no value was truncated.
- Spread within one eye across its six sectors: about 12 um on average, because the superior and
  inferior arcuate sectors are anatomically thicker than the nasal and temporal ones.
- Spread between patients, after averaging each patient's six sectors: about 6 to 8 um within a
  regimen.

## Note on the analysis unit

The CSV is deliberately left in its raw sector-level form, with all six rows per patient. The
comparison of the two regimens is to be made on **one averaged thickness value per patient**, so
the sample size for the test is 12 patients per arm, not 72 rows per arm.

## Second summary file

None. This brief calls for exactly one data CSV, so no separate per-patient summary CSV was
written; the per-patient averaging happens inside the analysis.
