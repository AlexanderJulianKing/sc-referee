# Data description

## File

`grip_strength.csv` — one comma-separated file, 104 data rows plus one header row.
The values are simulated, not measured. They were produced by `make_data.py`
(standard library only) with the fixed seed `20260867`, so the file can be
reproduced exactly by running that script again.

## What one row represents

One row is **one maximal handgrip trial performed by one volunteer**. Each
volunteer completed four trials in a single testing session, separated by short
rests, so each volunteer contributes four rows. The file therefore holds several
rows per volunteer, and any comparison between the two programmes has to reduce
those four rows to a single value per volunteer before treating volunteers as
independent units.

## Units and counts

- 26 volunteers, each with 4 trials, giving 104 rows.
- 13 volunteers followed the **heavy** programme (twice-weekly heavy resistance).
- 13 volunteers followed the **moderate** programme (three-times-weekly moderate load).
- Sex split: 7 male and 6 female volunteers in each group.
- The unit of analysis is the volunteer (n = 13 per group), not the trial.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `volunteer_id` | text | Identifier for the volunteer. `H01`–`H13` for the heavy programme, `M01`–`M13` for the moderate programme. Repeats across the four rows belonging to that volunteer. |
| `programme` | text | Training programme the volunteer followed: `heavy` or `moderate`. Constant within a volunteer. |
| `trial_number` | integer | Which of the four trials in the testing session this row records: 1, 2, 3, or 4, in the order performed. |
| `peak_force_kg` | number | Peak handgrip force recorded on that trial, in kilograms, rounded to one decimal place. This is the outcome variable. |
| `sex` | text | Volunteer's sex: `female` or `male`. Constant within a volunteer. |
| `body_mass_kg` | number | Volunteer's body mass in kilograms, rounded to one decimal place. Measured once, so it is constant within a volunteer. |

## How the values were generated

Each volunteer was given one underlying strength level drawn around the
programme mean (44.5 kg for heavy, 41.0 kg for moderate) with a between-volunteer
standard deviation of 7 kg. Each of that volunteer's four trials was then drawn
around their own level with a within-volunteer standard deviation of 1.8 kg,
minus a fatigue drift of 0.35 kg for each trial after the first. Volunteers
therefore differ from each other far more than a volunteer's own trials differ
from one another, which is the reason the four trials cannot be treated as four
independent observations.

Body mass was drawn separately by sex (female: mean 66 kg, SD 8.5; male: mean
79 kg, SD 9.5) and is independent of grip force in this simulation.

## Realised values in the file

These are the numbers actually present in `grip_strength.csv`, computed from the
per-volunteer trial averages:

- Heavy programme: mean 44.03 kg, standard deviation 6.60 kg (n = 13).
- Moderate programme: mean 40.28 kg, standard deviation 6.55 kg (n = 13).
- Average within-volunteer standard deviation across the four trials: 1.74 kg.
- Trial means across all 26 volunteers, trial 1 to trial 4: 43.02, 42.04, 42.03,
  41.53 kg, showing the small downward fatigue drift.
- Peak force ranges from 28.8 to 55.1 kg; body mass ranges from 46.2 to 100.4 kg
  (mean 71.5 kg).
