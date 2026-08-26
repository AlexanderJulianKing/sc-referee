# Acoustic working condition and operator voice health

End-of-week voice outcomes in 46 full-shift telephone operators, open-plan
workstation versus acoustically treated booth.

## Study

The customer-service centre asked whether the acoustic environment of the
workstation affects the voice health of its telephone operators. Forty-six
operators working full shifts on the phones took part. Each operator was
assigned to exactly one of two working conditions for one full working week: an
ordinary open-plan workstation (`open_plan`, n = 23) or an acoustically treated
booth fitted with sound-absorbing panels (`treated_booth`, n = 23). The
occupational health nurse measured the same set of voice outcomes half-way
through the week and again at the end of the week. The values analysed here are
the end-of-week measurements.

The protocol declared five voice outcomes, in this fixed order: maximum
phonation time, jitter, speaking fundamental frequency, Vocal Fatigue Index
total score, and end-of-shift self-rated throat dryness.

## Data description

The analysis input is `voice_outcomes.csv`. **One row is one operator**: the
operator's identifier, the working condition that operator spent the full week
in, and that operator's five end-of-week voice measurements. Each operator
appears exactly once, so the file has a header row and 46 data rows, 23 per
condition. Every cell is filled; there are no blanks and no missing-value codes.

| Column | Unit / values | What it holds |
| --- | --- | --- |
| `operator_id` | text, `OP-01` ... `OP-46` | Identifier of the operator, unique within the file. Numbering follows enrolment order. |
| `group` | text, exactly two values: `open_plan`, `treated_booth` | The working condition the operator was assigned to for the full week. `open_plan` is the ordinary open-plan workstation; `treated_booth` is the acoustically treated booth with sound-absorbing panels. |
| `mpt_s` | seconds, one decimal | Outcome 1, maximum phonation time: how long the operator could sustain a vowel on one breath. Longer is healthier. Observed range 13.3-23.4 s. |
| `jitter_pct` | percent, two decimals | Outcome 2, jitter: cycle-to-cycle variation in vocal fold frequency. Lower is healthier. Observed range 0.30-1.28 %. |
| `sff_hz` | hertz, one decimal | Outcome 3, speaking fundamental frequency: the average pitch of the operator's speaking voice. Observed range 107.5-224.7 Hz. The pooled range is broad because the workforce includes both women (typically about 170-225 Hz) and men (typically about 100-145 Hz). |
| `vfi_total` | points on a 0-76 scale | Outcome 4, Vocal Fatigue Index total score. Higher means more vocal fatigue. Observed range 6-39 points. |
| `dryness_vas` | points on a 0-100 visual analogue scale | Outcome 5, self-rated throat dryness at the end of the shift. Higher means a drier throat. Observed range 11-64 points. |

The five outcome columns appear in the order the protocol declares them.
Operator sex is not recorded in the table, although it is a known determinant of
speaking fundamental frequency. The half-way-through measurements are not part
of this file.

## Analysis

The five outcomes are separate aspects of voice health and each was declared as
a question in its own right, so each was treated on its own terms. For each
outcome the two working conditions were compared with a standard two-group
comparison of the operator values: Welch's two-sample t-test, which does not
assume equal variances in the two conditions. Each outcome was judged against
the conventional five percent threshold and carries its own conclusion. No
multiple-comparison adjustment of any kind was applied. The analysis is in
`analysis.py`, which handles the outcomes one after another in the declared
order.

Differences below are reported as treated booth minus open plan, so a positive
difference means the booth group scored higher.

## Results

**Outcome 1 - maximum phonation time (`mpt_s`, seconds).** Open plan 18.79 s
(SD 2.32); treated booth 19.91 s (SD 2.27). Difference +1.12 s (95 % CI
-0.24 to +2.49); t = 1.66, p = 0.105. Not significant at the five percent
threshold.

**Outcome 2 - jitter (`jitter_pct`, percent).** Open plan 0.73 % (SD 0.23);
treated booth 0.68 % (SD 0.24). Difference -0.05 % (95 % CI -0.19 to +0.09);
t = -0.69, p = 0.492. Not significant.

**Outcome 3 - speaking fundamental frequency (`sff_hz`, hertz).** Open plan
169.72 Hz (SD 39.93); treated booth 167.56 Hz (SD 35.75). Difference -2.17 Hz
(95 % CI -24.70 to +20.37); t = -0.19, p = 0.847. Not significant. The wide
interval reflects the pooled male and female pitch ranges rather than
measurement noise.

**Outcome 4 - Vocal Fatigue Index total (`vfi_total`, points on 0-76).** Open
plan 24.43 points (SD 7.37); treated booth 15.30 points (SD 6.05). Difference
-9.13 points (95 % CI -13.14 to -5.12); t = -4.59, p = 0.000039. Significant at
the five percent threshold: operators in the treated booth reported markedly
less vocal fatigue.

**Outcome 5 - end-of-shift throat dryness (`dryness_vas`, points on 0-100).**
Open plan 43.39 points (SD 13.38); treated booth 33.70 points (SD 12.21).
Difference -9.70 points (95 % CI -17.31 to -2.08); t = -2.57, p = 0.014.
Significant at the five percent threshold: operators in the treated booth
reported a less dry throat at the end of the shift.

### Summary table

| # | Outcome | Open plan | Treated booth | Difference | p | At alpha = 0.05 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Maximum phonation time (s) | 18.79 | 19.91 | +1.12 | 0.105 | not significant |
| 2 | Jitter (%) | 0.73 | 0.68 | -0.05 | 0.492 | not significant |
| 3 | Speaking fundamental frequency (Hz) | 169.72 | 167.56 | -2.17 | 0.847 | not significant |
| 4 | Vocal Fatigue Index total (points) | 24.43 | 15.30 | -9.13 | 0.000039 | significant |
| 5 | Throat dryness VAS (points) | 43.39 | 33.70 | -9.70 | 0.014 | significant |

## Conclusion

Two of the five declared voice outcomes differed between the two working
conditions: the Vocal Fatigue Index total score and end-of-shift throat dryness.
Both differences favour the acoustically treated booth, and both are the
self-reported symptom outcomes. Operators in the booth scored about 9 points
lower on the Vocal Fatigue Index, roughly a third of the open-plan group mean
and a difference large enough to matter to an operator's working day, and about
10 points lower on the 0-100 dryness scale.

The three instrumental outcomes showed no difference at the five percent
threshold. Maximum phonation time ran about a second longer in the booth, in the
direction one would expect if the booth helped, but the confidence interval
still includes zero at this sample size. Jitter and speaking fundamental
frequency were essentially identical in the two conditions; for fundamental
frequency this is unsurprising, since the pooled male and female pitch ranges
dominate the spread and the study did not record sex, so a real condition effect
of a few hertz would be hard to see here.

For workstation policy, the results support acoustic treatment as a way to
reduce the vocal fatigue and throat dryness that operators feel by the end of a
shift, which is the burden they actually report and the one linked to absence
and voice complaints in this workforce. They do not yet show a measurable change
in laryngeal function over a single week. That is a reasonable basis for
extending treated booths to the operators with the heaviest phone loads or
existing voice complaints, together with continued monitoring.

Three limitations should be read alongside these results. First, the study
covers one working week, so it cannot speak to whether the symptom benefit
persists or whether instrumental measures shift over months. Second, the two
outcomes that differed are self-reported by operators who know which working
condition they were in, so expectation cannot be separated from a genuine
acoustic effect. Third, the five outcomes were each tested at the five percent
threshold with no adjustment for the number of comparisons, as the protocol
specified; readers weighing the two positive findings should keep the number of
comparisons in view, and the Vocal Fatigue Index result is the more robust of
the two.
