# Data description

File: `exposure_data.csv`

## What one row represents

One row is one worker. The 58 workers of the glasshouse applicator study each
appear exactly once, and the row holds that worker's application method
together with all five declared outcome measurements taken around the same
monitored shift. There are 58 data rows under a single header row, 29 workers
per application method, and no missing cells.

The values in the CSV are fixed and committed. `make_data.py` is the generator
that produced the file; nothing in the project regenerates the data at run
time.

## Columns

The file has seven columns in this order.

| Column | Type | Description |
| --- | --- | --- |
| `worker_id` | text | Worker identifier, the prefix `W` plus a zero-padded serial number, `W01` through `W58`. Unique across the file. Serial numbers follow enrolment order, so the two application methods are mixed rather than blocked. |
| `application_method` | text | Group column. Exactly two distinct values: `knapsack` for the workers who applied the products with a hand-held knapsack lance while walking the crop rows, and `trolley` for the workers who used the automated spray trolley operated from outside the closed compartment. |
| `urinary_dap_ug_per_g_creatinine` | number, 1 decimal place | Declared outcome 1. Urinary dialkyl phosphate metabolite concentration in the post-shift sample, in micrograms per gram of creatinine. Observed range 1.9 to 23.9. |
| `cholinesterase_pct_baseline` | number, 1 decimal place | Declared outcome 2. Post-shift plasma cholinesterase activity, as a percentage of that same worker's own pre-season baseline. Values below 100 mean activity fell against the worker's baseline. Observed range 81.1 to 105.5. |
| `dermal_deposition_ug_per_hand` | whole number | Declared outcome 3. Dermal deposition from hand-wash sampling, in micrograms per hand. Observed range 12 to 559. |
| `inhalation_pad_ug` | number, 1 decimal place | Declared outcome 4. Inhalation pad loading over the monitored shift, in micrograms. Observed range 0.7 to 80.6. |
| `symptom_score_0_20` | whole number | Declared outcome 5. Self-reported irritation and neurological symptom score on the questionnaire's 0 to 20 scale, higher meaning more symptoms. Observed range 0 to 10. |

The five outcome columns appear in the declared order of the monitoring plan.

## Rounding and scales

Each outcome is stored at the precision its laboratory or questionnaire would
report: one decimal place for the urinary metabolite concentration, the
cholinesterase percentage and the inhalation pad loading; whole micrograms for
the hand-wash deposition; and whole points for the questionnaire score, which
is a sum of item scores and cannot fall outside 0 to 20.

The exposure measures (urinary metabolite, dermal deposition, inhalation pad)
are right-skewed, as occupational sampling data usually is, so a few workers in
each group sit well above their group's typical value. The two groups overlap
on every outcome.
