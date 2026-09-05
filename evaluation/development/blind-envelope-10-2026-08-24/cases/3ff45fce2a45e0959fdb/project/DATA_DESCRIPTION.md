# Data description

Community wound-care service comparison of two dressing types for chronic venous leg ulcers: a
standard foam dressing and an alginate dressing, both used under the same compression bandaging
regimen. Ninety adult patients, each with a single venous leg ulcer, forty-five assigned to each
dressing type, each followed for twelve weeks. One ulcer per patient.

## Files

| File | Role |
| --- | --- |
| `make_data.py` | Deterministic seeded generator (seed 20260824, NumPy `default_rng`). Running it rewrites the CSV below byte for byte. |
| `venous_ulcer_dressings.csv` | The analysis input. 90 data rows plus one header row. |

## `venous_ulcer_dressings.csv`

**One row is one patient**, and it carries that patient's single studied ulcer: the dressing the
patient was assigned to, plus the six protocol outcomes, each measured once for that patient over the
whole twelve-week follow-up period. No patient appears twice. There are no empty cells; every patient
has a value for every outcome.

Columns, in file order:

| Column | Type | Range in this file | Meaning |
| --- | --- | --- | --- |
| `patient_id` | text | `WLU-001` to `WLU-090` | Study identifier for the patient. Unique across the file. `WLU-001` through `WLU-045` are the foam arm, `WLU-046` through `WLU-090` the alginate arm. |
| `dressing_group` | text | exactly two values: `dressing_foam`, `dressing_alginate` | Which dressing the patient was assigned. 45 patients per value. |
| `area_reduction_pct` | number, 1 decimal | 17.5 to 95.0 | Ulcer area reduction from baseline, in percent, at twelve weeks. Higher means more of the ulcer closed. |
| `pain_vas_mm` | integer | 15 to 67 | Worst weekly ulcer pain the patient reported, on a 0 to 100 millimetre visual analogue scale. Higher means more pain. |
| `exudate_score` | number, 1 decimal | 1.0 to 8.0 | Clinician exudate (wound fluid) score on a 0 to 10 scale. Higher means a wetter wound. |
| `periwound_erythema_mm` | number, 1 decimal | 0.0 to 25.0 | Width of the reddened skin ring around the wound edge, in millimetres. Higher means more surrounding inflammation. |
| `days_to_half_healing` | integer | 10 to 80 | Days from baseline until the ulcer reached fifty percent of its starting area. Lower means faster healing. |
| `wound_qol_score` | integer | 40 to 90 | Wound-specific quality of life score on a 0 to 100 scale. Higher is better. |

The six outcome columns are listed here in the order the protocol declared them:
`area_reduction_pct`, `pain_vas_mm`, `exudate_score`, `periwound_erythema_mm`,
`days_to_half_healing`, `wound_qol_score`.

## How the values were produced

`make_data.py` draws each patient a standardised baseline ulcer severity value, then draws each of
the six outcomes from a group mean plus a loading on that severity value plus independent noise, and
clips each outcome to its plausible clinical range. The shared severity term is why the outcomes move
together within a patient: a larger, wetter, more painful ulcer also tends to heal more slowly and to
score worse on quality of life. Group means differ modestly on some outcomes and are set to be close
on others. A small number of values land exactly on a range boundary because of the clipping step
(for example `0.0` mm erythema, meaning no visible periwound redness).
