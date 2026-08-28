# Data description

## What the file holds

`data.csv` holds the week-twelve visit records for an ophthalmology study comparing two
formulations of the same glaucoma eye drop in patients with ocular hypertension. Sixty patients
contribute one study eye each: thirty allocated to the preservative-free formulation and thirty to
the preserved formulation. Every patient attended the week-twelve visit, and all measurements were
taken by masked assessors.

**One row is one patient**, identified by `patient_id`, holding that patient's formulation group and
that patient's week-twelve value for each of the five declared outcomes in the study eye. There are
sixty rows plus a single header row: no repeated rows, no summary or total rows, and no blank cells.

The five outcome columns appear in the order the outcomes were declared in the study protocol,
before allocation.

## Columns

| # | Column | Meaning | Unit or scale | Type and recording granularity |
|---|--------|---------|---------------|-------------------------------|
| 1 | `patient_id` | Patient identifier, unique within the file | none | Text, `oht_` prefix plus a zero-padded two-digit number, `oht_01` through `oht_60`, running in enrolment order |
| 2 | `formulation` | Formulation the patient was allocated to | none | Text, exactly two labels: `preservative_free` and `preserved` |
| 3 | `intraocular_pressure_mmhg` | Intraocular pressure in the study eye at week twelve, declared outcome 1 | millimetres of mercury (mmHg) | Integer, Goldmann applanation recorded to the nearest whole mmHg |
| 4 | `osdi_score_0_100` | Ocular Surface Disease Index symptom score at week twelve, declared outcome 2 | points on a 0 to 100 scale, higher means more symptoms | Decimal, one place |
| 5 | `tear_film_breakup_time_s` | Tear film break-up time in the study eye at week twelve, declared outcome 3 | seconds (s), higher means a more stable tear film | Decimal, one place |
| 6 | `conjunctival_hyperaemia_grade_0_3` | Conjunctival hyperaemia (redness) grade at week twelve, declared outcome 4 | grade on a 0 to 3 scale, higher means more redness | Decimal recorded in half-grade steps: 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0 |
| 7 | `corneal_staining_score_0_15` | Corneal staining score at week twelve, declared outcome 5 | points on a 0 to 15 scale, higher means more staining | Integer |

## Observed ranges in the file

| Column | Minimum | Maximum |
|--------|---------|---------|
| `intraocular_pressure_mmhg` | 11 | 34 |
| `osdi_score_0_100` | 0.0 | 48.8 |
| `tear_film_breakup_time_s` | 2.3 | 13.8 |
| `conjunctival_hyperaemia_grade_0_3` | 0.0 | 2.5 |
| `corneal_staining_score_0_15` | 0 | 6 |

## Data provenance notes

- Patient `oht_32` has a week-twelve intraocular pressure of 34 mmHg. The site later flagged that
  visit as a suspected tonometer calibration problem, so the reading is implausibly high for this
  population. The value is kept in `data.csv` exactly as recorded; it is neither corrected nor
  removed from the data file.
- Every patient has a value for every outcome, so there is no missing data to handle.
- `data.csv` is a fixed data file. It is read as input and is never generated, simulated, or
  overwritten by downstream code.
