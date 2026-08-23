# Week-eight plaque induration thickness: new topical formulation vs vehicle cream

## Summary

A small randomised comparison in adults with chronic plaque psoriasis. Twenty-four patients took
part, twelve on the new topical formulation and twelve on the vehicle cream. Four target plaques on
different body sites were selected per patient and each was measured with a calliper after eight
weeks of treatment, giving 96 measured plaques. Mean week-eight induration thickness was 1.06 mm on
the active formulation and 1.55 mm on the vehicle, a difference of 0.49 mm in favour of the active
formulation (Welch two-sample t-test, t = -7.03, p = 3.5e-10).

## Data description

The single data table is `plaque_thickness.csv`, at the project root. It has 96 rows and 6 columns
and no missing values.

**One row is one target plaque on one patient, measured once with a calliper after eight weeks of
treatment.** Each patient contributed four plaques on four different body sites, so a patient
appears on four rows; `patient_id`, `treatment_arm`, `age_years` and `sex` repeat unchanged across
those rows, while `plaque_site` and `thickness_mm` differ.

| Column | Type | Units | Description |
|---|---|---|---|
| `patient_id` | text | — | Patient identifier, `PT01` through `PT24`. |
| `treatment_arm` | text | — | Assigned arm, either `active` (new topical formulation) or `vehicle` (vehicle cream). |
| `plaque_site` | text | — | Body site of the measured plaque: `elbow`, `forearm`, `knee`, `lower_back`, `scalp` or `shin`. |
| `thickness_mm` | number | millimetres | Plaque induration thickness at week eight, by calliper, to two decimal places. Range in this file 0.37 to 2.29 mm. |
| `age_years` | integer | years | Patient age at enrolment. Range in this file 25 to 66 years. |
| `sex` | text | — | Patient sex, `F` or `M`. 14 female and 10 male patients. |

Counts: 24 patients, 4 plaques each, 96 rows. Twelve patients (48 plaques) on the active
formulation and twelve patients (48 plaques) on the vehicle. Values are invented but realistic; no
real patients are involved.

## Methods

The endpoint is `thickness_mm` at week eight. The two treatment arms were compared with an
independent two-sample t-test using Welch's correction, so the arms are not assumed to share a
variance. The comparison was applied to every row of the table: each measured plaque is one
observation, giving n = 96 observations in total, 48 per arm.

Alongside the test, the analysis reports each arm's mean, standard deviation, minimum and maximum,
the mean difference with a 95% confidence interval, Cohen's d using the pooled standard deviation,
and the relative reduction against the vehicle arm. Mean thickness by body site within each arm is
tabulated as a description. The analysis is in `analysis.py`, run with Python 3 using pandas and
SciPy.

## Results

### Arm summaries, week-eight thickness

| Arm | Plaques (n) | Mean (mm) | SD (mm) | Min (mm) | Max (mm) |
|---|---|---|---|---|---|
| active | 48 | 1.060 | 0.317 | 0.37 | 1.77 |
| vehicle | 48 | 1.548 | 0.362 | 0.73 | 2.29 |

### Two-sample comparison

| Quantity | Value |
|---|---|
| Observations entering the comparison | 96 |
| Mean difference (active - vehicle) | -0.489 mm |
| 95% confidence interval for the difference | -0.627 to -0.351 mm |
| t statistic | -7.032 |
| Degrees of freedom (Welch) | 92.41 |
| p-value | 3.46e-10 |
| Cohen's d | -1.435 |
| Relative reduction vs vehicle | 31.6% |

At the conventional 5% level the difference between the arms is statistically significant.

### Mean thickness by body site

| Body site | active (mm) | vehicle (mm) |
|---|---|---|
| elbow | 1.07 | 1.47 |
| forearm | 0.94 | 1.52 |
| knee | 1.04 | 1.59 |
| lower_back | 1.09 | 1.66 |
| scalp | 1.01 | 1.61 |
| shin | 1.28 | 1.46 |

The active arm reads lower than the vehicle arm at all six body sites.

## Interpretation

After eight weeks of treatment, plaques treated with the new topical formulation were on average
0.49 mm thinner than plaques treated with the vehicle cream, a reduction of about 32% against the
vehicle. The 95% confidence interval runs from 0.35 mm to 0.63 mm, so the whole interval sits on the
side of benefit, and the smallest reduction the data are consistent with is still around a third of
a millimetre.

For a clinician, that is a visible flattening of the plaque. Calliper measurement of induration is
the component of a plaque score that patients notice most directly, and a shift of half a millimetre
on a baseline of roughly one and a half millimetres moves a typical target lesion from clearly
raised toward nearly flat. The effect size, Cohen's d of about 1.4, is large by the usual
convention, and the direction is consistent at every body site examined, including sites that are
often harder to treat such as the scalp and the lower back. Thickness on the active arm never
exceeded 1.77 mm, while the vehicle arm reached 2.29 mm.

The practical reading is that the new formulation produces a meaningful reduction in plaque
induration relative to its vehicle over eight weeks. This was a small single-clinic study with 24
patients, so the size of the benefit should be confirmed in a larger trial, and duration of response
beyond eight weeks was not assessed here.
