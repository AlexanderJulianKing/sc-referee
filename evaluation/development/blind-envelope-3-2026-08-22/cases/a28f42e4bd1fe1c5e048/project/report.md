# Intensive dietary sodium counselling and ambulatory systolic blood pressure in stage 3 chronic kidney disease

## Data description

The analysis uses a single comma-separated file, `ckd_sodium_trial_bp.csv`, with one header row and
144 data rows.

**One row is one blood pressure measurement: the 24-hour ambulatory systolic average recorded at one
of a participant's six monthly follow-up visits.**

The file has six columns.

| Column | Type | Units / values | Description |
| --- | --- | --- | --- |
| `participant_id` | text | `P01`-`P24` | Identifier for the enrolled participant the measurement was taken from. |
| `trial_arm` | text | `usual_advice`, `intensive_counselling` | Randomised treatment assignment. |
| `visit_number` | integer | 1-6 | Which of the six monthly follow-up visits the measurement was taken at. |
| `systolic_bp_mmhg` | number | mmHg | The outcome: the 24-hour ambulatory systolic blood pressure average for that visit. Observed range 105.5 to 155.6 mmHg. |
| `age_years` | integer | years | Participant age at enrolment. Observed range 48 to 77 years. |
| `baseline_egfr_ml_min_1_73m2` | number | mL/min/1.73 m^2 | Baseline estimated glomerular filtration rate at enrolment. Observed range 35.1 to 56.0. |

There are no missing values. All 144 rows are complete on all six columns, and every one of the six
visit numbers is present for every participant.

## Design

This was a single-centre nutrition trial in adults living with stage 3 chronic kidney disease.
Twenty-four adults were enrolled and randomised 1:1: 12 to intensive dietary sodium counselling and
12 to the clinic's usual dietary advice. Each participant then attended six monthly follow-up
visits, and a 24-hour ambulatory systolic blood pressure average was recorded at each visit. Six
visits for each of 24 participants gives the 144 blood pressure measurements analysed here, 72 in
each arm.

The two arms were similar on the stable participant characteristics recorded at enrolment. Mean age
was 61.6 years in the usual-advice arm and 61.1 years in the intensive-counselling arm, and mean
baseline eGFR was 45.5 and 43.4 mL/min/1.73 m^2 respectively.

## Methods

The outcome was the 24-hour ambulatory systolic blood pressure average in mmHg. The two trial arms
were compared with an independent two-sample t-test on `systolic_bp_mmhg`, with each recorded
measurement entered as one observation. The sample size for the test is therefore the total number
of measurements, 144, split 72 and 72 between the arms. Group means and standard deviations were
computed on the same all-measurements basis, using the sample standard deviation with n - 1 degrees
of freedom.

The test was two-sided, and the difference is reported as intensive counselling minus usual advice,
so a negative difference means lower blood pressure under intensive counselling. Analyses were run
in Python 3 with pandas 2.0.3 and SciPy 1.9.1. The complete analysis is in `analysis.py` at the root
of the project, which reads the data file and prints every number reported below.

## Results

| Arm | n | Mean systolic BP (mmHg) | SD (mmHg) |
| --- | --- | --- | --- |
| Usual advice | 72 | 134.02 | 8.24 |
| Intensive counselling | 72 | 128.09 | 11.19 |
| **Total** | **144** | | |

Mean 24-hour ambulatory systolic blood pressure was 128.09 mmHg under intensive counselling and
134.02 mmHg under usual advice, a difference of -5.93 mmHg in favour of intensive counselling.

The independent two-sample t-test on all 144 measurements gave t = -3.62 on 142 degrees of freedom,
p = 0.000413.

## Conclusion

Intensive dietary sodium counselling lowered 24-hour ambulatory systolic blood pressure relative to
the clinic's usual dietary advice. The mean was 5.93 mmHg lower in the intensive-counselling arm,
and the difference reached statistical significance at the conventional 5% level (p = 0.000413). A
reduction of roughly 6 mmHg in ambulatory systolic pressure is a clinically meaningful amount in
stage 3 chronic kidney disease, and these results support offering intensive sodium counselling to
this population.
