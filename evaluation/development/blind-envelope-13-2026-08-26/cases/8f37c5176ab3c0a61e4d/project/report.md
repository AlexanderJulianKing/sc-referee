# Recreational screen time and cardiometabolic measurements in 96 adolescents

A two-stage screen-and-confirm analysis of a school-based adolescent cohort.
All numbers below are produced by `analysis.py`, run from the project root
against `screen_time_cohort.csv`.

## Data

`screen_time_cohort.csv` holds 96 data rows plus one header row.

**What one row represents.** One row is one adolescent, aged 14 to 16. Each
adolescent was measured once at a single morning fasting visit, so a row holds
that adolescent's identifier, their recreational screen time group, the half of
the fixed random allocation they fall in, and their six outcome measurements
from that one visit. No adolescent appears twice.

**Columns**, in the order they appear in the file:

| Column | Meaning | Unit |
| --- | --- | --- |
| `participant_id` | Identifier for the adolescent, `ADO-001` through `ADO-096` | none |
| `screen_time_group` | Recreational screen time group, assigned in advance from four weeks of device-recorded screen use. Two values: `high`, `low` | none |
| `analysis_half` | Which half of the fixed random allocation the adolescent falls in. Two values: `discovery` (screening stage) and `validation` (confirmation stage) | none |
| `bmi_z_score` | Body mass index z-score for age and sex | none (z-score) |
| `waist_circumference_cm` | Waist circumference | centimetres |
| `fasting_insulin_miu_l` | Fasting insulin | milli-international units per litre |
| `fasting_triglycerides_mmol_l` | Fasting triglycerides | millimoles per litre |
| `hdl_cholesterol_mmol_l` | HDL cholesterol | millimoles per litre |
| `alt_u_l` | Alanine aminotransferase | units per litre |

The six outcome columns are stored in the order the outcomes were declared in
the analysis plan.

The cohort is balanced: 48 high and 48 low screen time adolescents, and 48
adolescents in each analysis half, with 24 high and 24 low in the discovery half
and 24 high and 24 low in the validation half. There are no blank cells.

## Method

Every comparison in both stages uses the same test: Welch's two-sample t-test
comparing the high screen time group against the low screen time group, with the
difference reported as high minus low.

The analysis runs in two stages that use non-overlapping halves of the cohort.
Stage one screens all six declared outcomes in the discovery half. Stage two
tests only the outcomes carried forward, in the validation half, at a
significance level adjusted for how many outcomes were carried forward.

## Stage one: screening in the discovery half

Screening rule: an outcome is carried forward to stage two if its unadjusted
discovery-half p-value is below 0.10. All six declared outcomes were screened.

Discovery half, 24 high and 24 low.

| Outcome | Mean high | Mean low | Difference | t | p | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| BMI z-score | 0.593 | 0.059 | +0.534 | 2.115 | 0.0398 | carried forward |
| Waist circumference (cm) | 80.288 | 76.117 | +4.171 | 1.604 | 0.1160 | dropped |
| Fasting insulin (mIU/L) | 13.958 | 10.125 | +3.833 | 3.365 | 0.0018 | carried forward |
| Fasting triglycerides (mmol/L) | 1.164 | 0.948 | +0.217 | 2.517 | 0.0164 | carried forward |
| HDL cholesterol (mmol/L) | 1.209 | 1.397 | -0.188 | -2.450 | 0.0182 | carried forward |
| Alanine aminotransferase (U/L) | 26.325 | 20.146 | +6.179 | 2.624 | 0.0118 | carried forward |

Five of the six outcomes were carried forward: BMI z-score, fasting insulin,
fasting triglycerides, HDL cholesterol, and alanine aminotransferase. Waist
circumference was dropped.

These discovery-half numbers are screening output. They are not findings, and
none of them is reported here as a confirmed difference.

## Stage two: confirmation in the validation half

Five outcomes entered stage two. The confirmatory level was therefore adjusted
by Bonferroni over those five outcomes: 0.05 / 5 = 0.010000.

Validation half, 24 high and 24 low. No adolescent in this half contributed to
the screening stage.

| Outcome | Mean high | Mean low | Difference | t | p | Decision at 0.010000 |
| --- | --- | --- | --- | --- | --- | --- |
| BMI z-score | 0.715 | 0.356 | +0.359 | 1.383 | 0.1732 | not confirmed |
| Fasting insulin (mIU/L) | 13.633 | 10.067 | +3.567 | 2.359 | 0.0226 | not confirmed |
| Fasting triglycerides (mmol/L) | 1.261 | 1.116 | +0.145 | 1.302 | 0.1998 | not confirmed |
| HDL cholesterol (mmol/L) | 1.173 | 1.378 | -0.205 | -2.099 | 0.0414 | not confirmed |
| Alanine aminotransferase (U/L) | 23.025 | 18.529 | +4.496 | 2.049 | 0.0479 | not confirmed |

None of the five outcomes reached the adjusted level of 0.010000. Zero of the
five outcomes tested in stage two were confirmed.

Every conclusion in this report rests on the validation half alone. The
discovery half decided only which outcomes were worth testing; it contributed
nothing to what the study claims. An outcome that looked separated in the
discovery half but did not reach the adjusted level in the validation half is
reported as not confirmed, not as a weaker or borderline finding.

## Conclusion

In this cohort of 96 adolescents, the confirmatory stage did not establish a
difference between the high and low recreational screen time groups on any
cardiometabolic measurement. Five outcomes passed discovery screening and were
tested in the validation half at an adjusted level of 0.010000, and none of them
met it. The validation-half differences all run in the direction the screening
stage suggested, with the high screen time group higher on BMI z-score, fasting
insulin, triglycerides, and alanine aminotransferase, and lower on HDL
cholesterol, but the study reports no confirmed association between recreational
screen time and cardiometabolic measurements in these adolescents. Waist
circumference was never carried into the confirmatory stage, so this study makes
no claim about it either.
