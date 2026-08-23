# Data description

## The file

`tumour_volumes.csv` is the single data file for this project. It holds 120 data rows plus one
header row, in comma-separated form, with no missing cells.

The file is simulated. It was produced by `make_data.py`, a standard-library Python script run under
`/usr/local/bin/python3` with the fixed seed 20260822, so re-running the script reproduces the file
exactly. No value in it came from a live animal.

## What one row represents

One row is one calliper measurement of one animal on one week. It carries that animal's tumour
volume and body weight for that week, together with the labels that identify the animal, its
treatment group, and its cage.

Rows are therefore not independent of one another. Each animal supplies five rows, and those five
rows share whatever makes that animal's tumour large or small overall.

## Units and counts

- 24 animals, the experimental units, each measured once a week for five consecutive weeks.
- 5 measurement occasions per animal, weeks 1 through 5, complete for every animal with no dropout.
- 120 rows, which is 24 animals times 5 weeks.
- 12 cages, holding two animals each.

The number of animals, 24, is the sample size for the study. The number of rows, 120, is the number
of measurements those 24 animals contributed.

## The two groups

Treatment was assigned at the level of the animal, and each animal stayed in one group for the whole
five weeks.

- `vehicle`: 12 animals given the vehicle alone, identifiers V01 through V12, housed in cage_01
  through cage_06.
- `treated`: 12 animals given the candidate compound, identifiers T01 through T12, housed in
  cage_07 through cage_12.

Cages hold two animals from the same group and never mix groups. Cage is nested inside treatment
group, so the two cannot be told apart in this design.

## Columns

The file has six columns, in this order.

| Column | Type | Description |
| --- | --- | --- |
| `animal_id` | text | Identifier of the animal, the experimental unit. Values V01 to V12 for vehicle animals and T01 to T12 for treated animals. All 24 values are distinct across the whole file. Each one appears in exactly 5 rows, once per week. This is the column that groups repeated measurements. |
| `treatment_group` | text | Which arm the animal was in, either `vehicle` or `treated`. Constant within an animal. 60 rows carry each value. |
| `week` | integer | Week the measurement was taken, 1 to 5, one row per animal per week. Week 1 is the first measurement occasion, near the start of the study, and week 5 is the last. |
| `tumour_volume_mm3` | number | Tumour volume by calliper, in cubic millimetres, rounded to one decimal. This is the outcome. Values run from 72.2 to 1208.2. Group means start near 180 in both arms at week 1 and reach roughly 900 in the vehicle arm and roughly 610 in the treated arm by week 5. |
| `body_weight_g` | number | Body weight of the animal that week, in grams, rounded to one decimal. Values run from 257.7 to 309.4, centred near 280. Recorded alongside the tumour measurement as a general health and tolerability check. |
| `cage` | text | Cage the animal was housed in, `cage_01` to `cage_12`. Constant within an animal. Two animals share each cage, and both share a treatment group. |

Column headers are lowercase words joined by underscores.

## Spread built into the data

The simulation was built so that animals differ substantially from one another, with roughly 120
cubic millimetres of between-animal spread by the final week, and so that repeat measurements on the
same animal vary by about 60 cubic millimetres around that animal's own growth path. The
between-animal part is much the larger of the two, which is the reason the five measurements from
one animal cannot be treated as five independent observations.

Because 12 animals per group is a small draw, `make_data.py` centres and rescales each set of random
draws to its intended mean and standard deviation before use. The realised summary statistics
therefore sit closer to the design values than a fresh sample of this size normally would, and the
residuals are not an independent random sample. This is documented in the script's opening comment.
