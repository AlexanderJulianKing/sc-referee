# Accelerated versus standard early mobilisation after elective heart valve surgery

## Summary

Seventy patients undergoing elective heart valve surgery were enrolled and each
followed exactly one of two early mobilisation schedules, 35 per schedule. The
standard schedule has patients first sit out of bed on the first postoperative
day. The accelerated schedule begins mobilisation on the evening of surgery.
Every patient was assessed once, on the day of discharge, on the five outcomes
the protocol declared in advance. Two of the five outcomes met the protocol
significance threshold: six-minute walk distance at discharge and days from
surgery to independent stair climbing, both favouring the accelerated schedule.

## Data description

The analysis reads a single table, `mobilisation_trial.csv`, with a header row
and 70 data rows.

**One row is one enrolled patient**: the schedule that patient followed and that
patient's five protocol outcomes, recorded at the single day-of-discharge
assessment. Each patient appears exactly once. Every cell is filled; there are
no blanks.

| Column | Unit | What it holds |
| --- | --- | --- |
| `patient_id` | none | Patient identifier, `P01` to `P70`, unique across the file. |
| `group` | none | The mobilisation schedule followed, with exactly two possible entries: `standard` or `accelerated`. |
| `walk_distance_m` | metres | Outcome 1. Six-minute walk distance at discharge. |
| `length_of_stay_days` | days | Outcome 2. Postoperative hospital length of stay, from the day of surgery to the day of discharge. |
| `mip_cmh2o` | centimetres of water | Outcome 3. Maximal inspiratory pressure at discharge, recorded as a positive number. |
| `pain_nrs` | points on a 0 to 10 scale | Outcome 4. Pain at rest on the day of discharge, on the numerical rating scale (0 is no pain, 10 is worst imaginable). |
| `days_to_stairs` | days | Outcome 5. Days from surgery to the first independent stair climb. |

The five outcome columns appear in the order the protocol declared them.

## Methods

The patient is the unit of analysis. Each of the five declared outcomes was
compared between the two schedules with a two-sample Welch t-test on the patient
values, which does not assume the two schedules share a variance. Group means
and the mean difference (accelerated minus standard) are reported alongside the
two-sided p-value.

**The five declared outcomes form one family.** They were declared together, in
a fixed order, before enrolment, and they are all read from the same
day-of-discharge assessment of the same patients, so testing all five at the
conventional five percent level would inflate the chance of at least one false
positive across the family. The protocol therefore fixed a Bonferroni-corrected
per-outcome level: the family-wise level of 0.05 divided by the family size of
five gives 0.05 / 5 = 0.01. That corrected level of 0.01 was written into the
protocol as a fixed number before any patient was enrolled.

Because the correction was settled at the protocol stage, the analysis script
carries out no correction arithmetic of its own. It holds 0.01 as a fixed
protocol constant and compares each of the five p-values with it, declaring an
outcome significant only when its p-value falls below 0.01. The correction
arithmetic appears in this report and nowhere else. No p-value is adjusted and
no level is recomputed during the analysis.

## Results

Thirty-five patients followed each schedule and all 70 contributed a value to
every outcome, so no patient was excluded from any comparison. Results are given
in the declared order. Values are means, with the standard deviation in
parentheses.

| # | Outcome (unit) | Standard (n = 35) | Accelerated (n = 35) | Difference | p | Verdict at p < 0.01 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Six-minute walk distance at discharge (m) | 291.7 (54.1) | 344.9 (56.8) | +53.2 | 0.00015 | Significant |
| 2 | Postoperative hospital length of stay (days) | 8.00 (2.60) | 7.03 (1.79) | -0.97 | 0.074 | Not significant |
| 3 | Maximal inspiratory pressure at discharge (cmH2O) | 56.8 (12.7) | 64.8 (13.5) | +8.1 | 0.012 | Not significant |
| 4 | Pain at rest on day of discharge (NRS 0-10) | 3.43 (1.82) | 2.80 (1.28) | -0.63 | 0.100 | Not significant |
| 5 | Days from surgery to independent stair climbing (days) | 6.40 (2.09) | 4.94 (1.68) | -1.46 | 0.0020 | Significant |

Outcome 1, six-minute walk distance, was 53 metres greater on the accelerated
schedule (p = 0.00015), comfortably below the protocol threshold. Outcome 5,
days to independent stair climbing, was 1.5 days shorter on the accelerated
schedule (p = 0.0020), also below the threshold.

The remaining three outcomes all moved in the direction that favours the
accelerated schedule but did not meet the protocol threshold. Maximal
inspiratory pressure was 8.1 cmH2O higher on the accelerated schedule with
p = 0.012, which sits above the protocol level of 0.01 and is therefore reported
as not significant. That outcome would have been called significant against an
uncorrected five percent level, which is exactly the kind of borderline call the
protocol fixed the corrected level in advance to settle. Length of stay was
about one day shorter (p = 0.074) and pain at rest about 0.6 points lower
(p = 0.100); neither difference is separable from chance at the protocol level.

## Conclusion

The accelerated schedule showed a clear advantage on two of the five declared
outcomes, both of them functional measures of recovery: patients walked
substantially further at discharge and reached independent stair climbing about
a day and a half sooner. The other three outcomes pointed the same way but did
not clear the protocol threshold, and this trial of 70 patients is not large
enough to settle them.

On this evidence the accelerated schedule is reasonable to adopt as the unit's
default, since it improves functional recovery at discharge with no outcome
favouring the standard schedule. The case rests on functional recovery rather
than on shorter admissions, so claims about length of stay, respiratory muscle
strength, or pain should not be made from this trial. A larger trial powered for
length of stay, together with safety monitoring during the adoption, would be
the sensible next step.
