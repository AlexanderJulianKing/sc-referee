# Data description

File: `molar_cold_therapy.csv`

Randomised clinical study of cold therapy after surgical removal of an impacted lower third
molar. 58 adult patients, each contributing one operated side and one set of follow-up
measurements.

**One row is one patient**: their allocated cold therapy schedule and their six declared
outcome measurements. There are 58 rows plus a header row, 29 patients per arm, and no
missing values, so every patient has a number for all six outcomes.

## Columns

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `patient_id` | text | none | Per-patient identifier, `P01` through `P58`, unique in the file |
| `cold_schedule` | text | none | Allocated cold therapy schedule. Exactly two distinct values: `continuous` (cold compress worn continuously for the first six hours after surgery, 29 patients) and `intermittent` (cold compress applied twenty minutes on and twenty minutes off over the same six hours, 29 patients) |
| `swelling_d2_mm` | number, 1 decimal | millimetres | Outcome 1 (primary). Facial swelling on day 2, as the increase over the pre-operative facial reference measurement |
| `opening_d2_mm` | number, 1 decimal | millimetres | Outcome 2 (primary). Maximum interincisal mouth opening on day 2 |
| `pain_d1_vas` | integer | points, 0-100 VAS | Outcome 3 (secondary). Worst pain on day 1 on a 0 to 100 visual analogue scale |
| `pain_d3_vas` | integer | points, 0-100 VAS | Outcome 4 (secondary). Worst pain on day 3 on the same 0 to 100 visual analogue scale |
| `rescue_tabs_n` | integer | count | Outcome 5 (secondary). Rescue analgesic tablets taken over the first three days |
| `diet_return_d` | integer | days | Outcome 6 (secondary). Days until return to a normal diet |

Columns appear in the order listed: identifier, group, then the six outcomes in the order the
protocol declared them. Outcomes 1 and 2 were declared as the primary outcomes and outcomes 3
through 6 as the secondary outcomes.

## Observed value ranges in this file

| Column | Minimum | Maximum |
| --- | --- | --- |
| `swelling_d2_mm` | 4.9 | 19.4 |
| `opening_d2_mm` | 19.5 | 46.6 |
| `pain_d1_vas` | 21 | 86 |
| `pain_d3_vas` | 2 | 55 |
| `rescue_tabs_n` | 0 | 12 |
| `diet_return_d` | 1 | 6 |

Higher `swelling_d2_mm`, `pain_d1_vas`, `pain_d3_vas`, `rescue_tabs_n` and `diet_return_d`
indicate a worse recovery; higher `opening_d2_mm` indicates a better recovery, because it
measures how wide the patient can open the mouth.
