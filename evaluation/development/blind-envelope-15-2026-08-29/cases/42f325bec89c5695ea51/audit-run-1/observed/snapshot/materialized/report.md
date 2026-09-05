# Week-twelve comparison of a preservative-free and a preserved glaucoma eye drop

## Data

`data.csv` holds the week-twelve records for sixty patients with ocular hypertension. One row is
one patient, contributing one study eye, carrying that patient's allocated formulation and their
week-twelve value for each declared outcome. The columns are `patient_id`, the patient identifier,
text running `oht_01` to `oht_60`, no unit; `formulation`, the allocated group, text with exactly
two labels, `preservative_free` and `preserved`, no unit; `intraocular_pressure_mmhg`, intraocular
pressure in the study eye, in millimetres of mercury, recorded to the nearest whole mmHg;
`osdi_score_0_100`, the Ocular Surface Disease Index symptom score, in points on a 0 to 100 scale,
higher meaning more symptoms; `tear_film_breakup_time_s`, tear film break-up time, in seconds,
higher meaning a more stable tear film; `conjunctival_hyperaemia_grade_0_3`, conjunctival redness,
graded 0 to 3 in half-grade steps, higher meaning more redness; and `corneal_staining_score_0_15`,
corneal staining, in points on a 0 to 15 scale, higher meaning more staining. Every patient has a
value for every outcome.

## Design and declared outcomes

Thirty patients were allocated to the preservative-free formulation and thirty to the preserved
formulation, one study eye each. Every patient attended, and all week-twelve measurements were
taken by masked assessors. Five outcomes were declared in the protocol before allocation, in this
fixed order: intraocular pressure, OSDI score, tear film break-up time, conjunctival hyperaemia
grade, corneal staining score. They form one outcome family.

## How the comparison was done

Each outcome was compared between the two formulations with one two-sample test. Intraocular
pressure, OSDI score and tear film break-up time were compared with a Welch two-sample t-test,
which does not assume equal variances. Conjunctival hyperaemia and corneal staining, recorded on
coarse ordered grading scales, were compared with a Mann-Whitney U test. Because the five outcomes
form one declared family, all five p-values were collected and passed together in one
Holm-Bonferroni adjustment, controlling the family-wise error rate at the conventional 0.05 family
level. Every conclusion below rests on the adjusted p-value; raw values are given for transparency
only.

## Results

Both groups contain thirty patients. Figures are group means with standard deviations in brackets,
preservative-free first.

Intraocular pressure, 16.40 mmHg (2.47) against 17.20 mmHg (4.15), Welch t = -0.91, raw p = 0.3687,
adjusted p = 0.3687: the formulations are not separated at the 0.05 family level.

OSDI score, 13.54 points (9.85) against 25.00 points (9.23), Welch t = -4.65, raw p = 1.98e-05,
adjusted p = 9.88e-05: symptoms are lower on the preservative-free formulation, and the difference
holds at the 0.05 family level.

Tear film break-up time, 8.50 s (2.19) against 6.10 s (1.98), Welch t = 4.46, raw p = 3.81e-05,
adjusted p = 0.0002: break-up time is longer on the preservative-free formulation, and the
difference holds at the 0.05 family level.

Conjunctival hyperaemia grade, 0.87 (0.45) against 1.27 (0.50), median 1.00 in both groups,
Mann-Whitney U = 259, raw p = 0.0031, adjusted p = 0.0092: redness is lower on the
preservative-free formulation, and the difference holds at the 0.05 family level.

Corneal staining score, 2.03 points (1.54) against 2.63 points (1.43), Mann-Whitney U = 331, raw
p = 0.0718, adjusted p = 0.1436: the formulations are not separated at the 0.05 family level. The
raw p-value for this outcome falls below 0.05 while the adjusted one does not, and the conclusion
follows the adjusted value.

## Robustness check on intraocular pressure

Patient `oht_32` has a week-twelve intraocular pressure of 34 mmHg, recorded at a visit the site
later flagged as a suspected tonometer calibration problem; the value is kept in `data.csv` exactly
as recorded. As a separate robustness check, the intraocular pressure comparison alone was repeated
once with that patient excluded, leaving 59 patients: 16.40 mmHg (2.47) against 16.62 mmHg (2.72),
Welch t = -0.33, unadjusted p = 0.7457. This check sits outside the inferential analysis. Its
p-value was not entered into the family adjustment, it carries no significance verdict of its own,
and no conclusion above is restated on the basis of it. It shows only how much of the intraocular
pressure comparison rests on the flagged reading.

## What the study found

At week twelve the two formulations left intraocular pressure at a similar level, with no
difference demonstrated at the 0.05 family level. Where they differ is in ocular surface
tolerability. After adjusting the complete declared family for multiplicity, the preservative-free
formulation showed lower symptom scores, longer tear film break-up times and lower conjunctival
redness grades than the preserved formulation. Corneal staining did not differ at the 0.05 family
level.
