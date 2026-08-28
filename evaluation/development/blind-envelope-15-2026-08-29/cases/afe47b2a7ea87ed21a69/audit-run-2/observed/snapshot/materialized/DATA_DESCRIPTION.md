# Data description

`data.csv` holds the field records of an occupational hygiene survey of nail salon technicians and
solvent vapour exposure. Fifty-six technicians took part, each working in a different salon, each
monitored across one full working shift of similar length and client load. Twenty-eight worked at
benches fitted with source-capture local exhaust ventilation and twenty-eight worked at benches with
no source capture and general room ventilation only. Each technician wore a personal sampler for the
shift, gave an end-of-shift urine sample, and completed the symptom items at the end of the shift.

**One row is one technician**, carrying that technician's bench type and their five shift outcome
measurements. There are 56 data rows plus one header row. There are no repeated rows, no summary
rows, and no blank cells.

## Columns

| # | Column | Meaning | Unit or scale |
|---|--------|---------|---------------|
| 1 | `technician_id` | Identifier for the technician, and so for the salon and the monitored shift. Values run `tech_01` through `tech_56` and are unique. | text label |
| 2 | `ventilation` | Bench type the technician worked at. `capture` = bench fitted with source-capture local exhaust ventilation; `no_capture` = bench with no source capture, general room ventilation only. | text label, two levels |
| 3 | `tvoc_mg_m3` | Personal airborne total volatile organic compounds over the shift, from the technician's personal sampler. | milligrams per cubic metre, 2 decimals |
| 4 | `urinary_acetone_mg_l` | Acetone in the end-of-shift urine sample. | milligrams per litre, 2 decimals |
| 5 | `eye_irritation_0_10` | Self-reported eye irritation at the end of the shift. | 0 to 10 rating, whole numbers, higher is worse |
| 6 | `headache_0_10` | Self-reported headache at the end of the shift. | 0 to 10 rating, whole numbers, higher is worse |
| 7 | `neurobehavioural_score_0_30` | Score on the neurobehavioural symptom questionnaire completed at the end of the shift. | 0 to 30 points, whole numbers, higher is worse |

Columns 3 through 7 are the five outcomes that were declared in the survey protocol, and they appear
here in that declared order. Every technician has a value for every outcome, so there are no missing
values anywhere in the file.

Rounding follows the usual practice: the two laboratory measurements (airborne TVOC and urinary
acetone) are reported to two decimal places, and the three questionnaire outcomes are reported as
whole numbers because that is what the paper form records.

`data.csv` is a fixed data file. Analysis code reads it and never generates, simulates, or
overwrites it.
