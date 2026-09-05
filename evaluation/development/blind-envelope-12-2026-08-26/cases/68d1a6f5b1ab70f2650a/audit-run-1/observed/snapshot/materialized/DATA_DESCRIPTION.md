# Data description

## Files

### `make_data.py`
Deterministic, seeded Python generator (standard library only, `SEED = 20260826`). Running it
writes `allergy_spray_trial.csv` next to itself. Re-running reproduces the same file exactly.

### `allergy_spray_trial.csv`
The analysis input. 60 data rows plus one header row, comma separated, UTF-8, no missing values.

**One row represents one enrolled adult patient**, holding that patient's treatment arm and the
five protocol outcomes as recorded at their single end-of-treatment visit after four weeks of
treatment. Each patient appears exactly once. 30 patients are in each arm.

#### Columns, in file order

| Column | Type | Unit / scale | What it holds |
| --- | --- | --- | --- |
| `patient_id` | text | none | Patient identifier, `P001` through `P060`. Unique across the file. |
| `group` | text | none | Treatment arm. Exactly two possible entries: `corticosteroid` (intranasal corticosteroid spray, once daily) and `antihistamine` (intranasal antihistamine spray, twice daily). |
| `tnss_total` | integer | points, 0–12 | Total nasal symptom score at end of treatment. Sum of four nasal symptoms each scored 0–3. Higher is worse. |
| `pnif_l_min` | integer | litres per minute | Peak nasal inspiratory flow at end of treatment. Higher is better. |
| `disturbed_nights` | integer | nights, 0–7 | Number of nights in the past week with sleep disturbed by nasal symptoms. Higher is worse. |
| `tos_total` | integer | points, 0–9 | Total ocular symptom score. Sum of three eye symptoms each scored 0–3. Higher is worse. |
| `rqlq_total` | decimal, 2 places | points, 0–6 | Rhinoconjunctivitis quality of life total score, averaged to a 0–6 scale. Higher is worse. |

The five outcome columns appear in the protocol's declared order.

## How the values were made

Each patient gets one latent "residual allergy burden" draw, and all five outcomes are generated
from that draw plus independent measurement noise, so the outcomes are correlated within a patient
the way they are in real clinic data. Arm-specific baselines shift the outcomes between the two
regimens. Three patients in each arm are generated as poor responders: they are still clearly
symptomatic at the end-of-treatment visit. Every generated value is clamped to its instrument's
allowed range; counts and symptom scores are rounded to integers, and the quality of life score is
rounded to two decimal places.

Observed values in the delivered file:

| Column | Range across all 60 patients |
| --- | --- |
| `tnss_total` | 1 to 10 |
| `pnif_l_min` | 86 to 171 |
| `disturbed_nights` | 0 to 6 |
| `tos_total` | 1 to 6 |
| `rqlq_total` | 0.52 to 4.17 |
