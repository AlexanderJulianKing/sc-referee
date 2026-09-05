# Centre-based versus home-based pulmonary rehabilitation: end-of-programme outcomes

Seventy-four adults with stable chronic obstructive pulmonary disease completed an eight-week
pulmonary rehabilitation programme, 37 in a supervised centre-based format and 37 in a home-based
format with remote support. Each patient was assessed once, at the end of the programme, on the four
outcomes the protocol declared in advance.

## Data description

The analysis reads a single file, `pulmonary_rehab_outcomes.csv`.

**One row represents one patient**, assessed a single time at the end of the eight-week programme.
Each patient appears exactly once, and every patient has a value in every column. The file has 74
data rows and no empty cells.

| Column | Type | What it holds |
| --- | --- | --- |
| `patient_id` | text | Study identifier for the patient, `PR-001` through `PR-074`, unique across the file. |
| `program_group` | text | Delivery format the patient was enrolled in. Exactly two values occur, `centre_based` and `home_based`, with 37 patients in each. |
| `six_min_walk_m` | integer | Six-minute walk distance in metres at end of programme. |
| `cat_score` | integer | COPD assessment test score on the 0 to 40 scale. Higher means worse symptom burden. |
| `quad_torque_nm` | decimal | Quadriceps isometric peak torque in newton metres. |
| `sit_to_stand_reps` | integer | Repetitions completed in the thirty-second sit-to-stand test. |

The four outcome columns are the declared family, in the order the protocol fixed: six-minute walk
distance, CAT score, quadriceps peak torque, sit-to-stand repetitions.

## Group summaries

Mean and sample standard deviation for each group on each outcome (n = 37 per group).

| Outcome | centre_based mean (SD) | home_based mean (SD) |
| --- | --- | --- |
| Six-minute walk distance (m) | 386.70 (50.94) | 363.89 (63.48) |
| CAT score (0-40, higher worse) | 19.59 (4.59) | 18.41 (6.03) |
| Quadriceps peak torque (Nm) | 86.52 (21.29) | 87.62 (18.71) |
| 30-second sit-to-stand (reps) | 14.81 (3.09) | 12.76 (3.55) |

## Statistical approach

Each of the four outcomes was compared between the two formats with a Welch two-sample t-test for
independent samples.

All four raw p-values were then collected in the declared protocol order and **the complete family of
four was adjusted together, in a single step**, by the Holm-Bonferroni step-down procedure. That
procedure controls the family-wise error rate, meaning the chance of calling even one of the four
outcomes significant when no real difference exists is held to 0.05 across the whole family, not 0.05
per outcome. No outcome was adjusted on its own or in a subset.

The adjustment was carried out by `pingouin.multicomp` from the pingouin package, version 0.6.1, a
specialist third-party Python statistics package. **Every significance verdict below comes only from
the adjusted p-values that pingouin returned**, compared against the family-wise level of 0.05. The
raw p-values are shown for transparency and were not used to decide anything.

## Results

Outcomes in declared order. "Difference" is the home-based mean minus the centre-based mean, so a
negative value means the home-based group scored lower.

| # | Outcome | Difference (home - centre) | t | Raw p | Adjusted p | Verdict at family-wise 0.05 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Six-minute walk distance (m) | -22.81 | 1.705 | 0.0927 | 0.2782 | not significant |
| 2 | CAT score (0-40, higher worse) | -1.19 | 0.955 | 0.3428 | 0.6856 | not significant |
| 3 | Quadriceps peak torque (Nm) | +1.10 | -0.235 | 0.8145 | 0.8145 | not significant |
| 4 | 30-second sit-to-stand (reps) | -2.05 | 2.653 | 0.0098 | 0.0394 | **significant** |

One of the four declared outcomes, the thirty-second sit-to-stand test, is significant after the
family-wise adjustment. Patients in the home-based format completed 2.05 fewer repetitions on
average than patients in the centre-based format.

The other three outcomes are not significant after adjustment. Six-minute walk distance is worth a
note on its own: its raw p-value of 0.0927 would not have reached 0.05 even without any adjustment,
so it is not a case of a finding being lost to the correction. The centre-based group walked 22.81 m
further on average, but that gap is within what this sample size and spread can produce by chance.

## Clinical conclusion

On three of the four declared outcomes, symptom burden, quadriceps strength and walk distance, this
study found no difference between the two delivery formats that survives proper control of the
family-wise error rate. On the fourth, the thirty-second sit-to-stand test, the centre-based format
did better by about two repetitions, and that difference does survive adjustment.

The home-based format with remote support therefore looks like a reasonable alternative for patients
who cannot attend a centre, with one caveat worth acting on: the sit-to-stand result suggests
home-based patients may end the programme with less functional lower-limb performance. A service
offering the home-based format should consider strengthening the lower-limb component and checking
sit-to-stand performance at discharge. Note also that "no significant difference" on the other three
outcomes is not the same as demonstrated equivalence. This study was not designed as a
non-inferiority trial, and with 37 patients per group it can only rule out fairly large differences.
