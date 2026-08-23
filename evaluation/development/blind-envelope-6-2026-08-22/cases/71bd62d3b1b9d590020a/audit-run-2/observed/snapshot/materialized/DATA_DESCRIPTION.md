# Data description

## File

`pvf_repeated_measures.csv` — one CSV holding every repeated measurement. No rows are
averaged or collapsed.

The file is produced by `make_data.py` (Python standard library only, fixed random seed
`20260822`), so re-running the generator reproduces the file exactly.

## What one row represents

One row is **one visit by one dog**: a single force-platform gait trial summary for a single
dog at a single scheduled visit. Each dog appears on five rows, one per visit.

## Units and counts

- Units of randomisation and analysis: **24 client-owned dogs**, each enrolled once.
- Treatment arms: **2**, with **12 dogs in each**.
  - `established` — the established analgesic (comparator arm).
  - `new` — the new analgesic (test arm).
- Visits per dog: **5** (baseline plus weeks 2, 4, 8 and 12).
- Total rows: **120** data rows (24 dogs x 5 visits), plus one header row.
- No missing values; the design is fully balanced, so every dog has all five visits.

## Columns

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `dog_id` | string | — | Stable identifier for the individual dog, `D01`–`D24`. Repeats across the five rows belonging to that dog. This is the grouping variable that makes the rows non-independent. |
| `treatment_arm` | string | — | Which analgesic the dog was assigned to: `established` or `new`. Constant across all five rows for a given dog. |
| `visit_week` | integer | weeks since baseline | Scheduled visit time: `0` (baseline, before treatment), `2`, `4`, `8`, `12`. |
| `body_weight_kg` | float, 1 decimal | kilograms | Body weight recorded at that visit. Ranges from about 18 to 42 kg across the cohort and varies only slightly within a dog between visits. |
| `peak_vertical_force_pctbw` | float, 2 decimals | percent of body weight (%BW) | Outcome. Peak vertical force through the affected forelimb during the trial, expressed as a percentage of the dog's body weight. Higher values mean better weight-bearing on the affected limb. |

## How the values behave

- Baseline peak vertical force sits near 60 %BW in both arms.
- Force rises over the follow-up period in both arms, reaching roughly 66 %BW at week 12 in
  the `established` arm and roughly 71 %BW at week 12 in the `new` arm.
- Dogs differ substantially from one another, and those differences persist across all five
  of a dog's visits (a per-dog offset of roughly 3 %BW standard deviation). Visit-to-visit
  noise within a dog is smaller (about 1.2 %BW standard deviation).
- Because the five rows from one dog share that dog's offset, the rows are correlated.
  Treating the 120 rows as 120 independent observations would overstate the amount of
  information in the study; the effective sample size is 24 dogs.

## Note

These are simulated data created for this analysis project. They are not measurements from
real animals.
