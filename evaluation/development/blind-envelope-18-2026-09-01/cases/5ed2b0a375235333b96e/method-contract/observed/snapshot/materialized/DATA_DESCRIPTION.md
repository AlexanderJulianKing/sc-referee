# Data description: `data.csv`

Serum micronutrient status in adults with coeliac disease on a gluten-free diet for at least one
year, and in healthy adult controls matched on age band and sex.

## What one row represents

One row is one participant, sampled once. Each row carries that participant's identifier, disease
group, assigned study half, and the six serum measurements taken at that single visit. There are
120 rows plus a header: 120 participants, each appearing exactly once. Every participant has a
value for every outcome; there are no blank cells.

Group sizes are balanced by design: 60 coeliac and 60 control participants, 60 in the discovery
half and 60 in the validation half, and 30 of each disease group inside each half. The half
assignment was made by the study statistician before any measurement was taken.

## Columns

| Column | Type | Meaning |
| --- | --- | --- |
| `participant_id` | text | Participant identifier, `P001` through `P120`. Unique in the file. |
| `disease_group` | text | Disease status. Exactly two values: `coeliac` (coeliac disease, gluten-free diet for at least one year) or `control` (healthy adult control). |
| `study_half` | text | Which half the participant was assigned to before measurement. Exactly two values: `discovery` or `validation`. |
| `serum_ferritin_ug_l` | number | Declared outcome 1. Serum ferritin in micrograms per litre (ug/L). Reported as whole numbers. |
| `serum_vitamin_b12_pmol_l` | number | Declared outcome 2. Serum vitamin B12 in picomoles per litre (pmol/L). Reported as whole numbers. |
| `serum_folate_nmol_l` | number | Declared outcome 3. Serum folate in nanomoles per litre (nmol/L). Reported to one decimal place. |
| `serum_zinc_umol_l` | number | Declared outcome 4. Serum zinc in micromoles per litre (umol/L). Reported to one decimal place. |
| `serum_25oh_vitamin_d_nmol_l` | number | Declared outcome 5. Serum 25-hydroxyvitamin D in nanomoles per litre (nmol/L). Reported to one decimal place. |
| `serum_magnesium_mmol_l` | number | Declared outcome 6. Serum magnesium in millimoles per litre (mmol/L). Reported to two decimal places. |

The six outcome columns appear in the file in the order the analysis plan declared them: ferritin,
vitamin B12, folate, zinc, 25-hydroxyvitamin D, magnesium.

## Value ranges present in the file

| Column | Minimum | Maximum |
| --- | --- | --- |
| `serum_ferritin_ug_l` | 10 | 118 |
| `serum_vitamin_b12_pmol_l` | 173 | 580 |
| `serum_folate_nmol_l` | 8.6 | 34.3 |
| `serum_zinc_umol_l` | 9.0 | 18.3 |
| `serum_25oh_vitamin_d_nmol_l` | 24.4 | 87.9 |
| `serum_magnesium_mmol_l` | 0.69 | 0.98 |

## Provenance

`data.csv` is a fixed authored file, written once and then left unchanged. The analysis reads it
and never creates, simulates, or modifies data.
