# End-of-programme evaluation: motor-control exercise versus structured walking

Community physiotherapy service. Chronic non-specific low back pain pathway.

## What we did

We compared our two eight-week programmes for adults with chronic non-specific low back
pain: the supervised motor-control exercise programme and the structured walking programme
of matched contact time. Sixty-four adults took part, thirty-two allocated to each
programme, and all sixty-four attended a single end-of-programme assessment day. The unit
of the evaluation is the participant.

The evaluation plan declared four outcomes, in this fixed order: pain intensity,
Roland-Morris disability, average daily step count, and sit-to-stand repetitions. All four
are measured on every participant.

Each outcome was compared between the two programmes with a two-group Welch t-test. Because
the four outcomes were declared together as one family, the four raw p-values were adjusted
together, by the Holm-Bonferroni procedure, to hold the family-wise error rate at five
percent across the whole family. Every significance verdict below comes from the adjusted
p-value, not the raw one. The analysis is in `analysis.py` at the project root and reads
`back_pain_outcomes.csv`.

## Data description

The analysis input is `back_pain_outcomes.csv`: 64 data rows and a header row, six columns.

**What one row represents.** One participant, at their single end-of-programme assessment.
The row holds that person's identifier, the programme they were allocated to, and their four
declared outcome measurements from that assessment day. Each participant appears exactly
once, so 64 rows means 64 people. There are no repeated measures and no follow-up rows.
Every participant has a value in every outcome column, and the file contains no blank cells.

**Columns, in file order.**

| # | Column | Unit | What it holds |
| --- | --- | --- | --- |
| 1 | `participant_id` | text label, `P001` to `P064` | The participant identifier. Unique across the file. Carries no clinical meaning and no group information. |
| 2 | `group` | text, exactly two values: `motor_control`, `walking` | The eight-week programme the participant was allocated to. `motor_control` is the supervised motor-control exercise programme, `walking` is the structured walking programme of matched contact time. Thirty-two participants carry each value. |
| 3 | `pain_nrs` | points, 0 to 10 | Declared outcome 1. Average pain intensity over the past week on the 0 to 10 numerical rating scale, where 0 is no pain and 10 is the worst pain imaginable. Higher means more pain. |
| 4 | `rmdq_score` | points, 0 to 24 | Declared outcome 2. Roland-Morris disability questionnaire score, the count of the 24 items endorsed. Higher means more disability. |
| 5 | `daily_steps` | steps per day | Declared outcome 3. Average daily step count over the final week of the programme, from a waist-worn counter. Higher means more walking. Typical values in this population run from about 2500 to 14000 steps per day. |
| 6 | `sts_reps` | repetitions in 30 seconds | Declared outcome 4. Number of sit-to-stand repetitions completed in thirty seconds. Higher means better lower-limb function. Typical values run from about 6 to 20 repetitions. |

Columns 3 to 6 appear in the order the evaluation plan declared them.

One value needs flagging up front. Participant `P046`, in the walking programme, has a
`daily_steps` value of 39,784. That is far above anything an adult with chronic low back
pain reaches on foot in a day, and it is the pattern a waist-worn counter produces when it
is worn during a car journey or left attached to something else that moves. The value stays
in the file, and in the declared analysis, exactly as it came off the counter. Every other
field for that participant is an ordinary measurement.

## Results: the declared family of four outcomes

All four outcomes below form one family and were adjusted together. Verdicts are taken from
the adjusted p-values at the five percent family-wise level.

| # | Outcome | Motor-control mean | Walking mean | Raw p | Adjusted p | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Pain intensity (0-10 NRS) | 4.25 | 4.28 | 0.9270 | 0.9520 | Not significant |
| 2 | Roland-Morris disability (0-24) | 8.94 | 9.62 | 0.4760 | 0.9520 | Not significant |
| 3 | Daily step count (steps/day) | 6297.78 | 9772.34 | 0.0020 | 0.0080 | Significant |
| 4 | Sit-to-stand (reps in 30 s) | 12.62 | 11.78 | 0.1445 | 0.4335 | Not significant |

**1. Pain intensity.** Motor-control mean 4.25 points (SD 1.27, n = 32), walking mean 4.28
points (SD 1.44, n = 32), a difference of 0.03 points in favour of motor control. Welch
t(61.0) = -0.09, raw p = 0.9270, adjusted p = 0.9520. No difference between the programmes.

**2. Roland-Morris disability.** Motor-control mean 8.94 points (SD 4.15, n = 32), walking
mean 9.62 points (SD 3.49, n = 32), a difference of 0.69 points in favour of motor control.
Welch t(60.2) = -0.72, raw p = 0.4760, adjusted p = 0.9520. No difference between the
programmes. The gap is well inside the measurement noise on this scale.

**3. Daily step count.** Motor-control mean 6297.78 steps per day (SD 1367.51, n = 32),
walking mean 9772.34 steps per day (SD 5720.51, n = 32), a difference of 3474.56 steps per
day in favour of walking. Welch t(34.5) = -3.34, raw p = 0.0020, adjusted p = 0.0080.
Significant at the five percent family-wise level. This is the only declared outcome on
which the two programmes differ.

**4. Sit-to-stand repetitions.** Motor-control mean 12.62 repetitions (SD 2.03, n = 32),
walking mean 11.78 repetitions (SD 2.51, n = 32), a difference of 0.84 repetitions in favour
of motor control. Welch t(59.4) = 1.48, raw p = 0.1445, adjusted p = 0.4335. No difference
between the programmes.

Note that the step count standard deviation in the walking arm, 5720 steps, is inflated by
the single suspect counter reading described above. The section below shows what happens
without it.

## Robustness check: step count without the implausible counter reading

**This section is a robustness check. It is not an inferential result, it carries no verdict,
and it changes no conclusion in this report.** It sits outside the declared family of four,
so it is not adjusted for multiplicity. It was run once, on the step count outcome only, for
one purpose: to show that the family conclusion for step count does not hinge on one suspect
measurement. The step count conclusion of this evaluation remains the adjusted family result
reported above, adjusted p = 0.0080.

Excluding participant `P046` (walking programme, 39,784 steps per day) and re-running the
same two-group comparison on step count gives: motor-control mean 6297.78 steps per day
(SD 1367.51, n = 32), walking mean 8804.23 steps per day (SD 1680.25, n = 31), a difference
of 2506.44 steps per day in favour of walking. Welch t(57.8) = -6.48, unadjusted
p = 0.000000022.

Dropping the suspect reading lowers the walking mean by roughly 970 steps a day and cuts the
walking standard deviation from 5720 to 1680. The direction and the size of the step count
advantage for walking survive intact. The family conclusion for step count does not rest on
that one measurement.

## Conclusion

On the outcomes that matter most to the people we treat, the two programmes performed the
same. Pain intensity, disability and sit-to-stand capacity showed no difference between the
supervised motor-control programme and the structured walking programme once the four
declared outcomes were adjusted together. The one difference we found is in daily activity:
participants in the walking programme took about 3500 more steps a day at the end of the
eight weeks, and that finding holds up when the one suspect counter reading is set aside.

On this evidence the service should offer the structured walking programme as the default
option for adults with chronic non-specific low back pain, with the motor-control programme
retained for people who prefer supervised exercise or who need it for other clinical
reasons. The two programmes are matched on contact time and give equal pain and disability
results, and walking additionally leaves people more active day to day.

Two cautions belong with that recommendation. First, the walking programme trains the
behaviour that the step count measures, so some of the step count advantage reflects the
target of the programme rather than a broader gain in function. Second, this is a
single-day end-of-programme assessment with no follow-up, so it says nothing about whether
the activity difference persists after the eight weeks end. Both points are worth building
into the next round of the evaluation.
