# Data description

## Files

### `pulmonary_rehab_outcomes.csv`

The analysis input. It holds the end-of-programme assessment records for the 74 adults with
stable chronic obstructive pulmonary disease who took part in the pulmonary rehabilitation
delivery-format comparison, 37 in each format.

**One row represents one patient**, assessed a single time at the end of the eight-week
programme. Each patient appears exactly once. Every patient has a value in every column; the
file contains no empty cells.

| Column | Type | Description |
| --- | --- | --- |
| `patient_id` | text | Study identifier for the patient, formatted `PR-001` through `PR-074`. Unique across the file. |
| `program_group` | text | Delivery format the patient was enrolled in. Exactly two values occur: `centre_based` (supervised centre-based programme) and `home_based` (home-based programme with remote support). 37 rows carry each value. |
| `six_min_walk_m` | integer | Six-minute walk distance in metres at end of programme. Observed range 205 to 482. |
| `cat_score` | integer | COPD assessment test score on the 0 to 40 scale, higher meaning worse symptom burden. Observed range 8 to 31. |
| `quad_torque_nm` | decimal (1 dp) | Quadriceps isometric peak torque in newton metres. Observed range 45.5 to 128.8. |
| `sit_to_stand_reps` | integer | Number of repetitions completed in the thirty-second sit-to-stand test. Observed range 7 to 22. |

Row order in the file is not grouped by `program_group`; the two formats are interleaved.

### `make_data.py`

The deterministic generator that produced the CSV above. It is seeded (`SEED = 20260824`), so
re-running it with the same Python and NumPy versions rewrites a byte-identical CSV. It draws
each patient's four outcomes together from a correlated multivariate normal per format, so that
patients who walk further also tend to be stronger, complete more sit-to-stand repetitions, and
report a lower (better) CAT score. Draws falling outside an outcome's plausible clinical range
are rejected and redrawn rather than clipped, which keeps values from piling up at the range
edges. `make_data.py` is a data-preparation script, not part of the analysis.
