# Data description

## File

`sedation_abg.csv` — the single data file for this project. It holds the arterial blood gas
measurements collected in the single-centre ICU comparison of two sedation protocols.
The file has one header line and 144 data rows.

The data are synthetic. They were produced by `make_data.py` (Python standard library only,
fixed random seed) with plausible values and plausible variability. No real patient data and
no real dataset were used.

## What one row is

One row is one arterial blood gas measurement taken on one patient at one scheduled time point.

## Units and counts

- Units of observation: 24 mechanically ventilated adults with moderate respiratory failure,
  labelled `ICU-01` through `ICU-24`.
- Measurements per patient: 6, taken at enrolment and then at 6, 12, 24, 36 and 48 hours.
- Total data rows: 144 (24 patients x 6 time points). Every patient has all six time points,
  with no missing values.
- The six rows that share a `PatientID` are successive time points on the same person.

## The two groups

`SedationArm` splits the patients into two protocol groups of equal size:

| Arm     | Patients | Patient IDs        | Rows |
|---------|----------|--------------------|------|
| `light` | 12       | ICU-01 to ICU-12   | 72   |
| `deep`  | 12       | ICU-13 to ICU-24   | 72   |

A patient stays in the same arm for all six of their measurements.

## Columns

The columns appear in this order.

| # | Column               | Type            | Values / range        | Meaning |
|---|----------------------|-----------------|-----------------------|---------|
| 1 | `PatientID`          | text            | `ICU-01` … `ICU-24`   | Identifier of the patient the measurement was taken on. Repeats six times, once per time point. |
| 2 | `SedationArm`        | text (2 levels) | `light`, `deep`       | The sedation protocol the patient was managed under. Constant within a patient. |
| 3 | `HoursFromEnrolment` | integer         | 0, 6, 12, 24, 36, 48  | Hours between enrolment and this blood gas. `0` is the enrolment measurement. |
| 4 | `PFRatio`            | integer         | 114 – 339 as generated | Ratio of arterial oxygen tension to inspired oxygen fraction (PaO2/FiO2) for this blood gas, in mmHg. Whole numbers, generated inside a clinically believable 110–400 mmHg range. |

## How the values were generated

For each patient a single level was drawn around the average of their arm (about 245 mmHg for
light sedation and about 215 mmHg for deep sedation across the observation window), with a
between-patient standard deviation of 45 mmHg. Each of that patient's six measurements then
adds a mild upward drift of 15 mmHg spread linearly from enrolment to 48 hours, plus independent
measurement-to-measurement variation with a standard deviation of 30 mmHg. Results were rounded
to whole numbers and held inside 110–400 mmHg.

As generated, the light arm averages 243.8 mmHg and the deep arm 214.9 mmHg across all rows,
the standard deviation of the 24 patient-level means is 40.3 mmHg, and the row average rises
from 222.0 mmHg at enrolment to 238.2 mmHg at 48 hours.

## Reproducing the file

```
python3 make_data.py
```

This rewrites `sedation_abg.csv` in place. The seed is fixed in the script, so the file is
byte-for-byte reproducible. sha256 of the current file:

```
b9c4eed431344441df765b4b3dbe60ea243861f588317c0f52eb2a19033eaf6a
```
